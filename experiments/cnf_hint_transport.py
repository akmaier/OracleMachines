"""Turn parent implication traces into portable, independently checked core hints.

This is a proof-transport experiment, not an integrated discovery policy. A hint
is accepted only if its negation has a checked unit-conflict trace on the exact
child core. Parent provenance is useful for discovery, not required for trust.
"""
from collections import Counter
import json
import sqlite3
import time

from experiments.cnf_learning_core import check_core_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize
from experiments.cnf_learning_core import CoreLearningInventory
from experiments.cnf_fused_conditioning import FusedShortestClauseInventory
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import discover_equivalence_probes, check_equivalence_probes, substitute_block
from experiments.cnf_residual_dag import components, restrict, holds


def _validate(core, clause, counts):
    canonical, names = normalize(core, counts)
    if encode(core) != encode(canonical) or names != tuple(range(1, len(names)+1)):
        raise ValueError('Hint source must be the exact normalized core')
    if (any(type(l) is not int or not l or not 1 <= abs(l) <= len(names) for l in clause)
            or list(clause) != sorted(set(clause)) or any(-l in clause for l in clause)):
        raise ValueError('Invalid core hint clause')


def check_rup(core, clause, proof, counts):
    """Check a unit refutation under the negation of this exact clause.

No parent proof, hash identity, fixed-point claim or search result is trusted.
Reason indices refer directly to the normalized core, never a restricted list.
"""
    _validate(core, clause, counts)
    if not isinstance(proof, dict) or set(proof) != {'units', 'conflict'}:
        raise ValueError('Invalid core hint proof fields')
    assigned = {abs(l): l < 0 for l in clause}
    if not isinstance(proof['units'], list):
        raise ValueError('Invalid hint unit sequence')
    for entry in proof['units']:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError('Invalid hint unit entry')
        lit, cid = entry
        if (type(lit) is not int or not lit or abs(lit) in assigned or
                type(cid) is not int or not 0 <= cid < len(core)):
            raise ValueError('Invalid hint unit reason')
        reason = core[cid]
        counts['hint_check_literals'] += len(reason)
        if lit not in reason or any(abs(other) not in assigned or assigned[abs(other)] == (other > 0)
                                   for other in reason if other != lit):
            raise ValueError('Hint step is not forced by its core')
        assigned[abs(lit)] = lit > 0
    conflict = proof['conflict']
    if type(conflict) is not int or not 0 <= conflict < len(core):
        raise ValueError('Invalid hint conflict index')
    counts['hint_check_literals'] += len(core[conflict])
    if any(abs(l) not in assigned or assigned[abs(l)] == (l > 0) for l in core[conflict]):
        raise ValueError('Hint trace does not refute its negation')
    counts['verified_core_hints'] += 1


def _scan_clause(core, cid, assigned, units, counts):
    clause = core[cid]; counts['hint_search_literals'] += len(clause)
    if any(assigned.get(abs(l)) == (l > 0) for l in clause):
        return 'satisfied'
    remaining = [l for l in clause if abs(l) not in assigned]
    if not remaining:
        return 'conflict'
    if len(remaining) == 1:
        lit = remaining[0]; assigned[abs(lit)] = lit > 0; units.append([lit, cid])
        return 'unit'
    return 'open'


def discover_rup(core, clause, counts):
    """Fresh scan-based control, with the same independently checked output."""
    _validate(core, clause, counts)
    assigned = {abs(l): l < 0 for l in clause}; units = []
    while True:
        before = len(units)
        for cid in range(len(core)):
            if _scan_clause(core, cid, assigned, units, counts) == 'conflict':
                return dict(units=units, conflict=cid)
        if len(units) == before:
            return None


