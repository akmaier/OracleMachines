#!/usr/bin/env python3
"""Reuse frozen paired-cost analysis, adding native-probe retention evidence."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import analyze_cnf_transported_partition as old
from experiments import compare_cnf_probed_partition as study


def analyze(out):
    with patch.object(old,'study',study):old.analyze(out)
    a=study.base.load(out/'analysis.json');report=study.base.load(out/'report.json');probe={}
    for split in study.SPLITS:
        probe[split]={}
        for mode in study.MODES:
            counts=Counter();attempts=[]
            for sample in report['samples']:
                if (sample['split'],sample['mode'],sample['repeat'])!=(split,mode,0):continue
                for r in study.bound(study.bound(sample)['queries']):
                    if r.get('probe') is not None:
                        p=r['probe'];counts.update(dict(calls=1,completed=int(p['result'] is not None),expansions=p['metrics'].get('expanded_nodes',0),
                            retained_pending_records=p['metrics'].get('probe_retained_pending_records',0),committed_records=p['metrics'].get('batch_committed_records',0)))
                    attempts.append(dict(case=r['case'],variant=r['variant'],route=r['route'],expanded_nodes=r['expanded_nodes'],
                        probe_expansions=0 if r.get('probe') is None else r['probe']['metrics'].get('expanded_nodes',0),
                        branch_expansions=[b['metrics'].get('expanded_nodes',0) for b in r.get('branches',[])]))
            probe[split][mode]=dict(counts=dict(counts),attempts=attempts)
    a['probe']=probe;a['reuse']=reuse(out,report);a['limitations'].append('New native probes cap acquisitions only, restart after a stop, and retain already checked proof nodes. Their budget is charged to the same total; preparation, verification and storage costs remain separate.')
    study.base.write(out/'analysis.json',a)

def reuse(out,report):
    p=study.base.load(out/'protocol.json');summaries=[]
    for sample in report['samples']:
        if sample['split']!='fresh' or sample['repeat']!=0:continue
        data=study.bound(sample);rs=study.bound(data['queries']);prefix=study.read_zip(p['prefixes'][str(sample['case'])]['archive'])
        seed=dict(prefix[study.TABLES[0]]);rows={**seed,**dict(study.read_zip(data['delta'])[study.TABLES[0]])};earlier=set()
        def closure(roots,current):
            seen=set();todo=list(roots);edges=Counter()
            while todo:
                key=todo.pop()
                if key in seen:continue
                seen.add(key);node=json.loads(rows[key]);proof=node.get('proof',{})
                for f in ('child','low','high'):
                    if f in proof:
                        child=proof[f];edges['seed' if child in seed else 'previous_query' if child in earlier else 'this_query']+=1;todo.append(child)
            assert seen<=seed.keys()|earlier|current
            return dict(reachable=dict(Counter('seed' if key in seed else 'previous_query' if key in earlier else 'this_query' for key in seen)),dependency_edges=dict(edges))
        for r in rs:
            current=set(r['new_ids'][study.TABLES[0]])
            roots=[b['result']['root'] for b in r.get('branches',[]) if b.get('result') is not None]
            if not roots and r['result'] is not None and r['result']['authority']=='native':roots=[r['result']['root']]
            summaries.append(dict(case=sample['case'],mode=sample['mode'],variant=r['variant'],branches=closure(roots,current),
                premise=None if r['partition'] is None else closure([r['stronger_root']],current)))
            earlier.update(current)
    return dict(records=summaries,limitations=['Read-only posthoc dependency reachability. Previous-query nodes are absent from the common seed and published by earlier fresh attempts.',
        'This identifies exact saved proof dependencies, not a counterfactual runtime saving. Formula edits and prior state both change between queries; an independent-cold ablation remains necessary.'])

def next_branch(out):
    from tempfile import TemporaryDirectory
    from experiments.cnf_clause_partition import branch_sources
    from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
    from experiments.cnf_partition_screen import screen_branch
    p=study.base.load(out/'protocol.json');cases=study.bound(p['cases']);case=next(c for c in cases if (c['case'],c['split'],c['variant'])==(31,'fresh','delete'))
    report=study.base.load(out/'fresh-31-probe6-0/report.json');r=study.bound(report['queries'])[0];delta=study.read_zip(report['delta'])
    index=max(range(len(r['branches'])),key=lambda i:r['branches'][i]['metrics'].get('expanded_nodes',0))
    assert index==1 and r['branches'][index]['metrics']['expanded_nodes']==61
    # No fresh equivalence/affine publication occurs in this native-only query.
    assert all(not r['new_ids'][t] for t in study.TABLES[1:])
    count=r['probe']['metrics'].get('batch_committed_records',0)+r['preparation_counts'].get('inserted_nodes',0)
    count+=sum(b['metrics'].get('batch_committed_records',0) for b in r['branches'][:index])
    keys=r['new_ids'][study.TABLES[0]][:count];extra={t:[] for t in study.TABLES};extra[study.TABLES[0]]=[[k,v] for k,v in delta[study.TABLES[0]] if k in set(keys)]
    assert len(extra[study.TABLES[0]])==count
    source=branch_sources(case['source'],r['missing'])[1][index][2];prefix=study.read_zip(p['prefixes']['31']['archive'])
    with TemporaryDirectory() as td:
        path=Path(td)/'db';study.restore(prefix,path,extra);digest=study.base.sha(path);s=CanonicalVerifySnapshot(path)
        try:
            cnf,names,key=s._canonical(source);assert key==r['branches'][index]['result']['root'] and s._read(key,cnf) is None
            for k in keys:assert s._read(k) is not None
            assert s._read(r['stronger_root'])['answer'] is False
            for b in r['branches'][:index]:assert s._read(b['result']['root'])['answer']==b['result']['answer']
            screen=screen_branch(s,source,Counter());counts=dict(s.counts)
        finally:s.close()
        assert digest==study.base.sha(path)
    study.base.write(out/'next-branch.json',dict(source=[list(c) for c in source],root=key,branch=index,original_query=case,
        prefix=p['prefixes']['31']['archive'],trial_report=study.binding(out/'fresh-31-probe6-0/report.json'),extra_ids=keys,
        extra_count=count,screen=screen,reader_counts=counts,measured_branch_expansions=61,
        limitations=['Exact pre-branch proof state reconstructed from chronological publications: probe, support/premise, and completed earlier branches only. Target branch root is absent.',
        'Posthoc diagnostic, excluded from comparative timing. No search or publication occurs. Future work can restore the bound prefix plus these rows from the bound trial delta.',
        'This isolates the cost centre without attributing a new tractable class or assuming its whole-source conditions are discharged.']))

if __name__=='__main__':
    out=Path(sys.argv[1])
    if len(sys.argv)>2 and sys.argv[2]=='next':next_branch(out)
    else:analyze(out)
