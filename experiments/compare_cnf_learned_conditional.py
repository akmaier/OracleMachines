#!/usr/bin/env python3
"""Price chronological, lazy conditional-cover learning against shared preparation."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_template_preparation as prior
from experiments.cnf_template_preparation import prepare_and_publish
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_probed_partition import acquire
from experiments.cnf_learned_conditional import LearnedCoverBank

base = prior.base
binding, bound, read_zip, restore = prior.binding, prior.bound, prior.read_zip, prior.restore
TABLES = prior.TABLES
PARENT = Path('experiments/results/cnf-template-preparation')
MODES = ('baseline', 'learned')
FILES = ('experiments/cnf_learned_conditional.py', 'solver/test_cnf_learned_conditional.py',
         'experiments/probe_cnf_learned_conditional.py', 'experiments/compare_cnf_learned_conditional.py')
old_query = prior.query


def prepare(out):
    assert not (out / 'protocol.json').exists()
    parent = base.load(PARENT / 'checkpoint.json')
    old = base.load(PARENT / 'protocol.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    p = deepcopy(old)
    p.update(parent=binding(PARENT / 'checkpoint.json'), parent_manifest=binding(PARENT / 'manifest.json'),
             base_protocol=binding(PARENT / 'protocol.json'), exploration=binding(out / 'exploration.json'),
             orders=[list(MODES), list(reversed(MODES))] * 2,
             source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}})
    p['limitations'] += [
        'Chronological nineteen-source, six-supplied-guard stream. The discovery probe inspected the previous stream; this is an informed local experiment, not a held-out benchmark.',
        'Only negative native fallbacks costing at least three expansions register a source-name/origin descriptor. Same-guard candidates are tried oldest-first, at most four; extraction is lazy and capped at 64 node occurrences and 65536 inspected node literals.',
        'At most sixteen descriptors and 262144 encoded JSON bytes are retained. These are serialized-bank caps, not whole-process or transient-memory bounds. All lookup, extraction, checking and miss work is charged.',
        'Complete binary cover paths must imply each checked unit-template assumption; every support clause must occur in the target cofactor. Native split/unit recomposition checks every published target. Partial matches do not decide SAT or UNSAT.',
        'Learned bank serialization is included in worker hint persistence; cold bank validation/reload is measured separately. Initial donor, compact hints, native checking and fallback remain charged.'
    ]
    base.write(out / 'protocol.json', p)


def query(s, case, q, policy, hints, banks, budget):
    tick = time.perf_counter()
    s.counts = Counter()
    c = Counter()
    hints['format'] = 'learned-conditional-cache-v1'
    hints['learned'] = banks
    bank = LearnedCoverBank(s, banks)
    prepared, route = prepare_and_publish(s, case['source'], hints['entries'][q['template']]['template'], q['assignment'], c)
    learned = None
    if route is None:
        route = try_pools(s, prepared.cnf, prepared.key)
        if route is None:
            learned = bank.reuse(prepared.target, q['assignment'])
            if learned is not None:
                assert learned['root'] == prepared.key
                route = 'learned-cover'
            else:
                route = 'native'
                before = dict(s.counts)
                acquire(s, prepared.target, budget)
                c.update({'preliminary_' + k: v for k, v in before.items()})
                bank.register(prepared, q['assignment'], s.counts.get('expanded_nodes', 0))
    node = s._read(prepared.key, prepared.cnf, purpose='conditional_result')
    c.update(bank.counts)
    status = 'unresolved' if node is None else 'sat' if node['answer'] else 'unsat'
    return dict(case=case['index'], label=case['label'], template=q['template'], assignment=q['assignment'],
                root=prepared.key, status=status, route=route, recovery=None, screen=None, learned=learned,
                counts=dict(c), metrics=dict(s.counts), expanded_nodes=s.counts.get('expanded_nodes', 0),
                seconds=time.perf_counter() - tick)


def worker(out, p, policy):
    prior.query = query if policy == 'learned' else old_query
    prior.worker(out, p, 'shared')
    report = base.load(out / 'report.json')
    report['policy'] = policy
    base.write(out / 'report.json', report)


def run(out):
    p = base.load(out / 'protocol.json')
    samples = []
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
                              for k in ('attempts', 'query_seconds', 'expanded_nodes')}
                          for g in rows[0]['groups']}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), samples=samples, means=means, groups=groups))
    print(base.encode(dict(means=means, groups=groups)), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare(Path(sys.argv[2]))
    elif sys.argv[1] == 'worker':
        worker(Path(sys.argv[2]), base.load(sys.argv[3]), sys.argv[4])
    else:
        run(Path(sys.argv[1]))
