#!/usr/bin/env python3
"""Independently reconstruct stopped discovery prefixes, models and retained state."""
from pathlib import Path
from unittest.mock import patch
import copy, shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_negative_cover as study
from experiments.validate_cnf_mixed_completion import expected as prior_expected
from experiments.cnf_cross_family import truth_table
from experiments.cnf_incremental_support import check_proposals
from experiments.cnf_clause_deletion_guard import check_guard, ExtensionBank
from experiments.cnf_guard_chain import make_record
from experiments.validate_cnf_partition_screen import check_composed
from experiments.validate_cnf_premise_guard import expected_choice
from experiments.validate_cnf_terminal_guard import check_selection
from experiments.cnf_snapshot_replay import audit, SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base = study.base



def expected(s,source,limit,available,evidence):
    choice,trace=prior_expected(s,source,limit,available,evidence)
    d=trace['discovery']
    if d is None or (choice is not None and choice['kind']!='fallback-trace'):return choice,trace
    negative={}
    for item in d['completions']:
        if 'mixed' in item and item['mixed']['model'] is None:
            index=item['index'];negative.setdefault(d['attempts'][index]['clause'][0],index)
    for cid,raw in enumerate(source):
        clause=sorted(set(raw))
        if not clause or any(-l in clause for l in clause) or not all(l in negative for l in clause):continue
        cover=dict(clause_index=cid,clause=clause,attempts=[negative[l] for l in clause])
        trace.update(cover_previous_reason=trace['reason'],reason='negative-cover',cover=cover)
        return dict(kind='negative-cover',root=s._canonical(source)[2],**copy.deepcopy(cover)),trace
    return choice,trace


def check_result(s, row, target, guards, mode, eligible, limit, available):
    if not eligible or mode=='baseline': choice,trace=None,None
    elif mode=='cover': choice,trace=expected(s,target,limit,available,row['admission'])
    else: choice,trace=prior_expected(s,target,limit,available,row['admission'])
    assert eligible == row['local_eligible'] and choice == row['local_choice'] and trace == row['admission']
    assert row['local_probe'] == (None if trace is None else trace['discovery'])
    if mode in ('mixed', 'cover') and trace is not None and trace['discovery'] is not None:
        d = trace['discovery']; f = d['binary_filter']
        assert row['probe_counts'].get('binary_probe_skips', 0) == (len(f['skipped']) if f else 0)
        assert row['probe_counts'].get('local_premise_probes', 0) == len(d['attempts'])
    r = row['record']; guards = list(guards)
    if choice is not None and choice['kind'] == 'guard':
        g = r['guards'][-1]; assert g['stronger'] == [list(c) for c in target] + [choice['clause']]
        assert g['removed_clause'] == choice['clause'] and g['stronger_root'] == choice['screen']['root'] == row['premise']['root']
        assert row['premise']['answer'] is False
        assert row['premise']['metrics'].get('inserted_nodes', 0) == int(g['stronger_root'] not in available)
        assert row['child']['metrics'].get('expanded_nodes', 0) == 0
        assert sum(c['metrics'].get('inserted_nodes', 0) for c in (row['premise'], row['child'])) <= 2
        _, target = check_guard(s, target, g); guards.append(g)
    else:
        assert row['premise'] is None
        if choice is not None and choice['kind']=='negative-cover':
            assert row['child']['answer'] is False and row['child']['model'] is None
            assert row['child']['metrics'].get('expanded_nodes',0)==0
            assert row['child']['metrics']['negative_cover_publications']==1
            assert 1<=row['child']['metrics']['inserted_nodes']<=row['child']['metrics']['cover_planned_nodes']<=3*len(choice['clause'])-1
        if choice is not None and choice['kind'] == 'propagated':
            known = choice['exposed']['known']
            assert row['child']['metrics'].get('expanded_nodes', 0) <= (0 if known else 1)
            assert row['child']['metrics'].get('inserted_nodes', 0) <= (1 if known else 2)
        if choice is not None and choice['kind'] == 'fallback-trace':
            assert choice['screen']['trace'] and choice['screen']['conflict'] is None
            assert row['child']['metrics']['screen_trace_publications'] == 1
        if choice is not None and choice['kind'] == 'positive-model':
            assert row['child']['answer'] is True and row['child']['metrics'].get('expanded_nodes', 0) == 0
            assert row['child']['metrics']['inserted_nodes'] == row['child']['metrics']['positive_model_publications'] == 1
            assert base.load_json(base.encode(row['child']['model'])) == base.load_json(base.encode(dict(choice['model'])))
    assert guards == r['guards'] and row['child']['root'] == s._canonical(target)[2]
    assert all(r['child'][k] == row['child'][k] for k in ('root', 'answer', 'model'))
    return check_composed(s, r)


