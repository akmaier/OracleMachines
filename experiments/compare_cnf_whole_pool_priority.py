#!/usr/bin/env python3
"""Measure complete-result priority before automatically selected partial plans."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import compare_cnf_whole_proof_reuse as previous
from experiments.validate_cnf_ranked_binary_targets import TABLES as ALL_TABLES
from experiments.cnf_ordered_probe import OrderedProbeSolver
from experiments.cnf_whole_affine import WholeAffineSolver
from experiments.cnf_whole_proof_reuse import WholeProofReuseSolver
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_whole_lookahead import WholeLookaheadSolver
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = previous.base, previous.binding, previous.bound
PARENT = Path('experiments/results/cnf-whole-proof-reuse')
TABLES = previous.TABLES
MODES = ('completion', 'reuse', 'priority')
SPLITS = ('exposed', 'holdout')
FILES = ('experiments/cnf_whole_pool_priority.py', 'solver/test_cnf_whole_pool_priority.py',
    'experiments/compare_cnf_whole_pool_priority.py')


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (108, 132):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611240001)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    old_protocol = bound(parent['whole_proof_reuse']['protocol'])
    exposed = bound(old_protocol['cases']['holdout'])
    base.write(out/'cases.json', exposed)
    base.write(out/'transfer-cases.json', bound(old_protocol['cases']['exposed']))
    assert not {c['root'] for c in exposed} & {c['root'] for c in cases}
    base.write(out/'holdout-cases.json', cases)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'prior'
        base.restore_archive(parent['reference_union'], path)
        con = sqlite3.connect(path)
        try:
            known = {k for t in ALL_TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:
            con.close()
    base.write(out/'protocol.json', dict(parent=binding(PARENT/'checkpoint.json'),
        parent_manifest=binding(PARENT/'manifest.json'), previous_protocol=parent['whole_proof_reuse']['protocol'],
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json'),
            transfer=binding(out/'transfer-cases.json')),
        novelty={s:[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cs]
                 for s,cs in (('exposed',exposed),('holdout',cases))},
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'The preceding holdout (72 queries, sizes 102/126) is now exposed. Fresh sizes 108/132 with seed 202611240001 form a prospective 72-query holdout frozen before evaluation, with no outcome filtering.',
            'Only CNFs enter search. Workers start empty and retain checked chronological results. Archived novelty is recorded without seeding answers.',
            'Compare whole-input affine completion, automatic partial proof reuse, and the same partial policy with existing complete negative/model pools preferred after near-origin selection.',
            'The new gate runs at most once, only after an earlier checked native root missing exactly one target clause is selected. A complete hit bypasses partial extraction. A miss keeps all lookup/preparation work and the original partial continuation; no miss cache or family label is used.',
            'The shared native cap remains 256. Extraction remains capped at 64 proof-node occurrences and 65536 node literals. All published results use existing native authority; misses and open branches have no verdict.',
            'Four alternating serial repetitions charge setup, query, persistence, selected retained graph, RSS, warm reuse, cold replay/reconstruction, serialization and compression. Preparation and cumulative audit are separate.',
            'A separate single paired replay of the earlier 96/120 stream checks that the known case-70 partial transfer survives. It is a frozen regression diagnostic, not part of the four-repeat exposed/holdout means.',
            'Causal pool lookup may discover and materialize support, and later native fallback may repeat a miss. Reduced dispatches do not alone establish reduced total cost or arbitrary-CNF tractability.',
            'No new table, native proof format, persistent plan or default is introduced. The inherited partial composer requires exclusive synchronous use.'
        ]))


def worker(out, p, mode, split):
    harness.CLASSES = dict(completion=WholeAffineSolver, reuse=WholeProofReuseSolver, priority=WholePoolPrioritySolver)
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
    regressions=[]
    for mode in ('reuse','priority'):
        dest=out/f'transfer-{mode}-0'
        subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode,'transfer'],check=True)
        regressions.append(dict(split='transfer',mode=mode,repeat=0,**binding(dest/'report.json')))
        print('finished transfer',mode,flush=True)
    base.write(out/'report.json', dict(protocol=binding(out/'protocol.json'), samples=samples,regressions=regressions))
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
