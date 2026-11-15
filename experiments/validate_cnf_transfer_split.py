#!/usr/bin/env python3
"""Audit all alternatives and preserve their union with a source-bound proof."""
from collections import Counter,defaultdict
import gzip
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.continue_cnf_transfer_split as study
from experiments.cnf_expanded_coverage import expand,owner
from experiments.cnf_early_subsumption import check_family
from experiments.cnf_projection_bridge import verify_positive
from experiments.cnf_route_composition import compose
from experiments.cnf_trace_split import attach,verify


def check_checkpoint(report,path):
    """Independently validate source bindings, all history, all alternatives and proof."""
    tick=time.perf_counter();before=study.sha(path)
    if report.get('format')!='transfer-split-union-v1':raise ValueError('Unknown checkpoint format')
    if before!=report['archive']['database_sha256']:raise ValueError('Changed checkpoint bytes')
    for key in ('queries','proof','splits','protocol'):
        entry=report[key]
        if study.sha(entry['path'])!=entry['sha256']:raise ValueError('Changed checkpoint evidence')
    queries=study.load(report['queries']['path']);proof=study.load(report['proof']['path']);splits=study.load(report['splits']['path'])
    cases=study.load(report['protocol']['path'])['cases']
    if len(queries)!=len(cases) or any(q['source']!=c['source'] for q,c in zip(queries,cases,strict=True)):
        raise ValueError('Query catalog does not match the original frozen stream')
    h=study.CompleteAdmissionInventory(path,**report['options']);h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with study.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')):
            for key in study.rows(h):assert owner(h,key)._load(key) is not None
            for record in splits:verify(h,record,Counter())
            roots=[];early=0
            for query in queries:
                source=query['source']
                assert study.source_id(source)==query['source_sha256']
                if query['certificate'] is not None:
                    check_family(source,query['certificate']);early+=1
                else:
                    assert h._canonical(source,h.config['max_depth'])[2]==query['root']
                    roots.append(query['root'])
            assert roots==report['roots']
            checked=verify_positive(h,proof,roots,[[],[],[],splits,[]],[],Counter())
            assert len(queries)==42 and early+len(roots)==42
            return dict(seconds=time.perf_counter()-tick,checked_patterns=len(study.rows(h)),
                query_bindings=len(queries),early_family_queries=early,positive_roots=len(roots),
                positive_steps=len(checked.justified),no_acquisition=True,coverage=42)
    finally:
        h.close();assert study.sha(path)==before


def restore_checkpoint(report_path,path):
    """Resume from the union: all failed alternatives and split evidence survive."""
    report=study.load(report_path)
    for p,digest in report['source_fingerprints'].items():
        if study.sha(p)!=digest:raise ValueError('Changed checkpoint implementation')
    for key in ('initial_report','pair_report'):
        entry=report[key]
        if study.sha(entry['path'])!=entry['sha256']:raise ValueError('Changed checkpoint provenance')
    study.restore_archive(report['archive'],path)
    checked=check_checkpoint(report,path)
    return report,study.load(report['splits']['path']),checked


