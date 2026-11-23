"""Preserve a cheap unit conflict before lazily constructing a learned cover.

Candidate filtering is only a scheduling heuristic. Native publication rechecks
the full source identity and retained trace; a nonconflicting trace is reused by
the existing screened native fallback. All gate and miss work remains charged.
"""
import time
from experiments.cnf_conditional_unit_support import fixed_pairs
from experiments.cnf_learned_conditional import LearnedCoverBank
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import propagate
from experiments.cnf_transported_partition import native_query


def has_candidate(entries, guard, counts):
    fixed = sorted([[v, bit] for v, bit in fixed_pairs(guard).items()])
    for entry in entries:
        counts['unit_gate_index_entries'] += 1
        if not entry['rejected'] and entry['guard'] == fixed:
            counts['unit_gate_candidate_hits'] += 1
            return True
    return False


def run_after_pool_miss(solver, prepared, guard, entries, budget, counts, *, use_covers=True):
    """Return routing evidence; unknown results retain native budget semantics."""
    if type(budget) is not int or budget < 0:
        raise ValueError('Invalid native expansion budget')
    bank = LearnedCoverBank(solver, entries)
    screen = learned = None
    if has_candidate(entries, guard, counts):
        tick = time.perf_counter()
        _, trace, conflict = propagate(prepared.cnf, counts)
        counts['unit_gate_screen_seconds'] += time.perf_counter() - tick
        screen = dict(root=prepared.key, trace=trace, conflict=conflict)
        counts['unit_gate_screens'] += 1
        if conflict is not None:
            counts['unit_gate_conflicts'] += 1
        elif use_covers:
            tick = time.perf_counter()
            learned = bank.reuse(prepared.target, guard)
            counts['unit_gate_cover_seconds'] += time.perf_counter() - tick
    if learned is not None:
        counts.update(bank.counts)
        return dict(route='learned-cover', learned=learned, screen=screen, stopped=False)
    route = 'native' if screen is None else 'unit-conflict' if screen['conflict'] is not None else 'unit-fallback'
    before = dict(solver.counts)
    stopped = False
    if screen is None:
        outcome = acquire(solver, prepared.target, budget)
        stopped = outcome['result'] is None
    else:
        try:
            native_query(solver, prepared.target, budget, screen)
        except RuntimeError as error:
            if str(error) != BUDGET_MESSAGE:
                raise
            stopped = True
    counts.update({'preliminary_' + k: v for k, v in before.items()})
    if not stopped:
        bank.register(prepared, guard, solver.counts.get('expanded_nodes', 0))
    counts.update(bank.counts)
    return dict(route=route, learned=None, screen=screen, stopped=stopped)