def transport_hints(cnf, result, probe_limit, learn_limit, counts):
    """Check parent evidence, translate reason prefixes, then check core-only RUP.

Untranslatable hints remain explicit misses; there is no hidden fresh-search
fallback. Previously retained parent proofs and all older archives stay intact.
"""
    raw, fixed = check_core_probes(cnf, result, probe_limit, learn_limit, counts)
    core, names = normalize(raw, counts)
    output = dict(core=core, hints=[], omissions=[])
    if result['status'] != 'learned' or any(not c for c in core):
        return output
    continuation = result['continuation']
    mapping = (dict(continuation['witness']['mapping'])
               if continuation['status'] == 'equivalence' else {})
    rename = {v:i for i,v in enumerate(names, 1)}

    def transformed(clause):
        counts['hint_transport_literals'] += len(clause)
        mapped = [mapping.get(abs(l), abs(l))*(1 if l > 0 else -1) for l in clause]
        if any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in mapped):
            return None, 'satisfied'
        remaining = {l for l in mapped if abs(l) not in fixed}
        if any(-l in remaining for l in remaining):
            return None, 'tautology'
        if any(abs(l) not in rename for l in remaining):
            return None, 'outside_core'
        return tuple(sorted(rename[abs(l)]*(1 if l > 0 else -1) for l in remaining)), None

    index = {c:i for i,c in enumerate(core)}
    translated = [transformed(c)[0] for c in cnf]
    seen = set()
    for bi, hint in enumerate(result['batch']):
        clause, omitted = transformed(hint['clause'])
        if omitted or clause in index or clause in seen:
            output['omissions'].append(dict(batch_index=bi, reason=omitted or ('explicit' if clause in index else 'duplicate')))
            continue
        seen.add(clause)
        attempt = result['attempts'][hint['attempt']]
        assumption = attempt['variable']*(1 if attempt['value'] else -1)
        # Parent certificates index restrict(cnf, assumption), whose satisfied
        # clauses were removed. Reconstruct that index map before transporting.
        branch_indices = [i for i,c in enumerate(cnf) if assumption not in c]
        counts['hint_branch_map_literals'] += sum(map(len, cnf))
        prefix = attempt['certificate']['units'][:hint['unit']+1]
        assigned = {abs(l): l < 0 for l in clause}; units = []; proof = None
        for _, old_reason in prefix:
            counts['hint_transported_reasons'] += 1
            projected = translated[branch_indices[old_reason]]
            if projected is None:
                continue
            cid = index[projected]
            if _scan_clause(core, cid, assigned, units, counts) == 'conflict':
                proof = dict(units=units, conflict=cid)
                break
        if proof is None:
            output['omissions'].append(dict(batch_index=bi, clause=clause, reason='trace_did_not_refute'))
            counts['hint_transport_misses'] += 1
            continue
        check_rup(core, clause, proof, counts)
        output['hints'].append(dict(batch_index=bi, clause=clause, proof=proof))
    return output


