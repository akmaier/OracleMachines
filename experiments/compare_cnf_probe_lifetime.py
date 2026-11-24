#!/usr/bin/env python3
"""Separate reference retirement, budget transfer and a larger retention control."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import compare_cnf_probe_handoff as previous
from experiments.validate_cnf_ranked_binary_targets import TABLES as ALL_TABLES
from functools import partial
from experiments.cnf_probe_handoff import ProbeHandoffSolver
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = previous.base, previous.binding, previous.bound
PARENT = Path('experiments/results/cnf-probe-handoff')
TABLES = previous.TABLES
MODES = ('retain', 'clear', 'transfer', 'room')
SPLITS = ('exposed', 'holdout')
FILES = ('experiments/cnf_probe_lifetime.py', 'solver/test_cnf_probe_lifetime.py',
    'experiments/compare_cnf_probe_lifetime.py','experiments/inspect_cnf_probe_lifetime.py')
CLASSES = dict(retain=partial(ProbeHandoffSolver,handoff_bytes=2*1024*1024),
    clear=partial(ProbeLifetimeSolver,handoff_bytes=2*1024*1024,release_early=False),
    transfer=partial(ProbeLifetimeSolver,handoff_bytes=2*1024*1024),
    room=partial(ProbeHandoffSolver,handoff_bytes=4*1024*1024))


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (120, 144):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611240203)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    old_protocol = bound(parent['probe_handoff']['protocol'])
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
        parent_manifest=binding(PARENT/'manifest.json'), previous_protocol=parent['probe_handoff']['protocol'],
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json')),
        novelty={s:[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cs]
                 for s,cs in (('exposed',exposed),('holdout',cases))},
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        capacities=dict(retain=2*1024*1024,clear=2*1024*1024,transfer=2*1024*1024,room=4*1024*1024),
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'Previous 114/138 holdout is exposed. Fresh 120/144, seed 202611240203: 72 queries, 48 distinct roots, six families. Freeze before fresh evaluation; no outcome filtering.',
            'Four alternating serial repetitions compare full-visit retention at 2 MiB; reference cleanup with the same full-visit charging; cleanup plus early budget transfer at 2 MiB; and original retention at 4 MiB. The larger control is motivated by the 3.92 MB full-visit envelope on exposed case 37, not by fresh outcomes.',
            'Every arm starts empty with native cap 256 and unchanged pool/discovery priority. Only source CNFs enter search. Novelty against all six parent tables supplies no answers.',
            'Mutable private leases are cleared when canonicalization and any needed propagation finish. Unvisited offers and unconsumed propagation remain charged. All proof checking suppresses hints; checked prefixes survive stops.',
            'Early release changes the charge scope: pending preparation is bounded, but native visits still own their required data. Record a separate conservative full-visit envelope that keeps each released charge until its visit returns. It can exceed 2 MiB. This is not a whole-process memory bound or proof of lower RAM.',
            'Lease headers include an extra state slot charged by the same conservative estimator. Control containers, frames, allocator overhead and construction transients are outside that cap. Selected retained solver graph and RSS are measured separately.',
            'Charge sizing, freezing, failed admission, matching, copies, disposal, recognition, checking, persistence, serialization, warm/cold replay/reconstruction and compression. Worker timers exclude imports, source hashing, case loading and final report bookkeeping.',
            'Two exposed 38-query exact-prefix diagnostics compare early release and the 4 MiB retention control. Their timing and cumulative preservation/profile work are outside matched means.',
            'No new table, proof authority, persistent hint or production default. Exclusive synchronous execution only. Identical native search and certificate bytes are required, not inferred from aggregate coverage.']))


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
