"""Persist the deterministic probe frontier without treating open probes as SAT.

A cursor is search history, not a proof of exhaustion. Its exact input/policy
binding and schedule are checked on reload; every retained failed probe is
independently checked. Claimed open probes are not rerun on reload, so coverage
reuse assumes honestly produced history. Refutations never rely on that trust.
"""
from collections import deque
from experiments import cnf_b6_cursor_feedback as feedback
prior=feedback.cursor.prior
frozen=feedback.frozen
native=feedback.native
FORMAT='cnf-b7-probe-cursor-v1'
POLICY='b7-wide-occurrence-order-complement-first-v1'


def prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,b6_cursor_feedback_closure,counts,*,trace_limit=256):
    if type(trace_limit) is not int or trace_limit<1:raise ValueError('Invalid cursor trace bound')
    prepared=feedback.prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts)
    fixed=prior.check_closure(prepared[15],b6_cursor_feedback_closure,counts)
    bank,ids=prior.residual_bank(prepared[15],fixed,counts)
    active={abs(l) for cl in bank for l in cl}
    order=tuple(l for l in frozen.roots(prepared[0]) if abs(l) in active)
    # Full exact content, not a digest-only match. Include the actual closure
    # trace: changing its order can change transport and available trace budget.
    import json
    binding=json.dumps([POLICY,prepared[0],prepared[15],b6_cursor_feedback_closure,order,trace_limit],sort_keys=True,separators=(',',':'))
    counts['cursor_binding_bytes']+=len(binding.encode())
    return prepared,bank,ids,order,binding


def _program(probes,terminal,trace_limit,reason):
    return dict(status='refuted' if terminal else 'unresolved',reason='opposite_probes' if terminal else reason,
                mode='conditioned',probes=probes,terminal=terminal,trace_limit=trace_limit)


def _next(queue,promoted,tested):
    while promoted is not None or queue:
        priority=promoted is not None
        root=promoted if priority else queue.popleft();promoted=None
        if root not in tested:return root,priority
    return None,False


def load(prepared,order,binding,cursor,counts,trace_limit):
    if cursor is None:
        return deque(order),None,set(),[],[],{},None
    if type(cursor) is not dict or set(cursor)!={'format','binding','completed','probes'} or cursor['format']!=FORMAT or cursor['binding']!=binding:
        raise ValueError('Cursor input or policy changed')
    completed=cursor['completed'];probes=cursor['probes']
    if type(completed) is not list or any(type(v) is not int or not v for v in completed) or len(set(completed))!=len(completed):
        raise ValueError('Invalid completed probe sequence')
    # Verify all saved failures even when a result or root was already cached.
    prior.check_program(prepared[0],prepared[15],_program(probes,None,trace_limit,'complete'),counts)
    failures={p['assumption']:i for i,p in enumerate(probes)}
    if not failures.keys()<=set(completed):raise ValueError('Failure has no completed probe')
    queue=deque(order);promoted=None;tested=set();found={};terminal=None;seen_failures=[]
    for root in completed:
        expected,_=_next(queue,promoted,tested);promoted=None
        counts['cursor_schedule_checks']+=1
        if terminal is not None or root!=expected:raise ValueError('Cursor is not a valid policy prefix')
        tested.add(root)
        if root not in failures:continue
        found[root]=failures[root];seen_failures.append(failures[root])
        if -root in found:terminal=dict(low=found[-abs(root)],high=found[abs(root)])
        elif -root not in tested:promoted=-root
    if seen_failures!=list(range(len(probes))):raise ValueError('Failures are not in completed order')
    # Deep-copy portable proofs before any returned state can outlive its caller.
    from copy import deepcopy
    counts['cursor_reused_completed']+=len(completed)
    return queue,promoted,tested,list(completed),deepcopy(probes),found,terminal


