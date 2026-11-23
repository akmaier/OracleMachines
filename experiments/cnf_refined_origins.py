"""Admit selected completed partial proofs as lazy origins for later queries.

The eligibility heuristic is at least two native expansion dispatches during a
completed partial recomposition. Positive and stopped outcomes never qualify.
It predicts no future benefit. Existing guard filters, limits, extraction,
candidate ranking and native proof checks determine all subsequent use.
"""
from copy import deepcopy
from experiments import cnf_leaf_handoff as previous
from experiments.cnf_conditional_unit_support import fixed_pairs
from experiments.cnf_learned_conditional import origin_source


def register_recomposed(solver, prepared, guard, entries, evidence, counts,
                        *, entry_limit=16, byte_limit=262144):
    """Return admission metadata, never an answer or a prepared certificate."""
    if evidence['route'] != 'partial-cover' or evidence['stopped']:
        return None
    expanded = solver.counts.get('expanded_nodes', 0)
    if expanded < 2:
        counts['refined_small_skips'] += 1
        return None
    # Acquisition has committed; a stopped prefix is never a new root origin.
    if solver.db.active or solver.db.in_transaction:
        raise RuntimeError('Recomposed admission requires committed state')
    node = solver._read(prepared.key, prepared.cnf, purpose='refined_register')
    if node is None or node['answer'] is not False:
        counts['refined_positive_or_missing_skips'] += 1
        return None
    fixed = sorted([[v, b] for v, b in fixed_pairs(guard).items()])
    names = list(prepared.names)
    if any(e['origin'] == prepared.key and e['names'] == names and e['guard'] == fixed for e in entries):
        counts['refined_duplicate_skips'] += 1
        return None
    bank = previous.PartialCoverBank(solver, entries, entry_limit=entry_limit, byte_limit=byte_limit)
    entry = dict(origin=prepared.key, names=names, guard=fixed, cover=None, rejected=False)
    # Validate the source-coordinate map before persistent hint admission.
    source = origin_source(solver, entry)
    counts['refined_binding_literals'] += sum(map(len, source))
    entries.append(entry)
    while len(entries) > bank.entry_limit or bank.encoded_bytes() > bank.byte_limit:
        entries.pop(0)
        counts['refined_evictions'] += 1
    counts.update(bank.counts)
    admitted = any(e is entry for e in entries)
    counts['refined_admissions'] += int(admitted)
    return dict(origin=prepared.key, names=deepcopy(names), guard=deepcopy(fixed),
                expanded_nodes=expanded, admitted=admitted)


def run_after_pool_miss(solver, prepared, guard, entries, budget, counts):
    result = previous.run_after_pool_miss(solver, prepared, guard, entries, budget, counts)
    admission = register_recomposed(solver, prepared, guard, entries, result, counts)
    # This metadata describes a proposal after the query. It cannot be used by
    # that query and survives in the query log for chronological replay.
    if result['partial'] is not None:
        result['partial']['recomposed_admission'] = admission
    return result
