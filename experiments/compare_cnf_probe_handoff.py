#!/usr/bin/env python3
"""Measure exact child handoff at two explicit selected-payload capacities."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import compare_cnf_whole_pool_priority as previous
from experiments.validate_cnf_ranked_binary_targets import TABLES as ALL_TABLES
from functools import partial
from experiments.cnf_probe_handoff import ProbeHandoffSolver
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = previous.base, previous.binding, previous.bound
PARENT = Path('experiments/results/cnf-whole-pool-priority')
TABLES = previous.TABLES
MODES = ('priority', 'small', 'large')
SPLITS = ('exposed', 'holdout')
FILES = ('experiments/cnf_probe_handoff.py', 'solver/test_cnf_probe_handoff.py',
    'experiments/compare_cnf_probe_handoff.py','experiments/inspect_cnf_probe_handoff.py')
CLASSES = dict(priority=WholePoolPrioritySolver,small=ProbeHandoffSolver,
    large=partial(ProbeHandoffSolver,handoff_bytes=2*1024*1024))


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (114, 138):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611240057)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    old_protocol = bound(parent['whole_pool_priority']['protocol'])
    exposed = bound(old_protocol['cases']['holdout'])
    base.write(out/'cases.json', exposed)
    assert not {c['root'] for c in exposed} & {c['root'] for c in cases}
    base.write(out/'holdout-cases.json', cases)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'prior'
        restore_archive(parent['reference_union'], path)
        con = sqlite3.connect(path)
        try:
            known = {k for t in ALL_TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:
            con.close()
    base.write(out/'protocol.json', dict(parent=binding(PARENT/'checkpoint.json'),
        parent_manifest=binding(PARENT/'manifest.json'), previous_protocol=parent['whole_pool_priority']['protocol'],
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json')),
        novelty={s:[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cs]
                 for s,cs in (('exposed',exposed),('holdout',cases))},
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        capacities=dict(small=256*1024,large=2*1024*1024),
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'Previous 108/132 holdout is exposed. Fresh 114/138, seed 202611240057: 72 queries, 48 distinct roots, six families, no outcome filtering. Freeze before any fresh evaluation.',
            'Three arms: previous complete-pool priority; identical discovery with 256 KiB handoff; identical discovery with 2 MiB handoff. Four alternating serial repetitions. The two capacities are motivated by the exposed prefix; neither is tuned on fresh outcomes.',
            'Only source CNFs enter search. Start empty, keep checked chronological results. Parent novelty is recorded without seeding answers. Every arm retains native cap 256 and unchanged verification and priority.',
            'Offers bind source and counters by identity, exact one-variable Boolean assignment, and child by identity. They are single-use local preparation, never answers. Verification suppresses hints. Unused offers and retained ancestor offers are charged.',
            'Cap counts conservative selected offer payload including shared data repeatedly. It excludes control containers, stack, allocator overhead and construction transients. RSS and selected retained solver graphs are separate. Warm/cold query timings include dispatcher installation.',
            'Charge preparation, matching, trace freeze/copy, sizing, failed admission, discard, persistence, serialization, cold replay/reconstruction, compression and RSS. Imports, source hashing and case loading precede the complete-worker timer; final report bookkeeping follows it.',
            'Two earlier 41-query exposed diagnostics establish exact prefix payload equality at the two caps. Their times are excluded from matched means. Failed integration and serialization comparisons are preserved as development failures.',
            'No new proof format, table, persistent hint or production default. Exclusive synchronous session only; foreign restriction engines are rejected. Coverage and complexity are unchanged unless checked results demonstrate otherwise.']))


def worker(out, p, mode, split):
    harness.CLASSES = CLASSES
    harness.TABLES = TABLES
    harness.worker(out, p, mode, split)
    report = base.load(out/'report.json')
    cases, rows = bound(p['cases'][split]), bound(report['queries'])
    report['groups'] = {family: dict(seconds=sum(r['solve_seconds'] for c, r in zip(cases, rows) if c['family']==family),
        expanded=sum(r['metrics'].get('expanded_nodes', 0) for c, r in zip(cases, rows) if c['family']==family),
        statuses=dict(Counter(r['status'] for c, r in zip(cases, rows) if c['family']==family))) for family in FAMILIES}
    base.write(out/'report.json', report)


def run(out):
    p = base.load(out/'protocol.json')
    samples = []
    for split in SPLITS:
        for repeat, order in enumerate(p['orders']):
            for mode in order:
                dest = out/f'{split}-{mode}-{repeat}'
                subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out/'protocol.json'), mode, split], check=True)
                samples.append(dict(split=split, mode=mode, repeat=repeat, **binding(dest/'report.json')))
                print('finished', split, repeat, mode, flush=True)
    base.write(out/'report.json', dict(protocol=binding(out/'protocol.json'), samples=samples))
    summary = {}
    for split in SPLITS:
        summary[split] = {}
        for mode in MODES:
            reports = [bound(s) for s in samples if s['split']==split and s['mode']==mode]
            values = [r['summary'] for r in reports]
            for v in values[1:]:
                for k in ('statuses', 'native_digest', 'extension_digest', 'affine_digest', 'counters', 'checked_python_bytes'):
                    assert v[k] == values[0][k], k
            timed = [k for k in values[0] if k.endswith('_seconds') or k=='peak_rss_bytes']
            summary[split][mode] = {**{k:v for k, v in values[0].items() if k not in timed},
                **{'mean_'+k:sum(v[k] for v in values)/len(values) for k in timed},
                'groups': {f:dict(mean_seconds=sum(r['groups'][f]['seconds'] for r in reports)/len(reports),
                    expanded=reports[0]['groups'][f]['expanded'], statuses=reports[0]['groups'][f]['statuses']) for f in FAMILIES}}
    base.write(out/'analysis.json', dict(summary=summary))
    print(base.encode({s:{m:{k:v for k,v in a.items() if k in ('statuses','native_nodes','mean_solve_seconds','mean_complete_worker_seconds','checked_python_bytes')} for m,a in arms.items()} for s,arms in summary.items()}), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': prepare(Path(sys.argv[2]))
    elif sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), sys.argv[4], sys.argv[5])
    else: run(Path(sys.argv[1]))
