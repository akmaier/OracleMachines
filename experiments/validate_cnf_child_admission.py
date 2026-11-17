#!/usr/bin/env python3
"""Independent child-admission reconstruction, retained proofs and lineage audit."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_child_admission as study
from experiments.validate_cnf_local_guard import expected_local
from experiments.cnf_residual_dag import propagate, restrict
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_guard_chain import make_record
from experiments.validate_cnf_partition_screen import check_composed
from experiments.cnf_snapshot_replay import audit
from experiments.cnf_incremental_support import check_proposals
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_unsat_support import bound
base = study.base; old = study.old


def expected(s, source, limit, before):
    record = dict(reason=None, discovery=None, proposal=None, child=None)
    if not limit: record['reason'] = 'disabled'; return None, record
    cnf, _, root = s._canonical(source)
    if root in before: record['reason'] = 'known-target'; return None, record
    family = ('two-cnf' if max(map(len, cnf), default=0) <= 2 else
              'horn' if not any(len([l for l in c if l > 0]) > 1 for c in cnf) else
              'dual-horn' if not any(len([l for l in c if l < 0]) > 1 for c in cnf) else None)
    if family: record['reason'] = 'native-' + family; return None, record
    if any(set(c) & {-l for l in c} for c in source):
        record['reason'] = 'tautological-source'; return None, record
    choice, record['discovery'] = expected_local(s, source, limit); record['proposal'] = choice
    if choice is None: record['reason'] = 'no-proposal'; return None, record
    if choice['kind'] == 'terminal': record['reason'] = 'terminal-target'; return choice, record
    assignment = {abs(l): l < 0 for l in choice['clause']}
    # Direct restriction, independent of the production restriction helper.
    child = [[l for l in c if abs(l) not in assignment] for c in source
             if not any(abs(l) in assignment and assignment[abs(l)] == (l > 0) for l in c)]
    cnf, _, root = s._canonical(child); known = root in before; screen = None
    if not known:
        fixed, trace, conflict = propagate(cnf, Counter())
        screen = dict(root=root, trace=trace, conflict=conflict,
                      residual_literals=0 if conflict is not None else sum(map(len, restrict(cnf, fixed))))
    record['child'] = dict(root=root, known=known, screen=screen)
    if known or screen['conflict'] is not None:
        record['reason'] = 'known-child' if known else 'unit-conflict-child'
        return dict(**choice, child=record['child']), record
    record['reason'] = 'nonterminal-child'; return None, record


def validate(out):
    start = time.perf_counter(); report = base.load(out / 'report.json'); p = bound(report['protocol']); parent = bound(p['parent'])
    for f, h in p['source_fingerprints'].items(): assert base.sha(f) == h, f
    prior = base.load(study.PARENT / 'validation.json'); manifests = dict(prior['parent_manifests'])
    mp = str(study.PARENT / 'manifest.json'); manifests[mp] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, row in manifests.items():
        assert base.sha(path) == row['sha256']; entries = base.load(path)['artifacts']; assert len(entries) == row['artifacts_checked']
        for f, h in entries.items(): assert base.sha(f) == h, f
        artifacts += len(entries)
    assert (len(prior['source_fingerprints']), artifacts, len(manifests)) == (475, 5115, 88)
    base.write(out / 'parent-manifests.json', manifests)
    all_decisions = []; audits = []; frontiers = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = old.native.ResidualSolver(path)
            try: return old.native.rows(s)
            finally: s.close()
        union = read(parent['reference_union'], 'union'); assert len(union) == 21801
        hp = bound(p['historical_protocol']); ht = bound(p['historical_trial']); ft = bound(p['fresh_trial']); fp = bound(p['prior_protocol'])
        fi = read(bound(hp['parent'])['reference_union'], 'historical-initial'); ff = read(ht['archive'], 'historical-final')
        ni = read(bound(fp['parent'])['reference_union'], 'fresh-initial'); nf = read(ft['archive'], 'fresh-final')
        contexts = {}
        # Derive a prefix backwards from the final snapshot, removing the
        # selected query and all later insertions, then add only its preparation.
        for cohort, initial, final, rows, wanted in (
            ('historical', fi, ff, bound(ht['queries']), p['historical_cases']),
            ('fresh-baseline', ni, nf, bound(ft['queries']), p['fresh_cases'])):
            hashes = {base.key_sha(k): k for k in final}; assert len(hashes) == len(final)
            for i, row in enumerate(rows):
                if row['case'] not in wanted: continue
                excluded = {h for later in rows[i:] for h in later['new_ids']}
                prep = [] if cohort == 'historical' else row['ordinary_ids'] + row['near_ids']
                excluded -= set(prep); before = {k: v for k, v in final.items() if base.key_sha(k) not in excluded}
                assert initial.items() <= before.items()
                contexts[cohort, row['case']] = (before, row, prep)
        expected_order = [(cohort, cid, mode) for cohort, cases in (('historical', p['historical_cases']), ('fresh-baseline', p['fresh_cases'])) for cid in cases for mode in study.MODES]
        samples = [bound(e) for e in report['samples']]
        # Driver visits chronological stream order; protocol case order is a set.
        assert {(r['cohort'], r['case'], r['mode']) for r in samples} == set(expected_order) and len(samples) == 18
        baseline_controls = [bound(e) for e in bound(p['historical_controls'])['samples']]
        for r in samples:
            before, prior_row, prep = contexts[r['cohort'], r['case']]
            assert r['preparation_ids'] == prep and r['prefix_nodes'] == len(before)
            assert r['prefix_digest'] == base.key_sha(base.encode(sorted(before.items())))
            assert r['input_guards'] == prior_row['record']['guards']
            delta = bound(r['delta']); assert len(dict(delta)) == len(delta) == r['new_nodes']
            assert all(k not in before and union[k] == v for k, v in delta)
            assert r['new_payload_units'] == sum(len(k) + len(v) for k, v in delta)
            assert bound(r['records']) == [r['record']]
            path = tmp / 'arm'; path.unlink(missing_ok=True); s = old.native.ResidualSolver(path)
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', {**before, **dict(delta)}.items())
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Replay search')), patch.object(s, '_store', side_effect=AssertionError('Replay publication')):
                    source = prior_row['record']['source']; target = source; guards = list(r['input_guards'])
                    for g in guards: assert g['stronger_root'] in before; _, target = check_guard(s, target, g)
                    assert [list(c) for c in target] == r['input_target']
                    if r['mode'] == 'admitted':
                        choice, trace = expected(s, target, p['variable_limit'], before)
                        assert trace == r['admission'] and trace['discovery'] == r['local_probe']
                    elif r['mode'] == 'local':
                        choice, trace = expected_local(s, target, p['variable_limit']); assert trace == r['local_probe'] and r['admission'] is None
                    else:
                        choice = None; assert r['local_probe'] is None and r['admission'] is None
                    assert choice == r['local_choice']
                    if choice and choice['kind'] == 'guard':
                        g = r['record']['guards'][-1]
                        assert g['stronger'] == [list(c) for c in target] + [choice['clause']]
                        assert g['removed_clause'] == choice['clause'] and g['stronger_root'] == choice['screen']['root'] == r['premise']['root']
                        assert r['premise']['answer'] is False; _, target = check_guard(s, target, g); guards.append(g)
                        if r['mode'] == 'admitted': assert r['child']['metrics'].get('expanded_nodes', 0) == 0
                    else: assert r['premise'] is None
                    assert guards == r['record']['guards'] and r['child']['root'] == s._canonical(target)[2]
                    got = check_composed(s, r['record']); assert got['answer'] == prior_row['record']['answer']
            finally: s.close()
            assert r['summary'] == old.summarize([r])
            assert r['new_nodes'] == sum(c['metrics'].get('inserted_nodes', 0) for c in (r['premise'], r['child']) if c is not None)
            if r['cohort'] == 'historical' and r['mode'] in ('baseline', 'local'):
                control = next(x for x in baseline_controls if x['case'] == r['case'] and x['mode'] == r['mode'])
                assert dict(delta) == dict(bound(control['delta'])) and r['record'] == control['record']
            if r['cohort'] == 'fresh-baseline' and r['mode'] == 'baseline':
                engine_ids = set(prior_row['new_ids']) - set(prep)
                assert {base.key_sha(k) for k, _ in delta} == engine_ids and r['record'] == prior_row['record']
            all_decisions.append(r['record']); audits.append(dict(cohort=r['cohort'], case=r['case'], mode=r['mode'], passed=True))
        # Every acquired native payload already exists in the preserved union.
        # Reuse its archive byte-for-byte and retain only the new composed records.
        path = tmp / 'union'; s = old.native.ResidualSolver(path); rebuilt = []; direct = []
        ordinary = sum((bound(parent[f]) for f in old.FIELDS), [])
        previous = old.inherited(parent) + bound(parent['local_guard_decisions'])
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s, '_expand', side_effect=AssertionError('Union search')), patch.object(s, '_store', side_effect=AssertionError('Union publication')):
                for r in all_decisions:
                    target = r['source']
                    for g in r['guards']: _, target = check_guard(s, target, g)
                    rebuilt.append(make_record(s, r['source'], r['guards'], s.solve(target)))
                for r in previous + rebuilt: check_composed(s, r)
                for pr in bound(parent['conditioned_core_projections']): old.native.check_projection(s, pr)
                original = base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions']) + bound(parent['model_rotation_decisions']):
                    source = d['source'] if 'source' in d else original[d['case']]['source']; child = s.solve(source)
                    assert child['root'] == d['root'] and child['answer'] == d['answer']
                    assert child['model'] == (None if d['model'] is None else {int(k): v for k, v in d['model'].items()})
                    direct.append(dict(source=source, guard=None, witness=None, child=child, answer=child['answer'], model=child['model']))
                for name in ('active_support_proposals', 'extended_support_proposals', 'causal_support_proposals', 'incremental_causal_proposals'):
                    bank = bound(parent[name]); names = {o['catalog'] for o in bank['origins']}; catalogs = [(f, bound(parent[f])) for f in old.FIELDS if f in names]
                    assert {n for n, _ in catalogs} == names; lineage = check_proposals(s, bank, catalogs); ready = 0
                    for core in bank['cores']:
                        cnf, _, key = s._canonical(core['source']); node = s._read(key, cnf)
                        if node is not None: assert node['answer'] is False; ready += 1
                    frontiers[name] = dict(binding=parent[name], catalogs=len(catalogs), lineage=lineage, retained=len(bank['cores']), ready=ready, pending=len(bank['cores']) - ready)
            assert old.native.rows(s) == union
        finally: s.close()
        inherited_audit = audit(path, direct + ordinary)
        base.write(out / 'decisions.json', rebuilt); checkpoint = copy.deepcopy(parent)
        checkpoint.update(parent_checkpoint=p['parent'], source_fingerprints=p['source_fingerprints'],
                          child_admission_study=old.binding(out / 'report.json'), child_admission_decisions=old.binding(out / 'decisions.json'))
        base.write(out / 'checkpoint.json', checkpoint)
        _, structural = restore_checkpoint(out / 'checkpoint.json', tmp / 'patterns')
        assert structural == base.load(study.PARENT / 'reconstruction.json')['structural']
        supplemental = check_supplement(out / 'checkpoint.json')
    result = dict(passed=True, protocol=report['protocol'], report=old.binding(out / 'report.json'), checkpoint=old.binding(out / 'checkpoint.json'),
        audits=audits, preserved_keys=21801, union_keys=21801, new_keys=0, native_archive_unchanged=parent['reference_union'],
        inherited_decisions=len(direct) + len(ordinary), inherited_composed=len(previous), new_composed=len(rebuilt),
        projection_records=len(bound(parent['conditioned_core_projections'])), inherited_audit=inherited_audit,
        structural=structural, supplemental=supplemental, union_frontiers=frontiers,
        preservation=dict(prior_sources_unchanged=475, prior_artifacts_unchanged=artifacts, prior_manifests_unchanged=len(manifests)),
        seconds=time.perf_counter() - start)
    base.write(out / 'reconstruction.json', result)
    print(base.encode({k: result[k] for k in ('passed', 'preserved_keys', 'new_keys', 'inherited_decisions', 'inherited_composed', 'new_composed', 'seconds')}), flush=True)


if __name__ == '__main__': validate(Path(sys.argv[1]))
