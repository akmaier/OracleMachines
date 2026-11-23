#!/usr/bin/env python3
"""Price unit gating, retained-prefix fallback and learned covers separately."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import random, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_learned_conditional as prior
from experiments.cnf_template_preparation import prepare_and_publish
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_unit_cover_gate import run_after_pool_miss

base = prior.base
binding, bound, read_zip, restore = prior.binding, prior.bound, prior.read_zip, prior.restore
TABLES = prior.TABLES
PARENT = Path('experiments/results/cnf-learned-conditional')
MODES = ('baseline', 'learned', 'gate-only', 'unit-gated')
FILES = ('experiments/cnf_unit_cover_gate.py', 'solver/test_cnf_unit_cover_gate.py', 'experiments/compare_cnf_unit_cover_gate.py')


def prepare(out):
    assert not (out / 'protocol.json').exists()
    parent = base.load(PARENT / 'checkpoint.json'); old = base.load(PARENT / 'protocol.json')
    cases = deepcopy(bound(old['cases'])); rng = random.Random(202611231351)
    for origin in (16, 7):
        for index in range(2):
            original = cases[origin]; deleted = rng.randrange(len(original['source']))
            cases.append(dict(index=len(cases), label=f'unit-gate-additional-{origin}-{index}',
                source=[cl for i, cl in enumerate(original['source']) if i != deleted],
                queries=deepcopy(original['queries']), deleted_clause=original['source'][deleted], parent_case=origin))
    assert len(cases) == 23
    base.write(out / 'cases.json', cases)
    for f, h in parent['source_fingerprints'].items(): assert base.sha(f) == h, f
    p = deepcopy(old)
    p.update(parent=binding(PARENT / 'checkpoint.json'), parent_manifest=binding(PARENT / 'manifest.json'),
        base_protocol=binding(PARENT / 'protocol.json'), cases=binding(out / 'cases.json'),
        orders=[list(MODES), list(reversed(MODES))] * 2,
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}})
    p['limitations'] += [
        'Twenty-three sources with six supplied guards: the nineteen previous sources followed by four fixed-seed single-clause deletions from cases 16 and 7. No outcomes were filtered before measurement; these related edits are not an external benchmark.',
        'Four policies in four alternating serial orders. Gate-only uses the candidate metadata filter and retained unit-prefix fallback, but never extracts or applies learned covers; unit-gated adds that existing cover route only after a nonconflicting screen.',
        'Screening runs only after static-template and existing-pool misses with an eligible same-guard descriptor. A conflict uses the existing full-target native unit verifier; a missed cover reuses the checked prefix in native fallback.',
        'The expansion budget counts native dispatches, not screens or certificate checks. A unit conflict can publish at zero expansion budget; screen, recognition and verification costs remain charged. Unsuccessful bounded native work remains unresolved.',
        'New gate counters and per-query timings include failed gates, discovery and preparation before fallback resets its solver counters. Complete-worker cold answer replay and separate cold hint validation remain reported.'
    ]
    base.write(out / 'protocol.json', p)


def query(s, case, q, policy, hints, banks, budget):
    tick = time.perf_counter(); s.counts = Counter(); c = Counter()
    hints['format'] = 'learned-conditional-cache-v1'; hints['learned'] = banks
    prepared, route = prepare_and_publish(s, case['source'], hints['entries'][q['template']]['template'], q['assignment'], c)
    evidence = dict(screen=None, learned=None, stopped=False)
    if route is None:
        route = try_pools(s, prepared.cnf, prepared.key)
        if route is None:
            evidence = run_after_pool_miss(s, prepared, q['assignment'], banks, budget, c, use_covers=policy == 'unit-gated')
            route = evidence['route']
    node = s._read(prepared.key, prepared.cnf, purpose='conditional_result')
    status = 'unresolved' if node is None else 'sat' if node['answer'] else 'unsat'
    return dict(case=case['index'], label=case['label'], template=q['template'], assignment=q['assignment'],
        root=prepared.key, status=status, route=route, recovery=None, screen=evidence['screen'],
        learned=evidence['learned'], stopped=evidence['stopped'], counts=dict(c), metrics=dict(s.counts),
        expanded_nodes=s.counts.get('expanded_nodes', 0), seconds=time.perf_counter() - tick)


def worker(out, p, policy):
    if policy in ('gate-only', 'unit-gated'):
        prior.query = lambda s, case, q, mode, hints, banks, budget: query(s, case, q, policy, hints, banks, budget)
    prior.worker(out, p, 'learned' if policy in ('gate-only', 'unit-gated') else policy)
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
