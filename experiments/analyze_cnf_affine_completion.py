#!/usr/bin/env python3
"""Attribute checked affine completion, failed admissions and total acquisition cost."""
from pathlib import Path
from collections import Counter
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_completion as study
from experiments.analyze_cnf_cover_probe import audit_counts as audit_previous
from experiments.validate_cnf_affine_completion import inspect_bridge
from experiments.validate_cnf_mixed_completion import validate_mixed_certificate
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_counts(row,target):
    prior=deepcopy(row);trace=prior['admission']
    if trace is not None and trace['reason']=='affine-positive-model':
        trace['reason']=trace['affine_previous_reason']
        prior['local_choice']=(dict(kind='fallback-trace',screen=deepcopy(trace['discovery']['baseline']))
                               if trace['reason']=='retained-prefix' else None)
    details=audit_previous(prior,target)
    a=row['admission'];e=None if a is None else a.get('affine_bridge');d=None if a is None else a['discovery']
    choice=prior['local_choice'];eligible=d is not None and (choice is None or choice['kind']=='fallback-trace')
    assert (e is not None)==eligible
    expected={k:0 for k in study.AFFINE_FIELDS}
    if e is not None:
        s=study.native.ResidualSolver()
        try:recovered,checked=inspect_bridge(s,target,e)
        finally:s.close()
        assert checked==e
        if recovered is not None:assert recovered==row['local_choice']
        cnf=base.load_json(e['root'].split(':',1)[1]);af=e['affine'];eqs=af['equations'];left=af['leftovers'];space=e['space']
        expected.update(affine_bridge_calls=1,affine_grouping_literals=sum(map(len,cnf)),
            affine_elimination_xors=sum(len(r['using']) for r in af['reductions']),
            affine_extracted_equations=len(eqs),affine_leftover_clauses=len(left),
            affine_verification_literals=sum(len(cnf[cid]) for eq in eqs for cid in eq['clauses']),
            affine_verification_xors=sum(len(r['using']) for r in af['reductions']),affine_verified_certificates=1)
        statuses={'no-equations':'affine_bridge_no_equations','linear-conflict':'affine_bridge_linear_conflicts',
            'free-cap':'affine_bridge_free_caps','model':'affine_bridge_models','space-exhausted':'affine_bridge_exhausted'}
        expected[statuses[e['status']]]=1
        if space is not None:
            dim=e['free'];candidates=len(e['rejected'])+int(e['accepted'] is not None)
            expected.update(affine_space_backsub_rows=(dim+1)*e['summary']['rank'],
                affine_space_vectors_constructed=dim+1,affine_space_kernel_equation_checks=dim*len(eqs),
                affine_space_particular_equation_checks=len(eqs),affine_space_vectors_checked=dim+1,
                affine_bridge_packed_literals=sum(len(cnf[cid]) for cid in left),
                affine_bridge_candidates=candidates,affine_bridge_basis_xors=max(0,candidates-1),
                affine_bridge_clause_checks=sum(left.index(cid)+1 for cid in e['rejected'])+(len(left) if e['accepted'] else 0))
        if e['accepted'] is not None:
            expected.update(affine_bridge_model_variables=e['variables'],affine_bridge_model_literals=sum(map(len,target)))
    assert all(row['probe_counts'].get(k,0)==v for k,v in expected.items()),(row.get('case'),expected)
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
    details = []; groups = {}; modes = {}; audits = 0; diagnoses = []; late_diagnoses=[]; saved_rows={}; negative_covers=[]; partial_covers=[]; affine_details=[]
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        if entry['repeat']==0: saved_rows[mode]=records
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    if mode in ('affine', 'probe'):
                        target = row['record']['source']
                        # A successful guard appends one guard after selection.
                        guards = row['record']['guards']
                        if row['local_choice'] and row['local_choice']['kind'] == 'guard': guards = guards[:-1]
                        for g in guards: _, target = check_guard(s, target, g)
                        diagnosis = (audit_counts if mode=='affine' else audit_previous)(row, target); audits += 1
                        if entry['repeat']==0 and mode=='affine':
                            diagnoses.extend(dict(case=row['case'],family=cases[row['case']]['family'],**d) for d in diagnosis)
                            bridge=(row['admission'] or {}).get('affine_bridge')
                            if bridge is not None:
                                affine_details.append(dict(case=row['case'],family=cases[row['case']]['family'],answer=row['record']['answer'],
                                    status=bridge['status'],variables=bridge['variables'],free=bridge['free'],summary=bridge['summary'],
                                    candidates=len(bridge['rejected'])+int(bridge['accepted'] is not None),accepted=bridge['accepted'],
                                    acquired_nodes=row['new_nodes'],child_propagation=row['child']['metrics'].get('propagation_literal_visits',0)))
                            negative={d['assumption'][0] for d in diagnosis if not d['answer']}
                            covers=[c for c in target if c and set(c)<=negative]
                            if negative and not covers:
                                pending=[];discovery=row['admission']['discovery']
                                observed={x['clause'][0]:x['screen'] for x in discovery['attempts']}
                                gap=row['admission'].get('gap')
                                if gap is not None:observed[gap['attempt']['clause'][0]]=gap['attempt']['screen']
                                candidates={c[0] for c in discovery['candidates']}
                                skipped={c[0] for c in discovery['binary_filter']['skipped']}
                                for clause in target:
                                    members=set(clause);missing=members-negative
                                    if not members&negative or not missing or any(-l in members for l in members):continue
                                    status={str(l):('unit-conflict' if observed[l]['conflict'] is not None else 'attempted-unresolved') if l in observed else 'filtered' if l in skipped else 'unvisited' if l in candidates else 'outside-candidates' for l in sorted(missing)}
                                    pending.append(dict(clause=sorted(members),missing=sorted(missing),status=status))
                                pending.sort(key=lambda x:(len(x['missing']),len(x['clause']),x['clause']))
                                partial_covers.append(dict(case=row['case'],family=cases[row['case']]['family'],answer=row['record']['answer'],candidates=pending[:3]))
                            if covers:
                                assert row['record']['answer'] is False
                                negative_covers.append(dict(cohort='fresh',case=row['case'],family=cases[row['case']]['family'],clauses=covers,refuted_assumptions=sorted(negative),
                                    refutations=[dict(literal=d['assumption'][0],attempt_index=d['index'],residual_sha256=d['ordered_residual_sha256']) for d in diagnosis if not d['answer']]))
                        if entry['repeat']==0 and mode=='probe':
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
            if row['mode'] in ('probe','affine'):
                diagnosis=(audit_counts if row['mode']=='affine' else audit_previous)(row, row['input_target']); audits += 1
                if row['mode']=='affine':
                    negative={d['assumption'][0] for d in diagnosis if not d['answer']}
                    covers=[c for c in row['input_target'] if c and set(c)<=negative]
                    if covers:
                        assert row['record']['answer'] is False
                        negative_covers.append(dict(cohort=row['cohort'],case=row['case'],order=cohort,clauses=covers,refuted_assumptions=sorted(negative),
                                    refutations=[dict(literal=d['assumption'][0],attempt_index=d['index'],residual_sha256=d['ordered_residual_sha256']) for d in diagnosis if not d['answer']]))
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
    for late,early in zip(saved_rows['probe'],saved_rows['affine']):
        assert late['case']==early['case']
        a=late['admission'];b=early['admission']
        if a is None or a['discovery'] is None:
            assert b is None or b['discovery'] is None
            continue
        x=a['discovery'];y=b['discovery']
        # Publication can change later availability; record any changed discovery.
        prefix_checks.append(dict(case=early['case'],family=cases[early['case']]['family'],
            previous_probes=len(x['attempts']),base_probes=len(y['attempts']),unchanged=x==y,extra_probes=int(b.get('gap') is not None),
            avoided_probes=len(x['attempts'])-len(y['attempts']),reason=b['reason']))
    retrospective=[]
    for row in saved_rows['affine']:
        a=row['admission']
        if a is None or a['reason']!='gap-negative-cover':continue
        d=a['discovery'];cover=row['local_choice'];extra=len(d['attempts'])
        prior_indices=[i for i in cover['attempts'] if i!=extra]
        cutoff=max(prior_indices)+1
        retrospective.append(dict(case=row['case'],clause=cover['clause'],extra_literal=a['gap']['candidate']['literal'],
            required_prior_indices=prior_indices,required_prefix=cutoff,base_probes=extra,
            later_base_probes=extra-cutoff,additional_probes=1,
            limitation='Retrospective feasibility for this chosen clause; no implemented early admission rule or measured timing saving.'))
    negative_frontier=[d for d in affine_details if d['status'] in ('linear-conflict','space-exhausted')]
    assert all(d['answer'] is False for d in negative_frontier)
    result = dict(negative_affine_frontier=negative_frontier,affine_diagnoses=affine_details,retrospective_cover_prefixes=retrospective,partial_clause_covers=partial_covers,negative_clause_covers=negative_covers,late_conditioned_residuals=late_diagnoses,prefix_checks=prefix_checks,newly_ready_support=frontier_attribution(out, report), groups=groups, cases=details, controls=controls, counter_audits=audits, conditioned_residuals=diagnoses,
        timing_pairs=[dict(repeat=i, query_delta=modes['affine', i]['query_seconds']-modes['probe', i]['query_seconds'],
            complete_delta=modes['affine', i]['complete_worker_seconds']-modes['probe', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Posthoc audits independently bind extraction, check the complete basis, enumerate each candidate in direct Gray coordinates and check the first rejecting clause; they are excluded from timing.',
            'Only checked positive models change native publication. Negative affine diagnostics and budget misses retain the prior fallback; no new native proof kind or unrestricted-SAT claim.',
            'All grouping, elimination, checking, basis, packed-clause and candidate counters are reconstructed from bound evidence. Publication and historical replay remain separate charges.'])
    base.write(out/'attribution.json', result)
    print(base.encode(dict(counter_audits=audits, timing_pairs=result['timing_pairs'],
        successes=[d for d in details if d['reason']=='affine-positive-model'])))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
