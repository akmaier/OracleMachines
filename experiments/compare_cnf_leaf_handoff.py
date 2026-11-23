#!/usr/bin/env python3
"""Measure one-use missing-leaf preparation at the native acquisition boundary."""
from collections import Counter
from copy import deepcopy
from contextlib import nullcontext
from unittest.mock import patch
from pathlib import Path
import random, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_prepared_partial as prior
from experiments.cnf_template_preparation import prepare_and_publish
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_carried_origins import carried_origins
from experiments.cnf_leaf_handoff import run_after_pool_miss

base = prior.base
binding, bound, read_zip, restore = prior.binding, prior.bound, prior.read_zip, prior.restore
TABLES = prior.TABLES
PARENT = Path('experiments/results/cnf-carried-origins')
MODES = ('baseline', 'carried', 'handoff')
FILES = ('experiments/cnf_leaf_handoff.py', 'solver/test_cnf_leaf_handoff.py', 'experiments/compare_cnf_leaf_handoff.py')


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
        'Same twenty-three sources and six supplied guards. Native baseline, preceding carried-origin policy and leaf-handoff policy run in four alternating serial orders. No broader coverage or held-out discovery claim.',
        'Only the internal missing-leaf consumer changes. It receives the immutable source/name/key triple already constructed from the copied target. One identity-bound use restores ordinary canonicalization before recursion, proof checking or publication.',
        'No external prepared triple, general cache, capacity sizing, new solver rule or production default. The synchronous partial call requires exclusive solver ownership. Preparation, all native reads and checks, persistence and cold replay remain charged.',
        'Require identical native deltas, hints, routes, decisions, expansion counts and chronological origins. Counters and independent profiles expose saved normalization; temporary references are not retained-memory savings.'
    ]
    base.write(out / 'protocol.json', p)


def worker(out, p, policy):
    with carried_origins() if policy != 'baseline' else nullcontext():
        with patch.object(prior, 'run_after_pool_miss', run_after_pool_miss) if policy == 'handoff' else nullcontext():
            prior.worker(out, p, 'baseline' if policy == 'baseline' else 'prepared')
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
