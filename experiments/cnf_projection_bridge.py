"""Reuse an exact retained target after projection and checked subsumption.

The bridge proves target == exists(variable, source), up to the recorded
renaming. Every opposing pair is checked. Removed clauses require retained
subclauses; no SAT/UNSAT label or similarity score is trusted. The final clause
budget is checked after deletion, with a separate opposing-pair cap.
"""
from collections import Counter
import hashlib

from experiments.cnf_additive_elimination import check_additive_elimination, lift_additive_elimination
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_variable_elimination import _limit
from experiments.cnf_selected_routes import SelectedRoutes
from experiments.cnf_positive_primitives import PositiveReplay
from experiments.cnf_simplification import simplification_reconstruction
from experiments.cnf_single_pass_check import reconstruct_single_pass

FORMAT = 'projection-subsumption-bridge-v1'
KIND = 'projection_bridge'


def canonical(cnf, counts):
    if type(cnf) is not list or any(type(c) is not list for c in cnf):
        raise ValueError('Bridge endpoints must be explicit canonical CNFs')
    actual, names = normalize(cnf, counts)
    if encode(actual) != encode(cnf) or names != tuple(range(1, len(names)+1)):
        raise ValueError('Bridge endpoint is not canonical')
    return len(names)


def projection(source, variable, counts, pair_limit):
    # A pair produces at most one resolvent. This permits the intermediate
    # growth needed for deletion; the FINAL budget is checked separately.
    raw = check_additive_elimination(source, dict(variable=variable), counts,
        pair_limit=pair_limit, clause_growth_limit=pair_limit)
    if raw is None:
        raise ValueError('Bridge needs an actual eliminated variable')
    return normalize(raw, counts)


def check(source, target, proof, counts=None, *, pair_limit=64, clause_growth_limit=2):
    counts = Counter() if counts is None else counts
    _limit(pair_limit); _limit(clause_growth_limit)
    n = canonical(source, counts); m = canonical(target, counts)
    if m >= n or len(target) > len(source)+clause_growth_limit:
        raise ValueError('Bridge must reduce support within the final clause budget')
    if (type(proof) is not dict or set(proof) != {'format','variable','names','subsumers'}
            or proof['format'] != FORMAT or type(proof['subsumers']) is not list):
        raise ValueError('Invalid projection bridge fields')
    projected, names = projection(source, proof['variable'], counts, pair_limit)
    if encode(proof['names']) != encode(names) or len(names) != m:
        raise ValueError('Incorrect bridge variable transport or lost target support')
    wanted = {tuple(c) for c in target}
    if not wanted <= set(projected):
        raise ValueError('Target introduces an unproved clause')
    missing = [i for i,c in enumerate(projected) if c not in wanted]
    if len(proof['subsumers']) != len(missing):
        raise ValueError('Every removed clause needs a retained subsumer')
    for expected, item in zip(missing, proof['subsumers'], strict=True):
        if (type(item) is not list or len(item) != 2 or any(type(i) is not int for i in item)
                or item[0] != expected or not 0 <= item[1] < len(target)):
            raise ValueError('Invalid subsumption indices or duplicate deletion')
        clause = projected[expected]; retained = target[item[1]]
        counts['bridge_subsumption_literals'] += len(clause)+len(retained)
        if not set(retained) < set(clause):
            raise ValueError('Removed clause lacks a retained proper subclause')
    counts['bridge_removed_clauses'] += len(missing)
    counts['verified_projection_bridges'] += 1
    return names


