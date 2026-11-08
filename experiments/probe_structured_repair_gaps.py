#!/usr/bin/env python3
"""Diagnose missing coordinated reuse; supplied moves are witnesses, not a solver.

The generator knows the structure. Discovery and certified transition dispatch
are not implemented here. No runtime speedup is inferred from move existence.
"""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_affected_history import digest_rows
from experiments.compare_cnf_matching import domain_cnf


def source_for(family, width, blocks):
    source = []
    for block in range(blocks):
        if family == 'equivalence':
            variables = list(range(block*width+1, (block+1)*width+1))
            for a, b in zip(variables, variables[1:]):
                source.extend([(-a, b), (a, -b)])
        elif family == 'parity':
            variables = list(range(block*3+1, block*3+4))
            for values in itertools.product((False, True), repeat=3):
                if sum(values) % 2:
                    source.append(tuple(-v if bit else v for v, bit in zip(variables, values)))
        else:
            offset = block*width*width
            source.extend(tuple((abs(lit)+offset)*(1 if lit > 0 else -1) for lit in clause)
                          for clause in domain_cnf([range(width)]*width))
    return tuple(source)


def supplied_move(family, width, block, model):
    if family == 'equivalence':
        changed = list(range(block*width+1, (block+1)*width+1))
        var = changed[0]
    elif family == 'parity':
        changed = [block*3+1, block*3+2]
        var = changed[0]
    else:
        offset = block*width*width
        edge = lambda row, col: offset+row*width+col+1
        current = next(col for col in range(width) if model.get(edge(0, col), False))
        target = (current+1) % width
        other = next(row for row in range(1, width) if model.get(edge(row, target), False))
        changed = [edge(0, current), edge(0, target), edge(other, target), edge(other, current)]
        var = edge(0, target)
    update = {v: not model.get(v, False) for v in changed}
    return (var if update[var] else -var,), update


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    cases = []
    for family, widths in [('equivalence', (2, 8, 32)), ('parity', (3,)), ('matching', (2, 4))]:
        for width, blocks in itertools.product(widths, (8, 32)):
            case_id = len(cases)
            base = source = source_for(family, width, blocks)
            moves, records, versions, additions = [], [], [], []
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'probe.sqlite3'
                h = AffectedRepairHistory(path)
                started = time.perf_counter()
                acquired = h.prepare(base)
                preparation = time.perf_counter()-started
                assert acquired['answer']
                version = acquired['version']
                versions.append(version)
                for block in range(blocks):
                    model = h.witness(version)['model']
                    clause, changes = supplied_move(family, width, block, model)
                    expanded = source+(clause,)
                    assert not holds([clause], model)
                    alternative = {**model, **changes}
                    assert holds(expanded, alternative)
                    # Independent check that setting the new unit alone fails.
                    lit = clause[0]
                    assert not holds(source, {**model, abs(lit): lit > 0})
                    before = digest_rows(h)
                    started = time.perf_counter()
                    try:
                        result = h.append_repair(version, clause)
                    except UnsupportedExpansion as error:
                        rejected_seconds = time.perf_counter()-started
                        rejected_metrics = dict(h.counts)
                        assert digest_rows(h) == before
                        fallback_started = time.perf_counter()
                        rebuilt = h.materialize(version)['cnf']+(clause,)
                        result = h.prepare(rebuilt)
                        fallback_seconds = time.perf_counter()-fallback_started
                    else:
                        raise AssertionError('Diagnostic expected a single-variable repair miss')
                    assert result['answer']
                    version, source = result['version'], expanded
                    assert holds(source, h.witness(version)['model'])
                    versions.append(version)
                    additions.append(clause)
                    moves.append(dict(parent_version=versions[-2], clause=clause, changes=changes))
                    records.append(dict(rejected_seconds=rejected_seconds, rejected_metrics=rejected_metrics,
                                        fallback_seconds=fallback_seconds, solver_metrics=result['solver_metrics']))
                storage = h.storage()
                before = digest_rows(h)
                h.close()
                h = AffectedRepairHistory(path)
                for step, v in enumerate(versions):
                    assert h.query(v)['answer']
                    exact = base+tuple(additions[:step])
                    assert h.materialize(v)['cnf'] == exact
                    assert holds(exact, h.witness(v)['model'])
                    if step < len(moves):
                        parent_model = h.witness(v)['model']
                        assert holds(exact+(additions[step],), {**parent_model, **moves[step]['changes']})
                assert h.solver.counts.get('expanded_nodes', 0) == 0
                assert digest_rows(h) == before
                h.close()
                raw = path.read_bytes()
                name = f'archive-{case_id:02d}.sqlite3.gz'
                (out/name).write_bytes(gzip.compress(raw, mtime=0))
            cases.append(dict(family=family, width=width, blocks=blocks, base=base, additions=additions,
                              supplied_moves=moves, versions=versions, records=records,
                              preparation_seconds=preparation, storage=storage,
                              archive=name, database_bytes=len(raw), database_sha256=hashlib.sha256(raw).hexdigest(),
                              row_digest=before, cold_all_versions_checked=True))
            print(family, width, blocks, 'misses', len(records), 'bases', storage['bases'], flush=True)
    files = [Path(__file__), Path('experiments/cnf_affected_history.py'),
             Path('experiments/cnf_repair_history.py'), Path('experiments/cnf_residual_dag.py')]
    report = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  fingerprints={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  cases=cases, limitations=[
                      'Constructed disjoint families; generator supplies structural moves',
                      'No general structural discovery, block repair API or certified move dispatcher implemented',
                      'Full-source witness checking of supplied moves is untimed diagnostic validation',
                      'Operation timings are single samples of the current implementation, not a speedup comparison',
                      'Rejection and fallback times exclude optional digests and supplied-move construction/checking',
                      'In-memory allocation and cross-component boundary maintenance are not profiled'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
