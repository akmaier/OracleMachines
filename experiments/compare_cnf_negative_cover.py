#!/usr/bin/env python3
"""Price native compilation of retained negative source-clause covers."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_mixed_completion as previous
from experiments import compare_cnf_positive_child as positive
from experiments.cnf_negative_cover import select, publish_cover
from experiments.validate_cnf_unsat_support import bound

base = previous.base; binding = previous.binding; native = previous.native; prep = previous.prep
FIELDS = previous.FIELDS; OLD_FIELDS = previous.OLD_FIELDS
PARENT = Path('experiments/results/cnf-mixed-completion')
MODES = ('baseline', 'mixed', 'cover')
previous_evaluate = positive.evaluate
original_contexts = previous.contexts
previous_summary = positive.summarize
FILES = ('experiments/cnf_negative_cover.py', 'solver/test_cnf_negative_cover.py',
         'experiments/compare_cnf_negative_cover.py', 'experiments/validate_cnf_negative_cover.py')


def inherited(parent):
    return previous.inherited(parent) + bound(parent['mixed_completion_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def inputs(s, p):
    return previous.inputs(s, p)


def evaluate(s, source, target, guards, mode, eligible, limit):
    if mode != 'cover' or not eligible:
        return previous.evaluate(s, source, target, guards, mode, eligible, limit)
    start = time.perf_counter(); guards = list(guards); counts = Counter(); s.counts = Counter()
    with patch.object(s, '_expand', side_effect=AssertionError('Selection search')), patch.object(s, '_store', side_effect=AssertionError('Selection publication')):
        choice, trace = select(s, target, limit, counts)
    selection_seconds = time.perf_counter()-start; probe_metrics = dict(s.counts)
    premise = None; guard_counts = Counter(); guard_metrics = {}; premise_seconds = 0.
    if choice and choice['kind'] == 'guard':
        tick = time.perf_counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Premise search')):
            guard, _, target, premise = positive.publish_guard(s, target, choice, guard_counts)
        guards.append(guard); guard_metrics = dict(s.counts-Counter(premise['metrics']))
        premise_seconds = time.perf_counter()-tick
    tick = time.perf_counter()
    if choice and choice['kind'] == 'negative-cover':
        with patch.object(s,'_visit',side_effect=AssertionError('Cover search')):
            child=publish_cover(s,target,choice,trace['discovery'])
    elif choice and choice['kind'] == 'positive-model':
        with patch.object(s, '_visit', side_effect=AssertionError('Positive child acquisition')):
            child = positive.publish_model(s, target, choice)
    elif choice and choice['kind'] == 'guard':
        with patch.object(s, '_expand', side_effect=AssertionError('Admitted child search')):
            child = s.solve(target) if choice['child']['known'] else positive.publish_screened_branch(s, target, choice['child']['screen'])
    elif choice: child = positive.publish_screened_branch(s, target, choice['screen'])
    else: child = s.solve(target)
    child_seconds = time.perf_counter()-tick; tick = time.perf_counter(); before = Counter(s.counts)
    record = positive.make_record(s, source, guards, child)
    return dict(record=record, local_eligible=True, local_choice=choice, local_probe=trace['discovery'],
                admission=trace, child=child, premise=premise, probe_counts=dict(counts), probe_metrics=probe_metrics,
                guard_counts=dict(guard_counts), guard_metrics=guard_metrics, composition_metrics=dict(s.counts-before),
                selection_seconds=selection_seconds, premise_seconds=premise_seconds, child_seconds=child_seconds,
                composition_seconds=time.perf_counter()-tick, evaluation_seconds=time.perf_counter()-start)


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
    for field in ('binary_probe_skips', 'binary_filter_clause_visits', 'binary_filter_literal_visits', 'binary_filter_name_transports', 'positive_premise_attempts_scanned', 'positive_premise_models', 'positive_premise_reason_literals', 'positive_premise_literals_copied', 'positive_premise_model_literals', 'uniform_premise_attempts_scanned', 'uniform_premise_models', 'uniform_premise_misses', 'uniform_premise_literals_copied', 'uniform_premise_reason_literals', 'uniform_premise_model_literals', 'uniform_premise_recognition_clauses', 'uniform_premise_recognition_literal_visits', 'inline_completion_checks', 'inline_completion_clauses', 'inline_completion_literal_visits', 'inline_completion_model_variables', 'inline_completion_model_literals', 'inline_completion_models', 'mixed_recognition_clauses', 'mixed_scc_calls', 'mixed_scc_implication_edges', 'mixed_negative_conditions', 'mixed_model_variables', 'mixed_model_literals', 'mixed_positive_models', 'cover_completion_reads', 'cover_clause_visits', 'cover_literal_visits', 'cover_candidates'):
        summary[field] = sum(r['probe_counts'].get(field, 0) for r in records)
    for field in ('negative_cover_publications','cover_planned_nodes','cover_premise_literal_payload','cover_checked_reason_literals','cover_checked_implication_edges','cover_transport_reason_literals','cover_transport_path_literals','cover_path_repairs'):
        summary[field]=sum(r['child']['metrics'].get(field,0) for r in records)
    return summary


def worker(out, p, catalog, mode):
    assert mode in MODES
    # Family names and construction parameters are never arguments of evaluate.
    with patch.object(positive.old, 'inherited', inherited), patch.object(positive.old, 'evaluate', evaluate_with_familiarity), patch.object(positive.old, 'summarize', summarize):
        positive.old.worker(out, p, catalog, mode)


def contexts(p, tmp):
    cases = original_contexts(p, tmp)
    protocol = bound(bound(p['cover_control_stream'])['protocol']); trial = bound(p['cover_control_trial'])
    def read(entry, name):
        path=tmp/name; base.restore_archive(entry,path); s=native.ResidualSolver(path)
        try: return native.rows(s)
        finally: s.close()
    before=read(bound(protocol['parent'])['reference_union'],'cover-initial')
    final=read(trial['archive'],'cover-final'); by_hash={base.key_sha(k):k for k in final}
    for row in bound(trial['queries']):
        if row['case'] in p['cover_control_cases']:
            prefix=dict(before); ids=row['ordinary_ids']+row['near_ids']
            for h in ids:
                key=by_hash[h]; assert key not in prefix; prefix[key]=final[key]
            cases.append(dict(cohort='cover-target',case=row['case'],before=prefix,
                source=row['record']['source'],guards=row['record']['guards'],
                expected_answer=row['record']['answer'],preparation_ids=ids))
        for h in row['new_ids']:
            key=by_hash[h]; assert key not in before; before[key]=final[key]
    assert before==final and len(cases)==26
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
        limitations=['Twenty-six exact-prefix contexts compare mixed completion and negative clause-cover compilation. The new negative target59 repeats in reverse order.',
                    'Selection retains the same complete mixed-probe pass, then scans original source clauses for a full negative cover. No additional assumption probes or family labels.',
                    'Publication validates every premise unit trace and implication path, transports them into ordinary native split/unit/implication nodes, and reuses the source clause to force the last branch literal.',
                    'No SCC rediscovery, general native search or new proof kind. If extra assignments pin a contradictory path vertex, a charged unit-propagation repair produces a direct unit certificate.',
                    'Uniform false/true models and mixed positive models retain priority. Clauses shortened only by baseline propagation remain explicit recognition misses.',
                    'Fresh finite-generator transfer and two opposite serial worker orders charge discovery, compilation, native checks, persistence and inherited cold replay. Arbitrary-CNF coverage and uniform resource bounds remain open.'])
    p.update(cover_control_stream=binding(PARENT/'report.json'),
        cover_control_trial=binding(PARENT/'mixed-0/report.json'),cover_control_cases=[59])
    p['control_reports'] = binding(PARENT / 'controls/report.json')
    base.write(out / 'protocol.json', p)
    with patch.object(positive, 'contexts', contexts), patch.object(positive, 'MODES', ('mixed', 'cover')), patch.object(positive, 'evaluate', evaluate), patch.object(positive, 'summarize', summarize):
        positive.controls(out / 'controls', p)
    with patch.object(positive, 'contexts', lambda protocol, tmp: [c for c in contexts(protocol, tmp) if c['cohort']=='cover-target']), patch.object(positive, 'MODES', ('cover', 'mixed')), patch.object(positive, 'evaluate', evaluate), patch.object(positive, 'summarize', summarize):
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
