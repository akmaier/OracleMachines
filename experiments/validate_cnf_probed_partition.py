#!/usr/bin/env python3
"""Verify retained probe prefixes, exact seeds, chronological deltas and union."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probed_partition as study
from experiments import validate_cnf_transported_partition as inherited
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base=study.base;binding=study.binding;bound=study.bound;TABLES=inherited.TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=bound(p['parent']);cases=bound(p['cases']);report=base.load(out/'report.json')
    assert len(cases)==9 and len(report['samples'])==60 and report['protocol']==binding(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    oldv=base.load(study.PARENT/'validation.json');manifests=deepcopy(oldv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
        artifacts+=len(items)
    assert (len(manifests),artifacts)==(127,8866)
    prefixes={i:study.read_zip(v['archive']) for i,v in p['prefixes'].items()};new=Counter();alternatives=Counter();records={};audits=[];parts=[];query_count=0
    for index,entry in p['prefixes'].items():
        old_prefix=study.read_zip(entry['parent_prefix']);addition=bound(entry['addition_report']);rs=bound(addition['queries']);delta=study.read_zip(addition['delta'])
        assert entry['addition_ids']==rs[0]['new_ids']
        expected={t:old_prefix[t]+[[k,v] for k,v in delta[t] if k in set(rs[0]['new_ids'][t])] for t in study.TABLES}
        assert prefixes[index]==expected
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        merged=deepcopy(initial)
        for c in cases:
            assert c['source']==study.previous.target_source(c['candidate'])
            assert all(c['root'] not in dict(prefixes[str(c['case'])][t]) for t in study.TABLES)
            if c['split']=='fresh':assert all(c['root'] not in initial[t] for t in TABLES)
        for n,sample in enumerate(report['samples']):
            data=bound(sample);rs=bound(data['queries']);cs=[c for c in cases if (c['case'],c['split'])==(sample['case'],sample['split'])]
            prefix=prefixes[str(sample['case'])];delta=study.read_zip(data['delta']);available={t:dict(prefix[t]) for t in study.TABLES}
            assert len(cs)==len(rs);query_count+=len(rs)
            assert [r['partition'] for r in rs if r['partition'] is not None]==bound(data['partitions'])
            for c,r in zip(cs,rs):
                assert (r['root'],r['variant'])==(c['root'],c['variant']);assert r['expanded_nodes']<=p['node_limit']
                probe=r.get('probe')
                if sample['mode'] not in ('native','affine'):
                    counted=sum(b['metrics'].get('expanded_nodes',0) for b in r['branches'])
                    if probe is not None:
                        assert probe['metrics'].get('expanded_nodes',0)<=p['probe_limit'];counted+=probe['metrics'].get('expanded_nodes',0)
                        if probe['result'] is None:assert probe['metrics']['probe_budget_prefix_commits']==1
                        else:assert r['route']=='probe' and r['descriptor'] is None and not r['branches']
                    assert counted==r['expanded_nodes']
                    if r['route']=='partition':assert 2<=len(r['missing'])<=p['max_missing']
                for t in study.TABLES:
                    ids=r['new_ids'][t];values=dict(delta[t]);assert len(ids)==len(set(ids)) and not set(ids)&available[t].keys()
                    for key in ids:
                        payload=values[key]
                        if t==study.TABLES[0]:
                            proof=json.loads(payload).get('proof',{});assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                        available[t][key]=payload
                if r['result'] is None:assert r['status']=='unresolved' and r['partition'] is None and r['reason']==study.previous.BUDGET_MESSAGE
                else:assert r['result']['root']==c['root'] and r['status']==('sat' if r['result']['answer'] else 'unsat')
                if r['partition'] is not None:parts.append(r['partition'])
            for t in study.TABLES:
                assert available[t]==dict(prefix[t]+delta[t]);assert len(delta[t])==data['summary']['new_records'][t]
                assert base.key_sha(base.encode(delta[t]))==data['summary']['delta_digest'][t]
            db=temp/f'trial-{n}';study.restore(prefix,db,delta);audits.append(study.previous.validate_rows(db,cs,rs));db.unlink()
            records[(sample['split'],sample['case'],sample['mode'],sample['repeat'])]=rs
            for t,values in delta.items():
                for key,payload in values:
                    if key in merged[t]:
                        if payload!=merged[t][key]:
                            assert json.loads(payload)['answer']==json.loads(merged[t][key])['answer'];alternatives[t]+=1
                    else:merged[t][key]=payload;new[t]+=1
        assert query_count==90
        for split in study.SPLITS:
            for case in study.CASES:
                for mode in study.MODES:
                    for a,b in zip(records[(split,case,mode,0)],records[(split,case,mode,1)]):
                        for field in ('status','reason','route','partition','expanded_nodes','new_ids'):assert a[field]==b[field]
                        if a['result'] is not None:
                            for field in ('answer','model','root','authority'):assert a['result'][field]==b['result'][field]
                    for a,b in zip(records[(split,case,'affine',0)],records[(split,case,mode,0)]):
                        if a['result'] is not None and b['result'] is not None:assert a['status']==b['status']
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in values.items() if k not in initial[t]])
        finally:con.close()
        old_parts=bound(parent['transported_partition_study']['partitions']);readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for key in merged[TABLES[0]]:assert s._read(key) is not None
                for key in merged[TABLES[1]]:assert terminal.read(key) is not None
                for t in TABLES[2:5]:
                    for key in merged[t]:assert store.read(key) is not None
                for key,payload in merged[TABLES[-1]].items():cache.verify(key,payload)
                for r in old_parts+parts:check_record(s,r)
                for (split,index,mode,rep),rs in records.items():
                    for c,r in zip([c for c in cases if (c['case'],c['split'])==(index,split)],rs):
                        if r['result'] is not None and r['partition'] is None:study.previous.prior.check_answer(s,store,c['source'],r['result'])
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        legacy=inherited.previous;s=legacy.native.ResidualSolver(path)
        try:_,_,indices,prepared,_=legacy.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        historical=legacy.audit_records(path,legacy.inherited(parent),bound(parent['conditioned_core_projections']),prepared,[(n,bound(parent[n])) for n in legacy.OLD_FIELDS],indices)
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'union-partitions.json',parts)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probed_partition.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        probed_partition_study=dict(protocol=binding(out/'protocol.json'),report=binding(out/'report.json'),partitions=binding(out/'union-partitions.json'),
            decision='Optional supplied-candidate probe/partition pilot. Keep the affine baseline until broader discovery and cost evidence.'))
    base.write(out/'checkpoint.json',cp)
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,query_audits=query_count,
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),
        partition_records=len(parts),previous_partition_records=len(old_parts),old_composed_records=len(legacy.inherited(parent)),reader_counts=readers,historical_cold=historical,
        inherited_history_validation=binding(study.PARENT/'validation.json'),audits=audits,checkpoint=binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result);print(base.encode({k:result[k] for k in ('passed','new_records','alternative_payload_observations','partition_records','seconds')}),flush=True)

if __name__=='__main__':validate(Path(sys.argv[1]))
