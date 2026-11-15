#!/usr/bin/env python3
"""Exhaustively audit this checkpoint's small projection and pending frontier.

This is a bounded diagnostic, not an arbitrary-CNF projection algorithm.
"""
from collections import Counter
import gzip
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_affine_projection import check_projection, check_boundary, lift_projection
from experiments.cnf_materialized_checkpoint import sha
from experiments.cnf_residual_dag import holds
from experiments.continue_cnf_case1121_discovery import read_archive, sha_key


def load(path):
    return json.loads(Path(path).read_text())


def shape(cnf):
    return [len({abs(x) for c in cnf for x in c}), len(cnf), sum(map(len, cnf))]


def analyze(out):
    started = time.perf_counter()
    report = load(out/'report.json')
    cold = load(out/'reconstruction.json')
    assert cold['passed'] and cold['report_sha256'] == sha(out/'report.json')
    for source, digest in report['fingerprints'].items():
        assert sha(source) == digest
    delta = report['delta']
    assert sha(delta['path']) == delta['sha256']
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'delta'
        path.write_bytes(gzip.decompress(Path(delta['path']).read_bytes()))
        assert sha(path) == delta['database_sha256']
        with sqlite3.connect(path) as db:
            nodes = {k: json.loads(p) for k, p in db.execute('SELECT id,payload FROM cnf_patterns_v1')}
    projections = []
    for key, node in nodes.items():
        if node['kind'] != 'project':
            continue
        cnf = node['cnf']
        variables = sorted({abs(x) for c in cnf for x in c})
        assert len(variables) <= 16, 'Exhaustive diagnostic is deliberately bounded'
        affine = node['profile']['evidence']['explicit_affine']
        projection = node['profile']['projection']
        keep = projection['keep']
        counts = Counter()
        check_projection(affine['equations'], keep, projection['certificate'], counts)
        check_boundary(projection['certificate'], projection['blocks'], counts)
        target = [cnf[i] for i in affine['leftovers']] + [c for block in projection['blocks'] for c in block]
        child = nodes[node['edge']['key']]
        mapping = dict(enumerate(node['edge']['names'], 1))
        named_child = [[mapping[abs(x)] if x > 0 else -mapping[abs(x)] for x in c] for c in child['cnf']]
        canonical = lambda cs: sorted(tuple(sorted(c)) for c in cs)
        assert canonical(target) == canonical(named_child)
        projected_models, source_models = set(), 0
        for bits in itertools.product((False, True), repeat=len(variables)):
            model = dict(zip(variables, bits))
            if holds(cnf, model):
                source_models += 1
                projected_models.add(tuple(model[v] for v in keep))
        target_models = set()
        for bits in itertools.product((False, True), repeat=len(keep)):
            model = dict(zip(keep, bits))
            if holds(target, model):
                target_models.add(bits)
                lifted = lift_projection(affine['equations'], keep, projection['certificate'], model, counts)
                assert all(lifted[v] == model[v] for v in keep) and holds(cnf, lifted)
        assert projected_models == target_models
        projections.append(dict(source_sha256=sha_key(key), source_shape=shape(cnf), target_shape=shape(target),
            equations=len(affine['equations']), leftover_clauses=len(affine['leftovers']),
            eliminated_variables=len(projection['certificate']['internal']),
            boundary_widths=[projection['certificate']['rows'][i]['mask'].bit_count() for i in projection['certificate']['boundary']],
            encoded_clauses=sum(map(len, projection['blocks'])),
            encoded_literals=sum(len(c) for block in projection['blocks'] for c in block),
            source_assignments=2**len(variables), boundary_assignments=2**len(keep),
            satisfying_source_assignments=source_models, satisfying_boundary_assignments=len(target_models),
            lifted_models=len(target_models), target_kind=child['kind'], counts=dict(counts)))
    pending = []
    for bound in report['arms']:
        if bound['batch'] != 3:
            continue
        assert sha(bound['path']) == bound['sha256']
        arm = load(bound['path'])
        operation = read_archive(arm['steps'][-1]['operation'])
        branches = operation['acquisition']['branches']
        assert len(arm['entered_but_unstored_sha256']) == 0
        assert operation['pending'] and [(b['pending'], len(b['admitted'])) for b in branches] == [(False, 16), (True, 0)]
        pending.append(dict(repeat=bound['repeat'], source_shape=arm['steps'][-1]['source_shape'],
            entered_but_unstored=0, pending=True,
            branch_pending=[b['pending'] for b in branches], branch_admitted=[len(b['admitted']) for b in branches]))
    assert len(projections) == 1 and len(pending) == 2
    result = dict(passed=True, report_sha256=sha(out/'report.json'), reconstruction_sha256=sha(out/'reconstruction.json'),
        source_sha256=sha(__file__), projections=projections, pending_frontiers=pending,
        diagnostic_seconds=time.perf_counter()-started,
        limitations=['Exhaustive diagnostic costs are additional to producer and cold replay; this is not a runtime comparison.',
            'Projection applies to explicitly recognized affine equations and eliminates only variables absent from leftover clauses.',
            'Boundary CNF encoding can be exponential in equation width; the existing encoding budget can reject projection.',
            'No shared boundary identity across unrelated originals or complete arbitrary-SAT classification is established.'])
    (out/'projection-findings.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    analyze(Path(sys.argv[1]))
