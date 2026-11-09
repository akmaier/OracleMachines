#!/usr/bin/env python3
"""Read-only next-gap probe: Horn membership after consistent variable flips.

This is the established pair-constraint reduction, not a new SAT class or an
integrated inventory policy. Positive flips and negative implication paths are
checked here. Root recomposition, persistence and matched acquisition remain open.
"""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_residual_dag import holds, two_cnf


def probe(cnf):
    clauses = [list(pair) for c in cnf for pair in itertools.combinations(c, 2)]
    counts = Counter(); flips, refutation = two_cnf(clauses, counts)
    if flips is not None:
        assert holds(clauses, flips)
        transformed = [[-lit if flips.get(abs(lit), False) else lit for lit in c] for c in cnf]
        assert all(sum(lit > 0 for lit in c) <= 1 for c in transformed)
        certificate = dict(flipped=sorted(v for v, value in flips.items() if value))
    else:
        variable = refutation['variable']
        for name, start, finish in (('forward', variable, -variable), ('backward', -variable, variable)):
            previous = start
            for target, cid in refutation[name]:
                assert type(cid) is int and 0 <= cid < len(clauses)
                assert sorted(clauses[cid]) == sorted([-previous, target])
                previous = target
            assert previous == finish
        certificate = refutation
    return dict(recognized=flips is not None, certificate=certificate,
                pair_constraints=len(clauses), counts=dict(counts))


def main(output):
    if output.exists():raise FileExistsError(output)
    # Exhaustive normalized two-variable formulas, independently enumerating flips.
    small = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
             for signs in itertools.product((-1, 0, 1), repeat=2)]
    for mask in range(512):
        cnf = [c for i, c in enumerate(small) if mask >> i & 1]
        expected = any(all(sum((lit > 0) != bits[abs(lit)-1] for lit in c) <= 1 for c in cnf)
                       for bits in itertools.product((False, True), repeat=2))
        assert probe(cnf)['recognized'] == expected
    path = Path('experiments/results/cnf-implied-subsumption/mechanisms.json')
    frontier = json.loads(path.read_text())['frontier']; rows = []
    started = time.perf_counter()
    for row in frontier:
        rows.append(dict(key_sha256=row['key_sha256'], cnf=row['cnf'], **probe(row['cnf'])))
    elapsed = time.perf_counter()-started
    result = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        solver_sha256=hashlib.sha256(Path('experiments/cnf_residual_dag.py').read_bytes()).hexdigest(),
        input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=rows,
        recognized=sum(r['recognized'] for r in rows), pair_constraints=sum(r['pair_constraints'] for r in rows),
        diagnostic_seconds=elapsed, exhaustive_two_variable_cases=512,
        source='https://people.mpi-inf.mpg.de/~mehlhorn/ftp/RenamingHorn.pdf',
        limitations=['Read-only probe on 148 selected unresolved leaves, not an integrated or root-coverage improvement',
            'Positive flips directly checked on every clause; negative pair-formula implication paths independently replayed',
            'Pair construction costs sum of binomial clause widths; no claim to implement the faster recognition algorithm',
            '512 tiny formulas compare all variable flips; this complements the established reduction, not a proof of all Python behavior',
            'Diagnostic time includes construction, SCC solving and certificate checks; excludes loading, serialization and exhaustive self-check',
            'New policy identities, exact model transport, cold replay and whole-source recomposition remain obligations'])
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('recognized', 'pair_constraints', 'diagnostic_seconds')}), flush=True)


if __name__ == '__main__':main(Path(sys.argv[1]))
