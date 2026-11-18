#!/usr/bin/env python3
"""Attribute early positive stopping and its full discovery/persistence cost."""
from pathlib import Path
from collections import Counter
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_inline_completion as study
from experiments.analyze_cnf_uniform_premise import audit_counts as audit_uniform
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_counts(row, target):
    expected = dict(inline_completion_checks=0, inline_completion_clauses=0,
        inline_completion_literal_visits=0, inline_completion_model_variables=0,
        inline_completion_model_literals=0, inline_completion_models=0)
    a = row['admission']; d = None if a is None else a['discovery']; details=[]
    if d is not None:
        nonconflicts = [i for i,x in enumerate(d['attempts']) if x['screen']['conflict'] is None]
        assert [x['index'] for x in d['completions']] == nonconflicts
        for item in d['completions']:
            screen=d['attempts'][item['index']]['screen']; cnf=base.load_json(screen['root'].split(':',1)[1])
            fixed={abs(l): l>0 for l,_ in screen['trace']}
            residual=[[l for l in c if abs(l) not in fixed] for c in cnf
                if not any(abs(l) in fixed and fixed[abs(l)]==(l>0) for l in c)]
            assert all(len(c)>=2 for c in residual)
            expected['inline_completion_checks']+=1
            expected['inline_completion_clauses']+=len(residual)
            expected['inline_completion_literal_visits']+=sum(map(len,residual))
            assert item['residual_literals']==sum(map(len,residual))
            assert item['false_valid']==all(any(l<0 for l in c) for c in residual)
            assert item['true_valid']==all(any(l>0 for l in c) for c in residual)
            success=item['false_valid'] or item['true_valid']
            if success:
                assert item is d['completions'][-1] and item['index']==d['positive_selected']==len(d['attempts'])-1
                assert a['reason']=='inline-positive-model' and row['local_choice']['kind']=='positive-model'
                expected['inline_completion_models']+=1
                expected['inline_completion_model_variables']+=len({abs(l) for c in target for l in c})
                expected['inline_completion_model_literals']+=sum(map(len,target))+1
            details.append(dict(index=item['index'],accepted=success,residual_literals=item['residual_literals']))
        assert (d['positive_selected'] is not None)==bool(expected['inline_completion_models'])
    assert all(row['probe_counts'].get(k,0)==v for k,v in expected.items()), (row.get('case'),expected)
    assert not any(v for k,v in row['probe_counts'].items() if k.startswith(('positive_premise_','uniform_premise_')))
    return details


def frontier_attribution(out, report):
    checkpoint = out/'checkpoint.json'
    if not checkpoint.exists(): return None
    parent=bound(bound(report['protocol'])['parent']); current=base.load(checkpoint)
    groups={c['case']:c['family'] for c in bound(report['cases'])['cases']}
    results=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        base.restore_archive(parent['reference_union'],tmp/'old')
        base.restore_archive(current['reference_union'],tmp/'new')
        before=study.native.ResidualSolver(tmp/'old'); after=study.native.ResidualSolver(tmp/'new')
        try:
            old=study.native.rows(before); new=study.native.rows(after)
            for name in ('active_support_proposals','extended_support_proposals','causal_support_proposals','incremental_causal_proposals'):
                for index,core in enumerate(bound(parent[name])['cores']):
                    cnf,_,root=after._canonical(core['source'])
                    if root in old or root not in new: continue
                    assert after._read(root,cnf)['answer'] is False
                    key=base.key_sha(root); acquisitions=[]
                    for entry in report['samples']:
                        if entry['repeat']!=0: continue
                        for row in bound(bound(entry)['queries']):
                            if key in row['new_ids']:
                                acquisitions.append(dict(mode=entry['mode'],case=row['case'],family=groups[row['case']],
                                    phase='ordinary' if key in row['ordinary_ids'] else 'near' if key in row['near_ids'] else 'acquisition'))
                    results.append(dict(bank=name,core=index,root_sha256=key,source=core['source'],
                        native_bytes=len(root)+len(new[root]),acquisitions=acquisitions))
        finally: before.close();after.close()
    return results


