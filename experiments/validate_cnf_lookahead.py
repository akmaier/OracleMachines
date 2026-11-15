#!/usr/bin/env python3
"""Cold bank replay and diagnosis of missing source-pair availability."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.compare_cnf_lookahead as study


def validate(out):
    report=study.load(out/'report.json');protocol=study.load(out/'protocol.json');seed=study.load(out/'seed.json')
    assert study.sha(out/'protocol.json')==report['protocol_sha256'] and study.sha(out/'seed.json')==report['seed_sha256']
    for p,digest in protocol['source_fingerprints'].items():assert study.sha(p)==digest
    known=set()
    for p,digest in protocol['novelty_parents'].items():
        assert study.sha(p)==digest
        old=study.load(p)
        known.update(study.source_id(c['source']) for c in old['cases'])
    assert protocol['cases']==study.corpus()
    assert all(study.source_id(c['source']) not in known for c in protocol['cases'])
    samples=[];saved_reports={};missing=[];eligible=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'seed';study.restore_archive(seed['archive'],path);before=study.sha(path)
        h=study.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            h.db.execute('PRAGMA query_only=ON')
            with study.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')):
                initial=study.rows(h)
                for key in initial:assert study.owner(h,key)._load(key) is not None
                for case,row in zip(protocol['cases'],seed['records'],strict=True):
                    assert row['root'] is not None
                    assert h._canonical(case['source'],0)[2]==row['root']
                    assert h._load(row['root'])['summary']['closed']==row['closed']
                    node=h._load(row['leaf']) if row['leaf'] else None
                    if row['ranked']:eligible.append(row['case'])
                    elif node is not None:
                        assert node['kind']=='unresolved'
                        shape=node['profile']['shape'];binary=sum(len(c)==2 for c in node['cnf'])
                        attempts=len(node['profile']['probing']['attempts'])
                        missing.append(dict(case=row['case'],group=case['group'],shape=shape,
                            binary_clauses=binary,saved_attempts=attempts,probe_status=node['profile']['probing']['status']))
                assert all(x['binary_clauses']==x['saved_attempts']==0 for x in missing)
        finally:h.close();assert study.sha(path)==before
        for i,sample in enumerate(report['samples']):
            assert study.sha(sample['path'])==sample['sha256']
            data=study.load(sample['path']);path=tmp/f'sample-{i}';study.restore_archive(data['archive'],path)
            replay=study.replay(path,protocol,seed,data['records'],data['evidence'])
            h=study.LookaheadInventory(path,**protocol['options'])
            try:
                after=study.rows(h);assert initial.items()<=after.items()
                bank=list(h.db.execute(f'SELECT id,payload FROM {study.TABLE}'))
                for row in data['records']:
                    assert row['entered']<=40 and row['entered']==len(set(row['admitted_ids']))
                    assert not row['admission_counts'].get('denied_states',0)
                logical=sum(len(k.encode())+len(v.encode()) for k,v in bank)
            finally:h.close()
            samples.append(dict(mode=sample['mode'],repeat=sample['repeat'],bank_logical_bytes=logical,**replay))
            saved_reports[(sample['mode'],sample['repeat'])]=data
        for repeat in range(2):
            a=saved_reports[('lookahead_reuse',repeat)];b=saved_reports[('lookahead_recompute',repeat)];base=saved_reports[('size',repeat)]
            assert a['pattern_digest']==b['pattern_digest']==base['pattern_digest']
            assert [x['chosen'] for x in a['records']]==[x['chosen'] for x in b['records']]==[x['chosen'] for x in base['records']]
    reused=saved_reports[('lookahead_reuse',0)];recomputed=saved_reports[('lookahead_recompute',0)];base=saved_reports[('size',0)]
    result=dict(passed=True,report_sha256=study.sha(out/'report.json'),validator_sha256=study.sha(__file__),
        seed_patterns=len(initial),seed_cold_checked=True,archives=samples,original_queries=24,
        eligible_cases=eligible,missing_candidates=missing,
        reused_probe_attempts=recomputed['probes']-reused['probes'],
        extra_probe_attempts_over_size=reused['probes']-base['probes'],
        same_selected_pairs_and_pattern_graph=True,
        interpretation='The bank avoids repeated acquisition but this score changes no choice and adds no coverage. At depth-zero preparation, 22 inputs lack saved pairs because their selected residuals have no binary clauses. This is a restricted expansion prerequisite, not a failure of ordinary conditioning or a SAT/UNSAT result.',
        next_target='Use charged ordinary conditioning or explicit broadly ranked source-pair acquisition to expose binary interactions before testing selection; distinguish this from reusing already prepared pairs.')
    study.write(out/'reconstruction.json',result)
    print(study.json.dumps(dict(passed=True,archives=len(samples),eligible=eligible,missing_pairs=len(missing),
        bank_saved_probes=result['reused_probe_attempts'],extra_probes_over_size=result['extra_probe_attempts_over_size'],
        bank_logical_bytes=[r['bank_logical_bytes'] for r in samples if r['mode']=='lookahead_reuse'])))


if __name__=='__main__':validate(Path(sys.argv[1]))