def run(out):
    began=time.perf_counter();report=study.load(out/'report.json');frozen=study.load(out/'frozen.json')
    selection=study.load(out/'selection.json');control=study.load(out/'pair-control/report.json');cf=study.load(out/'pair-control/frozen.json')
    assert study.sha(out/'frozen.json')==report['frozen_sha256']
    assert study.sha(out/'selection.json')==report['selection_sha256']
    assert study.sha(out/'pair-control/frozen.json')==control['frozen_sha256']
    sources={**frozen['source_fingerprints'],**cf['source_fingerprints']}
    sources['experiments/validate_cnf_transfer_split.py']=study.sha(__file__)
    # The matched micro-control imports this unchanged, previously tracked helper.
    # Bind it explicitly in the resumable checkpoint as well as the inference code.
    sources['experiments/compare_cnf_trace_split.py']=study.sha('experiments/compare_cnf_trace_split.py')
    for p,digest in sources.items():assert study.sha(p)==digest,p
    archived=[];pairs=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';study.restore_archive(frozen['parent_archive'],seed)
        h=study.CompleteAdmissionInventory(seed,**frozen['options']);initial=study.rows(h);h.close()
        all_rows=dict(initial)
        for sample in report['samples']:
            assert study.sha(sample['path'])==sample['sha256']
            data=study.load(sample['path'])
            for step in data['steps']:
                path=tmp/f"first-{sample['mode']}-{sample['repeat']}-{step['batch']}"
                study.restore_archive(step['archive'],path)
                replay=study.replay(path,frozen['options'],selection['record'],data['roots'],step['closed'])
                archived.append({k:v for k,v in replay.items() if k!='positive'})
                h=study.CompleteAdmissionInventory(path,**frozen['options']);saved=study.rows(h);h.close()
                for key,value in saved.items():
                    assert key not in all_rows or all_rows[key]==value
                    all_rows[key]=value
                if sample['mode']=='history':assert initial.items()<=saved.items()
        for sample in control['samples']:
            assert study.sha(sample['path'])==sample['sha256']
            data=study.load(sample['path']);path=tmp/f"pair-{sample['index']}-{sample['repeat']}"
            study.restore_archive(data['archive'],path)
            assert data['record']==selection['ranked'][sample['index']]['record']
            replay=study.replay(path,frozen['options'],data['record'],data['roots'],data['closed'])
            archived.append({k:v for k,v in replay.items() if k!='positive'})
            assert data['entered']<=32 and set(data['stored_ids'])<=set(data['admitted_ids'])
            h=study.CompleteAdmissionInventory(path,**frozen['options']);saved=study.rows(h);h.close()
            assert initial.items()<=saved.items()
            for key,value in saved.items():
                assert key not in all_rows or all_rows[key]==value
                all_rows[key]=value
            if sample['repeat']==0:pairs.append(data)
        path=tmp/'union';study.restore_archive(frozen['parent_archive'],path)
        h=study.CompleteAdmissionInventory(path,**frozen['options']);h.set_admission_budget(0)
        try:
            with h.db:
                h.db.executemany('INSERT INTO cnf_patterns_v1 VALUES (?,?)',[(k,v) for k,v in all_rows.items() if k not in initial])
            assert initial.items()<=study.rows(h).items() and len(study.rows(h))==len(all_rows)
            splits=[x['record'] for x in sorted(pairs,key=lambda r:r['index'])]
            routes=SimpleNamespace(by_source=defaultdict(list))
            for record in splits:assert attach(h,routes,record,Counter())
            protocol=study.load('experiments/results/cnf-subsumption-transfer/protocol.json')
            prior=study.load(study.PARENT/'complete4096-0/report.json')
            queries=[dict(source=c['source'],source_sha256=study.source_id(c['source']),certificate=q['certificate'],root=q['root'])
                     for c,q in zip(protocol['cases'],prior['records'],strict=True)]
            roots=[q['root'] for q in queries if q['certificate'] is None]
            closed,plan=compose(h,roots,routes,Counter());assert all(closed)
            proof=expand(h,plan,roots,routes,Counter())
            verify_positive(h,proof,roots,[[],[],[],splits,[]],[],Counter())
            diagnostics=dict(proof_steps=len(proof['steps']),
                proof_kinds=dict(Counter(h._load(s['source'])['kind'] for s in proof['steps'])),
                used_external_rules=[dict(source_sha256=study.key_sha(s['source']),kind=s['rule']['kind'])
                    for s in proof['steps'] if s['rule']['kind']=='trace_split'])
        finally:h.close()
        for name,data in [('queries',queries),('splits',splits),('proof',proof)]:study.write(out/f'{name}.json',data)
        entry=study.archive(path,out)
        checkpoint=dict(format='transfer-split-union-v1',options=frozen['options'],source_fingerprints=sources,
            initial_report=dict(path=str(out/'report.json'),sha256=study.sha(out/'report.json')),
            pair_report=dict(path=str(out/'pair-control/report.json'),sha256=study.sha(out/'pair-control/report.json')),
            protocol=dict(path='experiments/results/cnf-subsumption-transfer/protocol.json',
                sha256=study.sha('experiments/results/cnf-subsumption-transfer/protocol.json')),
            archive=entry,roots=roots,coverage=42,next_selection=None,initial_patterns=len(initial),
            added_patterns=len(all_rows)-len(initial),retained_alternatives=len(splits),
            **{name:dict(path=str(out/f'{name}.json'),sha256=study.sha(out/f'{name}.json')) for name in ('queries','splits','proof')})
        study.write(out/'checkpoint.json',checkpoint)
        # Exercise the public cold restoration interface, not just the live DB.
        _,restored,check=restore_checkpoint(out/'checkpoint.json',tmp/'cold-union');assert restored==splits
    result=dict(passed=True,initial_report_sha256=study.sha(out/'report.json'),pair_report_sha256=study.sha(out/'pair-control/report.json'),
        checkpoint_sha256=study.sha(out/'checkpoint.json'),validator_sha256=study.sha(__file__),archives=archived,
        union_check=check,initial_patterns=len(initial),new_patterns=len(all_rows)-len(initial),
        final_patterns=len(all_rows),retained_alternatives=len(splits),diagnostics=diagnostics,
        selection_failure='The initial smaller-cofactor ranking chose variable 6. Variable 14 is the only one of the four independently tested pairs closing both children at the common 32-state allowance.',
        seconds=time.perf_counter()-began)
    study.write(out/'reconstruction.json',result)
    print(study.json.dumps({k:v for k,v in result.items() if k in ('passed','union_check','initial_patterns','new_patterns','final_patterns','retained_alternatives','diagnostics')}))


if __name__=='__main__':run(Path(sys.argv[1]))
