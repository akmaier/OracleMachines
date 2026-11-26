"""Iterate checked failed-literal rounds without inventing a new schema per bank.

Refutations concern the supplied seed CNF. An application using derived seed
clauses must separately check their original-source provenance. Open schedules
remain honest-history hints, never SAT certificates.
"""
from copy import deepcopy
import json
from experiments import cnf_b7_probe_cursor as engine
from experiments.cnf_fused_b7_expansion import _search
native=engine.native;frozen=engine.frozen;closure_check=engine.prior
FORMAT='cnf-checked-probe-saturation-v1'
POLICY='saturation-wide-complement-first-v1'


def prepare(seed,bank,closure,order_source,counts,trace_limit):
    fixed=closure_check.check_closure(bank,closure,counts)
    reduced,ids=closure_check.residual_bank(bank,fixed,counts)
    active={abs(l) for cl in reduced for l in cl}
    order=tuple(l for l in frozen.roots(order_source) if abs(l) in active)
    binding=json.dumps([POLICY,seed,bank,closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['saturation_binding_bytes']+=len(binding.encode())
    view=(seed,*([None]*14),bank,None)
    return view,reduced,ids,order,binding


def _seed(source,order_source,counts):
    seed=native.normalize(source,counts)[0]
    # Ordering is a heuristic only. All live seed coordinates must be covered.
    ordering=seed if order_source is None else tuple(map(tuple,order_source))
    if not {abs(l) for cl in seed for l in cl}<={abs(l) for cl in ordering for l in cl}:
        raise ValueError('Ordering omits seed coordinates')
    return seed,ordering


def _close(bank,counts):
    fixed,units,conflict=native.propagate(bank,counts)
    if conflict is not None:return None,dict(units=units,conflict=conflict)
    return dict(units=units,assignment=sorted([list(x) for x in fixed.items()])),None


def validate(source,result,counts,*,order_source=None):
    source,order_source,result=deepcopy((source,order_source,result));seed,ordering=_seed(source,order_source,counts)
    if type(result) is not dict or set(result)!={'format','seed','order_source','trace_limit','rounds','status','reason','proof'}:
        raise ValueError('Invalid saturation record')
    limit=result['trace_limit']
    if result['format']!=FORMAT or result['seed']!=list(map(list,seed)) or result['order_source']!=list(map(list,ordering)) or type(limit) is not int or limit<1 or type(result['rounds']) is not list:
        raise ValueError('Changed saturation seed or bound')
    bank=seed;terminal=None;pending=None;last_reason=None
    for i,row in enumerate(result['rounds']):
        if terminal is not None or pending is not None or type(row) is not dict or set(row)!={'closure','search'}:raise ValueError('Invalid saturation round order')
        closure=row['closure'];search=row['search'];view,reduced,ids,order,binding=prepare(seed,bank,closure,ordering,counts,limit)
        if type(search) is not dict or set(search)!={'action','program','cursor'} or search['action']!='searched':raise ValueError('Invalid round search')
        state=engine.load(view,order,binding,search['cursor'],counts,limit);p=search['program']
        closure_check.check_program(seed,bank,p,counts)
        if p!=engine._program(state[4],state[6],limit,p['reason']):raise ValueError('Round program disagrees with history')
        last_reason=p['reason']
        if p['status']=='refuted':terminal='opposite_probes'
        elif p['reason']=='complete':
            if engine._next(state[0],state[1],state[2])[0] is not None:raise ValueError('Round is not exhausted')
            if not p['probes']:terminal='fixed_point'
            else:
                grown=tuple(sorted(set(bank)|{(-x['assumption'],) for x in p['probes']}))
                if len(grown)<=len(bank):raise ValueError('Round made no strict progress')
                bank=grown
        else:pending=(bank,closure,search)
        counts['saturation_checked_rounds']+=1
    status,reason,proof=result['status'],result['reason'],result['proof']
    if terminal is not None:
        if reason!=terminal or status!=('refuted' if terminal=='opposite_probes' else 'unresolved') or proof is not None:raise ValueError('Wrong saturation terminal')
    elif pending is not None:
        if status!='unresolved' or reason!=last_reason or proof is not None:raise ValueError('Wrong pending saturation reason')
    elif status=='refuted' and reason=='units':frozen.check_trace(seed,bank,None,proof,counts,limit)
    elif status=='unresolved' and reason in ('round_limit','trace_limit') and proof is None:pass
    else:raise ValueError('Invalid saturation outcome')
    return seed,ordering,bank,pending,terminal


def discover(source,counts,*,order_source=None,previous=None,round_limit=8,probe_limit=512,work_limit=2097152,trace_limit=256):
    if any(type(x) is not int or x<1 for x in (round_limit,probe_limit,work_limit,trace_limit)):raise ValueError('Positive saturation bounds required')
    source,order_source,saved=deepcopy((source,order_source,previous));seed,ordering=_seed(source,order_source,counts)
    result=dict(format=FORMAT,seed=list(map(list,seed)),order_source=list(map(list,ordering)),trace_limit=trace_limit,
                rounds=[],status='unresolved',reason='round_limit',proof=None)
    bank=seed;pending=None
    if saved is not None:
        _,_,bank,pending,terminal=validate(source,saved,counts,order_source=ordering)
        if saved['trace_limit']!=trace_limit:raise ValueError('Changed saturation trace bound')
        if saved['status']=='refuted' or terminal=='fixed_point':counts['saturation_terminal_reuses']+=1;return saved
        result=saved
        if pending is not None:result['rounds'].pop()
    def finish(status,reason,proof=None):
        result.update(status=status,reason=reason,proof=proof);return result
    for _ in range(round_limit):
        if pending is None:
            closure,proof=_close(bank,counts)
            if proof is not None:
                if len(proof['units'])>trace_limit:return finish('unresolved','trace_limit')
                return finish('refuted','units',proof)
            cursor=None
        else:
            bank,closure,search=pending;cursor=search['cursor'];pending=None
        view,reduced,ids,order,binding=prepare(seed,bank,closure,ordering,counts,trace_limit)
        state=engine.load(view,order,binding,cursor,counts,trace_limit)
        search=_search(reduced,ids,binding,closure['units'],state,counts,probe_limit,work_limit,trace_limit)
        result['rounds'].append(dict(closure=closure,search=search));counts['saturation_searched_rounds']+=1
        p=search['program']
        if p['status']=='refuted':return finish('refuted','opposite_probes')
        if p['reason']!='complete':return finish('unresolved',p['reason'])
        if not p['probes']:return finish('unresolved','fixed_point')
        grown=tuple(sorted(set(bank)|{(-x['assumption'],) for x in p['probes']}))
        if len(grown)<=len(bank):raise ValueError('Round made no strict progress')
        counts['saturation_added_units']+=len(grown)-len(bank);bank=grown
    return finish('unresolved','round_limit')
