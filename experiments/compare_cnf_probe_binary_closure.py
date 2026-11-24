#!/usr/bin/env python3
"""Price binary closure in unit-consistent whole probes against exact handoff."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import compare_cnf_probe_lifetime as previous
from experiments.validate_cnf_ranked_binary_targets import TABLES as ALL_TABLES
from functools import partial
from experiments.cnf_probe_binary_closure import BinaryClosureSolver
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = previous.base, previous.binding, previous.bound
PARENT = Path('experiments/results/cnf-probe-lifetime')
TABLES = previous.TABLES
MODES = ('current', 'closure')
SPLITS = ('exposed', 'holdout')
FILES = ('experiments/cnf_probe_binary_census.py', 'experiments/inspect_cnf_probe_binary_census.py',
    'solver/test_cnf_probe_binary_census.py', 'experiments/cnf_probe_binary_closure.py',
    'solver/test_cnf_probe_binary_closure.py', 'experiments/compare_cnf_probe_binary_closure.py')
CLASSES = dict(current=partial(ProbeLifetimeSolver,handoff_bytes=2*1024*1024),
    closure=partial(BinaryClosureSolver,handoff_bytes=2*1024*1024))


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (126, 150):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611240303)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    old_protocol = bound(parent['probe_lifetime']['protocol'])
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
        parent_manifest=binding(PARENT/'manifest.json'), previous_protocol=parent['probe_lifetime']['protocol'],
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json')),
        novelty={s:[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cs]
                 for s,cs in (('exposed',exposed),('holdout',cases))},
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'Previous 120/144 holdout is exposed. Fresh 126/150, seed 202611240303: 72 queries, 48 distinct roots, six families. Freeze before fresh evaluation; no outcome filtering.',
            'Four alternating serial repetitions compare the preceding 2 MiB pending-handoff policy with native binary closure on its previously nonconflicting whole probes.',
            'Each arm starts empty with native expansion cap 256. Only source CNFs enter search. Parent-archive novelty supplies no answers.',
            'Discovery reuses exact forced assignments, restricts and canonicalizes only when needed, and uses the residual binary clauses. Satisfiable subsets remain inconclusive; full native proof checking precedes every negative publication.',
            'The existing unit and implication certificates compose the source cofactor proof. Existing negative residuals can be reused; all remaining work and proof records are charged. No new authority or permanent hint table.',
            'The native dispatch cap does not bound discovery, verification, publication, total time or memory. A compiled cofactor can introduce checked nodes without a native dispatch.',
            'Census targets 37/61/67 and 19 discovered refutations are exposed evidence, not a fresh holdout or a runtime estimate. The original search is unchanged during that census.',
            'Worker timers charge preparation, misses, SCC, source checking, publication, fallback, serialization, persistence, retained state, warm/cold replay, reconstruction and compression, but exclude imports, source hashes, case loading and final bookkeeping.',
            'Historical audit and the exposed census are outside matched means. Preserve unknowns, regressions, old authoritative payloads and alternative raw proofs.',
            'Selected pending preparation remains capped at 2 MiB; its full-visit envelope, construction transients and overall process RSS remain separate quantities. No polynomial solution of arbitrary SAT is claimed.']))


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