def discover(source, target, counts=None, *, pair_limit=64, candidate_limit=64, clause_growth_limit=2):
    """Bounded order-preserving target search; a miss is not non-equivalence."""
    counts = Counter() if counts is None else counts
    for value in (pair_limit, candidate_limit, clause_growth_limit):
        _limit(value)
    n = canonical(source, counts); m = canonical(target, counts)
    if m >= n or len(target) > len(source)+clause_growth_limit:
        return None
    wanted = {tuple(c) for c in target}; sets = list(map(set, target))
    for variable in range(1, min(n, candidate_limit)+1):
        counts['bridge_candidates_tested'] += 1
        try:
            projected, names = projection(source, variable, counts, pair_limit)
        except ValueError:
            counts['bridge_projection_misses'] += 1
            continue
        if len(names) != m or not wanted <= set(projected):
            counts['bridge_target_misses'] += 1
            continue
        subsumers = []
        for i, clause in enumerate(projected):
            if clause in wanted:
                continue
            superset = set(clause); match = None
            for j, subset in enumerate(sets):
                counts['bridge_discovery_subset_tests'] += 1
                counts['bridge_discovery_subset_literals'] += len(subset)+len(superset)
                if subset < superset:
                    match = j; break
            if match is None:
                break
            subsumers.append([i, match])
        else:
            proof = dict(format=FORMAT, variable=variable, names=list(names), subsumers=subsumers)
            check(source, target, proof, counts, pair_limit=pair_limit, clause_growth_limit=clause_growth_limit)
            return proof
        counts['bridge_subsumption_misses'] += 1
    return None


def lift(source, target, proof, model, counts=None):
    counts = Counter() if counts is None else counts
    names = check(source, target, proof, counts)
    if (type(model) is not dict or any(type(v) is not int or type(b) is not bool for v,b in model.items())
            or any(i not in model for i in range(1,len(names)+1)) or not holds(target, model)):
        raise ValueError('Invalid target model')
    original_names = {v:model[i] for i,v in enumerate(names,1)}
    result = lift_additive_elimination(source, dict(variable=proof['variable']), original_names,
        counts, pair_limit=64, clause_growth_limit=64)
    if not holds(source, result):
        raise ValueError('Bridge lift violates source')
    return result


def record_key(record):
    return hashlib.sha256(encode(record).encode()).hexdigest()


def verify(h, record, counts):
    if (type(record) is not dict or set(record) != {'source','target','proof'}
            or any(type(record[k]) is not str for k in ('source','target'))):
        raise ValueError('Invalid bridge record')
    source = h._load(record['source']); target = h._load(record['target'])
    if source is None or target is None:
        raise ValueError('Missing acquired bridge endpoint')
    if (source['depth'] != target['depth'] or
            h._canonical(source['cnf'], source['depth'])[2] != record['source'] or
            h._canonical(target['cnf'], source['depth'])[2] != record['target']):
        raise ValueError('Bridge endpoints differ in policy or depth')
    return check(source['cnf'], target['cnf'], record['proof'], counts)


def attach(h, routes, record, counts):
    verify(h, record, counts)
    item = (dict(kind=KIND, id=record_key(record)), [record['target']])
    if item not in routes.by_source[record['source']]:
        routes.by_source[record['source']].append(item)


class BridgeSelectedRoutes(SelectedRoutes):
    def __init__(self, h, evidence, bridges):
        super().__init__(h, evidence)
        self.bridges = {record_key(r):r for r in bridges}

    def select(self, h, source, rule):
        if type(rule) is not dict or rule.get('kind') != KIND:
            return super().select(h, source, rule)
        if set(rule) != {'kind','id'} or type(rule['id']) is not str:
            raise ValueError('Invalid selected bridge rule')
        record = self.bridges.get(rule['id'])
        if record is None or record['source'] != source:
            raise ValueError('Missing or foreign bridge evidence')
        attach(h, self, record, self.counts)


def verify_positive(h, certificate, roots, evidence, bridges, counts):
    replay = PositiveReplay(h, evidence, counts)
    replay.routes = BridgeSelectedRoutes(h, evidence, bridges)
    try:
        with simplification_reconstruction(reconstruct_single_pass):
            replay.verify(certificate, roots)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError('Malformed bridge coverage evidence') from exc
    return replay
