#!/usr/bin/env python3
"""Measure automatically discovered partial proof plans on whole-input edits."""
from collections import Counter
from pathlib import Path
import sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_probe_safe as harness
from experiments import compare_cnf_whole_affine as previous
from experiments.validate_cnf_ranked_binary_targets import TABLES as ALL_TABLES
from experiments.cnf_ordered_probe import OrderedProbeSolver
from experiments.cnf_whole_affine import WholeAffineSolver
from experiments.cnf_whole_proof_reuse import WholeProofReuseSolver
from experiments.cnf_fresh_mixtures import generate, FAMILIES, LIMIT
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_whole_lookahead import WholeLookaheadSolver
from experiments.cnf_residual_dag import normalize, token
base, binding, bound = previous.base, previous.binding, previous.bound
PARENT = Path('experiments/results/cnf-whole-affine')
TABLES = previous.TABLES
MODES = ('current', 'completion', 'reuse')
SPLITS = ('exposed', 'holdout')
FILES = ('experiments/cnf_partial_proof_plan.py', 'experiments/cnf_whole_proof_reuse.py',
    'solver/test_cnf_whole_proof_reuse.py', 'experiments/compare_cnf_whole_proof_reuse.py',
    'experiments/inspect_cnf_whole_proof.py')


def prepare(out):
    tick = time.perf_counter()
    assert not (out/'protocol.json').exists()
    parent = base.load(PARENT/'checkpoint.json')
    for f, h in parent['source_fingerprints'].items():
        assert base.sha(f) == h, f
    cases = []
    for size in (102, 126):
        for family in FAMILIES:
            for sample in (0, 1):
                start = len(cases)
                for variant, source in zip(('base', 'edit', 'repeat'),
                        generate(family, size, sample, seed=202611232256)):
                    cnf, names = normalize(source)
                    cases.append(dict(case=len(cases), family=family, size=size, sample=sample,
                        variant=variant, base_case=start, source=source, root=token(cnf, Counter()),
                        variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf))))
    old_protocol = bound(parent['whole_affine']['protocol'])
    exposed = bound(old_protocol['cases']['holdout'])
    base.write(out/'cases.json', exposed)
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
        parent_manifest=binding(PARENT/'manifest.json'), previous_protocol=parent['whole_affine']['protocol'],
        source_fingerprints={**parent['source_fingerprints'], **{f: base.sha(f) for f in FILES}},
        cases=dict(exposed=binding(out/'cases.json'), holdout=binding(out/'holdout-cases.json')),
        novelty={s:[dict(case=c['case'],known_in_parent=c['root'] in known) for c in cs]
                 for s,cs in (('exposed',exposed),('holdout',cases))},
        node_limit=LIMIT, orders=[list(MODES), list(reversed(MODES))]*2,
        preparation_seconds=time.perf_counter()-tick, limitations=[
            'The preceding holdout (72 queries, sizes 96/120) is now exposed. Fresh sizes 102/126 with seed 202611232256 form a prospective 72-query holdout frozen before evaluation; no outcome filtering.',
            'Only CNFs enter search. Each worker starts empty and retains checked base/edit/repeat results. Prior archive novelty is recorded without supplying answers to the solver.',
            'Compare the original binary policy, bounded whole-input affine completion with ordered probing, and that same policy with automatic partial proof-plan reuse.',
            'After exact-root misses, scan the existing bounded native negative pool in canonical coordinates. At most one earlier source missing exactly one clause is extracted per query, with at least one overlapping clause. No family, supplied guard or future answer selects an origin.',
            'Extract at most 64 native proof-node occurrences and 65536 source literals. Unsupported endpoints and extraction-budget frontiers become explicit open leaves. Checked surviving conditional unit supports guide the existing native partial composer; every open or broken leaf needs checked native acquisition under one 256-dispatch cap.',
            'Plans are transient, have no verdict authority, and are reconstructed from retained earlier native proofs on cold use. Successful query logs retain their plan; stopped queries retain checked native prefixes and all work counters. No new table, native proof format or default is introduced.',
            'The adapter scopes the existing serial composer survival checker to the new explicit open-leaf hint format. Exclusive synchronous use is required; it is not a concurrent in-process interface.',
            'Four alternating serial repetitions charge setup, query, persistence, selected retained graph, RSS, warm replay, cold replay/reconstruction and compression. Study preparation and cumulative audit are separate.',
            'Recognition and a bounded partial plan do not imply cheap completion of open leaves or a compact closure for unrestricted SAT. Discovery, source checking, publication and sidecar serialization are charged beyond the native dispatch cap.'
        ]))


def worker(out, p, mode, split):
    harness.CLASSES = dict(current=ConsequencePrioritySolver, completion=WholeAffineSolver, reuse=WholeProofReuseSolver)
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