class CoreHintStore:
    """Append-only exact-core proof storage; every lookup checks the saved proof."""
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(path); self.counts = Counter()
        self.db.execute('CREATE TABLE IF NOT EXISTS cnf_core_hints_v1 (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.commit()

    def close(self):
        self.db.close()

    def key(self, core, clause):
        key = encode(['core-rup-v1', core, clause])
        self.counts['hint_key_bytes'] += len(key.encode())
        return key

    def get(self, core, clause):
        key = self.key(core, clause)
        row = self.db.execute('SELECT payload FROM cnf_core_hints_v1 WHERE id=?', (key,)).fetchone()
        self.counts['hint_lookups'] += 1
        if row is None:
            return None
        record = json.loads(row[0]); self.counts['hint_read_bytes'] += len(row[0].encode())
        if (not isinstance(record, dict) or set(record) != {'core','clause','proof'} or
                encode(record['core']) != encode(core) or encode(record['clause']) != encode(clause)):
            raise ValueError('Invalid exact core-hint binding')
        check_rup(core, clause, record['proof'], self.counts)
        return record['proof']

    def put(self, core, clause, proof):
        check_rup(core, clause, proof, self.counts)
        if self.get(core, clause) is not None:
            return
        key = self.key(core, clause)
        payload = encode(dict(core=core, clause=clause, proof=proof))
        with self.db:
            self.db.execute('INSERT INTO cnf_core_hints_v1 VALUES (?,?)', (key,payload))
        self.counts['hint_inserted'] += 1
        self.counts['hint_serialized_bytes'] += len(key.encode())+len(payload.encode())

    def audit(self):
        count = 0
        for key,payload in self.db.execute('SELECT id,payload FROM cnf_core_hints_v1'):
            record = json.loads(payload)
            if key != self.key(record['core'],record['clause']):
                raise ValueError('Incorrect saved hint identity')
            self.get(record['core'], record['clause']); count += 1
        return count

    def storage(self):
        count,size = self.db.execute('SELECT count(*),coalesce(sum(length(CAST(id AS BLOB))+length(CAST(payload AS BLOB))),0) FROM cnf_core_hints_v1').fetchone()
        return dict(hints=count, logical_bytes=size)


class HintAssistedInventory(CoreLearningInventory):
    """Explicit one-generation hint plans; ordinary descendant plans stay intact.

Only inspect_hints opts into the extra bounded pass. Its persistent identity
includes the complete ordered hint set and policy. This is not an implicit,
history-dependent mutation of the ordinary core planner or solver.
"""
    def __init__(self, archive=':memory:', **kwargs):
        super().__init__(archive, **kwargs)
        # Share this connection, including in-memory databases.
        self.hints = CoreHintStore.__new__(CoreHintStore)
        self.hints.db = self.db; self.hints.counts = Counter()
        self.db.execute('CREATE TABLE IF NOT EXISTS cnf_core_hints_v1 (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS cnf_hint_plans_v1 (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.commit()

    def _hint_key(self, core, clauses, depth):
        key = encode(['hint-plan-core-choices-v1', self.config, core, clauses, depth])
        self.counts['hint_plan_key_bytes'] += len(key.encode())
        return key

    def _hint_prepared(self, core):
        core = tuple(tuple(c) for c in core)
        profile = FusedShortestClauseInventory._profile(self, core)
        groups = components(core, self.counts) if self.config['decompose'] else [core]
        return profile, groups

    def _hint_target(self, core, clauses, result):
        if result == dict(status='skipped'):
            return core, {}
        choices = probe_choices(core, self.config['probe_limit'], self.counts)
        augmented = tuple(tuple(c) for c in core)+tuple(tuple(c) for c in clauses)
        target,fixed = check_equivalence_probes(augmented,result,self.config['probe_limit'],self.counts,_choices=choices)
        if result['status']=='clear':
            return core, {}
        if any(not c for c in target):
            return ((),), fixed
        target = (substitute_block(core,result['witness'],self.counts)
                  if result['status']=='equivalence' else restrict(core,fixed,self.counts))
        if not {abs(l) for c in target for l in c} < {abs(l) for c in core for l in c}:
            raise ValueError('Hint rewrite must reduce original core support')
        return target,fixed

    def _check_hint_plan(self, key, plan):
        if set(plan) != {'core','clauses','depth','profile','probing','edge','summary'}:
            raise ValueError('Invalid hint plan fields')
        core,clauses,depth = plan['core'],plan['clauses'],plan['depth']
        if type(depth) is not int or not 0 <= depth <= self.config['max_depth']:
            raise ValueError('Invalid hint plan depth')
        if len(clauses)>self.config['learn_limit'] or len({encode(c) for c in clauses})!=len(clauses):
            raise ValueError('Invalid hint context size')
        canonical,_=normalize(core,self.counts)
        if encode(canonical)!=encode(core) or key != self._hint_key(core,clauses,depth):
            raise ValueError('Invalid hint context identity')
        for clause in clauses:
            if self.hints.get(core,clause) is None:
                raise ValueError('Missing portable hint proof')
        profile,groups = self._hint_prepared(core)
        if encode(profile)!=encode(plan['profile']):
            raise ValueError('Incorrect core recognition profile')
        enabled = bool(clauses) and self._probe_enabled(profile,groups)
        if (plan['probing'].get('status')=='skipped') == enabled:
            raise ValueError('Hint pass violates recognition priority')
        target,_ = self._hint_target(core,clauses,plan['probing'])
        self._check_edge(plan['edge'],target,depth)
        if encode(plan['summary'])!=encode(self._summary([plan['edge']])):
            raise ValueError('Incorrect hint plan summary')
        self.counts['verified_hint_plans'] += 1

    def inspect_hints(self, core, hints, depth):
        start=time.perf_counter();self.counts=Counter();self.hints.counts=Counter()
        canonical,_=normalize(core,self.counts)
        if encode(canonical)!=encode(core):
            raise ValueError('Expected a normalized child core')
        clauses=[list(h['clause']) for h in hints]
        if type(depth) is not int or not 0<=depth<=self.config['max_depth']:
            raise ValueError('Invalid hint plan depth')
        if len(clauses)>self.config['learn_limit'] or len({encode(c) for c in clauses})!=len(clauses):
            raise ValueError('Invalid hint context size')
        for hint in hints:self.hints.put(core,hint['clause'],hint['proof'])
        key=self._hint_key(core,clauses,depth)
        row=self.db.execute('SELECT payload FROM cnf_hint_plans_v1 WHERE id=?',(key,)).fetchone()
        if row is not None:
            plan=json.loads(row[0]);self._check_hint_plan(key,plan)
        else:
            profile,groups=self._hint_prepared(core)
            probing=dict(status='skipped')
            if clauses and self._probe_enabled(profile,groups):
                augmented=tuple(tuple(c) for c in core)+tuple(tuple(c) for c in clauses)
                choices=probe_choices(core,self.config['probe_limit'],self.counts)
                probing=discover_equivalence_probes(augmented,self.config['probe_limit'],self.counts,_choices=choices)
            target,_=self._hint_target(core,clauses,probing)
            edge=self._edge(target,depth)
            plan=dict(core=core,clauses=clauses,depth=depth,profile=profile,probing=probing,
                      edge=edge,summary=self._summary([edge]))
            self._check_hint_plan(key,plan);payload=encode(plan)
            with self.db:self.db.execute('INSERT INTO cnf_hint_plans_v1 VALUES (?,?)',(key,payload))
            self.counts['hint_plans_inserted']+=1
            self.counts['hint_plan_serialized_bytes']+=len(key.encode())+len(payload.encode())
        return dict(key=key,plan=plan,seconds=time.perf_counter()-start,
                    metrics=dict(self.counts),hint_metrics=dict(self.hints.counts))

    def lift_hint_plan(self, plan, child_model):
        self._check_hint_plan(self._hint_key(plan['core'],plan['clauses'],plan['depth']),plan)
        child=self._load(plan['edge']['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool
                for i in range(1,len(plan['edge']['names'])+1)) or not holds(child['cnf'],child_model)):
            raise ValueError('Invalid hint child model')
        _,fixed=self._hint_target(plan['core'],plan['clauses'],plan['probing'])
        model={abs(l):False for c in plan['core'] for l in c};model.update(fixed)
        model.update((v,child_model[i]) for i,v in enumerate(plan['edge']['names'],1))
        if plan['probing']['status']=='equivalence':
            for v,rep in plan['probing']['witness']['mapping']:
                model[v]=model[abs(rep)] if rep>0 else not model[abs(rep)]
        if not holds(plan['core'],model):raise ValueError('Hint lift violates core')
        return model

    def audit_hints(self):
        hints=self.hints.audit();plans=0
        for key,payload in self.db.execute('SELECT id,payload FROM cnf_hint_plans_v1'):
            self._check_hint_plan(key,json.loads(payload));plans+=1
        return dict(hints=hints,plans=plans)

    def hint_storage(self):
        plans,size=self.db.execute('SELECT count(*),coalesce(sum(length(CAST(id AS BLOB))+length(CAST(payload AS BLOB))),0) FROM cnf_hint_plans_v1').fetchone()
        return dict(self.hints.storage(),plans=plans,plan_bytes=size)
