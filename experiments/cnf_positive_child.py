"""Recover a whole-target SAT witness from a positive-terminal proposed child.

The failed-literal proposal guides discovery only. Publication checks the full
target model and does not acquire either the negative premise or child proof.
"""
from collections import Counter
from copy import deepcopy
import time
from experiments.cnf_trace_fallback import select as previous_select
from experiments.cnf_residual_dag import FORMAT, restrict, holds


def recover_model(solver, source, proposal, screen, counts=None):
    counts = Counter() if counts is None else counts
    clause = proposal['clause']
    if (proposal['kind'] != 'guard' or type(clause) is not list or len(clause) != 1
            or type(clause[0]) is not int or not clause[0]):
        raise ValueError('Expected a single-literal proposal')
    _, names, root = solver._canonical(source)
    variable = abs(clause[0]); assumed = clause[0] < 0
    if variable not in names: raise ValueError('Proposal variable is outside target')
    child_source = restrict(source, {variable: assumed}, counts)
    cnf, child_names, child_root = solver._canonical(child_source)
    if screen['root'] != child_root or screen['conflict'] is not None:
        raise ValueError('Unbound positive child')
    fixed = {}
    for literal, cid in screen['trace']:
        if (type(literal) is not int or not literal or type(cid) is not int
                or not 0 <= cid < len(cnf) or abs(literal) in fixed):
            raise ValueError('Invalid child unit trace')
        reason = cnf[cid]; counts['positive_child_reason_literals'] += len(reason)
        if (any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in reason)
                or [l for l in reason if abs(l) not in fixed] != [literal]):
            raise ValueError('Unforced child literal')
        fixed[abs(literal)] = literal > 0
    if restrict(cnf, fixed, counts):
        raise ValueError('Child is not positive-terminal')
    model = {variable: assumed}
    model.update({name: fixed.get(i + 1, False) for i, name in enumerate(child_names)})
    model = {name: model.get(name, False) for name in names}
    counts['positive_target_model_literals'] += sum(map(len, source))
    if not holds(source, model): raise ValueError('Lifted model fails original target')
    counts['positive_child_models'] += 1
    return dict(kind='positive-model', root=root, model=[[v, bit] for v, bit in model.items()])


def select(solver, source, variable_limit=4, counts=None):
    counts = Counter() if counts is None else counts
    choice, trace = previous_select(solver, source, variable_limit, counts)
    child = trace['child']
    screen = None if child is None else child['screen']
    if screen is None or screen['conflict'] is not None or screen['residual_literals'] != 0:
        return choice, trace
    recovered = recover_model(solver, source, trace['proposal'], screen, counts)
    if choice is not None and choice['kind'] == 'fallback-trace':
        counts['fallback_trace_reuses'] -= 1
        counts['fallback_forced_variables'] -= len(trace['discovery']['fixed'])
    trace['previous_reason'] = trace['reason']; trace['reason'] = 'positive-child-model'
    trace['positive_model'] = deepcopy(recovered)
    return recovered, trace


def publish_model(solver, source, choice):
    """Validate a full target witness before storing one ordinary SAT node."""
    started = time.perf_counter(); solver.counts = Counter()
    cnf, names, root = solver._canonical(source); pairs = choice['model']
    if (choice['kind'] != 'positive-model' or choice['root'] != root
            or type(pairs) is not list or len(pairs) != len(names)
            or any(type(p) is not list or len(p) != 2 or type(p[0]) is not int
                   or type(p[1]) is not bool for p in pairs)
            or [p[0] for p in pairs] != list(names)):
        raise ValueError('Unbound full-target model')
    model = dict(pairs); solver.counts['positive_publication_model_literals'] += sum(map(len, source))
    if not holds(source, model): raise ValueError('Invalid full-target model')
    node = solver._read(root, cnf, purpose='positive_child_target')
    if node is None:
        node = dict(format=FORMAT, cnf=[list(c) for c in cnf], answer=True,
                    model=[model[v] for v in names])
        before = solver.counts['inserted_nodes']; solver._store(root, node)
        solver.counts['positive_model_publications'] += solver.counts['inserted_nodes'] - before
    elif node['answer'] is not True:
        raise ValueError('Model contradicts checked target')
    model = dict(zip(names, node['model']))
    solver.counts['source_witness_literal_payload'] += sum(map(len, source))
    n, b = solver.archive_storage()
    return dict(answer=True, model=model, root=root, metrics=dict(solver.counts),
                seconds=time.perf_counter()-started, archive_nodes=n, archive_payload_bytes=b)
