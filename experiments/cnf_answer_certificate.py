"""Project a checked resolution archive to a current-answer certificate.

The complete archive remains the caller's retained knowledge. This function
does not mutate it or replace its role in later reuse. It checks even unused
input records before projecting; replay of the result uses the old checker.
"""
from collections import Counter
from copy import deepcopy
from experiments import cnf_resolution_learning as resolution


def project(source, archive, counts=None):
    counts = Counter() if counts is None else counts
    result = resolution.check_result(source, archive, counts)
    base = len(resolution.prior.prior.previous.capacity.canonical(source, counts))
    records = archive['derivations']
    needed = set()
    originals = set()
    pending = [archive['conclusion']] if archive['kind'] == 'unsat' else []
    while pending:
        index = pending.pop()
        counts['answer_projection_reference_visits'] += 1
        if index < base:
            originals.add(index)
        elif index not in needed:
            needed.add(index)
            start, steps, _ = records[index - base]
            pending.append(start)
            pending.extend(ref for _, ref in steps)
    kept = sorted(needed)
    mapping = {old: base + i for i, old in enumerate(kept)}

    def remap(index):
        return index if index < base else mapping[index]

    derived = []
    for old in kept:
        start, steps, clause = records[old - base]
        derived.append([remap(start), [[v, remap(ref)] for v, ref in steps], list(clause)])
        counts['answer_projection_copied_literals'] += len(clause)
        counts['answer_projection_copied_steps'] += len(steps)
    proof = dict(format=resolution.FORMAT, kind=archive['kind'],
                 witness=deepcopy(archive['witness']), derivations=derived,
                 conclusion=remap(archive['conclusion']) if archive['kind'] == 'unsat' else None)
    if resolution.check_result(source, proof, counts) != result:
        raise ValueError('Projection changed the checked answer')
    return proof, dict(original_derivations=len(records), retained_derivations=len(kept),
                       omitted_derivations=len(records) - len(kept),
                       reached_original_clauses=len(originals),
                       scope='Answer only; complete archive remains required for full future knowledge reuse.')
