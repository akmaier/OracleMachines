#!/usr/bin/env python3
"""Price uniform completion of retained conditioned residuals."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_positive_premise as previous
from experiments import compare_cnf_positive_child as positive
from experiments.cnf_uniform_premise import select
from experiments.validate_cnf_unsat_support import bound

base = previous.base; binding = previous.binding; native = previous.native; prep = previous.prep
FIELDS = previous.FIELDS; OLD_FIELDS = previous.OLD_FIELDS
PARENT = Path('experiments/results/cnf-positive-premise')
MODES = ('baseline', 'recovered', 'uniform')
previous_evaluate = positive.evaluate
original_contexts = previous.contexts
previous_summary = positive.summarize
FILES = ('experiments/cnf_uniform_premise.py', 'solver/test_cnf_uniform_premise.py',
         'experiments/compare_cnf_uniform_premise.py', 'experiments/validate_cnf_uniform_premise.py')


def inherited(parent):
    return previous.inherited(parent) + bound(parent['positive_premise_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def inputs(s, p):
    return previous.inputs(s, p)


def evaluate(s, source, target, guards, mode, eligible, limit):
    if mode == 'uniform':
        with patch.object(positive, 'select', select):
            return previous_evaluate(s, source, target, guards, 'positive', eligible, limit)
    return previous.evaluate(s, source, target, guards, mode, eligible, limit)


def evaluate_with_familiarity(s, source, target, guards, mode, eligible, limit):
    tick = time.perf_counter(); before = Counter(s.counts)
    cnf, names, root = s._canonical(target)
    familiarity = dict(root=root, known_after_preparation=not eligible, guards=len(guards),
                       variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf)))
    metrics = dict(s.counts-before); seconds = time.perf_counter()-tick
    result = evaluate(s, source, target, guards, mode, eligible, limit)
    result.update(familiarity=familiarity, familiarity_metrics=metrics, familiarity_seconds=seconds)
    return result


def summarize(records):
    summary = previous.summarize(records) if all('familiarity' in r for r in records) else previous_summary(records)
    for field in ('binary_probe_skips', 'binary_filter_clause_visits', 'binary_filter_literal_visits', 'binary_filter_name_transports', 'positive_premise_attempts_scanned', 'positive_premise_models', 'positive_premise_reason_literals', 'positive_premise_literals_copied', 'positive_premise_model_literals', 'uniform_premise_attempts_scanned', 'uniform_premise_models', 'uniform_premise_misses', 'uniform_premise_literals_copied', 'uniform_premise_reason_literals', 'uniform_premise_model_literals', 'uniform_premise_recognition_clauses', 'uniform_premise_recognition_literal_visits'):
        summary[field] = sum(r['probe_counts'].get(field, 0) for r in records)
    return summary


def worker(out, p, catalog, mode):
    assert mode in MODES
    # Family names and construction parameters are never arguments of evaluate.
    with patch.object(positive.old, 'inherited', inherited), patch.object(positive.old, 'evaluate', evaluate_with_familiarity), patch.object(positive.old, 'summarize', summarize):
        positive.old.worker(out, p, catalog, mode)


def contexts(p, tmp):
    cases = original_contexts(p, tmp)
    for cohort, stream_field, trial_field, ids_field in (
        ('uniform-target', 'uniform_control_stream', 'uniform_control_trial', 'uniform_control_cases'),
        ('recovery-controls', 'recovery_control_stream', 'recovery_control_trial', 'recovery_control_cases')):
        protocol = bound(bound(p[stream_field])['protocol']); trial = bound(p[trial_field])
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); solver = native.ResidualSolver(path)
            try: return native.rows(solver)
            finally: solver.close()
        before = read(bound(protocol['parent'])['reference_union'], cohort+'-initial')
        final = read(trial['archive'], cohort+'-final'); by_hash = {base.key_sha(k): k for k in final}
        for row in bound(trial['queries']):
            if row['case'] in p[ids_field]:
                prefix = dict(before); ids = row['ordinary_ids'] + row['near_ids']
                for h in ids:
                    key = by_hash[h]; assert key not in prefix; prefix[key] = final[key]
                cases.append(dict(cohort=cohort, case=row['case'], before=prefix,
                    source=row['record']['source'], guards=row['record']['guards'],
                    expected_answer=row['record']['answer'], preparation_ids=ids))
            for h in row['new_ids']:
                key = by_hash[h]; assert key not in before; before[key] = final[key]
        assert before == final
    assert len(cases) == 17
    return cases


def run(out):
    out.mkdir(exist_ok=False); parent = base.load(PARENT / 'checkpoint.json')
    bank = base.load('experiments/results/cnf-premise-guard/protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    base.write(out / 'previous-decisions.json', exclusions(parent))
    p = dict(base.load(PARENT / 'protocol.json'))
    p.update(parent=binding(PARENT / 'checkpoint.json'), source_fingerprints=sources,
        support_index=parent['extended_support_proposals'], causal_index=parent['causal_support_proposals'],
        template_catalog=bank['template_catalog'], cores=bank['cores'], bank_catalog=bank['bank_catalog'],
        previous_decisions=binding(out / 'previous-decisions.json'), node_limit=100000,
        alternative_budget=1, variable_limit=4, per_template=4, orders=[MODES, MODES[::-1]],
        limitations=['Seventeen saved-prefix contexts compare prior positive-premise recovery against uniform completion. A nonterminal target is repeated in reverse order. Prior successes and unresolved/regressing controls remain retained.',
                    'The optional policy only scans already retained nonconflicting premise attempts after earlier accepted paths. It checks the binding and unit trace, reconstructs the residual, recognizes all-false/all-true completions and verifies the full source-plus-assumption model.',
                    'Uniform failure is inconclusive; it never refutes a parent. No additional assumption probes, family labels or unbounded search are used in selection. Candidate-filter omissions and earlier guard priority remain restrictions.',
                    'Fresh transfer uses 48 finite-generator CNFs and 12 same-template neighbours, excluding inherited roots. Baseline shares native preparation. Two reverse worker orders, no concurrent tests/profiles/builds; all discovery, checking, persistence and cold replay remain charged.',
                    'This reuses established uniform witnesses, including unit-closed Horn/dual-Horn residuals and broader classes. No new tractability theorem or unrestricted-SAT bound.'])
    p['control_reports'] = binding(PARENT / 'controls/report.json')
    p.update(uniform_control_stream=binding(Path('experiments/results/cnf-binary-probe/report.json')),
        uniform_control_trial=binding(Path('experiments/results/cnf-binary-probe/filtered-0/report.json')), uniform_control_cases=[14],
        recovery_control_stream=binding(PARENT / 'report.json'), recovery_control_trial=binding(PARENT / 'recovered-0/report.json'), recovery_control_cases=[26,54])
    base.write(out / 'protocol.json', p)
    with patch.object(positive, 'contexts', contexts), patch.object(positive, 'MODES', ('recovered', 'uniform')), patch.object(positive, 'evaluate', evaluate), patch.object(positive, 'summarize', summarize):
        positive.controls(out / 'controls', p)
    with patch.object(positive, 'contexts', lambda protocol, tmp: [c for c in contexts(protocol, tmp) if c['cohort']=='uniform-target']), patch.object(positive, 'MODES', ('uniform', 'recovered')), patch.object(positive, 'evaluate', evaluate), patch.object(positive, 'summarize', summarize):
        positive.controls(out / 'reverse-control', p)
    tick = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'initial'; base.restore_archive(parent['reference_union'], path); s = native.ResidualSolver(path)
        try: catalog = inputs(s, p)
        finally: s.close()
    assert len(catalog['cases']) == 60
    base.write(out / 'cases.json', catalog)
    base.write(out / 'generation.json', dict(seconds=time.perf_counter()-tick, selection=catalog['selection']))
    samples = []
    for repeat, order in enumerate(p['orders']):
        for mode in order:
            dest = out / f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), str(out / 'cases.json'), mode], check=True)
            samples.append(dict(repeat=repeat, mode=mode, **binding(dest / 'report.json')))
            print('fresh', repeat, mode, flush=True)
    summary = {}
    for mode in MODES:
        data = [bound(e)['summary'] for e in samples if e['mode'] == mode]; first = data[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_bytes']
        fixed = [k for k in first if k not in timed and k not in ('mode', 'sidecar_bytes')]
        for other in data[1:]:
            for k in fixed: assert first[k] == other[k], k
        summary[mode] = {**{k: first[k] for k in fixed}, **{'mean_'+k: sum(r[k] for r in data)/len(data) for k in timed},
                         'sidecar_bytes': [r['sidecar_bytes'] for r in data]}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), controls=binding(out / 'controls/report.json'), reverse_control=binding(out / 'reverse-control/report.json'), cases=binding(out / 'cases.json'), samples=samples, summary=summary))
    print(base.encode(summary), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), base.load(sys.argv[4]), sys.argv[5])
    else: run(Path(sys.argv[1]))
