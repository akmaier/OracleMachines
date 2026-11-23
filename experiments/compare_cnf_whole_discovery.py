#!/usr/bin/env python3
"""Matched whole-input discovery, with a prospective larger-seed holdout."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import explore_cnf_whole_inputs as exploration
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_whole_lookahead import WholeLookaheadSolver
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = exploration.base, exploration.binding, exploration.bound
PARENT = exploration.PARENT
TABLES = exploration.prior.TABLES
MODES = ('current', 'lookahead')
SPLITS = ('exposed', 'holdout')
FILES = exploration.FILES + ('experiments/cnf_whole_lookahead.py',
    'solver/test_cnf_whole_lookahead.py', 'experiments/compare_cnf_whole_discovery.py')


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (84, 108):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611241956)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    exposed = base.load(out/'cases.json')
    assert not {c['root'] for c in exposed} & {c['root'] for c in cases}
    base.write(out/'holdout-cases.json', cases)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'prior'
        base.restore_archive(parent['reference_union'], path)
        con = sqlite3.connect(path)
        try:
            known = {k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:
            con.close()
    base.write(out/'protocol.json', dict(parent=binding(PARENT/'checkpoint.json'),
        parent_manifest=binding(PARENT/'manifest.json'), exploration=binding(out/'exploration.json'),
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json')),
        holdout_novelty=[dict(case=c['case'], known_in_parent=c['root'] in known) for c in cases],
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'Exposed 72 queries guided the candidate. Holdout 72 queries at sizes 84/108 and seed 202611241956 are frozen before candidate timing; no outcome filtering.',
            'Only CNFs enter the solver. Family labels organize reports; no guard, correspondence, final answer or archive is supplied. Each worker starts empty and retains checked base/edit/repeat results.',
            'One most-frequent variable, false then true, is probed after binary structural discovery misses. Constants/units and sources over 256 variables, 4096 clauses or 16384 literals skip probes.',
            'Both policies use the same 256 native-dispatch cap per query. Probe publication and verification are charged in time/counters but not counted as expansion dispatches. This is not a matched wall-time cap.',
            'Reuse the existing native unit and split proof rules. Misses convey no verdict. A budget stop retains only completed evidence and is reported as unresolved.',
            'Record setup, query, full worker, selected retained Python graph, RSS, persistence, warm exact reuse, independent cold replay and cold reconstruction. Cold timings include verification; profile separately.',
            'Lookahead and failed-literal probing are established SAT techniques. This study evaluates their bounded placement in the present persistent solver, without changing a production default or proving polynomial arbitrary SAT.'
        ]))


def worker(out, p, mode, split):
    harness.CLASSES = dict(current=ConsequencePrioritySolver, lookahead=WholeLookaheadSolver)
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
