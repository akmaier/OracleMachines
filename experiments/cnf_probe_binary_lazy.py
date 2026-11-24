"""Delay whole-residual normalization until raw binary discovery is negative.

The input is an exact canonical cofactor and its complete, nonconflicting unit
propagation result. Misses carry no canonical residual or authority. Hits rerun
SCC on the canonical residual to preserve the preceding gate's proof bytes;
the existing native checker remains the publication boundary.
"""
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_census import closure


def _binary(residual, counts):
    ids = []
    positive = negative = False
    for i, clause in enumerate(residual):
        counts['closure_width_checks'] += 1
        if len(clause) < 2:
            return 'not-unit-closed', ids, None
        if len(clause) == 2:
            ids.append(i)
            counts['closure_binary_literals'] += 2
            positive |= all(lit > 0 for lit in clause)
            negative |= all(lit < 0 for lit in clause)
    if not (positive and negative):
        return 'no-binary' if not ids else 'uniform-binary', ids, None
    counts['closure_scc_calls'] += 1
    _, proof = native.two_cnf(tuple(residual[i] for i in ids), counts)
    return 'binary-unsat' if proof is not None else 'binary-sat', ids, proof


def lazy_closure(canonical, up, counts):
    child, names, key = canonical
    fixed, trace, conflict, _ = up
    if conflict is not None:
        raise ValueError('Expected a nonconflicting probe')
    if not fixed:
        # Already canonical: a raw preflight would only duplicate SCC work.
        counts['lazy_already_canonical_calls'] += 1
        return closure(canonical, up, counts)

    counts['closure_calls'] += 1
    counts['lazy_raw_calls'] += 1
    raw = native.restrict_scan(child, fixed, counts)
    before = counts['closure_scc_calls']
    status, _, raw_proof = _binary(raw, counts)
    counts['lazy_raw_scc_calls'] += counts['closure_scc_calls'] - before
    if raw_proof is None:
        counts['lazy_normalizations_avoided'] += 1
        return dict(status=status, nodes=[])

    # Relabelling and duplicate removal preserve satisfiability, but can alter
    # the SCC traversal/path choices. Reconstruct rather than transport a raw
    # path so publication is byte-identical to the preceding canonical gate.
    counts['lazy_canonical_reconstructions'] += 1
    residual, _ = native.normalize(raw, counts)
    residual_key = native.token(residual, counts)
    before = counts['closure_scc_calls']
    status, ids, proof = _binary(residual, counts)
    counts['lazy_certificate_scc_calls'] += counts['closure_scc_calls'] - before
    if proof is None:
        raise AssertionError('Raw binary contradiction lost during normalization')
    counts['closure_refutations'] += 1
    for label in ('forward', 'backward'):
        proof[label] = [[literal, ids[cid]] for literal, cid in proof[label]]
        counts['closure_path_edges'] += len(proof[label])
    return dict(status=status, residual=residual, root=residual_key,
        binary_clauses=len(ids), nodes=[
            dict(key=residual_key, node=dict(format=native.FORMAT,
                cnf=[list(c) for c in residual], answer=False, proof=proof)),
            dict(key=key, node=dict(format=native.FORMAT,
                cnf=[list(c) for c in child], answer=False,
                proof=dict(kind='units', trace=[list(p) for p in trace],
                           child=residual_key)))])
