"""Validate a complete portable result and construct its owned session once.

Only this function creates the handoff. No externally supplied 'already checked'
flag, digest or prepared token is accepted. The private session layout belongs
to the frozen PreparedB6Search implementation recorded in the source ledger.
"""
from copy import deepcopy
from experiments.cnf_prepared_b6_search import PreparedB6Search,candidate


def restore(*inputs,result,counts):
    # Keep the full result contract, not just the cursor's failure traces.
    if type(result) is not dict or set(result)!={'action','program','cursor'}:raise ValueError('Invalid cursor result')
    if result['action']!='searched':raise ValueError('Invalid B6 action')
    if type(result['cursor']) is not dict:raise ValueError('Missing cursor state')
    if type(result['program']) is not dict or type(result['program'].get('trace_limit')) is not int:raise ValueError('Invalid cursor program')
    owned=deepcopy(inputs);saved=deepcopy(result);counts['prepared_input_copies']+=1;counts['restore_result_copies']+=1
    program=saved['program'];trace_limit=program['trace_limit']
    prepared,bank,ids,order,binding=candidate.prepare(*owned,counts,trace_limit=trace_limit)
    state=candidate.load(prepared,order,binding,saved['cursor'],counts,trace_limit)
    queue,promoted,tested,completed,probes,found,terminal=state
    candidate.prior.check_program(prepared[0],prepared[13],program,counts)
    if program!=candidate._program(probes,terminal,trace_limit,program['reason']):raise ValueError('Program disagrees with cursor')
    # Allocate the mutable continuation only after every full-result check has
    # succeeded. All retained inputs have been copied/normalized privately.
    session=object.__new__(PreparedB6Search)
    session._queue=queue;session._promoted=promoted;session._tested=tested
    session._completed=completed;session._probes=probes;session._found=found;session._terminal=terminal
    session._binding=binding;session._prefix=tuple(map(tuple,owned[13]['units']));session._ids=tuple(ids);session._trace_limit=trace_limit
    session._bank=tuple(map(tuple,bank));session._index=None;session._pending=None
    counts['prepared_sessions']+=1;counts['b6_continued_cursors']+=1;counts['checked_b6_restores']+=1
    return session
