#!/usr/bin/env python3
"""Independently reconstruct local rankings, stream availability and composition."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy, shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_local_guard as study
from experiments.cnf_residual_dag import propagate, restrict
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


def expected_local(s, target, limit):
    record = dict(baseline=None, fixed=[], ranks=[], candidates=[], attempts=[], selected=None)
    if not limit: return None, record
    def screen(source):
        cnf, names, root = s._canonical(source); fixed, trace, conflict = propagate(cnf, Counter())
        residual = () if conflict is not None else restrict(cnf, fixed)
        return cnf, names, fixed, dict(root=root, trace=trace, conflict=conflict, residual_literals=sum(map(len, residual)))
    cnf, names, fixed, baseline = screen(target); record['baseline'] = baseline
    record['fixed'] = [[names[v - 1], bit] for v, bit in sorted(fixed.items())]
    if baseline['conflict'] is not None: return dict(kind='terminal', screen=baseline), record
    scores = {v: sum(sum(abs(l) == v for l in c) for c in cnf if len(c) == 2) for v in range(1, len(names) + 1) if v not in fixed}
    ranked = sorted(scores, key=lambda v: (-scores[v], names[v - 1]))
    record['ranks'] = [dict(variable=names[v - 1], binary_incidence=scores[v]) for v in ranked]
    record['candidates'] = [[sign * names[v - 1]] for v in ranked[:limit] for sign in (-1, 1)]
    for clause in record['candidates']:
        _, _, _, candidate = screen([list(c) for c in target] + [clause])
        record['attempts'].append(dict(clause=clause, screen=candidate))
        if candidate['conflict'] is not None:
            record['selected'] = len(record['attempts']) - 1
            return dict(kind='guard', clause=clause, screen=candidate), record
    return None, record


def check_result(s, row, target, guards, mode, eligible, limit, available):
    choice, trace = expected_local(s, target, limit) if mode == 'local' and eligible else (None, None)
    assert (choice, trace) == (row['local_choice'], row['local_probe']) and eligible == row['local_eligible']
    r = row['record']; guards = list(guards)
    if choice is not None and choice['kind'] == 'guard':
        g = r['guards'][-1]; assert g['stronger'] == [list(c) for c in target] + [choice['clause']]
        assert g['removed_clause'] == choice['clause'] and g['stronger_root'] == choice['screen']['root'] == row['premise']['root']
        assert row['premise']['answer'] is False
        assert row['premise']['metrics'].get('inserted_nodes', 0) == int(base.key_sha(g['stronger_root']) not in available)
        _, target = check_guard(s, target, g); guards.append(g)
    else: assert row['premise'] is None
    assert guards == r['guards']
    assert row['child']['root'] == s._canonical(target)[2]
    assert all(r['child'][k] == row['child'][k] for k in ('root', 'answer', 'model'))
    return check_composed(s, r)


def validate(out):
    started = time.perf_counter(); report = base.load(out / 'report.json'); p = bound(report['protocol']); parent = bound(p['parent'])
    for f, h in p['source_fingerprints'].items(): assert base.sha(f) == h, f
    assert bound(p['previous_decisions']) == study.exclusions(parent)
    ordinary = sum((bound(parent[f]) for f in study.FIELDS), []); old = study.inherited(parent)
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
        # Historical arms never see results added by later queries or this run.
        hp = bound(p['historical_protocol']); authority = bound(hp['parent']); trial = bound(p['historical_trial']); old_rows = bound(trial['queries'])
        hi = read(authority['reference_union'], 'historical-initial'); hf = read(trial['archive'], 'historical-final')
        prefixes = study.partition.partition_study.prefixes(hi, hf, old_rows)
        controls = [bound(e) for e in bound(p['historical_baselines'])['samples']]
        diagnosis = bound(p['diagnosis'])
        hs = [bound(e) for e in bound(report['historical'])['samples']]
        assert [(r['case'], r['mode']) for r in hs] == [(cid, m) for cid in p['historical_cases'] for m in study.MODES]
        hbindings = dict(legacy=hp['support_index'], causal=hp['causal_index']); hindices = {n: bound(e) for n, e in hbindings.items()}
        hprepared = study.prep.ordinary.compose(hindices, hbindings); hused = [(n, bound(authority[n])) for n in study.OLD_FIELDS]
        for data in hs:
            cid = data['case']; mode = data['mode']; before = prefixes[cid]; saved = dict(before); delta = bound(data['delta'])
            assert data['prefix_nodes'] == len(before) and data['prefix_digest'] == base.key_sha(base.encode(sorted(before.items())))
            for k, v in delta: assert k not in saved; saved[k] = v
            r = bound(data['records'])[0]; assert r == data['record']; original = next(x['record'] for x in old_rows if x['case'] == cid)
            assert r['source'] == original['source'] and r['answer'] == original['answer']
            path = tmp / 'history-arm'; shutil.copyfile(tmp / 'historical-initial', path); s = study.native.ResidualSolver(path)
            try:
                with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in saved.items() if k not in hi])
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Historical validation search')), patch.object(s, '_store', side_effect=AssertionError('Historical validation publication')):
                    target = original['source']
                    for g in original['guards']: assert g['stronger_root'] in before; _, target = check_guard(s, target, g)
                    check_result(s, data, target, original['guards'], mode, True, p['variable_limit'], set(map(base.key_sha, before)))
                    if mode == 'baseline':
                        expected = next(x for x in controls if x['case'] == cid and x['mode'] == mode)
                        assert dict(delta) == dict(bound(expected['delta'])) and r == bound(expected['records'])[0]
                    else:
                        diagnosed = next(x for x in diagnosis['cases'] if x['case'] == cid)
                        prior_probe = next(x for x in diagnosed['modes'] if x['mode'] == 'original-binary')
                        assert data['prefix_digest'] == diagnosed['prefix_digest']
                        assert data['local_choice'] == prior_probe['choice']
                        assert data['local_probe']['ranks'] == prior_probe['ranks']
                        assert data['probe_counts']['propagation_literal_visits'] == prior_probe['probe_counts']['propagation_literal_visits']
            finally: s.close()
            assert data['new_nodes'] == len(delta) == sum(c['metrics'].get('inserted_nodes', 0) for c in (data['child'], data['premise']) if c is not None)
            assert data['new_payload_units'] == sum(len(k) + len(v) for k, v in delta)
            assert data['summary'] == study.summarize([data])
            cold = study.native.audit_records(path, [r], [], hprepared, hused, hindices)
            audits.append(dict(cohort='historical', case=cid, mode=mode, cold=cold)); all_decisions.append(r); merge(dict(delta), data['delta'])
        # Independently regenerate the excluded catalogue and check every stream prefix.
        catalog = bound(report['cases']); s = study.native.ResidualSolver(tmp / 'initial')
        try:
            assert study.prep.ordinary.eager.previous.inputs(s, p) == catalog
            keys = {s._canonical(c['source'])[2] for c in catalog['cases']}
            assert len(keys) == 192 and not keys & set(initial) and not keys & {r['query_root'] for r in ordinary + old}
        finally: s.close()
        assert [(e['repeat'], e['mode']) for e in report['samples']] == [(i, m) for i, order in enumerate(p['orders']) for m in order]
        for num, entry in enumerate(report['samples']):
            data = bound(entry); mode = entry['mode']; records = bound(data['queries']); warm = bound(data['warm'])
            path = tmp / f'trial-{num}'; base.restore_archive(data['archive'], path); s = SnapshotResidualSolver(path)
            try:
                final = study.native.rows(s); assert initial.items() <= final.items(); available = set(map(base.key_sha, initial))
                by_hash = {base.key_sha(k): k for k in final}; assert len(by_hash) == len(final)
                assert len(records) == len(warm) == 192
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
                        got = check_result(s, row, target, guards, mode, eligible_local, p['variable_limit'], current)
                        acquired = [c for c in (row['child'], row['premise']) if c is not None]
                        assert row['new_nodes'] == len(ordinary_ids) + len(near_ids) + sum(c['metrics'].get('inserted_nodes', 0) for c in acquired)
                        assert all(base.key_sha(c['root']) in available | ids for c in acquired)
                        assert base.load_json(base.encode(got)) == w['result']; available.update(ids)
                assert available == set(by_hash); summary = data['summary']
                assert summary['row_digest'] == base.key_sha(base.encode(sorted(final.items())))
                assert summary['new_nodes'] == len(final) - len(initial) == sum(r['new_nodes'] for r in records)
                assert summary['new_payload_units'] == sum(len(k) + len(v) for k, v in final.items() if k not in initial)
                assert all(summary[k] == v for k, v in study.summarize(records).items())
                truth = [r['record']['answer'] for r in records]
                if fresh_answers is None: fresh_answers = truth
                else: assert fresh_answers == truth
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
        inherited_audit = audit(path, direct + ordinary)
        composed_audit = study.native.audit_records(path, old + rebuilt, bound(parent['conditioned_core_projections']), prepared, used, indices)
        if union == initial: archive = parent['reference_union']
        else:
            dest = out / 'reference-union'; dest.mkdir(); archive = base.archive(path, dest)
        base.write(out / 'decisions.json', rebuilt); checkpoint = copy.deepcopy(parent)
        checkpoint.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=p['source_fingerprints'],
                          local_guard_study=study.binding(out / 'report.json'), local_guard_decisions=study.binding(out / 'decisions.json'))
        base.write(out / 'checkpoint.json', checkpoint)
        _, old_structural = restore_checkpoint(p['parent']['path'], tmp / 'old-patterns')
        _, structural = restore_checkpoint(out / 'checkpoint.json', tmp / 'patterns'); assert structural == old_structural
        supplemental = check_supplement(out / 'checkpoint.json')
    result = dict(passed=True, protocol=report['protocol'], report=study.binding(out / 'report.json'), checkpoint=study.binding(out / 'checkpoint.json'),
                  audits=audits, alternate_certificate_occurrences=alternates, preserved_keys=len(initial), union_keys=len(union), new_keys=len(union) - len(initial),
                  inherited_decisions=len(direct) + len(ordinary), inherited_composed=len(old), new_composed=len(rebuilt), fresh_queries=192,
                  projection_records=len(bound(parent['conditioned_core_projections'])), inherited_audit=inherited_audit, composed_audit=composed_audit,
                  structural=structural, supplemental=supplemental, seconds=time.perf_counter() - started)
    base.write(out / 'reconstruction.json', result)
    print(base.encode({k: result[k] for k in ('passed', 'preserved_keys', 'union_keys', 'new_keys', 'inherited_decisions', 'inherited_composed', 'new_composed', 'fresh_queries', 'seconds')}), flush=True)


if __name__ == '__main__': validate(Path(sys.argv[1]))