def equivalent(prepared,old_closure,new_closure,history,trace_limit,counts):
    counts['b7_compare_bank_literals']+=sum(map(len,prepared[13]))+sum(map(len,prepared[15]))
    counts['b7_compare_closure_slots']+=sum(len(c['assignment'])+2*len(c['units']) for c in (old_closure,new_closure))
    return (prepared[13]==prepared[15] and old_closure==new_closure
            and history['program']['trace_limit']==trace_limit)


def discover(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,b6_cursor_feedback_closure,counts,*,policy="reuse",cursor=None,probe_limit=64,work_limit=262144,trace_limit=256):
    if policy not in ("restart","reuse") or any(type(v) is not int or v<1 for v in (probe_limit,work_limit,trace_limit)):
        raise ValueError('Invalid cursor probe bounds')
    prepared,bank,ids,order,binding=prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,b6_cursor_feedback_closure,counts,trace_limit=trace_limit)
    same=equivalent(prepared,b5_cursor_feedback_closure,b6_cursor_feedback_closure,b6_probe_cursor,trace_limit,counts)
    if cursor is None and policy=='reuse' and same:
        from copy import deepcopy
        cursor=deepcopy(b6_probe_cursor['cursor'])
        cursor.update(format=FORMAT,binding=binding)
        counts['b7_imported_completed']+=len(cursor['completed'])
        counts['b7_imported_failures']+=len(cursor['probes'])
        counts['b7_imported_cursors']+=1
    elif cursor is None:counts['b7_fresh_cursors']+=1
    else:counts['b7_continued_cursors']+=1
    queue,promoted,tested,completed,probes,found,terminal=load(prepared,order,binding,cursor,counts,trace_limit)
    prefix=b6_cursor_feedback_closure['units'];attempts=0
    def result(reason):
        state=dict(format=FORMAT,binding=binding,completed=completed,probes=probes)
        return dict(action='searched',program=_program(probes,terminal,trace_limit,reason),cursor=state)
    if terminal is not None:return result('opposite_probes')
    if len(prefix)>trace_limit:return result('trace_limit')
    index=frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits']
    while True:
        root,priority=_next(queue,promoted,tested);promoted=None
        if root is None:return result('complete')
        if attempts>=probe_limit:return result('probe_limit')
        attempts+=1;counts['probe_roots']+=1
        counts['cursor_promoted_probes' if priority else 'cursor_base_probes']+=1
        try:
            proof=index.probe(root,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit-len(prefix))
        except frozen.ProbeLimit as error:
            # The interrupted root is NOT completed. Replaying completed history
            # reconstructs it as the next root, even if it was a promoted one.
            counts['cursor_interrupted_probes']+=1
            return result(str(error))
        completed.append(root);tested.add(root);counts['cursor_completed_probes']+=1
        if proof is None:continue
        proof=dict(units=[list(p) for p in prefix]+[[l,ids[cid]] for l,cid in proof['units']],conflict=ids[proof['conflict']])
        counts['cursor_lifted_steps']+=len(prefix)
        probes.append(dict(assumption=root,proof=proof));found[root]=len(probes)-1;counts['probe_exclusions']+=1
        if -root in found:
            terminal=dict(low=found[-abs(root)],high=found[abs(root)])
            return result('opposite_probes')
        if -root not in tested:promoted=-root


def validate(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,b6_cursor_feedback_closure,result,counts):
    if type(result) is not dict or set(result)!={'action','program','cursor'}:raise ValueError('Invalid cursor result')
    if result['action']!='searched':raise ValueError('Invalid B7 action')
    if type(result['cursor']) is not dict:raise ValueError('Missing cursor state')
    program=result['program']
    if type(program) is not dict or type(program.get('trace_limit')) is not int:raise ValueError('Invalid cursor program')
    prepared,_,_,order,binding=prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,b6_cursor_feedback_closure,counts,trace_limit=program['trace_limit'])
    _,_,_,_,probes,_,terminal=load(prepared,order,binding,result['cursor'],counts,program['trace_limit'])
    prior.check_program(prepared[0],prepared[15],program,counts)
    if program!=_program(probes,terminal,program['trace_limit'],program['reason']):raise ValueError('Program disagrees with cursor')
    return prepared
