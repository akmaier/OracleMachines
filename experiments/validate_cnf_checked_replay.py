#!/usr/bin/env python3
"""Check matched replay artifacts, exact outputs, costs and frozen ancestry."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_canonical_source import sha, read_archive
from experiments.compare_cnf_checked_replay import STAGES, LATEST


def validate(out):
    r=json.loads((out/'report.json').read_text())
    assert Path(r['parent']['path'])==LATEST and sha(LATEST)==r['parent']['sha256']
    parent=json.loads(LATEST.read_text())
    for p,d in r['fingerprints'].items():assert sha(p)==d,p
    assert sha(r['base']['path'])==r['base']['sha256']
    assert r['seed_unchanged'] and r['legacy_audit']['covered']==sum(parent['final_closed'])==69
    assert all(r['legacy_audit'][k] for k in ('selection_matches','certificate_matches','no_discovery'))
    assert [(a['repeat'],a['mode']) for a in r['runs']]==[(0,'fresh'),(0,'retained'),(1,'retained'),(1,'fresh')]
    runs=[]
    for item in r['runs']:
        assert sha(item['path'])==item['sha256']
        arm=json.loads(Path(item['path']).read_text());assert arm['mode']==item['mode']
        assert arm['table_digests']==parent['logical_table_digests']
        assert arm['history_bytes']==parent['expanded_database_bytes']
        assert arm['global_query']['closed']==[parent['final_closed'],parent['without_growth_closed']]
        assert read_archive(arm['selection'])==read_archive(parent['next_selection'])
        assert read_archive(arm['certificate'])==read_archive(parent['certificate'])
        assert len(arm['stages'])==len(STAGES)
        for stage,(_,name) in zip(arm['stages'],STAGES,strict=True):
            bound=stage['report'];p=Path('experiments/results')/name/'report.json'
            assert Path(bound['path'])==p and sha(p)==bound['sha256']
            prior=json.loads(p.read_text())
            expected_rows=sum(prior['delta']['added'].values()) if 'added' in prior['delta'] else None
            # Every supported delta row is visited; append count is not used as
            # a substitute for certificate-check count when rows overlap.
            assert stage['delta_check']['checked_delta_rows']>=stage['delta_check']['appended_rows']>=0
            if expected_rows is not None:assert stage['delta_check']['checked_delta_rows']==expected_rows
        assert arm['sequence_seconds']>=arm['suffix_seconds']+arm['startup_seconds']
        runs.append((item,arm))
    for repeat in range(2):
        group={i['mode']:a for i,a in runs if i['repeat']==repeat}
        for a,b in zip(group['fresh']['stages'],group['retained']['stages'],strict=True):
            assert a['delta_check']==b['delta_check'] and a['positive_check']==b['positive_check']
        assert group['fresh']['handoff_checked_nodes']==0
        assert group['retained']['handoff_checked_nodes']>0
        assert group['retained']['inventory_counts']['verified_pattern_nodes']==group['retained']['final_checked_nodes']
    metrics=('suffix_seconds','startup_seconds','sequence_seconds','session_construction_seconds',
             'handoff_checked_nodes','final_checked_nodes','peak_checked_nodes','history_bytes')
    means={mode:{k:sum(a[k] for i,a in runs if i['mode']==mode)/2 for k in metrics} for mode in ('fresh','retained')}
    for mode in means:
        means[mode]['verified_pattern_nodes']=sum(a['inventory_counts']['verified_pattern_nodes'] for i,a in runs if i['mode']==mode)/2
    summary=dict(report_sha256=sha(out/'report.json'),passed=True,covered=69,new_patterns=0,
        means=means,savings_percent={k:100*(means['fresh'][k]-means['retained'][k])/means['fresh'][k]
             for k in ('suffix_seconds','startup_seconds','sequence_seconds','verified_pattern_nodes')},
        sequence_samples={mode:[a['sequence_seconds'] for i,a in runs if i['mode']==mode] for mode in means},
        independent_legacy_audit=r['legacy_audit'],common_restore_seconds=r['common_restore_seconds'],
        pipeline_seconds=r['seconds'],validator_sha256=sha(__file__))
    (out/'comparison-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':validate(Path(sys.argv[1]))
