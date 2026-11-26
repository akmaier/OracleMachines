"""Probe a checked joint bank; reuse old schedules only after exact comparison.

The frozen B7 engine is used with an explicit source/bank view. Its internal
cursor envelope is translated only after checking the distinct joint format
and exact binding. Open history remains scheduling data, never a SAT proof.
"""
from copy import deepcopy
import json
from experiments import cnf_joint_cursor_feedback as joint
from experiments.cnf_fused_b7_expansion import _search
c=joint.cursor
FORMAT='cnf-joint-probe-cursor-v1'
POLICY='joint-wide-occurrence-order-complement-first-v1'


def prepare(*inputs,closure,counts,trace_limit=256):
    if type(trace_limit) is not int or trace_limit<1:raise ValueError('Invalid joint trace bound')
    prepared=joint.prepare(*inputs,counts=counts)
    fixed=c.prior.check_closure(prepared[17],closure,counts)
    bank,ids=c.prior.residual_bank(prepared[17],fixed,counts)
    active={abs(l) for cl in bank for l in cl}
    order=tuple(l for l in c.frozen.roots(prepared[0]) if abs(l) in active)
    binding=json.dumps([POLICY,prepared[0],prepared[17],closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['joint_probe_binding_bytes']+=len(binding.encode())
    # The shared engine reads only source at 0 and the current bank at 15.
    view=(*prepared[:15],prepared[17],prepared[18])
    return prepared,view,bank,ids,order,binding


def _load(view,order,binding,cursor,counts,trace_limit):
    if cursor is not None:
        if type(cursor) is not dict or cursor.get('format')!=FORMAT:raise ValueError('Invalid joint cursor format')
        cursor=deepcopy(cursor);cursor['format']=c.FORMAT
    return c.load(view,order,binding,cursor,counts,trace_limit)


def equivalent(prepared,closure,inputs,trace_limit,counts):
    counts['joint_probe_compare_literals']+=sum(map(len,prepared[15]))+sum(map(len,prepared[17]))
    counts['joint_probe_compare_closure_slots']+=sum(len(x['assignment'])+2*len(x['units']) for x in (closure,inputs[15]))
    return prepared[15]==prepared[17] and closure==inputs[15] and inputs[16]['program']['trace_limit']==trace_limit


def discover(*inputs,closure,counts,policy='reuse',cursor=None,probe_limit=64,work_limit=262144,trace_limit=256):
    if policy not in ('reuse','restart','matched') or any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):
        raise ValueError('Invalid joint search options')
    prepared,view,bank,ids,order,binding=prepare(*inputs,closure=closure,counts=counts,trace_limit=trace_limit)
    same=equivalent(prepared,closure,inputs,trace_limit,counts)
    if cursor is None and policy=='matched' and same:
        extra=len(inputs[16]['cursor']['completed']);probe_limit+=extra;work_limit*=1+(extra+63)//64
    if cursor is None and policy=='reuse' and same:
        cursor=deepcopy(inputs[16]['cursor']);cursor.update(format=FORMAT,binding=binding)
        counts['joint_probe_imported_completed']+=len(cursor['completed']);counts['joint_probe_imported_cursors']+=1
    elif cursor is None:counts['joint_probe_fresh_cursors']+=1
    else:counts['joint_probe_continued_cursors']+=1
    state=_load(view,order,binding,cursor,counts,trace_limit)
    out=_search(bank,ids,binding,closure['units'],state,counts,probe_limit,work_limit,trace_limit)
    out['cursor']['format']=FORMAT
    return out


def validate(*inputs,closure,result,counts):
    if type(result) is not dict or set(result)!={'action','program','cursor'} or result['action']!='searched':raise ValueError('Invalid joint search result')
    p=result['program']
    if type(p) is not dict or type(p.get('trace_limit')) is not int:raise ValueError('Invalid joint search program')
    prepared,view,_,_,order,binding=prepare(*inputs,closure=closure,counts=counts,trace_limit=p['trace_limit'])
    if type(result['cursor']) is not dict:raise ValueError('Missing joint cursor')
    state=_load(view,order,binding,result['cursor'],counts,p['trace_limit'])
    c.prior.check_program(prepared[0],prepared[17],p,counts)
    if p!=c._program(state[4],state[6],p['trace_limit'],p['reason']):raise ValueError('Joint program disagrees with cursor')
    return prepared
