#!/usr/bin/env python3
"""Fresh matched streams for the unchanged child-admission policy."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_local_guard as old
from experiments import compare_cnf_child_admission as gate
from experiments.validate_cnf_unsat_support import bound
base = old.base; binding = old.binding; native = old.native; prep = old.prep
FIELDS = old.FIELDS; OLD_FIELDS = old.OLD_FIELDS
PARENT = Path('experiments/results/cnf-child-admission')
FILES = ('experiments/compare_cnf_child_stream.py', 'experiments/validate_cnf_child_stream.py')
MODES = ('baseline', 'admitted')
original_evaluate = old.evaluate; original_inherited = old.inherited; original_summarize = old.summarize


def inherited(parent):
    return original_inherited(parent) + bound(parent['local_guard_decisions']) + bound(parent['child_admission_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def evaluate(s, source, target, guards, mode, eligible, limit):
    if mode == 'admitted' and eligible:
        return gate.evaluate(s, source, target, guards, mode, limit)
    result = original_evaluate(s, source, target, guards, 'baseline', eligible, limit)
    result['admission'] = None
    return result


def summarize(records):
    summary = original_summarize(records)
    summary.update(admission_calls=sum(r['admission'] is not None for r in records),
                   admission_reasons=dict(Counter(r['admission']['reason'] for r in records if r['admission'] is not None)))
    return summary


def worker(out, p, catalog, mode):
    assert mode in MODES
    with patch.object(old, 'inherited', inherited), patch.object(old, 'evaluate', evaluate), patch.object(old, 'summarize', summarize):
        old.worker(out, p, catalog, mode)


def run(out):
    out.mkdir(exist_ok=False); parent = base.load(PARENT / 'checkpoint.json')
    bank = base.load('experiments/results/cnf-premise-guard/protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    base.write(out / 'previous-decisions.json', exclusions(parent))
    p = dict(parent=binding(PARENT / 'checkpoint.json'), source_fingerprints=sources,
        support_index=parent['extended_support_proposals'], causal_index=parent['causal_support_proposals'],
        template_catalog=bank['template_catalog'], cores=bank['cores'], bank_catalog=bank['bank_catalog'],
        previous_decisions=binding(out / 'previous-decisions.json'), controls=binding(PARENT / 'report.json'),
        node_limit=100000, alternative_budget=1, variable_limit=4, per_template=64, orders=[MODES, MODES[::-1]],
        limitations=['192 new double-deletion query roots from three templates, excluding all inherited ordinary/composed roots and native roots. This is not an arbitrary-SAT distribution.',
                    'The child-admission rule and four-variable local ranking are unchanged. The frozen worker is reused with scoped callbacks for inheritance, evaluation and summary only.',
                    'Two reversed-order pairs run in separate fresh processes. No test, profile or build overlaps timed production. Discovery, rejected probes, fallback, checking, serialization, persistence and full inherited cold replay are retained.',
                    'Known native targets bypass optional discovery. Shared ordinary and near-guard preparation is identical in both modes. The eighteen prior exact-prefix controls remain bound and preserved, not rerun as fresh cases.',
                    'All prior native payloads and composed results remain retained; new records use the existing guard-chain schema. No new Lean, optimality or unrestricted-SAT resource bound.'])
    base.write(out / 'protocol.json', p); tick = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'initial'; base.restore_archive(parent['reference_union'], path); s = native.ResidualSolver(path)
        try: catalog = prep.ordinary.eager.previous.inputs(s, p)
        finally: s.close()
    assert len(catalog['cases']) == 192
    base.write(out / 'cases.json', catalog); base.write(out / 'preflight.json', dict(seconds=time.perf_counter() - tick, selection=catalog['selection']))
    samples = []
    for repeat, order in enumerate(p['orders']):
        for mode in order:
            dest = out / f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), str(out / 'cases.json'), mode], check=True, stdout=subprocess.DEVNULL)
            samples.append(dict(repeat=repeat, mode=mode, **binding(dest / 'report.json'))); print('fresh', repeat, mode, flush=True)
    summary = {}
    for mode in MODES:
        data = [bound(e)['summary'] for e in samples if e['mode'] == mode]; first = data[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_bytes']
        fixed = [k for k in first if k not in timed and k not in ('mode', 'sidecar_bytes')]
        for other in data[1:]:
            for k in fixed: assert first[k] == other[k], k
        summary[mode] = {**{k: first[k] for k in fixed}, **{'mean_' + k: sum(r[k] for r in data) / len(data) for k in timed}, 'sidecar_bytes': [r['sidecar_bytes'] for r in data]}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), cases=binding(out / 'cases.json'), samples=samples, summary=summary))
    print(base.encode(summary), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), base.load(sys.argv[4]), sys.argv[5])
    else: run(Path(sys.argv[1]))
