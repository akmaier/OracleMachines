#!/usr/bin/env python3
"""Attribute uniform completions, recognition misses and remaining two-CNF opportunities."""
from pathlib import Path
from collections import Counter
from itertools import product
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_uniform_premise as study
from experiments.analyze_cnf_positive_premise import audit_counts as audit_previous
from experiments.cnf_residual_dag import two_cnf
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_counts(row, target):
    a = row['admission']; u = None if a is None else a.get('uniform_premise')
    prior = dict(row)
    if u is not None: prior['local_choice'] = None
    audit_previous(prior, target)
    expected = dict(uniform_premise_attempts_scanned=0, uniform_premise_models=0,
        uniform_premise_misses=0, uniform_premise_literals_copied=0,
        uniform_premise_reason_literals=0, uniform_premise_model_literals=0,
        uniform_premise_recognition_clauses=0, uniform_premise_recognition_literal_visits=0)
    diagnoses = []
    if u is not None:
        success = u['selected'] is not None
        expected.update(uniform_premise_attempts_scanned=u['selected']+1 if success else len(a['discovery']['attempts']),
            uniform_premise_models=int(success), uniform_premise_misses=len(u['attempts'])-int(success),
            uniform_premise_literals_copied=(sum(map(len, target))+1)*len(u['attempts']),
            uniform_premise_model_literals=(sum(map(len, target))+1)*int(success))
        for item in u['attempts']:
            attempt = a['discovery']['attempts'][item['index']]
            cnf = base.load_json(attempt['screen']['root'].split(':', 1)[1])
            fixed = {abs(l): l > 0 for l, _ in attempt['screen']['trace']}
            ids = [cid for _, cid in attempt['screen']['trace']]; assert len(ids)==len(set(ids))
            residual = [[l for l in c if abs(l) not in fixed] for c in cnf
                if not any(abs(l) in fixed and fixed[abs(l)]==(l>0) for l in c)]
            expected['uniform_premise_reason_literals'] += sum(len(cnf[cid]) for cid in ids)
            expected['uniform_premise_recognition_clauses'] += len(residual)
            expected['uniform_premise_recognition_literal_visits'] += sum(map(len, residual))
            assert item['residual_literals']==sum(map(len,residual))
            flags = dict(horn=all(sum(l>0 for l in c)<=1 for c in residual),
                dual_horn=all(sum(l<0 for l in c)<=1 for c in residual),
                two_cnf=all(len(c)<=2 for c in residual))
            assert all(len(c)>=2 for c in residual) # Genuine full unit closure.
            assert item['false_valid']==all(any(l<0 for l in c) for c in residual)
            assert item['true_valid']==all(any(l>0 for l in c) for c in residual)
            if flags['horn']: assert item['false_valid']
            if flags['dual_horn']: assert item['true_valid']
            detail=dict(index=item['index'],assumption=attempt['clause'],flags=flags,
                residual_literals=sum(map(len,residual)), residual_variables=len({abs(l) for c in residual for l in c}),
                accepted=item['false_valid'] or item['true_valid'])
            if not detail['accepted'] and flags['two_cnf']:
                counts=Counter(); model, proof=two_cnf(residual,counts)
                lifted = None
                if model is not None:
                    assert not set(model) & set(fixed)
                    merged={**model,**fixed}
                    assert all(any(merged.get(abs(l),False)==(l>0) for l in c) for c in cnf)
                    names=sorted({abs(l) for c in target for l in c})
                    lifted={v:merged.get(i+1,False) for i,v in enumerate(names)}
                    assert all(any(lifted[abs(l)]==(l>0) for l in c) for c in [*target,attempt['clause']])
                else:
                    variable=proof['variable']; assert variable in {abs(l) for c in residual for l in c}
                    for start,end,path in ((variable,-variable,proof['forward']),(-variable,variable,proof['backward'])):
                        current=start
                        for nxt,cid in path:
                            assert 0<=cid<len(residual) and set(residual[cid])=={-current,nxt}
                            current=nxt
                        assert current==end
                detail['posthoc_two_cnf']=dict(answer=model is not None,model=None if model is None else sorted(model.items()),
                    lifted_target_model=None if lifted is None else sorted(lifted.items()), proof=proof,counts=dict(counts))
            diagnoses.append(detail)
    assert all(row['probe_counts'].get(k,0)==v for k,v in expected.items())
    return diagnoses


