#!/usr/bin/env python3
"""Audit prefix exclusion, chronological deltas, partition authority and history."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_transported_partition as study
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
from experiments.cnf_transported_partition import prepare_support
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.validate_cnf_ordered_normalization import TABLES,PILOTS
base=study.base;bound=study.bound;binding=study.binding;prior=study.prior;previous=prior.prior.previous


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=bound(p['parent']);report=base.load(out/'report.json');cases=bound(p['cases'])
    assert len(cases)==9 and len(report['samples'])==60 and report['protocol']==binding(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
        artifacts+=len(items)
    assert (len(manifests),artifacts)==(126,8539)
    historical=bound(p['historical_queries']);prefixes={k:study.read_zip(v['archive']) for k,v in p['prefixes'].items()}
    new=Counter();alternatives=Counter();audits=[];records={};query_count=0;all_partitions=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        merged=deepcopy(initial)
        finalpath=temp/'historical-final';base.restore_archive(p['historical_archive'],finalpath);reader=CanonicalVerifySnapshot(finalpath)
        try:historical_tables={t:dict(v) for t,v in study.tables(reader).items()}
        finally:reader.close()
        for index,rows in prefixes.items():
            for t in study.TABLES:
                ids={key for r in historical[:int(index)] for key in r['new_ids'][t]}
                assert set(dict(rows[t]))==ids and len(rows[t])==len(ids)
                assert dict(rows[t]).items()<=historical_tables[t].items()
            c=next(c for c in cases if c['case']==int(index) and c['split']=='historical')
            assert c['candidate']['origin'] in dict(rows[study.TABLES[0]])
            # Recompute the selected support using only the allowed prefix.
            db=temp/('prefix-'+index);study.restore(rows,db);s=CanonicalVerifySnapshot(db)
            try:plan,desc=prepare_support(s,c['candidate']);assert len(desc['missing'])=={25:5,31:5,61:3}[int(index)]
            finally:s.close()
        for c in cases:
            assert c['source']==study.target_source(c['candidate'])
            assert all(c['root'] not in dict(prefixes[str(c['case'])][t]) for t in study.TABLES)
            if c['split']=='edits':assert all(c['root'] not in initial[t] for t in TABLES)
        for n,sample in enumerate(report['samples']):
            data=bound(sample);rs=bound(data['queries']);cs=[c for c in cases if c['case']==sample['case'] and c['split']==sample['split']]
            delta=study.read_zip(data['delta']);prefix=prefixes[str(sample['case'])];available={t:dict(prefix[t]) for t in study.TABLES}
            assert [r['partition'] for r in rs if r['partition'] is not None]==bound(data['partitions'])
            assert len(rs)==len(cs);query_count+=len(rs)
            for c,r in zip(cs,rs):
                assert (c['case'],c['variant'],c['root'])==(r['case'],r['variant'],r['root'])
                assert 0<=r['expanded_nodes']<=p['node_limit']
                for t in study.TABLES:
                    values=dict(delta[t]);ids=r['new_ids'][t];assert len(ids)==len(set(ids)) and not set(ids)&available[t].keys()
                    # Native dependencies must precede their parents in the
                    # committed publication stream, not merely exist at trial end.
                    for key in ids:
                        payload=values[key];node=json.loads(payload)
                        if t==study.TABLES[0]:
                            proof=node.get('proof',{});assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                        available[t][key]=payload
                if r['result'] is None:assert r['partition'] is None and r['status']=='unresolved' and r['reason']==study.BUDGET_MESSAGE
                else:assert r['result']['root']==c['root'] and r['status']==('sat' if r['result']['answer'] else 'unsat')
                if r['partition'] is not None:all_partitions.append(r['partition'])
            for t in study.TABLES:
                assert available[t]==dict(prefix[t]+delta[t]);assert len(delta[t])==data['summary']['new_records'][t]
                assert base.key_sha(base.encode(delta[t]))==data['summary']['delta_digest'][t]
            db=temp/f'trial-{n}';study.restore(prefix,db,delta)
            audits.append(study.validate_rows(db,cs,rs));db.unlink()
            key=(sample['split'],sample['case'],sample['mode'],sample['repeat']);records[key]=rs
            for t,values in delta.items():
                for key,payload in values:
                    if key in merged[t]:
                        if merged[t][key]!=payload:
                            assert json.loads(merged[t][key])['answer']==json.loads(payload)['answer'];alternatives[t]+=1
                    else:merged[t][key]=payload;new[t]+=1
        assert query_count==90
        for split in study.SPLITS:
            for case in study.CASES:
                for mode in study.MODES:
                    a=records[(split,case,mode,0)];b=records[(split,case,mode,1)]
                    for x,y in zip(a,b):
                        for f in ('status','reason','route','result','partition','expanded_nodes','new_ids'):
                            if f=='result' and x[f] is not None:
                                for k in ('root','answer','model','authority'):assert x[f][k]==y[f][k]
                            else:assert x[f]==y[f],(split,case,mode,f)
                baseline=records[(split,case,'affine',0)]
                for mode in study.MODES:
                    for x,y in zip(baseline,records[(split,case,mode,0)]):
                        if x['result'] is not None and y['result'] is not None:assert x['status']==y['status']
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():
                    con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in values.items() if k not in initial[t]])
        finally:con.close()
        old_cases=bound(parent['larger_mixtures']['cases']);old_rows=bound(parent['larger_mixtures']['queries']);recovery=bound(parent['larger_mixtures']['recovery'])
        streams=[(old_cases,old_rows)];stream_counts={}
        for field in ('witness_pool_study','negative_edit_pool_study','support_plan_study','affine_probe_study','partial_residual_study','residual_transport_study'):
            op=bound(parent[field]['protocol']);rr=bound(parent[field]['report']);selected=[(bound(op['cases'][e['split']]),bound(bound(e)['queries'])) for e in rr['samples']]
            streams+=selected;stream_counts[field]=sum(len(rs) for _,rs in selected)
        reader_counts={}
        for reader in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=reader(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for key in merged[TABLES[0]]:assert s._read(key) is not None
                for key in merged[TABLES[1]]:assert terminal.read(key) is not None
                for t in TABLES[2:5]:
                    for key in merged[t]:assert store.read(key) is not None
                for key,payload in merged[TABLES[-1]].items():cache.verify(key,payload)
                for record in all_partitions:check_record(s,record)
                for r in sum((bound(parent[f]) for f in PILOTS),[]):prior.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
                for cs,rs in streams:
                    for c,r in zip(cs,rs):
                        if r['result'] is not None:prior.check_answer(s,store,c['source'],r['result'])
                for (split,index,mode,repeat),rs in records.items():
                    for c,r in zip([c for c in cases if c['case']==index and c['split']==split],rs):
                        if r['result'] is not None and r['partition'] is None:prior.check_answer(s,store,c['source'],r['result'])
                prior.check_answer(s,store,old_cases[recovery['target_case']]['source'],recovery['result'])
                reader_counts[reader.__name__]=dict(s.counts)
            finally:s.close()
        s=previous.native.ResidualSolver(path)
        try:_,_,indices,prepared,_=previous.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        history=previous.audit_records(path,previous.inherited(parent),bound(parent['conditioned_core_projections']),prepared,[(n,bound(parent[n])) for n in previous.OLD_FIELDS],indices)
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
        inventory=bound(parent['larger_mixtures']['discovery']);ip=temp/'inventory';base.restore_archive(inventory['archive'],ip);before=base.sha(ip)
        s=PatternInventory(ip,**inventory['config'])
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_discover',side_effect=AssertionError('Discovery forbidden')):
                for key, in s.db.execute('SELECT id FROM cnf_patterns_v1'):assert s._load(key) is not None
            inventory_nodes=s.counts['verified_pattern_nodes']
        finally:s.close()
        assert base.sha(ip)==before
    base.write(out/'union-partitions.json',all_partitions)
    checkpoint=deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,
        source_fingerprints={**p['source_fingerprints'],'experiments/validate_cnf_transported_partition.py':base.sha(__file__)},
        transported_partition_study=dict(protocol=binding(out/'protocol.json'),report=binding(out/'report.json'),partitions=binding(out/'union-partitions.json'),
            decision='Residual-level supplied-candidate pilot; keep the affine baseline pending net-cost and automatic-discovery evidence.'))
    base.write(out/'checkpoint.json',checkpoint)
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=checkpoint['source_fingerprints'],
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),
        query_audits=query_count,partition_records=len(all_partitions),old_stream_counts=stream_counts,old_composed_records=len(previous.inherited(parent)),
        old_pilot_records=sum(len(bound(parent[f])) for f in PILOTS),old_inventory_nodes=inventory_nodes,old_larger_queries=len(old_rows),
        reader_counts=reader_counts,audits=audits,historical_cold=history,checkpoint=binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result);print(base.encode({k:result[k] for k in ('passed','new_records','alternative_payload_observations','partition_records','seconds')}),flush=True)

if __name__=='__main__':validate(Path(sys.argv[1]))