def analyze(out):
    started = time.perf_counter(); report = base.load(out/'report.json')
    cases = {c['case']: c for c in bound(report['cases'])['cases']}
    details = []; groups = {}; modes = {}; audits = 0; diagnoses = []; late_diagnoses=[]; saved_rows={}
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        if entry['repeat']==0: saved_rows[mode]=records
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    if mode in ('inline', 'uniform'):
                        target = row['record']['source']
                        # A successful guard appends one guard after selection.
                        guards = row['record']['guards']
                        if row['local_choice'] and row['local_choice']['kind'] == 'guard': guards = guards[:-1]
                        for g in guards: _, target = check_guard(s, target, g)
                        diagnosis = (audit_counts if mode=='inline' else audit_uniform)(row, target); audits += 1
                        if entry['repeat']==0 and mode=='inline':
                            diagnoses.extend(dict(case=row['case'],family=cases[row['case']]['family'],**d) for d in diagnosis)
                        if entry['repeat']==0 and mode=='uniform':
                            late_diagnoses.extend(dict(case=row['case'],family=cases[row['case']]['family'],**d) for d in diagnosis)
                    if entry['repeat'] != 0: continue
                    details.append(dict(case=row['case'], family=cases[row['case']]['family'], mode=mode,
                        configuration=cases[row['case']]['configuration'], answer=row['record']['answer'],
                        new_rows=row['new_nodes'], native_bytes=sum(sizes[h] for h in row['new_ids']),
                        expanded_nodes=row['child']['metrics'].get('expanded_nodes', 0),
                        discovery_propagation=row['probe_counts'].get('propagation_literal_visits', 0),
                        child_propagation=row['child']['metrics'].get('propagation_literal_visits', 0),
                        reason=None if row['admission'] is None else row['admission']['reason'],
                        familiarity=row['familiarity']))
            finally: s.close()
        for family in sorted({c['family'] for c in cases.values()}):
            selected = [r for r in records if cases[r['case']]['family'] == family]
            summary = study.summarize(selected)
            summary.update(queries=len(selected), rows=sum(r['new_nodes'] for r in selected),
                query_seconds=sum(r['seconds'] for r in selected),
                discovery_propagation=sum(r['probe_counts'].get('propagation_literal_visits', 0) for r in selected),
                child_propagation=sum(r['child']['metrics'].get('propagation_literal_visits', 0) for r in selected),
                normalization_literal_visits=sum(r['probe_metrics'].get('normalization_literal_visits',0) for r in selected),
                key_serialized_bytes=sum(r['probe_metrics'].get('key_serialized_bytes',0) for r in selected))
            groups.setdefault(family, {}).setdefault(mode, []).append(summary)
    controls = []
    for cohort in ('controls', 'reverse_control'):
        for entry in bound(report[cohort])['samples']:
            row = bound(entry)
            if row['mode'] in ('uniform','inline'):
                (audit_counts if row['mode']=='inline' else audit_uniform)(row, row['input_target']); audits += 1
            controls.append(dict(cohort=row['cohort'], case=row['case'], mode=row['mode'], order=cohort,
                new_rows=row['new_nodes'], native_bytes=row['new_payload_units'], retained_bytes=row['retained_bytes'],
                report_bytes=Path(entry['path']).stat().st_size,
                reason=row['admission']['reason'], summary=row['summary'],
                probe_counts=row['probe_counts'], probe_metrics=row['probe_metrics'],
                child_metrics=row['child']['metrics'],
                **{k: row[k] for k in ('selection_seconds', 'child_seconds', 'evaluation_seconds',
                    'warm_seconds', 'cold_seconds', 'open_seconds', 'prefix_write_seconds',
                    'serialization_seconds', 'complete_arm_seconds')}))
    prefix_checks=[]
    for late,early in zip(saved_rows['uniform'],saved_rows['inline']):
        assert late['case']==early['case']
        a=late['admission'];b=early['admission']
        if a is None or a['discovery'] is None:
            assert b is None or b['discovery'] is None
            continue
        x=a['discovery'];y=b['discovery']
        assert x['candidates']==y['candidates'] and x['baseline']==y['baseline']
        assert y['attempts']==x['attempts'][:len(y['attempts'])]
        assert x['binary_filter']['skipped'][:len(y['binary_filter']['skipped'])]==y['binary_filter']['skipped']
        prefix_checks.append(dict(case=early['case'],family=cases[early['case']]['family'],
            late_probes=len(x['attempts']),inline_probes=len(y['attempts']),
            avoided_probes=len(x['attempts'])-len(y['attempts']),reason=b['reason']))
    result = dict(late_conditioned_residuals=late_diagnoses,prefix_checks=prefix_checks,newly_ready_support=frontier_attribution(out, report), groups=groups, cases=details, controls=controls, counter_audits=audits, conditioned_residuals=diagnoses,
        timing_pairs=[dict(repeat=i, query_delta=modes['inline', i]['query_seconds']-modes['uniform', i]['query_seconds'],
            complete_delta=modes['inline', i]['complete_worker_seconds']-modes['uniform', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Posthoc counter audits are excluded from timing. Every early-stop model and saved trace is independently checked by reconstruction.',
            'The unchanged candidate budget is evaluated only up to the first model or negative guard. Positive priority can change native certificate payloads. No expanded candidate coverage is claimed.',
            'Uniform misses and negative conditions remain unresolved by this step; early checks can add work on misses. Two timing orders and finite families do not establish arbitrary-CNF scaling.'])
    base.write(out/'attribution.json', result)
    print(base.encode(dict(counter_audits=audits, timing_pairs=result['timing_pairs'],
        successes=[d for d in details if d['reason']=='inline-positive-model'])))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