def miss_embedding_audit():
    # Exhaustive finite check of the general fresh-variable embedding argument.
    pool = [[sign*(i+1) for i,sign in enumerate(signs)] for signs in product((-1,1),repeat=3)]
    def satisfies(cnf, bits):
        return all(any(bits[abs(l)-1] == (l>0) for l in c) for c in cnf)
    positives=negatives=0
    for mask in range(256):
        source=[c for i,c in enumerate(pool) if mask>>i&1]
        embedded=source+[[4,5],[-4,-5]]
        assert all(len(c)>=2 for c in embedded)
        assert not satisfies(embedded,(False,)*5) and not satisfies(embedded,(True,)*5)
        answer=any(satisfies(source,bits) for bits in product((False,True),repeat=3))
        assert answer==any(satisfies(embedded,bits) for bits in product((False,True),repeat=5))
        positives+=answer;negatives+=not answer
    return dict(formulas=256,satisfiable=positives,unsatisfiable=negatives,passed=True,
        limitation='Finite check supports, but does not replace, the general fresh-variable conjunction argument.')


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
    details = []; groups = {}; modes = {}; audits = 0; diagnoses = []
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    if mode == 'uniform':
                        target = row['record']['source']
                        # A successful guard appends one guard after selection.
                        guards = row['record']['guards']
                        if row['local_choice'] and row['local_choice']['kind'] == 'guard': guards = guards[:-1]
                        for g in guards: _, target = check_guard(s, target, g)
                        diagnosis = audit_counts(row, target); audits += 1
                        if entry['repeat']==0:
                            diagnoses.extend(dict(case=row['case'],family=cases[row['case']]['family'],**d) for d in diagnosis)
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
                child_propagation=sum(r['child']['metrics'].get('propagation_literal_visits', 0) for r in selected))
            groups.setdefault(family, {}).setdefault(mode, []).append(summary)
    controls = []
    for cohort in ('controls', 'reverse_control'):
        for entry in bound(report[cohort])['samples']:
            row = bound(entry)
            if row['mode'] == 'uniform': audit_counts(row, row['input_target']); audits += 1
            controls.append(dict(cohort=row['cohort'], case=row['case'], mode=row['mode'], order=cohort,
                new_rows=row['new_nodes'], native_bytes=row['new_payload_units'], retained_bytes=row['retained_bytes'],
                report_bytes=Path(entry['path']).stat().st_size,
                reason=row['admission']['reason'], summary=row['summary'],
                probe_counts=row['probe_counts'], probe_metrics=row['probe_metrics'],
                child_metrics=row['child']['metrics'],
                **{k: row[k] for k in ('selection_seconds', 'child_seconds', 'evaluation_seconds',
                    'warm_seconds', 'cold_seconds', 'open_seconds', 'prefix_write_seconds',
                    'serialization_seconds', 'complete_arm_seconds')}))
    result = dict(newly_ready_support=frontier_attribution(out, report), uniform_miss_embedding=miss_embedding_audit(), groups=groups, cases=details, controls=controls, counter_audits=audits, conditioned_residuals=diagnoses,
        timing_pairs=[dict(repeat=i, query_delta=modes['uniform', i]['query_seconds']-modes['recovered', i]['query_seconds'],
            complete_delta=modes['uniform', i]['complete_worker_seconds']-modes['recovered', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Posthoc counter audits and SCC diagnoses are excluded from the timed policy.',
            'Uniform completion does not add missing probes, stop earlier discovery or solve mixed residuals. Both uniform assignments failing is not an UNSAT certificate.',
            'Posthoc SAT two-CNF models are transported and checked against each raw target-plus-assumption. Negative implication paths are checked, but parent recomposition and timed acquisition remain open.',
            'Saved control14 is selected evidence, not held-out coverage. The four finite fresh generators and two orders do not establish arbitrary-CNF scaling.'])
    base.write(out/'attribution.json', result)
    print(base.encode(dict(counter_audits=audits, timing_pairs=result['timing_pairs'],
        successes=[d for d in details if d['reason']=='uniform-premise-model'])))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
