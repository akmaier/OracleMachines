#!/usr/bin/env python3
"""Reconstruct bounded probes independently and replay every retained proof."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy, shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_assumption_guard as study
from experiments.cnf_residual_dag import propagate, restrict
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_guard_chain import check_record, GuardChainBank
from experiments.validate_cnf_partition_screen import check_composed
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_unsat_support import bound
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base = study.base


def expected(s, target, candidates, limit):
    def screen(source):
        cnf, _, key = s._canonical(source)
        fixed, trace, conflict = propagate(cnf, Counter())
        residual = () if conflict is not None else restrict(cnf, fixed)
        return dict(root=key, trace=trace, conflict=conflict, residual_literals=sum(map(len, residual)))
    trace = dict(baseline=None, attempts=[], selected=None)
    if not limit: return None, trace
    baseline = screen(target); trace['baseline'] = baseline
    if baseline['conflict'] is not None: return dict(kind='terminal', screen=baseline), trace
    members = {tuple(sorted(set(c))) for c in target}; variables = {abs(l) for c in target for l in c}; seen = set()
    for raw in candidates[:limit]:
        assert all(type(l) is int and l for l in raw)
        clause = tuple(sorted(set(raw))); assert not any(-l in clause for l in clause)
        reason = ('empty' if not clause else 'contained' if clause in members else
                  'outside' if not {abs(l) for l in clause} <= variables else 'duplicate' if clause in seen else None)
        seen.add(clause); entry = dict(clause=list(clause), skipped=reason, screen=None); trace['attempts'].append(entry)
        if reason: continue
        entry['screen'] = screen([list(c) for c in target] + [list(clause)])
        if entry['screen']['conflict'] is not None:
            trace['selected'] = len(trace['attempts']) - 1
            return dict(kind='guard', clause=list(clause), screen=entry['screen']), trace
    return None, trace


def validate(out):
    started = time.perf_counter(); report = base.load(out / 'report.json'); p = bound(report['protocol']); parent = bound(p['parent'])
    for f, h in p['source_fingerprints'].items(): assert base.sha(f) == h, f
    hp = bound(p['historical_protocol']); authority = bound(hp['parent']); trial = bound(p['historical_trial']); records = bound(trial['queries'])
    prior = [bound(e) for e in bound(p['prior_study'])['samples']]
    diagnosis = bound(p['diagnosis']); samples = [bound(e) for e in report['samples']]
    assert [(r['case'], r['mode']) for r in samples] == [(t['case'], m) for t in p['targets'] for m in p['modes']]
    bindings = dict(legacy=hp['support_index'], causal=hp['causal_index']); indices = {n: bound(e) for n, e in bindings.items()}
    prepared = study.previous.history.previous.ordinary.compose(indices, bindings)
    catalogs = [(n, bound(authority[n])) for n in study.OLD_FIELDS]
    decisions = []; audits = []; alternates = []; pairs = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = study.previous.ResidualSolver(path)
            try: return study.previous.rows(s)
            finally: s.close()
        initial = read(authority['reference_union'], 'initial'); final = read(trial['archive'], 'final')
        preserved = read(parent['reference_union'], 'union'); union = dict(preserved)
        prefixes = study.previous.history.partition_study.prefixes(initial, final, records)
        for selection in p['targets']:
            cid = selection['case']; old = next(r for r in records if r['case'] == cid); before = prefixes[cid]; paired = {}
            diagnosed = next(r for r in diagnosis['cases'] if r['case'] == cid)
            assert selection['missing'] == [r['assumption'] for r in diagnosed['single_assumptions']]
            for data in (r for r in samples if r['case'] == cid):
                mode = data['mode']; delta = bound(data['delta']); rs = bound(data['records']); assert len(rs) == 1; r = rs[0]
                assert data['prefix_nodes'] == len(before) and data['prefix_digest'] == base.key_sha(base.encode(sorted(before.items()))) == diagnosed['prefix_digest']
                assert data['candidates'] == selection['missing']
                saved = dict(before)
                for k, v in delta: assert k not in saved; saved[k] = v
                assert r['source'] == old['record']['source'] and r['answer'] == old['record']['answer']
                acquired = [c for c in (data['child'], data['premise']) if c is not None]
                assert data['new_nodes'] == len(delta) == sum(c['metrics'].get('inserted_nodes', 0) for c in acquired)
                assert data['new_payload_units'] == sum(len(k) + len(v) for k, v in delta)
                assert data['expanded_nodes'] == sum(c['metrics'].get('expanded_nodes', 0) for c in acquired)
                assert data['retained_bytes'] == sum(Path(data[f]['path']).stat().st_size for f in ('delta', 'records'))
                path = tmp / 'arm'; shutil.copyfile(tmp / 'initial', path); s = study.previous.ResidualSolver(path)
                try:
                    with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in saved.items() if k not in initial])
                    s.db.execute('PRAGMA query_only=ON')
                    with patch.object(s, '_expand', side_effect=AssertionError('Validation search')), patch.object(s, '_store', side_effect=AssertionError('Validation publication')):
                        guards = old['record']['guards']; assert r['guards'][:len(guards)] == guards
                        target = r['source']
                        for g in guards: assert g['stronger_root'] in before; _, target = check_guard(s, target, g)
                        choice, trace = (None, None) if mode == 'baseline' else expected(s, target, selection['missing'], p['limit'])
                        assert (choice, trace) == (data['choice'], data['probe'])
                        if choice is not None and choice['kind'] == 'guard':
                            assert len(r['guards']) == len(guards) + 1
                            g = r['guards'][-1]; assert g['removed_clause'] == choice['clause']
                            assert g['stronger'] == [list(c) for c in target] + [choice['clause']]
                            assert g['stronger_root'] == choice['screen']['root'] == data['premise']['root']
                            assert data['premise']['answer'] is False
                            _, target = check_guard(s, target, g)
                        else:
                            assert r['guards'] == guards and data['premise'] is None
                        assert all(r['child'][k] == data['child'][k] for k in ('root', 'answer', 'model'))
                        check_record(s, r); assert GuardChainBank(s, [r]).lookup(r['source']) == check_record(s, r)
                        if mode == 'baseline':
                            old_baseline = next(x for x in prior if x['case'] == cid and x['mode'] == 'baseline')
                            assert r == bound(old_baseline['records'])[0] and dict(delta) == dict(bound(old_baseline['delta']))
                finally: s.close()
                cold = study.previous.audit_records(path, [r], [], prepared, catalogs, indices)
                assert cold['composed']['native']['lineage'] == data['cold']['composed']['native']['lineage']
                audits.append(dict(case=cid, mode=mode, cold=cold)); decisions.append(r); paired[mode] = (data, delta, r)
                for k, v in delta:
                    if k in union and union[k] != v:
                        assert base.load_json(union[k])['answer'] == base.load_json(v)['answer']
                        alternates.append(dict(root_sha256=base.key_sha(k), delta=data['delta']))
                    union.setdefault(k, v)
            a, da, ra = paired['native-guard']; b, db, rb = paired['trace-guard']
            assert a['choice'] == b['choice'] and a['probe'] == b['probe'] and a['probe_counts'] == b['probe_counts']
            pairs.append(dict(case=cid, same_selection=True, same_records=ra == rb, same_native_payloads=dict(da) == dict(db),
                              same_child_metrics=a['child']['metrics'] == b['child']['metrics']))
        path = tmp / 'union'; s = study.previous.ResidualSolver(path); direct = []
        try:
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in union.items() if k not in preserved])
            assert study.previous.rows(s) == union; s.db.execute('PRAGMA query_only=ON')
            with patch.object(s, '_expand', side_effect=AssertionError('Union search')), patch.object(s, '_store', side_effect=AssertionError('Union publication')):
                for r in study.inherited(parent) + decisions: check_composed(s, r)
                for pr in bound(parent['conditioned_core_projections']): study.previous.check_projection(s, pr)
                original = base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions']) + bound(parent['model_rotation_decisions']):
                    source = d['source'] if 'source' in d else original[d['case']]['source']; child = s.solve(source)
                    assert child['root'] == d['root'] and child['answer'] == d['answer']
                    assert child['model'] == (None if d['model'] is None else {int(k): v for k, v in d['model'].items()})
                    direct.append(dict(source=source, guard=None, witness=None, child=child, answer=child['answer'], model=child['model']))
        finally: s.close()
        ordinary = direct + sum((bound(parent[f]) for f in study.FIELDS), [])
        inherited_audit = audit(path, ordinary)
        composed_audit = study.previous.audit_records(path, study.inherited(parent) + decisions,
            bound(parent['conditioned_core_projections']), prepared, [(n, bound(parent[n])) for n in study.OLD_FIELDS], indices)
        if union == preserved: archive = parent['reference_union']
        else:
            dest = out / 'reference-union'; dest.mkdir(); archive = base.archive(path, dest)
        base.write(out / 'decisions.json', decisions); checkpoint = copy.deepcopy(parent)
        checkpoint.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=p['source_fingerprints'],
                          assumption_guard_study=study.binding(out / 'report.json'), assumption_guard_decisions=study.binding(out / 'decisions.json'))
        base.write(out / 'checkpoint.json', checkpoint)
        _, old_structural = restore_checkpoint(p['parent']['path'], tmp / 'old-patterns')
        _, structural = restore_checkpoint(out / 'checkpoint.json', tmp / 'patterns'); assert structural == old_structural
        supplemental = check_supplement(out / 'checkpoint.json')
    result = dict(passed=True, protocol=report['protocol'], report=study.binding(out / 'report.json'), checkpoint=study.binding(out / 'checkpoint.json'),
        audits=audits, pairs=pairs, alternate_certificates=alternates, preserved_keys=len(preserved), union_keys=len(union),
        new_keys=len(union) - len(preserved), archive_reused=union == preserved, inherited_decisions=len(ordinary),
        inherited_composed=len(study.inherited(parent)), new_composed=len(decisions), projection_records=len(bound(parent['conditioned_core_projections'])),
        inherited_audit=inherited_audit, composed_audit=composed_audit, structural=structural, supplemental=supplemental, seconds=time.perf_counter() - started)
    base.write(out / 'reconstruction.json', result)
    print(base.encode({k: result[k] for k in ('passed', 'preserved_keys', 'union_keys', 'new_keys', 'archive_reused', 'inherited_decisions', 'inherited_composed', 'new_composed', 'seconds')}), flush=True)


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
