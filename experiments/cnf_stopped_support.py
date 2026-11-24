"""Check captured source bindings and build plans with explicitly open leaves."""
from collections import Counter
from copy import deepcopy
import json
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import check_template, fixed_pairs
from experiments.cnf_partial_proof_plan import check_plan, PLAN_FORMAT


def conditional_unit(source, guards, counts):
    """Independently derive a source-clause unit certificate under these guards."""
    fixed = fixed_pairs(guards)
    raw = []; origins = []
    for i,clause in enumerate(source):
        restricted = native.restrict_scan((clause,),fixed,counts)
        if restricted:
            raw.append(restricted[0]); origins.append(i)
    _,trace,conflict = native.propagate(tuple(raw),counts)
    if conflict is None: return None
    conflict = origins[conflict]
    lifted = [(lit,origins[cid]) for lit,cid in trace]
    needed = {abs(lit) for lit in source[conflict]}; kept = []
    for lit,cid in reversed(lifted):
        counts['stopped_slice_steps'] += 1
        if abs(lit) not in needed: continue
        needed.remove(abs(lit))
        needed.update(abs(l) for l in source[cid] if l != lit)
        kept.append((lit,cid))
    if not needed <= fixed.keys(): raise ValueError('Unclosed conditional source dependency')
    kept.reverse()
    ids = sorted({conflict}|{cid for _,cid in kept})
    clauses = sorted(tuple(source[cid]) for cid in ids)
    positions = {cl:i for i,cl in enumerate(clauses)}
    remap = {cid:positions[tuple(source[cid])] for cid in ids}
    result = dict(clauses=[list(cl) for cl in clauses],
        assumptions=[[v,fixed[v]] for v in sorted(needed)],
        trace=[[lit,remap[cid]] for lit,cid in kept],conflict=remap[conflict])
    check_template(result,counts)
    return result


def extract(source, candidates, reader, counts=None):
    """A checked negative residual supplies a candidate, never a source verdict."""
    c = Counter() if counts is None else counts
    source = tuple(tuple(cl) for cl in source)
    if native.normalize(source,c)[0] != source: raise ValueError('Canonical source required')
    variables = {abs(l) for cl in source for l in cl}
    templates = []; seen = set(); observations = []
    for candidate in candidates:
        fixed = fixed_pairs([list(p) for p in candidate['fixed']])
        guards = fixed_pairs([list(p) for p in candidate['guards']])
        mapping = dict(candidate['mapping'])
        if (len(mapping)!=len(candidate['mapping']) or
                any(type(v) is not int or type(w) is not int or v<=0 or w not in variables for v,w in mapping.items()) or
                len(set(mapping.values()))!=len(mapping) or not fixed.keys()<=variables or
                any(fixed.get(v)!=b for v,b in guards.items())):
            raise ValueError('Invalid captured coordinate binding')
        node = reader._read(candidate['key'])
        if node is None:
            c['stopped_unretained_endpoints'] += 1
            observations.append(dict(kind='unretained',route=candidate['route'],
                guard_variables=len(guards),fixed_variables=len(fixed),template=None))
            continue
        if node['answer'] is not False: raise ValueError('Checked negative endpoint required')
        local = tuple(map(tuple,node['cnf']))
        if not {abs(l) for cl in local for l in cl} <= mapping.keys():
            raise ValueError('Incomplete captured map')
        image = {tuple(sorted((1 if l>0 else -1)*mapping[abs(l)] for l in cl)) for cl in local}
        residual = set(native.restrict_scan(source,fixed,c))
        if not image <= residual: raise ValueError('Captured residual is not a conditioned source subset')
        template = conditional_unit(source,[list(p) for p in candidate['guards']],c)
        record = dict(kind=node['proof']['kind'],route=candidate['route'],
            guard_variables=len(guards),fixed_variables=len(fixed),template=None)
        if template is not None:
            identity = json.dumps(template,sort_keys=True,separators=(',',':'))
            if identity not in seen:
                seen.add(identity); templates.append(template)
            record['template'] = next(i for i,t in enumerate(templates) if t==template)
        observations.append(record)
    return dict(templates=templates,observations=observations)


def make_open_plan(templates, *, node_limit=129, counts=None):
    """A bounded decision tree; every assignment ends in a proof or an open leaf.

    Deterministic first-compatible-template ordering is a census baseline, not a
    claim to find a minimum cover or cheapest acquisition order.
    """
    if type(node_limit) is not int or not 1<=node_limit<=129:
        raise ValueError('Plan node limit must be between 1 and 129')
    c = Counter() if counts is None else counts
    templates = deepcopy(templates)
    guards = []
    for t in templates:
        check_template(t,c); guards.append(fixed_pairs(t['assumptions']))
    credits = (node_limit-1)//2
    used = []; indices = {}; open_index = None
    def leaf(index):
        nonlocal open_index
        if index is None:
            if open_index is None:
                open_index=len(used); used.append(dict(open=True,clauses=[]))
            return dict(leaf=open_index)
        if index not in indices:
            indices[index]=len(used); used.append(templates[index])
        return dict(leaf=indices[index])
    def walk(context, choices):
        nonlocal credits
        c['stopped_plan_nodes'] += 1
        choices = [i for i in choices if all(v not in context or context[v]==b for v,b in guards[i].items())]
        for i in choices:
            if guards[i].items()<=context.items(): return leaf(i)
        if not choices or credits==0: return leaf(None)
        variable = min(v for v in guards[choices[0]] if v not in context)
        credits -= 1
        return dict(variable=variable,low=walk({**context,variable:False},choices),
                    high=walk({**context,variable:True},choices))
    tree = walk({},list(range(len(templates))))
    plan = dict(format=PLAN_FORMAT,tree=tree,templates=used)
    check_plan(plan,c,node_limit=node_limit)
    return plan