def validate(out):
    started = time.perf_counter(); report = base.load(out / 'report.json'); p = bound(report['protocol']); parent = bound(p['parent'])
    for f, h in p['source_fingerprints'].items(): assert base.sha(f) == h, f
    assert bound(p['previous_decisions']) == study.exclusions(parent)
    ordinary = sum((bound(parent[f]) for f in study.FIELDS), []); old = study.inherited(parent)
    prior = base.load(study.PARENT / 'validation.json'); manifests = dict(prior['parent_manifests'])
    mp = str(study.PARENT / 'manifest.json'); manifests[mp] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert base.sha(path) == entry['sha256']; entries = base.load(path)['artifacts']; assert len(entries) == entry['artifacts_checked']
        for f, h in entries.items(): assert base.sha(f) == h, f
        artifacts += len(entries)
    assert (len(prior['source_fingerprints']), artifacts, len(manifests)) == (529, 6431, 99)
    base.write(out / 'parent-manifests.json', manifests); frontiers = {}
    all_decisions = []; audits = []; alternates = []; fresh_answers = None; by_mode = {}
    bindings = dict(legacy=p['support_index'], causal=p['causal_index']); indices = {n: bound(e) for n, e in bindings.items()}
    prepared = study.prep.ordinary.compose(indices, bindings); used = [(n, bound(parent[n])) for n in study.OLD_FIELDS]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = study.native.ResidualSolver(path)
            try: return study.native.rows(s)
            finally: s.close()
        initial = read(parent['reference_union'], 'initial'); union = dict(initial)
        def merge(rows, evidence):
            for k, v in rows.items():
                if k in union and union[k] != v:
                    assert base.load_json(union[k])['answer'] == base.load_json(v)['answer']
                    alternates.append(dict(root_sha256=base.key_sha(k), evidence=evidence))
                union.setdefault(k, v)
        # Restore exact control prefixes independently by removing future insertions.
        cp = bound(p['control_protocol']); hp = bound(cp['historical_protocol']); ht = bound(cp['historical_trial']); ct = bound(cp['fresh_trial']); cfp = bound(cp['prior_protocol'])
        rt = bound(p['reuse_trial']); rp = bound(bound(p['prior_stream'])['protocol'])
        bt = bound(p['fallback_trial']); bp = bound(bound(p['fallback_stream'])['protocol'])
        pt = bound(p['positive_trial']); pp = bound(bound(p['positive_stream'])['protocol'])
        mt = bound(p['premise_trial']); mp = bound(bound(p['premise_stream'])['protocol'])
        contexts = {}
        groups = [
            ('historical', bound(hp['parent'])['reference_union'], ht, cp['historical_cases']),
            ('fresh-baseline', bound(cfp['parent'])['reference_union'], ct, cp['fresh_cases']),
            ('reuse-stream', bound(rp['parent'])['reference_union'], rt, [p['reuse_case']]),
            ('fallback-stream', bound(bp['parent'])['reference_union'], bt, p['fallback_cases']),
            ('positive-stream', bound(pp['parent'])['reference_union'], pt, p['positive_cases']),
            ('premise-stream', bound(mp['parent'])['reference_union'], mt, p['premise_cases'])]
        for cohort, stream_field, trial_field, ids_field in (
            ('uniform-target', 'uniform_control_stream', 'uniform_control_trial', 'uniform_control_cases'),
            ('recovery-controls', 'recovery_control_stream', 'recovery_control_trial', 'recovery_control_cases'),
            ('mixed-controls', 'mixed_control_stream', 'mixed_control_trial', 'mixed_control_cases'),
            ('cover-target', 'cover_control_stream', 'cover_control_trial', 'cover_control_cases')):
            sp = bound(bound(p[stream_field])['protocol'])
            groups.append((cohort, bound(sp['parent'])['reference_union'], bound(p[trial_field]), p[ids_field]))
        control_finals = {}
        for cohort, initial_entry, trial, cases in groups:
            first = read(initial_entry, cohort + '-initial'); final = read(trial['archive'], cohort + '-final'); records = bound(trial['queries']); control_finals[cohort] = final
            for index, r in enumerate(records):
                if r['case'] not in cases: continue
                prep_ids = [] if cohort == 'historical' else r['ordinary_ids'] + r['near_ids']
                excluded = {h for later in records[index:] for h in later['new_ids']} - set(prep_ids)
                before = {k: v for k, v in final.items() if base.key_sha(k) not in excluded}
                assert first.items() <= before.items(); contexts[cohort, r['case']] = (before, r, prep_ids)
        control_rows = [bound(e) for e in bound(report['controls'])['samples']]
        assert len(control_rows) == 52 and {(r['cohort'], r['case'], r['mode']) for r in control_rows} == {(cohort, cid, mode) for cohort, cid in contexts for mode in ('mixed', 'cover')}
        previous_controls = [bound(e) for e in bound(p['control_reports'])['samples']]
        reverse_rows = [bound(e) for e in bound(report['reverse_control'])['samples']]
        assert [(r['cohort'], r['case'], r['mode']) for r in reverse_rows] == [('cover-target', 59, 'cover'), ('cover-target', 59, 'mixed')]
        for row in control_rows + reverse_rows:
            before, original, prep_ids = contexts[row['cohort'], row['case']]
            assert row['prefix_nodes'] == len(before) and row['prefix_digest'] == base.key_sha(base.encode(sorted(before.items())))
            assert row['input_guards'] == original['record']['guards'] and row['preparation_ids'] == prep_ids
            delta = bound(row['delta']); assert len(dict(delta)) == len(delta) == row['new_nodes']
            assert all(k not in before for k, _ in delta)
            path = tmp / 'control'; path.unlink(missing_ok=True); s = study.native.ResidualSolver(path)
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', {**before, **dict(delta)}.items())
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Control search')), patch.object(s, '_store', side_effect=AssertionError('Control publication')):
                    source = original['record']['source']; target = source
                    for g in row['input_guards']: assert g['stronger_root'] in before; _, target = check_guard(s, target, g)
                    assert [list(c) for c in target] == row['input_target']
                    answer = check_result(s, row, target, row['input_guards'], row['mode'], True, p['variable_limit'], set(before))
                    assert answer['answer'] == original['record']['answer']
            finally: s.close()
            assert bound(row['records']) == [row['record']] and row['summary'] == study.summarize([row])
            assert row['new_payload_units'] == sum(len(k) + len(v) for k, v in delta)
            assert row['new_nodes'] == sum(c['metrics'].get('inserted_nodes', 0) for c in (row['premise'], row['child']) if c is not None)
            comparators = [x for x in previous_controls if x['cohort'] == row['cohort'] and x['case'] == row['case'] and x['mode'] == 'mixed']
            if comparators:
                expected_delta = dict(bound(comparators[0]['delta'])); expected_record = comparators[0]['record']
            else:
                expected_ids = set(original['new_ids']) - set(prep_ids)
                expected_delta = {k: v for k, v in control_finals[row['cohort']].items() if base.key_sha(k) in expected_ids}
                expected_record = original['record']
            if row['mode'] == 'mixed' or row['admission']['reason'] != 'negative-cover':
                assert dict(delta) == expected_delta and row['record'] == expected_record
            else:
                assert 1<=row['new_nodes']<=3*len(row['local_choice']['clause'])-1 and row['premise'] is None
            if row in reverse_rows:
                first = next(x for x in control_rows if (x['cohort'], x['case'], x['mode']) == (row['cohort'], row['case'], row['mode']))
                assert bound(first['delta']) == delta and first['record'] == row['record']
            all_decisions.append(row['record']); merge(dict(delta), row['delta'])
            audits.append(dict(cohort=row['cohort'], case=row['case'], mode=row['mode'], passed=True))
        # Independently regenerate the excluded catalogue and check every stream prefix.
        catalog = bound(report['cases']); s = study.native.ResidualSolver(tmp / 'initial')
        try:
            assert study.inputs(s, p) == catalog
            keys = {s._canonical(c['source'])[2] for c in catalog['cases']}
            assert len(keys) == 60 and not keys & set(initial) and not keys & {r['query_root'] for r in ordinary + old}
        finally: s.close()
        truth_started = time.perf_counter()
        truth = {c['case']: truth_table(c['source']) for c in catalog['cases'] if c['family'] != 'neighbour-control'}
        base.write(out / 'truth.json', dict(cases=truth, seconds=time.perf_counter()-truth_started))
        assert len(truth) == 48
        assert [(e['repeat'], e['mode']) for e in report['samples']] == [(i, m) for i, order in enumerate(p['orders']) for m in order]
        for num, entry in enumerate(report['samples']):
            data = bound(entry); mode = entry['mode']; records = bound(data['queries']); warm = bound(data['warm'])
            path = tmp / f'trial-{num}'; base.restore_archive(data['archive'], path); s = SnapshotResidualSolver(path)
            try:
                final = study.native.rows(s); assert initial.items() <= final.items(); available = set(map(base.key_sha, initial))
                by_hash = {base.key_sha(k): k for k in final}; assert len(by_hash) == len(final)
                assert len(records) == len(warm) == 60
                extensions = ExtensionBank(bound(p['bank_catalog'])['bank'])
                with patch.object(s, '_expand', side_effect=AssertionError('Stream validation search')), patch.object(s, '_store', side_effect=AssertionError('Stream validation publication')):
                    for row, case, w in zip(records, catalog['cases'], warm):
                        r = row['record']; assert row['case'] == case['case'] == w['case'] and r['source'] == case['source']
                        ids = set(row['new_ids']); assert len(ids) == row['new_nodes'] == len(row['new_ids']) and not ids & available
                        ordinary_ids = set(row['ordinary_ids']); near_ids = set(row['near_ids'])
                        assert not ordinary_ids & near_ids and ordinary_ids | near_ids <= ids
                        normal = dict(row['ordinary'], new_ids=row['new_ids']); assert normal['source'] == case['source']
                        check_selection(s, extensions, normal, prepared, available, 'ready', p['alternative_budget'])
                        guards = [] if normal['guard'] is None else [normal['guard']]
                        target = case['source'] if not guards else check_guard(s, case['source'], guards[0])[1]
                        current = available | ordinary_ids
                        eligible = bool(guards) and not normal['target_known'] and normal['cofactor'] is None
                        assert eligible == row['near_eligible']
                        choice = expected_choice(s, target, prepared['cores'], current, 'premise-first') if eligible else None
                        assert choice == row['near_choice']
                        if choice:
                            g = r['guards'][len(guards)]
                            assert g['stronger'] == [list(c) for c in target] + [choice['missing_clause']] and g['removed_clause'] == choice['missing_clause']
                            assert near_ids == ({base.key_sha(g['stronger_root'])} if choice['inserted'] else set())
                            _, target = check_guard(s, target, g); guards.append(g)
                        else: assert not near_ids
                        current |= near_ids; eligible_local = base.key_sha(s._canonical(target)[2]) not in current
                        cnf, names, root = s._canonical(target)
                        assert row['familiarity'] == dict(root=root, known_after_preparation=not eligible_local, guards=len(guards),
                            variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf)))
                        got = check_result(s, row, target, guards, mode, eligible_local, p['variable_limit'], {by_hash[h] for h in current})
                        if case['case'] in truth: assert got['answer'] == truth[case['case']]['answer']
                        acquired = [c for c in (row['child'], row['premise']) if c is not None]
                        assert row['new_nodes'] == len(ordinary_ids) + len(near_ids) + sum(c['metrics'].get('inserted_nodes', 0) for c in acquired)
                        assert all(base.key_sha(c['root']) in available | ids for c in acquired)
                        assert base.load_json(base.encode(got)) == w['result']; available.update(ids)
                assert available == set(by_hash); summary = data['summary']
                assert summary['row_digest'] == base.key_sha(base.encode(sorted(final.items())))
                assert summary['new_nodes'] == len(final) - len(initial) == sum(r['new_nodes'] for r in records)
                assert summary['new_payload_units'] == sum(len(k) + len(v) for k, v in final.items() if k not in initial)
                assert all(summary[k] == v for k, v in study.summarize(records).items())
                answers = [r['record']['answer'] for r in records]
                if fresh_answers is None: fresh_answers = answers
                else: assert fresh_answers == answers
                if mode in by_mode: assert final == by_mode[mode]
                else: by_mode[mode] = final
                if entry['repeat'] == 0: all_decisions.extend(r['record'] for r in records)
            finally: s.close()
            cold = study.native.audit_records(path, old + [r['record'] for r in records], bound(parent['conditioned_core_projections']), prepared, used, indices)
            audits.append(dict(cohort='fresh', mode=mode, repeat=entry['repeat'], cold=cold)); merge(final, data['archive'])
        # Retain all previous payloads; reconstruct new witnesses against this union.
        path = tmp / 'union'; shutil.copyfile(tmp / 'initial', path); s = study.native.ResidualSolver(path); rebuilt = []; direct = []
        try:
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in union.items() if k not in initial])
            assert study.native.rows(s) == union; s.db.execute('PRAGMA query_only=ON')
            with patch.object(s, '_expand', side_effect=AssertionError('Union search')), patch.object(s, '_store', side_effect=AssertionError('Union publication')):
                for r in all_decisions:
                    target = r['source']
                    for g in r['guards']: _, target = check_guard(s, target, g)
                    rebuilt.append(make_record(s, r['source'], r['guards'], s.solve(target)))
                for r in old + rebuilt: check_composed(s, r)
                for pr in bound(parent['conditioned_core_projections']): study.native.check_projection(s, pr)
                original = base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions']) + bound(parent['model_rotation_decisions']):
                    source = d['source'] if 'source' in d else original[d['case']]['source']; child = s.solve(source)
                    assert child['root'] == d['root'] and child['answer'] == d['answer']
                    assert child['model'] == (None if d['model'] is None else {int(k): v for k, v in d['model'].items()})
                    direct.append(dict(source=source, guard=None, witness=None, child=child, answer=child['answer'], model=child['model']))
        finally: s.close()
        # Retained support banks are checked against the expanded union without acquisition.
        s = study.native.ResidualSolver(path)
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s, '_expand', side_effect=AssertionError('Frontier search')), patch.object(s, '_store', side_effect=AssertionError('Frontier publication')):
                for name in ('active_support_proposals', 'extended_support_proposals', 'causal_support_proposals', 'incremental_causal_proposals'):
                    bank = bound(parent[name]); names = {o['catalog'] for o in bank['origins']}; catalogs = [(f, bound(parent[f])) for f in study.FIELDS if f in names]
                    assert {n for n, _ in catalogs} == names; lineage = check_proposals(s, bank, catalogs); ready = 0
                    for core in bank['cores']:
                        cnf, _, key = s._canonical(core['source']); node = s._read(key, cnf)
                        if node is not None: assert node['answer'] is False; ready += 1
                    frontiers[name] = dict(binding=parent[name], catalogs=len(catalogs), lineage=lineage, retained=len(bank['cores']), ready=ready, pending=len(bank['cores']) - ready)
        finally: s.close()
        inherited_audit = audit(path, direct + ordinary)
        composed_audit = study.native.audit_records(path, old + rebuilt, bound(parent['conditioned_core_projections']), prepared, used, indices)
        if union == initial: archive = parent['reference_union']
        else:
            dest = out / 'reference-union'; dest.mkdir(); archive = base.archive(path, dest)
        base.write(out / 'decisions.json', rebuilt); checkpoint = copy.deepcopy(parent)
        checkpoint.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=p['source_fingerprints'],
                          negative_cover_study=study.binding(out / 'report.json'), negative_cover_decisions=study.binding(out / 'decisions.json'))
        base.write(out / 'checkpoint.json', checkpoint)
        _, old_structural = restore_checkpoint(p['parent']['path'], tmp / 'old-patterns')
        _, structural = restore_checkpoint(out / 'checkpoint.json', tmp / 'patterns'); assert structural == old_structural
        supplemental = check_supplement(out / 'checkpoint.json')
    result = dict(passed=True, protocol=report['protocol'], report=study.binding(out / 'report.json'), checkpoint=study.binding(out / 'checkpoint.json'),
                  audits=audits, alternate_certificate_occurrences=alternates, preserved_keys=len(initial), union_keys=len(union), new_keys=len(union) - len(initial),
                  inherited_decisions=len(direct) + len(ordinary), inherited_composed=len(old), new_composed=len(rebuilt), fresh_queries=60,
                  projection_records=len(bound(parent['conditioned_core_projections'])), inherited_audit=inherited_audit, composed_audit=composed_audit,
                  structural=structural, supplemental=supplemental, union_frontiers=frontiers,
                  preservation=dict(prior_sources_unchanged=529, prior_artifacts_unchanged=artifacts, prior_manifests_unchanged=len(manifests)),
                  seconds=time.perf_counter() - started)
    base.write(out / 'reconstruction.json', result)
    print(base.encode({k: result[k] for k in ('passed', 'preserved_keys', 'union_keys', 'new_keys', 'inherited_decisions', 'inherited_composed', 'new_composed', 'fresh_queries', 'seconds')}), flush=True)


if __name__ == '__main__': validate(Path(sys.argv[1]))
