#!/usr/bin/env python3
"""Audit early pool authority, proof identity and all preserved solver records."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pool_priority as study
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
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json');profile=base.load(out/'profile.json')
    assert report['protocol']==study.binding(out/'protocol.json') and len(cases)==19 and len(report['samples'])==10
    assert profile['script_sha256']==base.sha('experiments/profile_cnf_pool_priority.py') and profile['proofs_and_routes_unchanged']
    sources=p['source_fingerprints']
    for f,h in sources.items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=deepcopy(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(142,12606)
    oldp=study.bound(p['base_protocol']);assert cases[:15]==study.bound(oldp['cases']);assert p['prefix']==oldp['prefix'] and p['donor']==oldp['donor']
    prefix=study.read_zip(p['prefix']);hints=base.load(study.PARENT/'compact-0/hints.json');check_cache(hints);templates=[e['template'] for e in hints['entries']]
    samples=report['samples']+[dict(policy='pools-native',repeat='profile',**profile['trial'])]
    records={};deltas={};new=Counter();alternatives=Counter();audits=[];attempts=0;reloads=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial)
        def chronological(available,delta):
            for t,rows in delta.items():
                for k,v in rows:
                    assert k not in available[t]
                    if t==TABLES[0]:
                        proof=json.loads(v).get('proof',{});assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                    available[t][k]=v
        for n,sample in enumerate(samples):
            data=study.bound(sample);rs=study.bound(data['queries']);delta=study.read_zip(data['delta']);prep=study.read_zip(data['preparation_delta']);policy=sample['policy'];attempts+=len(rs);assert len(rs)==114
            assert data['protocol']==report['protocol'] and data['policy']==policy
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
                    if r['route'] in ('negative-pool','witness-pool'):
                        expected=r['route']=='witness-pool';assert node['answer']==expected and r['expanded_nodes']==0
                        assert r['metrics']['pool_priority_'+r['route'].replace('-','_')+'_hits']==1
                        assert r['metrics']['witness_hits' if expected else 'negative_hits']==1
                        assert r.get('screen') is None and r.get('recovery') is None
                    if r.get('recovery') is not None:
                        rec=r['recovery'];plan=proposal(case['source'],templates[q['template']],q['assignment']);assert rec['plan']==plan
                        screen=r['screen'];assert screen['root']==key;units,trace,conflict=propagate(cnf,Counter());assert trace==screen['trace'] and conflict is None
                        fixed={**dict(q['assignment']),**{names[v-1]:b for v,b in units.items()}}
                        assert rec['forced']==[[v,b] for v,b in plan['forced'] if v not in fixed] and len(rec['forced'])==1
                        child_cnf,_,childkey=s._canonical(restrict(case['source'],{**fixed,**dict(rec['forced'])}))
                        assert childkey==rec['child']['result']['root'] and s._read(childkey,child_cnf)['answer']==node['answer']
                    if r['route']=='template':assert match(case['source'],templates[q['template']])
                for t in study.TABLES:assert available[t]==dict(prefix[t]+delta[t])
                for k,v in delta[TABLES[0]]:assert s._read(k) is not None
                audits.append(dict(sample=n,counts=dict(s.counts)))
            finally:s.close();db.unlink()
            for t,rows in delta.items():
                for k,v in rows:
                    if k in merged[t]:assert json.loads(v)['answer']==json.loads(merged[t][k])['answer'];alternatives[t]+=v!=merged[t][k]
                    else:merged[t][k]=v;new[t]+=1
            records[(policy,sample['repeat'])]=rs;deltas[(policy,sample['repeat'])]=delta
            assert data['summary']['statuses']==dict(Counter(r['status'] for r in rs))=={'sat':11,'unsat':103}
            assert data['summary']['expanded_nodes']==sum(r['expanded_nodes'] for r in rs)
        assert attempts==1254
        reference=records[('compact',0)]
        for rs in records.values():assert [(r['root'],r['status']) for r in rs]==[(r['root'],r['status']) for r in reference]
        for policy in study.MODES:
            for a,b in zip(records[(policy,0)],records[(policy,1)]):
                for field in ('root','status','route','expanded_nodes','new_ids'):assert a[field]==b[field],field
            assert deltas[(policy,0)]==deltas[(policy,1)]
        for repeat in (0,1,'profile'):assert deltas[('pools-native',repeat)]==deltas[('compact',0)]
        for policy,oldpath in [('compact','gate-compact-0'),('gated','gate-gated-0')]:
            oldrs=base.load(study.PARENT/oldpath/'queries.json')
            for a,b in zip(records[(policy,0)][:90],oldrs):
                for field in ('root','status','expanded_nodes','new_ids'):assert a[field]==b[field],field
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
    base.write(out/'hint-reload.json',dict(samples=reloads,limitations=['Separate diagnostic read/binding/validation cost, outside the measured complete-worker answer-replay timer.']))
    work={}
    for policy in study.MODES:
        c=Counter()
        for r in records[(policy,0)]:
            c.update(r['metrics'])
            for k,v in r['counts'].items():c[k.removeprefix('preliminary_')]+=v
        work[policy]=dict(c)
    cases_compare=[dict(case=a['case'],template=a['template'],assignment=a['assignment'],before_route=a['route'],after_route=b['route'],before_seconds=a['seconds'],after_seconds=b['seconds'],before_metrics=a['metrics'],after_metrics=b['metrics']) for a,b in zip(reference,records[('pools-native',0)])]
    analysis=dict(means=report['means'],groups=report['groups'],work=work,queries=cases_compare,profile=study.binding(out/'profile.json'),identical_compact_pool_proof_bytes=True,
        next_target='Reuse the already computed source/assignment/cofactor in the 71 template publications. Query has just checked that exact canonical target; materialize repeats source containment, restriction and normalization. Bind immutable inputs, retain native verification and measure full costs.',
        limitations=['Early pool hits avoid search dispatch, not full-target verification. Some miss checks repeat during native fallback and remain charged.',
        'Two process orders show a local timing difference, not statistical significance or a robust end-to-end speedup. All native proof bytes and selected-container endpoints match compact reuse for pools-native.',
        'The profile is query-only and instrumented; cumulative timings overlap. Selected-container Python sizes omit sets, native allocations and other state.',
        'Pool-first recovery still has worse total query time and larger proof payload than compact reuse. No default solver or unrestricted-SAT bound changes.'])
    base.write(out/'analysis.json',analysis)
    sources={**sources,**{f:base.sha(f) for f in ('experiments/profile_cnf_pool_priority.py','experiments/validate_cnf_pool_priority.py')}}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        pool_priority=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json'),profile=study.binding(out/'profile.json'),hint_reload=study.binding(out/'hint-reload.json'),decision='Optional early existing-pool lookup without recovery preserves identical compact proof bytes and avoids twelve search dispatches. Recovery remains experimental; next remove duplicated template preparation.'))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,query_audits=attempts,paired_attempts=1140,profile_attempts=114,prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),partition_records=0,previous_partition_records=len(older_parts),reader_counts=readers,audits=audits,checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,
        limitations=['Both readers replay cumulative native and extension records and all 342 earlier partition sidecars; other earlier composed audits remain bound through immutable manifests.',
        'Alternative valid payloads remain in raw deltas; the cumulative union keeps earlier authoritative bytes. No new native proof rule or whole-input partition is introduced.'])
    base.write(out/'validation.json',v);print(base.encode({k:v[k] for k in ('passed','new_records','preserved_tables','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
