"""Own and validate a B6 result once, then compose and search B7 internally.

No caller-supplied prepared object or verified marker is accepted. Empty checked
failure sets reuse the old bank, exact closure trace, residual view and schedule.
A contradictory composition is outside this search API (use the feedback checker).
"""
from copy import deepcopy
import json
from experiments import cnf_b7_probe_cursor as c
old=c.feedback.cursor


def expand(*inputs,counts,policy='reuse',cursor=None,probe_limit=64,work_limit=262144,trace_limit=256,reuse_unchanged=True):
    if policy not in ('reuse','restart','matched') or type(reuse_unchanged) is not bool or any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):
        raise ValueError('Invalid fused expansion options')
    if len(inputs)!=15:raise ValueError('Original B6 inputs and full result required')
    history=inputs[-1]
    if type(history) is not dict or set(history)!={'action','program','cursor'} or history['action']!='searched':raise ValueError('Invalid B6 result')
    if type(history['cursor']) is not dict or type(history['program']) is not dict or type(history['program'].get('trace_limit')) is not int:raise ValueError('Invalid B6 program or cursor')
    owned=deepcopy(inputs);history=owned[-1];program=history['program'];counts['expansion_input_copies']+=1
    prepared,oldbank,oldids,oldorder,oldbinding=old.prepare(*owned[:-1],counts,trace_limit=program['trace_limit'])
    oldstate=old.load(prepared,oldorder,oldbinding,history['cursor'],counts,program['trace_limit'])
    old.prior.check_program(prepared[0],prepared[13],program,counts)
    if program!=old._program(oldstate[4],oldstate[6],program['trace_limit'],program['reason']):raise ValueError('Program disagrees with cursor')
    if program['status']!='unresolved':raise ValueError('Unresolved B6 result required')
    # This is an internal proof of a no-op: there are no checked exclusions to
    # append. It is established only after validating the complete old result.
    if reuse_unchanged and not program['probes']:
        prepared=(*prepared,prepared[13],prepared[14]);closure=owned[13]
        bank,ids,order=oldbank,oldids,oldorder;same=program['trace_limit']==trace_limit
        counts['expansion_empty_layers_reused']+=1
        counts['expansion_reused_bank_clauses']+=len(prepared[13])
    else:
        prepared=c.feedback._append_checked(prepared,program,counts)
        fixed,trace,conflict=c.native.propagate(prepared[15],counts)
        if conflict is not None:raise ValueError('Contradictory composition requires the feedback refutation API')
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
        if c.prior.check_closure(prepared[15],closure,counts)!=fixed:raise ValueError('Invalid generated closure')
        bank,ids=c.prior.residual_bank(prepared[15],fixed,counts)
        active={abs(l) for cl in bank for l in cl}
        order=tuple(l for l in c.frozen.roots(prepared[0]) if abs(l) in active)
        same=c.equivalent(prepared,owned[13],closure,history,trace_limit,counts)
        counts['expansion_rebuilt_layers']+=1
    binding=json.dumps([c.POLICY,prepared[0],prepared[15],closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['cursor_binding_bytes']+=len(binding.encode())
    if policy=='matched' and cursor is None and same:
        extra=len(history['cursor']['completed']);probe_limit+=extra;work_limit*=1+(extra+63)//64
    if cursor is None and policy=='reuse' and same:
        # Bank/trace/order/allowance match; oldstate was fully checked above.
        state=oldstate;counts['b7_imported_completed']+=len(state[3]);counts['b7_imported_failures']+=len(state[4]);counts['b7_imported_cursors']+=1
        counts['expansion_checked_schedule_handoffs']+=1
    else:
        counts['b7_fresh_cursors' if cursor is None else 'b7_continued_cursors']+=1
        state=c.load(prepared,order,binding,deepcopy(cursor),counts,trace_limit)
    result=_search(bank,ids,binding,closure['units'],state,counts,probe_limit,work_limit,trace_limit)
    return dict(closure=closure,result=result)


def _search(bank,ids,binding,prefix,state,counts,probe_limit,work_limit,trace_limit):
    queue,promoted,tested,completed,probes,found,terminal=state;attempts=0
    def result(reason):
        return dict(action='searched',program=c._program(probes,terminal,trace_limit,reason),
                    cursor=dict(format=c.FORMAT,binding=binding,completed=completed,probes=probes))
    if terminal is not None:return result('opposite_probes')
    if len(prefix)>trace_limit:return result('trace_limit')
    index=c.frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits']
    while True:
        root,priority=c._next(queue,promoted,tested);promoted=None
        if root is None:return result('complete')
        if attempts>=probe_limit:return result('probe_limit')
        attempts+=1;counts['probe_roots']+=1;counts['cursor_promoted_probes' if priority else 'cursor_base_probes']+=1
        try:proof=index.probe(root,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit-len(prefix))
        except c.frozen.ProbeLimit as error:
            counts['cursor_interrupted_probes']+=1;return result(str(error))
        completed.append(root);tested.add(root);counts['cursor_completed_probes']+=1
        if proof is None:continue
        proof=dict(units=[list(p) for p in prefix]+[[l,ids[cid]] for l,cid in proof['units']],conflict=ids[proof['conflict']])
        counts['cursor_lifted_steps']+=len(prefix)
        probes.append(dict(assumption=root,proof=proof));found[root]=len(probes)-1;counts['probe_exclusions']+=1
        if -root in found:
            terminal=dict(low=found[-abs(root)],high=found[abs(root)]);return result('opposite_probes')
        if -root not in tested:promoted=-root
