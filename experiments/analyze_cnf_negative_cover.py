#!/usr/bin/env python3
"""Attribute negative clause-cover compilation and its retained proof costs."""
from pathlib import Path
from collections import Counter
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_negative_cover as study
from experiments.analyze_cnf_mixed_completion import audit_counts as audit_mixed
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_counts(row,target):
    details=audit_mixed(row,target)
    a=row['admission'];d=None if a is None else a['discovery'];choice=row['local_choice']
    expected=dict(cover_completion_reads=0,cover_clause_visits=0,cover_literal_visits=0,cover_candidates=0)
    eligible=d is not None and (choice is None or choice['kind'] in ('fallback-trace','negative-cover'))
    if eligible:
        expected['cover_completion_reads']=len(d['completions'])
        negative={d['attempts'][c['index']]['clause'][0] for c in d['completions'] if 'mixed' in c and c['mixed']['model'] is None}
        if negative:
            for cid,clause in enumerate(target):
                expected['cover_clause_visits']+=1;expected['cover_literal_visits']+=len(clause)
                literals=sorted(set(clause))
                if literals and not any(-l in literals for l in literals) and set(literals)<=negative:
                    expected['cover_candidates']=1
                    assert choice['kind']=='negative-cover' and choice['clause_index']==cid and choice['clause']==literals
                    break
    assert all(row['probe_counts'].get(k,0)==v for k,v in expected.items())
    checked=dict(cover_premise_literal_payload=0,cover_checked_reason_literals=0,cover_checked_implication_edges=0)
    if choice and choice['kind']=='negative-cover':
        assert row['child']['answer'] is False and row['child']['metrics'].get('expanded_nodes',0)==0
        by_index={x['index']:x for x in d['completions']}
        for literal,index in zip(choice['clause'],choice['attempts']):
            attempt=d['attempts'][index];assert attempt['clause']==[literal]
            cnf=base.load_json(attempt['screen']['root'].split(':',1)[1]);proof=by_index[index]['mixed']['proof']
            checked['cover_premise_literal_payload']+=sum(map(len,target))+1
            checked['cover_checked_reason_literals']+=sum(len(cnf[cid]) for _,cid in attempt['screen']['trace'])
            checked['cover_checked_implication_edges']+=len(proof['forward'])+len(proof['backward'])
        assert row['child']['metrics']['cover_planned_nodes']<=3*len(choice['clause'])-1
        assert row['child']['metrics'].get('cover_path_repairs',0)<=len(choice['clause'])
    assert all(row['child']['metrics'].get(k,0)==v for k,v in checked.items())
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
    details = []; groups = {}; modes = {}; audits = 0; diagnoses = []; late_diagnoses=[]; saved_rows={}; negative_covers=[]; partial_covers=[]
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        if entry['repeat']==0: saved_rows[mode]=records
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    if mode in ('cover', 'mixed'):
                        target = row['record']['source']
                        # A successful guard appends one guard after selection.
                        guards = row['record']['guards']
                        if row['local_choice'] and row['local_choice']['kind'] == 'guard': guards = guards[:-1]
                        for g in guards: _, target = check_guard(s, target, g)
                        diagnosis = (audit_counts if mode=='cover' else audit_mixed)(row, target); audits += 1
                        if entry['repeat']==0 and mode=='cover':
                            diagnoses.extend(dict(case=row['case'],family=cases[row['case']]['family'],**d) for d in diagnosis)
                            negative={d['assumption'][0] for d in diagnosis if not d['answer']}
                            covers=[c for c in target if c and set(c)<=negative]
                            if negative and not covers:
                                pending=[];discovery=row['admission']['discovery']
                                observed={x['clause'][0]:x['screen'] for x in discovery['attempts']}
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
                        if entry['repeat']==0 and mode=='mixed':
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
            if row['mode'] in ('mixed','cover'):
                diagnosis=(audit_counts if row['mode']=='cover' else audit_mixed)(row, row['input_target']); audits += 1
                if row['mode']=='cover':
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
    for late,early in zip(saved_rows['mixed'],saved_rows['cover']):
        assert late['case']==early['case']
        a=late['admission'];b=early['admission']
        if a is None or a['discovery'] is None:
            assert b is None or b['discovery'] is None
            continue
        x=a['discovery'];y=b['discovery']
        assert x==y # Cover recognition occurs after the unchanged discovery pass.
        assert y['attempts']==x['attempts'][:len(y['attempts'])]
        assert x['binary_filter']['skipped'][:len(y['binary_filter']['skipped'])]==y['binary_filter']['skipped']
        prefix_checks.append(dict(case=early['case'],family=cases[early['case']]['family'],
            late_probes=len(x['attempts']),inline_probes=len(y['attempts']),
            avoided_probes=len(x['attempts'])-len(y['attempts']),reason=b['reason']))
    result = dict(partial_clause_covers=partial_covers,negative_clause_covers=negative_covers,late_conditioned_residuals=late_diagnoses,prefix_checks=prefix_checks,newly_ready_support=frontier_attribution(out, report), groups=groups, cases=details, controls=controls, counter_audits=audits, conditioned_residuals=diagnoses,
        timing_pairs=[dict(repeat=i, query_delta=modes['cover', i]['query_seconds']-modes['mixed', i]['query_seconds'],
            complete_delta=modes['cover', i]['complete_worker_seconds']-modes['mixed', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Posthoc counter audits are excluded from timing. Every saved trace and compiled native negative proof is independently checked by reconstruction.',
            'The complete preceding mixed-completion probe pass is unchanged. Source-clause covers are checked afterwards; no new assumption probes, SCC solving or native proof kind.',
            'A parent refutation requires a whole source-clause cover. Compilation and native checking remain charged; clauses shortened only by baseline propagation remain recognition misses. Two timing orders and finite families do not establish arbitrary-CNF scaling.'])
    base.write(out/'attribution.json', result)
    print(base.encode(dict(counter_audits=audits, timing_pairs=result['timing_pairs'],
        successes=[d for d in details if d['reason']=='negative-cover'])))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
