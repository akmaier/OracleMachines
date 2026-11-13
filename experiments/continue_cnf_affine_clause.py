#!/usr/bin/env python3
"""Extend the saved-split checkpoint with checked affine/one-clause routes.

The immutable inventory stays byte-identical. The fifth evidence list contains
the new positive family proofs; future callers must retain it via routes_for.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_saved_splits import restore_checkpoint as restore_parent
from experiments.compare_cnf_split_batch import routes_for as old_routes, closure
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, compressed
from experiments.cnf_affine_clause import discover, check_certificate, attach, record_key
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_target_probe import remaining
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.continue_cnf_learning import preserved_reference
from experiments.cnf_pattern_inventory import encode

PARENT = Path('experiments/results/cnf-saved-splits/report.json')
FORMAT = 'affine-one-clause-checkpoint-v1'
FILES = ['experiments/cnf_affine_clause.py', 'experiments/continue_cnf_affine_clause.py',
         'solver/test_cnf_affine_clause.py']


def routes_for(h, evidence):
    if len(evidence) != 5: raise ValueError('Expected preserved routes plus affine family proofs')
    routes = old_routes(h, evidence[:4])
    for record in evidence[4]: attach(h, routes, record, Counter())
    return routes


def restore_checkpoint(report_path, path, tmp):
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or sha(r['parent']['path']) != r['parent']['sha256']:
        raise ValueError('Changed affine checkpoint parent')
    for filename, digest in r['fingerprints'].items():
        if sha(filename) != digest: raise ValueError('Changed affine checkpoint implementation')
    parent, *evidence = restore_parent(Path(r['parent']['path']), path, tmp)
    if (parent['final_closed'] != r['baseline_closed'] or digests(path) != r['logical_table_digests']
            or sha(path) != r['inventory_sha256']):
        raise ValueError('Changed preserved affine checkpoint inventory')
    return r, *evidence, read_archive(r['families'])


def selected_frontiers(h, roots, routes, closed):
    cases = [i for i,b in enumerate(closed) if not b]
    rows = remaining(h, [dict(source=roots[i], target=roots[i]) for i in cases], routes, Counter())
    leaves = {}
    for case, row in zip(cases, rows, strict=True):
        if row['closed']: raise ValueError('Closed case in open frontier')
        for leaf in row['leaves']:
            if leaf['pending']: raise ValueError('Unacquired leaf needs a separate discovery policy')
            leaves.setdefault(leaf['source'], []).append(case)
    return dict(cases=cases, frontiers=rows), leaves


def reference(records, r, parent, out, tmp):
    started = time.perf_counter(); ep = parent['reference']; path = tmp/'reference'
    if sha(ep['path']) != ep['sha256']: raise ValueError('Changed parent reference')
    unpack(ep['path'], path, ep['database_sha256']); shutil.copyfile(path, tmp/'reference-seed')
    seed_seconds = time.perf_counter()-started
    solver = AccountedResidualSolver(path); rows = []; originals = []; started = time.perf_counter()
    for record in records:
        proof = record['proof']; result = solver.solve(proof['cnf'])
        assert result['answer'] == check_certificate(proof)['sat']
        if result['answer']: assert holds(proof['cnf'], result['model'])
        rows.append(dict(id=record_key(record), result=result))
    for case in r['gains']:
        result = solver.solve(r['cases'][case]['source'])
        if result['answer']: assert holds(r['cases'][case]['source'], result['model'])
        originals.append(dict(case=case, result=result))
    solver.close(); elapsed = time.perf_counter()-started; before = sha(path)
    started = time.perf_counter(); solver = ResidualSolver(path)
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
    nodes = len(solver.checked); solver.close(); assert sha(path) == before
    cold = time.perf_counter()-started; archive = out/'reference.sqlite3.gz'
    started = time.perf_counter(); compressed(path, archive); persistence = time.perf_counter()-started
    return dict(rows=rows, originals=originals, seed_seconds=seed_seconds, seconds=elapsed, cold_seconds=cold,
        persistence_seconds=persistence, verified_nodes=nodes, preserved_nodes=preserved_reference(tmp/'reference-seed',path),
        path=str(archive), sha256=sha(archive), database_sha256=before,
        database_bytes=path.stat().st_size, compressed_bytes=archive.stat().st_size)


def run(out):
    pipeline = time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); path = tmp/'history'; started = time.perf_counter()
        parent, *evidence = restore_parent(PARENT, path, tmp)
        r = dict(format=FORMAT, parent=dict(path=str(PARENT), sha256=sha(PARENT)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
            fingerprints={f:sha(f) for f in FILES}, cases=parent['cases'], options=parent['options'],
            baseline_closed=parent['final_closed'], restore_seconds=time.perf_counter()-started,
            logical_table_digests=digests(path), inventory_sha256=sha(path), inventory_bytes=path.stat().st_size,
            limitations=['All selected open leaves of 83 reused development originals, not a fresh holdout or all possible routes.',
                'Only explicit complete parity encodings plus at most one leftover clause. Multiple clauses remain unresolved.',
                'Family proofs are sidecars; unchanged historical inventory is not retroactively relabelled.',
                'Cold replay checks reachable route dependencies, not every unrelated node. Parent full audit is retained.',
                'Dense nullspace representation can use quadratic bits; input extraction, checking and prior construction are charged.',
                'No Lean refinement, minimum-cost expansion or uniformly polynomial arbitrary-SAT claim.'])
        started = time.perf_counter(); h = BudgetedInventory(path, **r['options']); h.set_admission_budget(0)
        routes = old_routes(h, evidence); roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h, roots, routes, Counter())[0] == r['baseline_closed']
        navigation, leaves = selected_frontiers(h, roots, routes, r['baseline_closed'])
        r['preparation_seconds'] = time.perf_counter()-started
        print(json.dumps(dict(open_originals=len(navigation['cases']), selected_leaves=len(leaves))), flush=True)
        started = time.perf_counter(); records = []; diagnostics = []; counts = Counter()
        for source, cases in sorted(leaves.items()):
            node = h._load(source); affine = node['profile']['evidence']['explicit_affine']
            proof = discover(node['cnf'], counts, affine=affine)
            summary = check_affine(node['cnf'], affine, counts)
            diagnostics.append(dict(source=source, original_cases=cases, clauses=len(node['cnf']),
                variables=len({abs(l) for c in node['cnf'] for l in c}), affine=summary,
                accepted=proof is not None, result=None if proof is None else check_certificate(proof)))
            if proof is not None:
                record = dict(source=source, proof=proof); attach(h, routes, record, counts); records.append(record)
        r['acquisition'] = dict(seconds=time.perf_counter()-started, counts=dict(counts),
            tested=len(leaves), accepted=len(records), new_inventory_states=len(h.admitted))
        started = time.perf_counter(); r['families'] = archive_json(out/'families.json.gz', records)
        r['selection'] = archive_json(out/'selection.json.gz', dict(navigation=navigation, diagnostics=diagnostics))
        r['family_selection_persistence_seconds'] = time.perf_counter()-started
        started = time.perf_counter(); summary, plan = closure(h, roots, routes, r['baseline_closed']); r.update(summary)
        after, after_leaves = selected_frontiers(h, roots, routes, r['final_closed'])
        r['composition_seconds'] = time.perf_counter()-started
        r['remaining_originals'] = len(after['cases']); r['remaining_selected_leaves'] = len(after_leaves)
        started = time.perf_counter(); r['certificate'] = archive_json(out/'coverage.json.gz',plan)
        r['open_originals'] = archive_json(out/'open-originals.json.gz',after)
        r['coverage_persistence_seconds'] = time.perf_counter()-started
        assert not h.admitted; h.close(); assert sha(path) == r['inventory_sha256']
        r['reference'] = reference(records, r, parent, out, tmp)
        print(json.dumps(dict(accepted=len(records), closed=sum(r['final_closed']), gains=r['gains'])), flush=True)
    r['pipeline_seconds'] = time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(seconds=r['pipeline_seconds'], acquisition=r['acquisition'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output',type=Path); run(p.parse_args().output)
