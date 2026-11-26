"""Validate common B6 provenance once inside a joint discovery/checking call.

All inputs are privately copied. Independent original/comparison histories keep
their own trace-bound bindings and proof checks. No caller-supplied prepared
state, verified marker or cross-call authority cache is accepted.
"""
from copy import deepcopy
import json
from experiments import cnf_joint_probe_cursor as prior
b7=prior.c;b6=b7.feedback.cursor


def _header(result):
    if type(result) is not dict or set(result)!={'action','program','cursor'} or result['action']!='searched' or type(result['cursor']) is not dict:raise ValueError('Invalid source history')
    p=result['program']
    if type(p) is not dict or type(p.get('trace_limit')) is not int or p['trace_limit']<1:raise ValueError('Invalid source program')
    return p


def _binding(policy,source,bank,closure,order,trace_limit,counts):
    value=json.dumps([policy,source,bank,closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['cursor_binding_bytes']+=len(value.encode());return value


def _check(module,prepared,slot,order,binding,result,counts):
    p=_header(result);state=module.load(prepared,order,binding,result['cursor'],counts,p['trace_limit'])
    module.prior.check_program(prepared[0],prepared[slot],p,counts)
    if p!=module._program(state[4],state[6],p['trace_limit'],p['reason']):raise ValueError('Source program disagrees with cursor')
    if p['status']!='unresolved':raise ValueError('Unresolved source histories required')
    counts['shared_joint_histories_checked']+=1


def _joint(inputs,counts):
    if len(inputs)!=18:raise ValueError('Original joint inputs required')
    original,upper,comparison=(_header(inputs[i]) for i in (14,16,17))
    prepared,_,_,order,binding=b6.prepare(*inputs[:14],counts,trace_limit=original['trace_limit'])
    counts['shared_joint_prefix_preparations']+=1
    _check(b6,prepared,13,order,binding,inputs[14],counts)
    # A trace bound affects the serialized binding, not the common B6 bank,
    # residual or source-derived order. Keep each history's actual bound.
    if comparison['trace_limit']==original['trace_limit']:
        comparison_binding=binding;counts['shared_joint_bindings_reused']+=1
    else:
        comparison_binding=_binding(b6.POLICY,prepared[0],prepared[13],inputs[13],order,comparison['trace_limit'],counts)
    _check(b6,prepared,13,order,comparison_binding,inputs[17],counts)
    prepared=b7.feedback._append_checked(prepared,original,counts)
    fixed=b7.prior.check_closure(prepared[15],inputs[15],counts)
    bank,_=b7.prior.residual_bank(prepared[15],fixed,counts)
    active={abs(l) for cl in bank for l in cl}
    order=tuple(l for l in b7.frozen.roots(prepared[0]) if abs(l) in active)
    binding=_binding(b7.POLICY,prepared[0],prepared[15],inputs[15],order,upper['trace_limit'],counts)
    _check(b7,prepared,15,order,binding,inputs[16],counts)
    bank={cl:entry for cl,entry in zip(prepared[15],prepared[16])}
    for kind,p in (('b6_comparison_probe',comparison),('b7_probe',upper)):
        for i,row in enumerate(p['probes']):
            cl=(-row['assumption'],);counts['joint_exclusions']+=1
            if cl not in bank:bank[cl]=dict(kind=kind,index=i);counts['joint_added_units']+=1
    clauses=tuple(sorted(bank));return (*prepared,clauses,[bank[cl] for cl in clauses])


def _prepare(inputs,closure,counts,trace_limit):
    if type(trace_limit) is not int or trace_limit<1:raise ValueError('Invalid joint trace bound')
    prepared=_joint(inputs,counts)
    fixed=b7.prior.check_closure(prepared[17],closure,counts)
    bank,ids=b7.prior.residual_bank(prepared[17],fixed,counts)
    active={abs(l) for cl in bank for l in cl}
    order=tuple(l for l in b7.frozen.roots(prepared[0]) if abs(l) in active)
    binding=json.dumps([prior.POLICY,prepared[0],prepared[17],closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['joint_probe_binding_bytes']+=len(binding.encode())
    return prepared,(*prepared[:15],prepared[17],prepared[18]),bank,ids,order,binding


def discover(*inputs,closure,counts,policy='reuse',cursor=None,probe_limit=64,work_limit=262144,trace_limit=256):
    if policy not in ('reuse','restart','matched') or any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):raise ValueError('Invalid joint search options')
    owned,cl,saved=deepcopy((inputs,closure,cursor));counts['shared_joint_owned_copies']+=1
    prepared,view,bank,ids,order,binding=_prepare(owned,cl,counts,trace_limit)
    same=prior.equivalent(prepared,cl,owned,trace_limit,counts)
    if saved is None and policy=='matched' and same:
        extra=len(owned[16]['cursor']['completed']);probe_limit+=extra;work_limit*=1+(extra+63)//64
    if saved is None and policy=='reuse' and same:
        saved=deepcopy(owned[16]['cursor']);saved.update(format=prior.FORMAT,binding=binding)
        counts['joint_probe_imported_completed']+=len(saved['completed']);counts['joint_probe_imported_cursors']+=1
    elif saved is None:counts['joint_probe_fresh_cursors']+=1
    else:counts['joint_probe_continued_cursors']+=1
    state=prior._load(view,order,binding,saved,counts,trace_limit)
    result=prior._search(bank,ids,binding,cl['units'],state,counts,probe_limit,work_limit,trace_limit)
    result['cursor']['format']=prior.FORMAT
    return result


def validate(*inputs,closure,result,counts):
    owned,cl,saved=deepcopy((inputs,closure,result));counts['shared_joint_owned_copies']+=1
    p=_header(saved)
    prepared,view,_,_,order,binding=_prepare(owned,cl,counts,p['trace_limit'])
    state=prior._load(view,order,binding,saved['cursor'],counts,p['trace_limit'])
    b7.prior.check_program(prepared[0],prepared[17],p,counts)
    if p!=b7._program(state[4],state[6],p['trace_limit'],p['reason']):raise ValueError('Joint program disagrees with cursor')
    return prepared
