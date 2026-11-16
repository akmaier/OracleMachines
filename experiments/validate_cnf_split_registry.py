#!/usr/bin/env python3
"""Independent cold replay; the live registry never replaces proof validation."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_split_registry as study
from experiments.cnf_incremental_coverage import catalog
from experiments.validate_cnf_bootstrap import restore_checkpoint
base = study.base


def validate(out):
    report = base.load(out/'report.json');protocol = base.load(out/'protocol.json')
    assert report['protocol_sha256'] == base.sha(out/'protocol.json')
    for name in ('parent','seed','expected','checkpoint'):
        entry = protocol[name];assert base.sha(entry['path']) == entry['sha256']
    for p, digest in protocol['source_fingerprints'].items():assert base.sha(p) == digest, p
    assert protocol['cases'] == base.load(protocol['parent']['path'])['cases']
    expected = base.load(protocol['expected']['path']);evidence = expected['evidence']
    samples = list(report['samples'])
    diagnostic_path = out/'diagnostic/report.json'
    if diagnostic_path.exists():
        diagnostic = base.load(diagnostic_path)
        assert diagnostic['parent_report_sha256'] == base.sha(out/'report.json')
        samples.append(dict(mode='diagnostic',path=str(out/'diagnostic/incremental/report.json'),
                            sha256=diagnostic['sample_sha256']))
    checks = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i, sample in enumerate(samples):
            assert base.sha(sample['path']) == sample['sha256'];data = base.load(sample['path'])
            assert data['evidence_binding'] == protocol['expected']
            for row, old in zip(data['records'], expected['records'], strict=True):
                assert all(row[k] == old[k] for k in study.QUERY_FIELDS)
                assert row['entered'] <= 40
            path = tmp/f'cold-{i}';base.restore_archive(data['archive'],path);before = base.sha(path)
            assert before == expected['archive']['database_sha256']
            cold = base.replay(path,protocol,data['records'],evidence)
            assert cold['proof'] == expected['cold']['proof']
            assert base.key_sha(base.encode(cold['proof'])) == data['cold_proof_sha256']
            h = base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
            try:
                with (base.no_acquisition(), patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
                      patch.object(base.split,'discover_simplification',side_effect=AssertionError('new assumption'))):
                    registry = study.SplitRegistry(h)
                    reference = base.routes_for(h,evidence)
                    assert catalog(registry) == catalog(reference)
                    stats = registry.statistics();assert stats['records'] == len(evidence) == 86
                    assert registry.counts['registry_verified_records'] == 86
                    with patch.object(base.split,'verify',side_effect=AssertionError('old evidence rechecked')):
                        for _ in range(16):registry.refresh()
                    assert catalog(registry) == catalog(reference)
                    outcomes = [base.compose(h,[r['root']],registry,Counter())[0][0] for r in data['records']]
                    assert outcomes == cold['final_closed']
            finally:h.close();assert base.sha(path) == before
            checks.append(dict(mode=sample['mode'],patterns=cold['patterns'],pairs=cold['pairs'],
                original_bindings=cold['queries'],covered=sum(cold['final_closed']),
                cold_registry_checks=86,warm_refreshes_without_rechecking=16,
                pending_dependencies=stats['pending_dependencies'],no_acquisition=True,
                seconds=cold['seconds']))
        seed = base.load(protocol['seed']['path']);path = tmp/'seed';base.restore_archive(seed['archive'],path)
        h = base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
        try:
            with base.no_acquisition(), patch.object(h,'_admit',side_effect=AssertionError('acquisition')):
                for key in base.rows(h):assert base.owner(h,key)._load(key) is not None
                for case,row in zip(protocol['cases'],seed['records'],strict=True):
                    assert h._canonical(case['source'],0)[2] == row['root']
        finally:h.close();assert base.sha(path) == seed['archive']['database_sha256']
        _, parent_check = restore_checkpoint(protocol['checkpoint']['path'],tmp/'parent-union')
        next_checked = False
        if (out/'next-discovery.json').exists():
            target = base.load(out/'next-discovery.json');case = target['case']
            assert target['checkpoint'] == protocol['checkpoint']
            assert target['original_source'] == protocol['cases'][case]['source']
            assert target['source'] == seed['records'][case]['leaf']
            assert target['source_sha256'] == base.key_sha(target['source'])
            h = base.CompleteAdmissionInventory(tmp/'parent-union',**base.OPTIONS);h.set_admission_budget(0)
            try:
                with base.no_acquisition(), patch.object(h,'_admit',side_effect=AssertionError('acquisition')):
                    assert h._load(target['source'])['profile']['shape'] == target['shape']
                    evidence = [base.load_json(row[0]) for row in h.db.execute(f'SELECT payload FROM {base.split.TABLE} ORDER BY rowid')]
                    routes = base.routes_for(h,evidence)
                    pairs = [r for r in evidence if r['source'] == target['source']]
                    assert len(pairs) == len(target['prior_pairs']) == 4
                    for record, saved in zip(pairs,target['prior_pairs'],strict=True):
                        assert record['variable'] == saved['variable']
                        for value, branch, saved_branch in zip((False,True),record['branches'],saved['branches'],strict=True):
                            key = branch['edge']['key'];node = h._load(key)
                            assert saved_branch == dict(value=value,child=key,key_sha256=base.key_sha(key),
                                present=node is not None,closed=node is not None and base.compose(h,[key],routes,Counter())[0][0],
                                shape=node['profile']['shape'] if node else None,kind=node['kind'] if node else None)
                    next_checked = True
            finally:h.close()
    result = dict(passed=True,report_sha256=base.sha(out/'report.json'),validator_sha256=base.sha(__file__),
        archives=checks,seed_checked=True,unchanged_parent_checkpoint=parent_check,next_discovery_checked=next_checked,
        notes=['All archive bytes, source pair payloads, graphs, selected choices, pending flags and positive proofs match the frozen enumeration baseline.',
               'Every cold registry rechecks all 86 pairs; sixteen subsequent unchanged refreshes perform zero split rechecks.',
               'Full no-acquisition positive replay is unchanged and performed separately from registry reconstruction.'])
    base.write(out/'reconstruction.json',result)
    print(base.encode(dict(passed=True,archives=len(checks)+2,original_query_bindings=sum(c['original_bindings'] for c in checks),
        parent_patterns=parent_check['patterns'],parent_pairs=parent_check['pairs'],parent_covered=parent_check['covered'])))


if __name__ == '__main__':validate(Path(sys.argv[1]))
