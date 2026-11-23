#!/usr/bin/env python3
"""Measure shared residual and leaf preparation against identical partial-cover proofs."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import random, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partial_cover as prior
from experiments.cnf_template_preparation import prepare_and_publish
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_prepared_partial import run_after_pool_miss

base = prior.base
binding, bound, read_zip, restore = prior.binding, prior.bound, prior.read_zip, prior.restore
TABLES = prior.TABLES
PARENT = Path('experiments/results/cnf-partial-cover')
MODES = ('baseline', 'partial', 'prepared')
FILES = ('experiments/cnf_prepared_partial.py', 'solver/test_cnf_prepared_partial.py', 'experiments/compare_cnf_prepared_partial.py')


def prepare(out):
    assert not (out / 'protocol.json').exists()
    parent = base.load(PARENT / 'checkpoint.json'); old = base.load(PARENT / 'protocol.json')
    cases = deepcopy(bound(old['cases']))
    assert len(cases) == 23
    base.write(out / 'cases.json', cases)
    for f, h in parent['source_fingerprints'].items(): assert base.sha(f) == h, f
    p = deepcopy(old)
    p.update(parent=binding(PARENT / 'checkpoint.json'), parent_manifest=binding(PARENT / 'manifest.json'),
        base_protocol=binding(PARENT / 'protocol.json'), cases=binding(out / 'cases.json'),
        orders=[list(MODES), list(reversed(MODES))] * 2,
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}})
    p['limitations'] += [
        'Same twenty-three sources and six supplied guards. Baseline, preceding partial-cover policy and prepared partial-cover policy run in four alternating serial orders. This is a construction ablation, not broader coverage or held-out pattern discovery.',
        'The prepared route copies the raw target and cover, validates their binding, shares internally constructed residual/name/key frames across unchanged contexts and leaf publication, and keeps all native verification. No external preparation is accepted.',
        'The prepared route resets counters before its initial canonicalization, closing the preceding root-work counter omission. Wall time charged that work in both arms.',
        'Require identical proof deltas, routes, decisions, expansion dispatches, chronological origins and hints between both partial policies. Compare complete worker, persistence and cold reconstruction as well as preparation/query time.'
    ]
    base.write(out / 'protocol.json', p)


def worker(out, p, policy):
    if policy == 'prepared':
        prior.run_after_pool_miss = run_after_pool_miss
    prior.worker(out, p, 'partial' if policy == 'prepared' else policy)
    report = base.load(out / 'report.json'); report['policy'] = policy
    rows = bound(report['queries'])
    report['groups'] = {label: dict(attempts=len(rs), query_seconds=sum(r['seconds'] for r in rs),
        expanded_nodes=sum(r['expanded_nodes'] for r in rs), routes=dict(Counter(r['route'] for r in rs)),
        statuses=dict(Counter(r['status'] for r in rs)))
        for label, rs in [('controls', [r for r in rows if r['case'] < 19]), ('additional', [r for r in rows if r['case'] >= 19])]}
    base.write(out / 'report.json', report)


def run(out):
    p = base.load(out / 'protocol.json'); samples = []
    for repeat, order in enumerate(p['orders']):
        for policy in order:
            dest = out / f'{policy}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), policy], check=True)
            samples.append(dict(policy=policy, repeat=repeat, **binding(dest / 'report.json')))
    means, groups = {}, {}
    for policy in MODES:
        rows = [bound(s) for s in samples if s['policy'] == policy]
        means[policy] = {k: sum(r['summary'][k] for r in rows) / len(rows)
            for k, value in rows[0]['summary'].items() if type(value) in (int, float)}
        groups[policy] = {g: {k: sum(r['groups'][g][k] for r in rows) / len(rows)
            for k in ('attempts', 'query_seconds', 'expanded_nodes')} for g in rows[0]['groups']}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), samples=samples, means=means, groups=groups))
    print(base.encode(dict(means=means, groups=groups)), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': prepare(Path(sys.argv[2]))
    elif sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), sys.argv[4])
    else: run(Path(sys.argv[1]))
