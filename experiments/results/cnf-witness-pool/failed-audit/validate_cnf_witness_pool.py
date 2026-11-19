#!/usr/bin/env python3
"""Check automatic witness reuse, independent certificates, and append-only history."""
from collections import Counter
from itertools import product
from pathlib import Path
from unittest.mock import patch
import copy,json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_witness_pool as study
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_residual_dag import holds
from experiments.cnf_cross_family import truth_table
from experiments.validate_cnf_ordered_normalization import TABLES,PILOTS
base=study.base;previous=study.prior.previous


def tiny(out):
    clauses=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
    cases=[];records=[];dest=out/'tiny';dest.mkdir()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=WitnessPoolSolver(path,pool_capacity=4,candidate_limit=2)
        try:
            for bits in product((False,True),repeat=len(clauses)):
                source=[c for b,c in zip(bits,clauses) if b];r=study.attempt(s,source)
                assert r['result']['answer']==truth_table(source)['answer']
                if r['result']['answer']:assert holds(source,r['result']['model'])
                cases.append(dict(case=len(cases),source=source));records.append(r)
        finally:s.close()
        audit=study.cold(path,cases,records);archive=base.archive(path,dest)
    base.write(dest/'queries.json',records)
    return dict(formulas=len(cases),statuses=dict(Counter(r['status'] for r in records)),audit=audit,archive=archive,queries=study.binding(dest/'queries.json'))


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);report=base.load(out/'report.json')
    cases={split:study.bound(b) for split,b in p['cases'].items()}
    for split,cs in cases.items():assert cs==study.catalog(split)
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=dict(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
        artifacts+=len(items)
    assert (len(manifests),artifacts)==(119,8088)
    audits=[];by_mode={};alternatives=Counter();new=Counter();query_audits=0
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'union';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        merged=copy.deepcopy(initial)
        known=set().union(*(set(initial[t]) for t in TABLES if 'equivalence' in t or t=='cnf_residual_v1'))
        novelty={split:dict(queries=len(cs),known_queries=sum(c['root'] in known for c in cs),distinct_roots=len({c['root'] for c in cs})) for split,cs in cases.items()}
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);cs=cases[sample['split']]
            assert len(rows)==len(cs)==108
            db=tmp/('-'.join(str(sample[k]) for k in ('split','mode','repeat')));base.restore_archive(data['archive'],db)
            s=SnapshotResidualSolver(db)
            try:tables={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in study.TABLES}
            finally:s.close()
            available={t:set() for t in study.TABLES};sizes=Counter()
            for c,r in zip(cs,rows):
                query_audits+=1;assert r['case']==c['case'];added=payload=0
                for t in study.TABLES:
                    ids=r['new_ids'][t];assert len(ids)==len(set(ids)) and not set(ids)&available[t]
                    available[t].update(ids);size=sum(len(k)+len(tables[t][k]) for k in ids);added+=len(ids);payload+=size
                    sizes[t+'_nodes']+=len(ids);sizes[t+'_payload']+=size
                assert dict(sizes)==r['retained']
                assert r['metrics'].get('batch_committed_records',0)==added
                assert r['metrics'].get('batch_committed_payload',0)==payload
                assert r['metrics'].get('witness_peak_entries',0)<=p['pool_limits']['pool_capacity']
                assert r['metrics'].get('witness_candidates',0)<=p['pool_limits']['candidate_limit']*r['metrics'].get('witness_probes',0)
                assert r['metrics'].get('witness_index_entries',0)<=p['pool_limits']['pool_capacity']*r['metrics'].get('witness_probes',0)
                for key in r['new_ids'][study.TABLES[0]]:
                    proof=json.loads(tables[study.TABLES[0]][key]).get('proof',{})
                    assert {proof[f] for f in ('child','low','high') if f in proof}<=available[study.TABLES[0]]
                if r['status']=='unresolved':assert r['result'] is None and r['reason']==BUDGET_MESSAGE and r['metrics']['expanded_nodes']==p['node_limit']
                else:
                    assert r['result']['root']==c['root'] and r['status']==('sat' if r['result']['answer'] else 'unsat')
                    assert c['root'] in set().union(*available.values())
                    assert r['metrics'].get('expanded_nodes',0)<=p['node_limit']
            assert all(available[t]==set(tables[t]) for t in study.TABLES)
            audits.append(study.cold(db,cs,rows))
            by_mode[(sample['split'],sample['mode'],sample['repeat'])]=rows
            for t,values in tables.items():
                for key,payload in values.items():
                    if key in merged[t]:
                        if payload!=merged[t][key]:
                            # Each entire trial was checked above. Keep the earlier
                            # authoritative bytes, even when another witness differs.
                            assert json.loads(payload)['answer']==json.loads(merged[t][key])['answer']
                            alternatives[t]+=1
                    else:merged[t][key]=payload;new[t]+=1
        comparisons=0
        for split in cases:
            control=by_mode[(split,'batch32',0)]
            for mode in study.MODES:
                a=by_mode[(split,mode,0)];b=by_mode[(split,mode,1)]
                for x,y in zip(a,b):
                    for field in ('case','status','reason','metrics','new_ids','retained'):assert x[field]==y[field]
                    if x['result'] is not None:
                        for field in ('answer','model','root','authority','quotient_choice'):assert x['result'][field]==y['result'][field]
                for x,y in zip(control,a):
                    if x['result'] is not None and y['result'] is not None:assert x['status']==y['status'];comparisons+=1
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():
                    for key,payload in values.items():
                        if key not in initial[t]:con.execute(f'INSERT INTO {t}(id,payload) VALUES (?,?)',(key,payload))
        finally:con.close()
        old_cases=study.bound(parent['larger_mixtures']['cases']);old_rows=study.bound(parent['larger_mixtures']['queries']);recovery=study.bound(parent['larger_mixtures']['recovery'])
        reader_counts={}
        for reader in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=reader(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for key in merged['cnf_residual_v1']:assert s._read(key) is not None
                for t in TABLES[2:5]:
                    for key in merged[t]:assert store.read(key) is not None
                for key in merged[TABLES[1]]:assert terminal.read(key) is not None
                for key,payload in merged[TABLES[-1]].items():cache.verify(key,payload)
                for r in sum((study.bound(parent[f]) for f in PILOTS),[]):study.prior.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
                for cs,rs in [(old_cases,old_rows)]+[(cases[split],rs) for (split,mode,rep),rs in by_mode.items() if rep==0]:
                    for c,r in zip(cs,rs):
                        if r['result'] is not None:study.prior.check_answer(s,store,c['source'],r['result'])
                study.prior.check_answer(s,store,old_cases[recovery['target_case']]['source'],recovery['result']['result'])
                reader_counts[reader.__name__]=dict(s.counts)
            finally:s.close()
        s=previous.native.ResidualSolver(path)
        try:_,_,indices,prepared,_=previous.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS],indices)
        dest=out/'union';dest.mkdir();archive=base.archive(path,dest)
        # Explicitly check the preceding classification archive, not just its hash.
        inventory=study.bound(parent['larger_mixtures']['discovery']);ip=tmp/'inventory';base.restore_archive(inventory['archive'],ip)
        before=base.sha(ip);s=PatternInventory(ip,**inventory['config'])
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_discover',side_effect=AssertionError('Old discovery')):
                for key, in s.db.execute('SELECT id FROM cnf_patterns_v1'):assert s._load(key) is not None
                for c,r in zip(old_cases,study.bound(inventory['records'])):
                    _,names,key=s._canonical(c['source'],1);assert r['result']['root']==dict(key=key,names=names)
                    node=s._load(key);assert node['summary']==r['result']['summary'] and node['profile']==r['result']['profile']
                    source=json.loads(s.db.execute('SELECT payload FROM cnf_pattern_sources_v1 WHERE id=?',(r['result']['source_id'],)).fetchone()[0])
                    assert source==dict(source=c['source'],root=r['result']['root'],config=inventory['config'])
            old_inventory_nodes=s.counts['verified_pattern_nodes']
        finally:s.close()
        assert before==base.sha(ip)
    tiny_result=tiny(out)
    analysis={}
    for split in cases:
        rows={mode:by_mode[(split,mode,0)] for mode in study.MODES};arms=report['summary'][split]
        groups={}
        for field in ('family','variant'):
            groups[field]={}
            for value in sorted({c[field] for c in cases[split]}):
                groups[field][value]={}
                for mode in study.MODES:
                    selected=[r for c,r in zip(cases[split],rows[mode]) if c[field]==value]
                    groups[field][value][mode]=dict(seconds=sum(r['seconds'] for r in selected),expansions=sum(r['metrics'].get('expanded_nodes',0) for r in selected),new_nodes=sum(len(r['new_ids']['cnf_residual_v1']) for r in selected),hits=sum(r['metrics'].get('witness_hits',0) for r in selected),statuses=dict(Counter(r['status'] for r in selected)))
        reductions={key:1-arms['pool'][key]/arms['batch32'][key] for key in ('mean_query_seconds','mean_complete_worker_seconds','mean_cold_seconds','native_nodes','native_payload','database_bytes','compressed_bytes','checked_python_bytes')}
        paired=[]
        for repeat in (0,1):
            summaries={m:study.bound(next(s for s in report['samples'] if s['split']==split and s['repeat']==repeat and s['mode']==m))['summary'] for m in study.MODES}
            paired.append({k:summaries['pool'][k]-summaries['batch32'][k] for k in ('query_seconds','complete_worker_seconds','warm_seconds','cold_seconds','reconstruction_seconds')})
        analysis[split]=dict(groups=groups,reductions=reductions,paired_pool_minus_baseline=paired,unknown_cases={m:[r['case'] for r in rows[m] if r['status']=='unresolved'] for m in study.MODES})
    base.write(out/'analysis.json',analysis)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_witness_pool.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],source_fingerprints=sources,reference_union=archive,
        witness_pool_study=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json'),solver=study.binding('experiments/cnf_witness_pool.py')))
    base.write(out/'checkpoint.json',checkpoint)
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),
        query_audits=query_audits,completed_status_comparisons=comparisons,novelty=novelty,old_composed_records=len(previous.inherited(parent)),old_pilot_records=sum(len(study.bound(parent[f])) for f in PILOTS),
        old_larger_queries=len(old_rows),old_inventory_nodes=old_inventory_nodes,reader_counts=reader_counts,audits=audits,historical_cold=historical,tiny=tiny_result,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result);print(base.encode({k:result[k] for k in ('passed','new_records','alternative_payload_observations','novelty','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
