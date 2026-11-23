#!/usr/bin/env python3
"""Replay conditional certificates, price hint reload, and preserve prior authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_unit_support as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_conditional_unit_support import extract,check_template,match
from experiments.cnf_conditional_unit_cache import compact,check_cache
from experiments.cnf_residual_dag import restrict
from experiments.cnf_conditioned_core import check_record as check_projection
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base=study.base;TABLES=inherited.TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases'])
    main=base.load(out/'report.json');supp=base.load(out/'compact-report.json');cp=study.bound(supp['protocol'])
    assert main['protocol']==study.binding(out/'protocol.json') and cp['original']==main['protocol']
    assert len(cases)==11 and len(main['samples'])==6 and len(supp['samples'])==4
    sources=cp['source_fingerprints']
    for f,h in sources.items():assert base.sha(f)==h,f
    old=base.load(study.PARENT/'validation.json');manifests=deepcopy(old['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(140,12442)
    exploration=study.bound(p['exploration']);bundle=study.bound(exploration['bundle']);prefix=study.read_zip(p['prefix'])
    previous=base.load(study.PARENT/'protocol.json');assert prefix==study.read_zip(previous['prefixes']['branch-original']['archive'])
    assert p['donor']==exploration['source'] and exploration['script_sha256']==base.sha('experiments/probe_cnf_conditional_unit_support.py')
    first=base.load(out/'exploration-first-report.json');assert first['script_sha256']==base.sha(out/'probe-first-version.py.txt')
    assert study.bound(first['bundle'])==bundle and study.read_zip(first['donor_delta'])==study.read_zip(exploration['donor_delta'])
    records={};new=Counter();alternatives=Counter();audits=[];hint_audits=[];attempts=0
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial)
        def merge(delta):
            for t,rows in delta.items():
                for k,v in rows:
                    if k in merged[t]:
                        assert json.loads(v)['answer']==json.loads(merged[t][k])['answer'];alternatives[t]+=v!=merged[t][k]
                    else:merged[t][k]=v;new[t]+=1
        def chronological(available,delta):
            for t,rows in delta.items():
                for k,v in rows:
                    assert k not in available[t]
                    if t==TABLES[0]:
                        proof=json.loads(v).get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available[t].keys()
                    available[t][k]=v
        donor_delta=study.read_zip(exploration['donor_delta']);merge(donor_delta)
        db=temp/'donor';study.restore(prefix,db,donor_delta);s=SnapshotResidualSolver(db)
        try:
            actual,counts=extract(s,p['donor']);assert actual==bundle and counts==exploration['extract_counts']
            for k,v in donor_delta[TABLES[0]]:assert s._read(k) is not None
            for row in exploration['samples']:
                matched=[i for i,e in enumerate(bundle['entries']) if match(row['source'],e['template'])]
                assert matched==row['matched']
                assert (set(map(tuple,exploration['whole_core']['source']))<=set(map(tuple,row['source'])))==row['whole_causal_core_contained']
        finally:s.close();db.unlink()
        for n,sample in enumerate(main['samples']+supp['samples']):
            data=study.bound(sample);rs=study.bound(data['queries']);hints=study.bound(data['hints']);delta=study.read_zip(data['delta']);prep=study.read_zip(data['preparation_delta'])
            policy=sample.get('policy',sample.get('mode'));assert len(rs)==66;attempts+=len(rs)
            if 'policy' in sample:assert data['policy']==policy and data['compact_protocol']==supp['protocol']
            db=temp/f'trial{n}';study.restore(prefix,db,delta)
            # Separately charge reading and checking persisted hints. Main worker
            # cold time replays answers only; it does not include this operation.
            tick=time.perf_counter();reloaded=base.load(data['hints']['path']);c=Counter()
            if policy in ('templates','compact'):
                if policy=='compact':check_cache(reloaded,c)
                else:
                    for e in reloaded['entries']:check_template(e['template'],c)
            elif policy=='causal':
                rd=SnapshotResidualSolver(db)
                try:
                    for core in reloaded:
                        cnf,_,key=rd._canonical(core['source']);assert key==core['root'];assert rd._read(key,cnf)['answer'] is False
                    c.update(rd.counts)
                finally:rd.close()
            else:assert reloaded==[]
            hint_audits.append(dict(sample=sample,hint_binding=data['hints'],seconds=time.perf_counter()-tick,counts=dict(c)))
            s=SnapshotResidualSolver(db)
            try:
                if policy=='templates':assert hints==bundle
                elif policy=='compact':assert hints==compact(bundle)
                elif policy=='causal':
                    for core,projection in zip(hints,data['preparation']['projections']):
                        check_projection(s,projection['record'])
                        assert set(map(tuple,core['source']))<=set(map(tuple,projection['record']['source']))
                        assert core['origin']==projection['record']['root']
                        cnf,_,key=s._canonical(core['source']);assert key==core['root'];assert s._read(key,cnf)['answer'] is False
                available={t:dict(prefix[t]) for t in study.TABLES};chronological(available,prep)
                for r,(case,q) in zip(rs,((case,q) for case in cases for q in case['queries'])):
                    assert (r['case'],r['template'],r['assignment'])==(case['index'],q['template'],q['assignment'])
                    additions={t:[[k,dict(delta[t])[k]] for k in r['new_ids'][t]] for t in study.TABLES};chronological(available,additions)
                    source=restrict(case['source'],dict(q['assignment']));cnf,_,key=s._canonical(source);assert key==r['root']
                    node=s._read(key,cnf);assert node is not None and r['status']==('sat' if node['answer'] else 'unsat')
                    if r['route']=='template':assert match(case['source'],hints['entries'][q['template']]['template'])
                    if r['route']=='causal':assert set(map(tuple,hints[q['template']]['source']))<=set(map(tuple,source))
                    assert r['expanded_nodes']<=p['node_limit'] and key in available[TABLES[0]]
                for t in study.TABLES:assert available[t]==dict(prefix[t]+delta[t])
                for k,v in delta[TABLES[0]]:assert s._read(k) is not None
                audits.append(dict(sample=n,counts=dict(s.counts)))
            finally:s.close();db.unlink()
            merge(delta);records[(policy,sample['repeat'],'cache' if 'policy' in sample else 'main')]=rs
            summary=data['summary'];assert summary['statuses']==dict(Counter(r['status'] for r in rs))=={'sat':7,'unsat':59}
            assert summary['routes']==dict(Counter(r['route'] for r in rs))
            assert summary['expanded_nodes']==sum(r['expanded_nodes'] for r in rs)
        reference=records[('templates',0,'main')]
        for key,rs in records.items():
            assert [(r['root'],r['status']) for r in rs]==[(r['root'],r['status']) for r in reference]
            if key[0]!='native':assert [r['route']=='native' for r in rs]==[r['route']=='native' for r in reference]
        main_delta=study.read_zip(base.load(out/'templates-0/report.json')['delta'])
        for name in ('templates-1','cache-templates-0','cache-templates-1','cache-compact-0','cache-compact-1'):
            assert study.read_zip(base.load(out/name/'report.json')['delta'])==main_delta
        assert attempts==660
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
    base.write(out/'hint-reload.json',dict(samples=hint_audits,limitations=['Diagnostic serial read and validation costs, outside original worker timing. Causal reload includes reader construction and native proof checks; self-contained templates require no donor database. Query-time containment and native publication are separately included in query costs.']))
    fallback=[dict(r,source=cases[r['case']]['source']) for r in reference if r['route']=='native']
    fallback.sort(key=lambda r:(r['expanded_nodes'],r['seconds']),reverse=True)
    analysis=dict(main=main['means'],compact=supp['means'],fallback=fallback,templates=[dict(clauses=len(e['template']['clauses']),literals=sum(map(len,e['template']['clauses'])),assumptions=len(e['template']['assumptions']),path_assumptions=len(e['path_assignment'])) for e in bundle['entries']],
        next_target='Explain the highest-expansion support-missing cofactor before adding discovery. Preserve its original guard, prefix, all preparation IDs and preceding query IDs; distinguish automatic map discovery from recovery after a reason deletion.',
        limitations=['All 40 template hits also hit the conditioned causal baseline. This provides no incremental coverage over that stronger baseline, and no whole-input verdict.',
        'Compaction removes diagnostic metadata only from the active hint cache. All donor proofs and extraction provenance remain archived, and full native target proofs still accumulate.',
        'Endpoint Python size omits set contents, SQLite/native allocator memory and bank instance internals; it is a selected-container diagnostic, not total live memory. No RSS improvement is claimed.',
        'The supplied-guard comparison excludes automatic guard selection and discovery of variable correspondence. Complete-worker measurements omit persisted-hint revalidation, which is separately recorded.'])
    base.write(out/'analysis.json',analysis)
    sources={**sources,__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    checkpoint=deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        conditional_unit_support=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),compact_protocol=study.binding(out/'compact-protocol.json'),compact_report=study.binding(out/'compact-report.json'),analysis=study.binding(out/'analysis.json'),hint_reload=study.binding(out/'hint-reload.json'),
            decision='Optional guarded unit refutations and provenance-free active cache; same conditional coverage as conditioned causal cores on exposed edits. Preserve full native checking, all donor provenance and unsupported endpoint obligations.'))
    base.write(out/'checkpoint.json',checkpoint)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,query_audits=attempts,
        prior_tables={t:len(v) for t,v in initial.items()},preserved_tables={t:len(v) for t,v in merged.items()},new_records=dict(new),alternative_payload_observations=dict(alternatives),
        partition_records=0,previous_partition_records=len(older_parts),reader_counts=readers,audits=audits,checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,
        limitations=['Cumulative native/extension records and all 342 prior partition sidecars replayed with both readers. Other earlier composed audits are inherited through immutable manifests.',
        'Alternative valid native payloads remain in trial deltas; the union preserves earlier authoritative bytes. No new whole-input partition record is introduced.'])
    base.write(out/'validation.json',v);print(base.encode({k:v[k] for k in ('passed','new_records','preserved_tables','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
