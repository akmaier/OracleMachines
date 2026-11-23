#!/usr/bin/env python3
"""Price guarded unit templates against native solving and conditioned causal cores."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import json,random,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_prefix as prior
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_joint_prefix import reused_joint_prefix
from experiments.cnf_conditional_unit_support import extract,match,materialize
from experiments.cnf_support_plan import CausalPlan
from experiments.cnf_causal_support import CausalSupportExtractor,CausalCoreBank
from experiments.cnf_conditioned_core import project_core,check_record as check_projection
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import restrict
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.compare_cnf_transported_partition import prior as transport_prior
base=prior.base;PARENT=Path('experiments/results/cnf-joint-prefix');MODES=('native','causal','templates')
binding=prior.binding;bound=prior.bound;TABLES=prior.TABLES;read_zip=prior.read_zip;write_zip=prior.write_zip;restore=prior.restore;tables=prior.tables
FILES=('experiments/cnf_conditional_unit_support.py','experiments/probe_cnf_conditional_unit_support.py','experiments/compare_cnf_conditional_unit_support.py','solver/test_cnf_conditional_unit_support.py')


def prepare(out):
    assert not (out/'protocol.json').exists();exploration=base.load(out/'exploration.json');bundle=bound(exploration['bundle']);parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    sources=[];seen=set()
    def add(label,source):
        identity=tuple(sorted(map(tuple,source)))
        if identity not in seen:seen.add(identity);sources.append(dict(label=label,source=source))
    for row in exploration['samples']:add(row['label'],row['source'])
    rng=random.Random(202611230833);donor=exploration['source']
    for i in range(4):
        removed=set(rng.sample(range(len(donor)),3));add(f'random-three-deletions-{i}',[cl for j,cl in enumerate(donor) if j not in removed])
    add('empty-positive-control',[])
    cases=[dict(index=i,**row,queries=[dict(template=j,assignment=e['template']['assumptions']) for j,e in enumerate(bundle['entries'])]) for i,row in enumerate(sources)]
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),exploration=binding(out/'exploration.json'),cases=binding(out/'cases.json'),
        prefix=exploration['prefix'],donor=donor,node_limit=256,orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Every worker restores the same historical prefix and acquires the donor with the preceding solver. No final union or target answer is seeded. Donor acquisition and all hint preparation are charged.',
        'These are supplied conditional queries, not whole-query answers. Guards and donor are exposed and supplied identically to all arms; automatic guard selection, donor discovery and variable correspondence are not measured.',
        'The causal baseline materializes the existing whole causal core, conditions it under each supplied guard, acquires and slices each conditional core, then uses the existing CausalCoreBank. Template preparation lifts original leaf reasons without publishing cores.',
        'Targeted support deletions, four fixed-seed nearby deletions and an empty positive control are retained. Repeated roots and cached answers remain visible. This is not an external benchmark or independent SAT coverage theorem.',
        'Two opposite serial process orders. Complete-worker time includes preparation, checking, warm reads, proof/hint serialization, cold replay and reconstruction, excluding interpreter startup. No whole-process peak memory improvement is inferred.',
        'No default solver policy, proof rule, native schema or unrestricted complexity bound changes. Missing support falls back to the same bounded native acquisition.']))


def prepare_hints(s,p,mode):
    if mode=='native':return [],[],{}
    if mode=='templates':
        bundle,counts=extract(s,p['donor']);return bundle,[],dict(extract=counts,solver=dict(s.counts))
    cnf,names,root=s._canonical(p['donor']);plan=CausalPlan(s);core=plan.prepare(root);plan.emit(root)
    source=[[(1 if l>0 else -1)*names[abs(l)-1] for l in cnf[i]] for i in core['indices']];whole=dict(source=source,root=core['root'])
    statistics=dict(plan=dict(plan.counts),initial_solver=dict(s.counts),projections=[]);cores=[]
    guards=bound(bound(p['exploration'])['bundle'])['entries']
    for e in guards:
        fixed=dict(e['template']['assumptions']);c=Counter();s.counts=Counter();record=project_core(s,whole,fixed,c)
        r=acquire(s,record['source'],p['node_limit']);assert r['status']=='unsat';acquisition=dict(s.counts)
        check_projection(s,record,c);extractor=CausalSupportExtractor(s);small=extractor.extract(r['result']['root'])
        local,oldnames,_=s._canonical(record['source'])
        hint=dict(source=[[(1 if l>0 else -1)*oldnames[abs(l)-1] for l in local[i]] for i in small['indices']],root=small['root'],origin=r['result']['root'])
        cores.append(hint);statistics['projections'].append(dict(record=record,acquisition=acquisition,extractor=dict(extractor.counts),checks=dict(c),solver=dict(s.counts)))
    return cores,[CausalCoreBank(s,[core]) for core in cores],statistics


def query(s,case,q,mode,hints,banks,budget):
    tick=time.perf_counter();s.counts=Counter();counts=Counter();fixed=dict(q['assignment']);cofactor=restrict(case['source'],fixed,counts);cnf,_,key=s._canonical(cofactor)
    old=s._read(key,cnf,purpose='conditional_query');route='cached';result=None
    if old is None:
        route='native'
        if mode=='templates':
            t=hints['entries'][q['template']]['template']
            if match(case['source'],t,counts):
                materialize(s,case['source'],t,context=q['assignment'],counts=counts);route='template'
        elif mode=='causal':
            bank=banks[q['template']];before=Counter(bank.counts);got=bank.reuse(cofactor);counts.update(bank.counts-before)
            if got is not None:route='causal'
        if route=='native':
            preliminary=dict(s.counts);result=acquire(s,cofactor,budget);counts.update({'preliminary_'+k:v for k,v in preliminary.items()})
    node=s._read(key,cnf,purpose='conditional_result') if result is None or result['result'] is not None else None
    status='unresolved' if node is None else 'sat' if node['answer'] else 'unsat'
    return dict(case=case['index'],label=case['label'],template=q['template'],assignment=q['assignment'],root=key,status=status,route=route,
        counts=dict(counts),metrics=dict(s.counts),expanded_nodes=s.counts.get('expanded_nodes',0),seconds=time.perf_counter()-tick)


def cold(path,cases,records):
    tick=time.perf_counter();readers={}
    for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
        rd=cls(path)
        try:
            for r in records:
                if r['status']=='unresolved':continue
                source=restrict(cases[r['case']]['source'],dict(r['assignment']));cnf,_,key=rd._canonical(source);assert key==r['root']
                node=rd._read(key,cnf);assert node is not None and ('sat' if node['answer'] else 'unsat')==r['status']
            readers[cls.__name__]=dict(rd.counts)
        finally:rd.close()
    return dict(seconds=time.perf_counter()-tick,readers=readers)


def worker(out,p,mode):
    began=time.perf_counter();out.mkdir();cases=bound(p['cases']);prefix=read_zip(p['prefix'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter();restore(prefix,path);restore_seconds=time.perf_counter()-tick
        tick=time.perf_counter();s=ConsequencePrioritySolver(path);setup_seconds=time.perf_counter()-tick
        try:
            tick=time.perf_counter()
            with fused_preimages(),reused_joint_prefix():
                mode_setup=time.perf_counter()-tick;donor=acquire(s,p['donor'],p['node_limit']);assert donor['status']=='unsat'
                s.counts=Counter();tick=time.perf_counter();hints,banks,preparation=prepare_hints(s,p,mode);prepare_seconds=time.perf_counter()-tick
                prepared=tables(s);records=[];marks={t:len(v) for t,v in prepared.items()}
                for case in cases:
                    for q in case['queries']:
                        r=query(s,case,q,mode,hints,banks,p['node_limit']);current=tables(s)
                        r['new_ids']={t:[k for k,v in current[t][marks[t]:]] for t in TABLES};marks={t:len(v) for t,v in current.items()};records.append(r)
                tick=time.perf_counter()
            mode_setup+=time.perf_counter()-tick;final=tables(s)
            memory=transport_prior.prior.deep_size((s.checked,s.negative_pool,s.witness_pool,hints,banks))
            tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm search')):
                for r in records:
                    if r['status']=='unresolved':continue
                    assert s._read(r['root'])['answer']==(r['status']=='sat')
            warm_seconds=time.perf_counter()-tick;assert tables(s)==final
            delta={t:final[t][len(prefix[t]):] for t in TABLES};prep_delta={t:prepared[t][len(prefix[t]):] for t in TABLES}
        finally:s.close()
        audited=cold(path,cases,records);database_bytes=path.stat().st_size
        tick=time.perf_counter();archive=write_zip(out/'delta.json.gz',delta);prep_archive=write_zip(out/'preparation-delta.json.gz',prep_delta);base.write(out/'hints.json',hints);persistence=time.perf_counter()-tick
        tick=time.perf_counter();rebuilt=Path(td)/'rebuilt';restore(prefix,rebuilt,read_zip(archive));rebuild=time.perf_counter()-tick;replayed=cold(rebuilt,cases,records)
    base.write(out/'queries.json',records)
    summary=dict(mode=mode,attempts=len(records),statuses=dict(Counter(r['status'] for r in records)),routes=dict(Counter(r['route'] for r in records)),
        query_seconds=sum(r['seconds'] for r in records),expanded_nodes=sum(r['expanded_nodes'] for r in records),donor_seconds=donor['seconds'],prepare_seconds=prepare_seconds,
        preparation_and_queries=prepare_seconds+sum(r['seconds'] for r in records),restore_seconds=restore_seconds,setup_seconds=setup_seconds,mode_setup_seconds=mode_setup,warm_seconds=warm_seconds,
        cold_seconds=audited['seconds'],reconstruction_seconds=rebuild+replayed['seconds'],persistence_seconds=persistence,
        new_records={t:len(v) for t,v in delta.items()},new_payload_bytes=sum(len(k.encode())+len(v.encode()) for rows in delta.values() for k,v in rows),
        proof_delta_compressed_bytes=archive['compressed_bytes'],hint_bytes=(out/'hints.json').stat().st_size,checked_python_bytes=memory,database_bytes=database_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),complete_worker_seconds=time.perf_counter()-began)
    base.write(out/'report.json',dict(summary=summary,donor=donor,preparation=preparation,queries=binding(out/'queries.json'),hints=binding(out/'hints.json'),delta=archive,preparation_delta=prep_archive,cold=audited,reconstructed=replayed))
    print(base.encode(summary),flush=True)


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        rows=[bound(s)['summary'] for s in samples if s['mode']==mode]
        summary[mode]={k:sum(r[k] for r in rows)/len(rows) for k in rows[0] if type(rows[0][k]) in (int,float)}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,means=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
