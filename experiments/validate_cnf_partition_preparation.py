#!/usr/bin/env python3
"""Audit frozen seeds, chronological authority and cumulative preservation."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_preparation as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base=study.base;TABLES=inherited.TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    assert len(cases)==12 and len(report['samples'])==48 and report['protocol']==study.binding(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=deepcopy(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(133,10783)
    prefixes={i:study.read_zip(v['archive']) for i,v in p['prefixes'].items()}
    previous=base.load(study.PARENT/'protocol.json')
    for i in ('25','31','61'):assert prefixes[i]==study.read_zip(previous['prefixes'][i]['archive'])
    records={};new=Counter();alternatives=Counter();parts=[];attempts=0;audits=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial)
        for c in cases:
            cnf,_=study.normalize(c['source']);assert study.token(cnf,Counter())==c['root']
            prefix=prefixes[c['split'] if study.native_split(c['split']) else str(c['case'])]
            assert all(c['root'] not in dict(prefix[t]) for t in study.TABLES)
            if c['split']=='novel':assert all(c['root'] not in initial[t] for t in TABLES)
        for n,sample in enumerate(report['samples']):
            data=study.bound(sample);rs=study.bound(data['queries']);cs=[c for c in cases if (c['split'],c['case'])==(sample['split'],sample['case'])]
            assert len(cs)==len(rs);attempts+=len(rs)
            prefix=prefixes[sample['split'] if study.native_split(sample['split']) else str(sample['case'])];delta=study.read_zip(data['delta'])
            available={t:dict(prefix[t]) for t in study.TABLES}
            assert [r['partition'] for r in rs if r['partition'] is not None]==study.bound(data['partitions'])
            for c,r in zip(cs,rs):
                assert r['root']==c['root'] and r['variant']==c['variant'] and r['expanded_nodes']<=256
                for t in study.TABLES:
                    ids=r['new_ids'][t];values=dict(delta[t]);assert len(ids)==len(set(ids)) and not set(ids)&available[t].keys()
                    for k in ids:
                        if t==study.TABLES[0]:
                            proof=json.loads(values[k]).get('proof',{});assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                        available[t][k]=values[k]
                if not study.native_split(sample['split']):
                    acquisitions=([r['probe']] if r['probe'] is not None else [])+r['branches']
                    assert sum(a['metrics'].get('expanded_nodes',0) for a in acquisitions)==r['expanded_nodes']
                    if r['probe'] is not None:assert r['probe']['metrics'].get('expanded_nodes',0)<=8
                    if r['partition'] is not None:assert 2<=len(r['missing'])<=6
                if r['partition'] is not None:parts.append(r['partition'])
                if r['result'] is not None:assert r['status']==('sat' if r['result']['answer'] else 'unsat') and r['result']['root']==r['root']
                else:assert r['status']=='unresolved' and r['partition'] is None
            for t in study.TABLES:
                assert available[t]==dict(prefix[t]+delta[t])
                assert base.key_sha(base.encode(delta[t]))==data['summary']['delta_digest'][t]
                for k,v in delta[t]:
                    if k in merged[t]:
                        assert json.loads(v)['answer']==json.loads(merged[t][k])['answer']
                        alternatives[t]+=v!=merged[t][k]
                    else:merged[t][k]=v;new[t]+=1
            # Independently replay each new native node and its recursively
            # checked prerequisites, rather than trusting worker timing logs.
            db=temp/f'trial{n}';study.restore(prefix,db,delta);reader=SnapshotResidualSolver(db)
            try:
                for k,v in delta[study.TABLES[0]]:assert reader._read(k) is not None
                for c,r in zip(cs,rs):
                    if r['partition'] is not None:check_record(reader,r['partition'])
                    elif r['result'] is not None:assert reader._read(r['root'])['answer']==r['result']['answer']
                audits.append(dict(sample=n,counts=dict(reader.counts)))
            finally:reader.close();db.unlink()
            records[(sample['split'],sample['case'],sample['mode'],sample['repeat'])]=rs
        assert attempts==96
        groups={(c['split'],c['case']) for c in cases}
        for split,index in groups:
            for mode in study.MODES:
                for a,b in zip(records[(split,index,mode,0)],records[(split,index,mode,1)]):
                    for f in ('status','reason','route','partition','expanded_nodes','new_ids'):assert a.get(f)==b.get(f),f
                for a,b in zip(records[(split,index,'binary1',0)],records[(split,index,mode,0)]):
                    if a['result'] is not None and b['result'] is not None:assert a['status']==b['status']
        # Preparation changes neither search nor proof bytes in either policy.
        for split,index in groups:
            for repeat in range(2):
                for parent_mode,prepared in (('binary1','binary-prepared'),('handoff','handoff-prepared')):
                    left=base.load(out/f'{split}-{index}-{parent_mode}-{repeat}/report.json')
                    right=base.load(out/f'{split}-{index}-{prepared}-{repeat}/report.json')
                    assert study.read_zip(left['delta'])==study.read_zip(right['delta'])
                    assert study.bound(left['partitions'])==study.bound(right['partitions'])
                    for a,b in zip(records[split,index,parent_mode,repeat],records[split,index,prepared,repeat],strict=True):
                        for field in ('status','reason','route','partition','expanded_nodes','new_ids'):
                            assert a.get(field)==b.get(field),field
                        if a['result'] is not None:
                            for field in ('answer','model','root'):assert a['result'].get(field)==b['result'].get(field)
                        if parent_mode=='handoff':
                            assert a['cofactor_handoff']==b['cofactor_handoff']
                            offer=b['cofactor_handoff'];assert offer['capacity']==p['handoff_bytes']
                            assert offer['peak_bytes']<=offer['capacity']
                            assert offer['admissions']==offer['consumed']+offer['discarded']
        # Old policies reproduce their earlier streams under identical seeds.
        for index in (25,31,61):
            for mode in ('binary1','handoff'):
                oldrs=base.load(study.PARENT/f'novel-{index}-{mode}-0/queries.json')
                for a,b in zip(oldrs,records[('controls',index,mode,0)]):
                    for f in ('status','expanded_nodes','new_ids','partition'):assert a[f]==b[f],f
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in values.items() if k not in initial[t]])
        finally:con.close()
        older_parts=[]
        for field in ('transported_partition_study','probed_partition_study','ranked_binary_targets','binary_routing','bipolar_routing','prepared_cofactors','cofactor_handoff'):older_parts.extend(study.bound(parent[field]['partitions']))
        readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(path);equiv=MultiEquivalenceStore(s);affine=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for k in merged[TABLES[0]]:assert s._read(k) is not None
                for k in merged[TABLES[1]]:assert affine.read(k) is not None
                for t in TABLES[2:5]:
                    for k in merged[t]:assert equiv.read(k) is not None
                for k,v in merged[TABLES[-1]].items():cache.verify(k,v)
                for r in older_parts+parts:check_record(s,r)
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'union-partitions.json',parts)
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in ('experiments/analyze_cnf_partition_preparation.py','experiments/validate_cnf_partition_preparation.py')}}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        partition_preparation=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json'),
            partitions=study.binding(out/'union-partitions.json'),decision='Optional immutable partition preparation; proof bytes and search must match each parent policy. Independent sidecar reconstruction remains mandatory; no default change or general speed guarantee.'))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,query_audits=attempts,
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),
        alternative_payload_observations=dict(alternatives),partition_records=len(parts),previous_partition_records=len(older_parts),reader_counts=readers,
        historical_validation=study.binding(study.PARENT/'validation.json'),audits=audits,checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,
        limitations=['Cumulative native/extension records and all current/preceding partition sidecars are replayed with both readers. Other older composed/inventory audits are inherited through immutable manifests, not rerun.',
        'Alternative valid native payloads remain in trial deltas; the cumulative union keeps the earlier authoritative payload.'])
    base.write(out/'validation.json',v);print(base.encode({k:v[k] for k in ('passed','new_records','alternative_payload_observations','partition_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
