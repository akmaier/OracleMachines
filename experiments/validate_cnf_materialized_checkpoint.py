#!/usr/bin/env python3
"""Audit matched snapshot/replay outputs and derive charged amortization costs."""
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_materialized_checkpoint import PARENT, PARENT_SHA, FORMAT
from experiments.cnf_materialized_checkpoint import sha
from experiments.continue_cnf_retained_discovery import read_archive


def validate(out):
    r = json.loads((out/'report.json').read_text())
    assert r['format'] == FORMAT and r['parent'] == dict(path=str(PARENT),sha256=PARENT_SHA)
    assert sha(PARENT) == PARENT_SHA
    parent = json.loads(PARENT.read_text())
    for p,d in r['fingerprints'].items(): assert sha(p)==d, p
    for p,d in parent['fingerprints'].items(): assert sha(p)==d, p
    assert sha(r['descriptor']['path']) == r['descriptor']['sha256']
    descriptor = json.loads(Path(r['descriptor']['path']).read_text())
    assert descriptor['parent'] == r['parent'] and descriptor['options'] == parent['options']
    assert descriptor['table_digests'] == parent['logical_table_digests']
    assert r['evidence_counts'] == parent['evidence_counts_after'] and r['bridges'] == len(read_archive(parent['bridges']))
    assert r['seed_unchanged']
    assert [(a['repeat'],a['mode']) for a in r['runs']] == [(0,'legacy'),(0,'materialized'),(1,'materialized'),(1,'legacy')]
    arms = []
    for bound in r['runs']:
        assert sha(bound['path'])==bound['sha256']; a=json.loads(Path(bound['path']).read_text())
        assert (a['repeat'],a['mode'])==(bound['repeat'],bound['mode'])
        assert a['table_digests']==parent['logical_table_digests']
        assert a['database_sha256']==descriptor['database']['raw_sha256']
        assert a['database_bytes']==descriptor['database']['bytes']==parent['expanded_database_bytes']
        assert a['evidence_sha256']==r['evidence_sha256']
        assert a['no_discovery'] and a['covered']==sum(parent['final_closed'])==72
        assert a['sequence_seconds']>=a['restore_seconds']+a['startup_seconds']
        if a['mode']=='materialized':
            assert a['restore_metrics']['mode']=='materialized' and a['restore_metrics']['positive_checks']
        item=a['startup_report'];assert sha(item['path'])==item['sha256']
        startup=json.loads(Path(item['path']).read_text())
        assert startup['closed']==[parent['final_closed'],parent['without_growth_closed']]
        assert read_archive(startup['selection'])==read_archive(parent['next_selection'])
        assert read_archive(startup['certificate'])==read_archive(parent['certificate'])
        arms.append(a)
    metrics=('restore_seconds','startup_seconds','sequence_seconds','identity_audit_seconds')
    means={mode:{k:sum(a[k] for a in arms if a['mode']==mode)/2 for k in metrics} for mode in ('legacy','materialized')}
    savings=means['legacy']['sequence_seconds']-means['materialized']['sequence_seconds']
    build=r['materialization']['seconds']; from_scratch=build+r['preparation_restore_seconds']
    summary=dict(passed=True,report_sha256=sha(out/'report.json'),validator_sha256=sha(__file__),
        covered=72,originals=83,new_patterns=0,means=means,
        savings_percent={k:100*(means['legacy'][k]-means['materialized'][k])/means['legacy'][k]
                         for k in ('restore_seconds','startup_seconds','sequence_seconds')},
        sequence_samples={mode:[a['sequence_seconds'] for a in arms if a['mode']==mode] for mode in means},
        materialization_seconds=build,preparation_restore_seconds=r['preparation_restore_seconds'],
        cache_bytes=r['materialization']['cached_bytes'],database_bytes=descriptor['database']['bytes'],
        database_compressed_bytes=descriptor['database']['compressed_bytes'],
        evidence_bytes=descriptor['evidence']['bytes'],evidence_compressed_bytes=descriptor['evidence']['compressed_bytes'],
        retained_checked_nodes=[a['retained_checked_nodes'] for a in arms],
        future_reloads_to_repay_build_from_already_checked_history=math.ceil(build/savings) if savings>0 else None,
        future_reloads_to_repay_extra_reconstruction_and_build=math.ceil(from_scratch/savings) if savings>0 else None,
        pipeline_seconds=r['seconds'],limitations='Amortization divides separately measured one-time costs by the observed mean complete-sequence saving; it is conditional on this workload and excludes cache eviction and peak RAM. Four full global queries preserve complete frontier checking. No new SAT coverage or general acquisition bound.')
    (out/'comparison-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__': validate(Path(sys.argv[1]))
