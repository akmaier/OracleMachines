#!/usr/bin/env python3
"""Check native recovery authority, chronological seeds and cumulative retention."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_recovery as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_conditional_unit_cache import check_cache
from experiments.cnf_conditional_unit_support import match
from experiments.cnf_conditional_recovery import proposal
from experiments.cnf_residual_dag import restrict,propagate
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base=study.base;TABLES=inherited.TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json');gate=base.load(out/'gate-report.json');gp=study.bound(gate['protocol'])
    assert report['protocol']==study.binding(out/'protocol.json') and gp['original']==report['protocol']
    assert len(cases)==15 and len(report['samples'])==8 and len(gate['samples'])==4
    sources=gp['source_fingerprints']
    for f,h in sources.items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=deepcopy(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(141,12521)
    oldp=study.bound(p['base_protocol']);assert cases[:11]==study.bound(oldp['cases']);assert p['prefix']==oldp['prefix'] and p['donor']==oldp['donor']
    prefix=study.read_zip(p['prefix']);hints=base.load(study.PARENT/'cache-compact-0/hints.json');check_cache(hints);templates=[e['template'] for e in hints['entries']]
    exploration=study.bound(p['exploration_recovery']);assert exploration['script_sha256']==base.sha('experiments/probe_cnf_conditional_recovery.py')
    oldtrial=study.bound(exploration['trial']);oldrs=study.bound(oldtrial['queries']);olddelta=study.read_zip(oldtrial['delta']);oldprep=study.read_zip(oldtrial['preparation_delta'])
    records={};new=Counter();alternatives=Counter();audits=[];attempts=0;reloads=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial)
        def merge(delta):
            for t,rows in delta.items():
                for k,v in rows:
                    if k in merged[t]:assert json.loads(v)['answer']==json.loads(merged[t][k])['answer'];alternatives[t]+=v!=merged[t][k]
                    else:merged[t][k]=v;new[t]+=1
        def chronological(available,delta):
            for t,rows in delta.items():
                for k,v in rows:
                    assert k not in available[t]
                    if t==TABLES[0]:
                        proof=json.loads(v).get('proof',{});assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                    available[t][k]=v
        for obs in exploration['observations']:
            index=obs['position'];r=oldrs[index];case=cases[r['case']];assert obs['baseline']==r and obs['source']==case['source']
            extra={t:oldprep[t]+[[k,dict(olddelta[t])[k]] for before in oldrs[:index] for k in before['new_ids'][t]] for t in study.TABLES}
            assert obs['extra_ids']=={t:[k for k,v in rows] for t,rows in extra.items()}
            fixed=dict(r['assignment']);c=Counter();contained=[i for i,t in enumerate(templates) if match(case['source'],t,c)]
            compatible=[i for i in contained if not any(v in fixed and fixed[v]!=b for v,b in templates[i]['assumptions'])]
            assert obs['contained']==contained and obs['compatible']==compatible and obs['extending']==[i for i in compatible if all(fixed.get(v)==b for v,b in templates[i]['assumptions'])]
            assert obs['extending']==[]
            units,trace,conflict=propagate(restrict(case['source'],fixed),Counter());assert obs['unit_trace']==trace and obs['unit_conflict']==conflict
            plan=proposal(case['source'],templates[r['template']],r['assignment']);assert plan==obs['plan']
            assert obs['new_forces']==([] if plan is None else [[v,b] for v,b in plan['forced'] if v not in units])
            if 'delta' in obs:
                delta=study.read_zip(obs['delta']);db=temp/f'probe{index}';study.restore(prefix,db,{t:extra[t]+delta[t] for t in study.TABLES});s=SnapshotResidualSolver(db)
                try:
                    for k,v in delta[TABLES[0]]:assert s._read(k) is not None
                    assert s._read(r['root'])['answer']==(r['status']=='sat')
                finally:s.close();db.unlink()
                merge(delta)
        for n,sample in enumerate(report['samples']+gate['samples']):
            data=study.bound(sample);rs=study.bound(data['queries']);delta=study.read_zip(data['delta']);prep=study.read_zip(data['preparation_delta']);policy=sample['policy'];attempts+=len(rs);assert len(rs)==90
            assert data['protocol']==report['protocol']
            if n>=8:assert data['gate_protocol']==gate['protocol'] and data['experiment_policy']==policy
            else:assert data['policy']==policy
            tick=time.perf_counter();loaded=study.bound(data['hints']);c=Counter()
            if policy!='native':check_cache(loaded,c);assert loaded==hints
            else:assert loaded==[]
            reloads.append(dict(sample=sample,seconds=time.perf_counter()-tick,counts=dict(c)))
            db=temp/f'trial{n}';study.restore(prefix,db,delta);s=SnapshotResidualSolver(db)
            try:
                available={t:dict(prefix[t]) for t in study.TABLES};chronological(available,prep)
                for r,(case,q) in zip(rs,((case,q) for case in cases for q in case['queries'])):
                    assert (r['case'],r['template'],r['assignment'])==(case['index'],q['template'],q['assignment'])
                    additions={t:[[k,dict(delta[t])[k]] for k in r['new_ids'][t]] for t in study.TABLES};chronological(available,additions)
                    target=restrict(case['source'],dict(q['assignment']));cnf,names,key=s._canonical(target);assert key==r['root']
                    node=s._read(key,cnf);assert node is not None and r['status']==('sat' if node['answer'] else 'unsat')
                    assert key in available[TABLES[0]] and r['expanded_nodes']<=p['node_limit']
                    if r.get('recovery') is not None:
                        rec=r['recovery'];plan=proposal(case['source'],templates[q['template']],q['assignment']);assert rec['plan']==plan
                        screen=r['screen'];assert screen['root']==key
                        units,trace,conflict=propagate(cnf,Counter());assert trace==screen['trace'] and conflict is None
                        fixed={**dict(q['assignment']),**{names[v-1]:b for v,b in units.items()}}
                        assert rec['forced']==[[v,b] for v,b in plan['forced'] if v not in fixed]
                        assert len(rec['forced'])==1
                        child=restrict(case['source'],{**fixed,**dict(rec['forced'])});child_cnf,_,childkey=s._canonical(child)
                        assert childkey==rec['child']['result']['root'];assert s._read(childkey,child_cnf)['answer']==node['answer']
                        assert rec['result']['root']==key and rec['result']['answer']==node['answer']
                    if r['route']=='template':assert match(case['source'],templates[q['template']])
                for t in study.TABLES:assert available[t]==dict(prefix[t]+delta[t])
                for k,v in delta[TABLES[0]]:assert s._read(k) is not None
                audits.append(dict(sample=n,counts=dict(s.counts)))
            finally:s.close();db.unlink()
            merge(delta);records[(policy,sample['repeat'],'gate' if n>=8 else 'main')]=rs
            assert data['summary']['statuses']==dict(Counter(r['status'] for r in rs))=={'sat':9,'unsat':81}
            assert data['summary']['expanded_nodes']==sum(r['expanded_nodes'] for r in rs)
        assert attempts==1080
        reference=records[('compact',0,'main')]
        for key,rs in records.items():assert [(r['root'],r['status']) for r in rs]==[(r['root'],r['status']) for r in reference]
        for a,b in zip(reference[:66],oldrs):
            for field in ('root','status','expanded_nodes','new_ids'):assert a[field]==b[field],field
        for policy,split in [('native','main'),('compact','main'),('screen','main'),('repair','main'),('compact','gate'),('gated','gate')]:
            for a,b in zip(records[(policy,0,split)],records[(policy,1,split)]):
                for field in ('root','status','route','expanded_nodes','new_ids'):assert a[field]==b[field],field
        con=sqlite3.connect(path)
        try:
            with con:
                for t,values in merged.items():con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in values.items() if k not in initial[t]])
        finally:con.close()
        older_parts=[]
        for field in ('transported_partition_study','probed_partition_study','ranked_binary_targets','binary_routing','bipolar_routing','prepared_cofactors','cofactor_handoff','partition_preparation','binary_interactions','live_fallback','joint_backbone','consequence_priority','preimage_fusion','joint_prefix'):older_parts.extend(study.bound(parent[field]['partitions']))
        assert len(older_parts)==342;readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(path);equiv=MultiEquivalenceStore(s);affine=TerminalStore(s);cache=BinaryCoreCache(s)
            try:
                for t in TABLES:assert initial[t].items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for k in merged[TABLES[0]]:assert s._read(k) is not None
                for k in merged[TABLES[1]]:assert affine.read(k) is not None
                for t in TABLES[2:5]:
                    for k in merged[t]:assert equiv.read(k) is not None
                for k,v in merged[TABLES[-1]].items():cache.verify(k,v)
                for r in older_parts:check_record(s,r)
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        dest=out/'union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
    base.write(out/'hint-reload.json',dict(samples=reloads,limitations=['Separate diagnostic cost of reading, binding and validating compact hints; not included in original complete-worker time.']))
    comparisons=[]
    for before,after in zip(records[('compact',0,'gate')],records[('gated',0,'gate')]):
        comparisons.append(dict(case=before['case'],template=before['template'],assignment=before['assignment'],source=cases[before['case']]['source'],root=before['root'],status=before['status'],before_expansions=before['expanded_nodes'],after_expansions=after['expanded_nodes'],before_seconds=before['seconds'],after_seconds=after['seconds'],recovery=after.get('recovery'),before_metrics=before['metrics'],after_metrics=after['metrics']))
    comparisons.sort(key=lambda r:r['after_seconds']-r['before_seconds'],reverse=True)
    analysis=dict(main=report['means'],groups=report['groups'],gate=gate['means'],gate_groups=gate['groups'],query_comparisons=comparisons,
        next_target='Price full-CNF reconstruction and excluded-branch publication on the highest-cost forced query against retaining one checked guard sidecar. Avoid redoing discovery or claiming lower expansion counts are lower total cost.',
        limitations=['Every policy decides the same supplied cofactors. Existing deletion-guard and failed-literal reasoning supplies the implication; this adds no novel inference rule or arbitrary-SAT tractability theorem.',
        'A saturated nonconflicting unit prefix leaves at most one unassigned literal in a sole missing clause of a unit-refutable strengthening. The implementation caps initial reduced missing width at three; its API also accepts valid partial unit prefixes.',
        'Repair can change subsequent proof-cache and pool contents. Keep the screened-only and ordinary-fallback comparators, all regressions, and per-query counters.',
        'Selected-container Python memory omits set contents, bank internals and native allocations. Complete-worker timing excludes persisted-hint reload, separately recorded. No reliable general or end-to-end speedup follows from two orders.'])
    base.write(out/'analysis.json',analysis);sources={**sources,__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        conditional_recovery=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),gate_protocol=study.binding(out/'gate-protocol.json'),gate_report=study.binding(out/'gate-report.json'),analysis=study.binding(out/'analysis.json'),hint_reload=study.binding(out/'hint-reload.json'),decision='Optional missing-clause guidance with ordinary native certificates. Preserve mixed runtime/storage results and all previous proof authority.'))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,query_audits=attempts,exploratory_queries=sum('delta' in o for o in exploration['observations']),prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),partition_records=0,previous_partition_records=len(older_parts),reader_counts=readers,audits=audits,checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,
        limitations=['Both readers replay cumulative native and extension records plus all 342 previous partition sidecars. Other earlier composed audits remain bound through immutable manifests.',
        'Alternative valid native payloads remain in raw trial deltas; the union keeps earlier authoritative bytes.'])
    base.write(out/'validation.json',v);print(base.encode({k:v[k] for k in ('passed','new_records','preserved_tables','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
