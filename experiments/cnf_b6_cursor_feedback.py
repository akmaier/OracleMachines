"""Compose checked B6 failures into B7; keep all reasons on their prior bank.

Every derived exclusion is justified on the preceding bank. Open scheduling
history supplies no axiom. This module checks composition; it publishes no native
record on its own.
"""
from experiments import cnf_b6_probe_cursor as cursor,cnf_direct_unit_closure as direct
from experiments.cnf_prepared_publication import prepare_frame
from experiments.cnf_conditional_unit_support import transport,match,fixed_pairs,restrict,propagate
parent=cursor.feedback;prior=parent.prior;previous=parent.previous;layered=parent.layered;feedback=parent.feedback
frozen=cursor.frozen;support=parent.support;native=cursor.native
checked_options=direct.checked_options;DirectUnits=direct.DirectUnits


def _append_checked(prepared,program,counts):
    bank={cl:entry for cl,entry in zip(prepared[13],prepared[14])}
    for i,row in enumerate(program['probes']):
        cl=(-row['assumption'],);counts['b6_feedback_exclusions']+=1
        if cl not in bank:bank[cl]=dict(kind='b6_cursor_probe',index=i);counts['b6_feedback_added_units']+=1
    clauses=tuple(sorted(bank))
    return (*prepared,clauses,[bank[cl] for cl in clauses])


def add_layer(prepared,program,counts):
    cursor.prior.check_program(prepared[0],prepared[13],program,counts)
    if program['status']!='unresolved':raise ValueError('Unresolved B6 probe program required')
    return _append_checked(prepared,program,counts)


def prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts):
    prepared=cursor.validate(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts)
    if b6_probe_cursor['action']!='searched' or b6_probe_cursor['program']['status']!='unresolved':raise ValueError('Unresolved searched B6 cursor required')
    return _append_checked(prepared,b6_probe_cursor['program'],counts)


def discover(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts,*,mode='feedback',work_limit=262144,trace_limit=256):
    if mode not in ('base','feedback') or any(type(v) is not int or v<1 for v in (work_limit,trace_limit)):
        raise ValueError('Invalid B6 feedback bounds')
    prepared=prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts)
    bank=prepared[13] if mode=='base' else prepared[15]
    index=frozen.UnitIndex(bank,counts);start=counts['probe_occurrence_visits']
    try:proof=index.probe(None,counts,lambda:work_limit-(counts['probe_occurrence_visits']-start),trace_limit)
    except frozen.ProbeLimit as error:return dict(status='unresolved',reason=str(error),trace_limit=trace_limit,proof=None,mode=mode)
    return dict(status='refuted' if proof is not None else 'unresolved',reason='units' if proof is not None else 'open',trace_limit=trace_limit,proof=proof,mode=mode)


def check_program(prepared,program,counts):
    if (type(program) is not dict or set(program)!={'status','reason','trace_limit','proof','mode'}
        or type(program['trace_limit']) is not int or program['trace_limit']<1 or program['mode'] not in ('base','feedback')):
        raise ValueError('Invalid B6 feedback program')
    bank=prepared[13] if program['mode']=='base' else prepared[15]
    if program['status']=='refuted' and program['reason']=='units':frozen.check_trace(prepared[0],bank,None,program['proof'],counts,program['trace_limit'])
    elif not (program['status']=='unresolved' and program['reason'] in ('open','work_limit','trace_limit') and program['proof'] is None):raise ValueError('Invalid B6 feedback outcome')


def validate(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,program,counts):
    prepared=prepare(source,templates,seed,closure,new,next_closure,third,feedback_closure,probe_cursor,cursor_feedback_closure,b4_probe_cursor,b4_cursor_feedback_closure,b5_probe_cursor,b5_cursor_feedback_closure,b6_probe_cursor,counts)
    check_program(prepared,program,counts)
    return prepared

