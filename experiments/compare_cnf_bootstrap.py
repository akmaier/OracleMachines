#!/usr/bin/env python3
"""Supplemental conditioning/candidate-acquisition control on the frozen 24 CNFs.

All arms share freshly charged depth-zero preparation under a policy allowing
remaining depth one. Ordinary restarts the whole original at depth one; external
splits preserve its depth-zero ancestors and expand one selected unresolved leaf.
"""
from collections import Counter,defaultdict
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments import cnf_bootstrap_conditioning as split
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted,FrontierIndex
from experiments.cnf_expanded_coverage import owner,expand
from experiments.cnf_route_composition import compose
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_subsumption_transfer import sha,load,key_sha,source_id,no_acquisition
from experiments.compare_cnf_complete_admission import rows,write,archive
from experiments.continue_cnf_transfer_split import restore_archive

PARENT=Path('experiments/results/cnf-lookahead-bank')
OPTIONS=dict(max_depth=1,probe_limit=4,learn_limit=4,clause_growth_limit=2)
MODES=('ordinary','first','size','enumerate')
FILES=['experiments/cnf_bootstrap_conditioning.py','experiments/compare_cnf_bootstrap.py',
       'solver/test_cnf_bootstrap_conditioning.py','solver/fixtures/trace-split.json']


def source_fingerprints(previous):
    result=dict(previous)
    paths=set(FILES)
    for module in list(sys.modules.values()):
        name=getattr(module,'__name__','');filename=getattr(module,'__file__',None)
        if name.startswith('experiments.') and filename and filename.endswith('.py'):
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT):paths.add(str(path.relative_to(ROOT)))
    result.update({p:sha(p) for p in paths})
    return result


def prepare(out,protocol):
    began=time.perf_counter();records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'seed';h=CompleteAdmissionInventory(path,**OPTIONS);split.initialize(h)
        try:
            for i,case in enumerate(protocol['cases']):
                h.set_admission_budget(256);h.counts=Counter();tick=time.perf_counter();root=None;leaf=None
                try:root=h._edge(case['source'],0)['key']
                except AdmissionExhausted:pass
                closed=root is not None and h._load(root)['summary']['closed']
                if root is not None and not closed:
                    leaves=FrontierIndex(h).frontier(root)
                    leaf=max(leaves,key=lambda k:(h._load(k)['profile']['shape']['literals'],k))
                candidates=split.choices(h,leaf,Counter(),4) if leaf else []
                records.append(dict(case=i,root=root,leaf=leaf,closed=closed,variables=candidates,
                    entered=len(h.admitted),probes=h.counts['probe_attempts'],seconds=time.perf_counter()-tick))
            patterns=len(rows(h))
        finally:h.close()
        entry=archive(path,out)
    result=dict(records=records,archive=entry,patterns=patterns,seconds=time.perf_counter()-began)
    write(out/'seed.json',result);return result


def routes_for(h,records):
    routes=SimpleNamespace(by_source=defaultdict(list))
    for record in records:split.attach(h,routes,record,Counter())
    return routes


def acquire(h,record):
    targets,_=split.verify(h,record,Counter());pending=[]
    for target,branch in zip(targets,record['branches'],strict=True):
        try:edge=h._edge(target,h._load(record['source'])['depth'])
        except AdmissionExhausted:pending.append(True)
        else:assert edge==branch['edge'];pending.append(False)
    return pending


def final_coverage(h,records,evidence):
    routes=routes_for(h,evidence)
    return [h._load(row['root']) is not None and compose(h,[row['root']],routes,Counter())[0][0] for row in records]


def replay(path,protocol,records,evidence):
    tick=time.perf_counter();before=sha(path);h=CompleteAdmissionInventory(path,**OPTIONS);h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with (no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')),
              patch('experiments.cnf_bootstrap_conditioning.discover_simplification',side_effect=AssertionError('Fresh assumptions forbidden'))):
            for key in rows(h):assert owner(h,key)._load(key) is not None
            saved={}
            for key,payload in h.db.execute(f'SELECT id,payload FROM {split.TABLE}'):
                record=load_json(payload);assert key==split.record_key(record);split.verify(h,record,Counter());saved[key]=record
            assert saved=={split.record_key(r):r for r in evidence}
            for case,row in zip(protocol['cases'],records,strict=True):
                assert source_id(case['source'])==row['source_sha256']
                assert h._canonical(case['source'],row['root_depth'])[2]==row['root']
            closed=final_coverage(h,records,evidence)
            assert all(b or not a['closed'] for a,b in zip(records,closed,strict=True))
            roots=[r['root'] for r,b in zip(records,closed,strict=True) if b]
            routes=routes_for(h,evidence);_,plan=compose(h,roots,routes,Counter())
            proof=expand(h,plan,roots,routes,Counter());checked=split.verify_positive(h,proof,roots,evidence,Counter())
            return dict(seconds=time.perf_counter()-tick,patterns=len(rows(h)),pairs=len(saved),queries=len(records),
                final_closed=closed,positive_steps=len(checked.justified),no_acquisition=True,proof=proof)
    finally:h.close();assert sha(path)==before


def load_json(value):
    import json
    return json.loads(value)


def worker(out,protocol,seed,mode):
    out.mkdir();began=time.perf_counter();records=[];evidence={}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';restore_archive(seed['archive'],path);h=CompleteAdmissionInventory(path,**OPTIONS);h.set_admission_budget(0)
        initial=rows(h)
        try:
            for key in initial:assert owner(h,key)._load(key) is not None
            setup=time.perf_counter()-began;queries_started=time.perf_counter()
            for case,old in zip(protocol['cases'],seed['records'],strict=True):
                tick=time.perf_counter();h.set_admission_budget(40);h.counts=Counter();counts=Counter();before=rows(h)
                root_depth=1 if mode=='ordinary' else 0
                root=h._canonical(case['source'],root_depth)[2]
                chosen=[];pending=[];ranked=[];candidate_seconds=0;closed=False;capped=False
                if mode=='ordinary':
                    try:edge=h._edge(case['source'],1)
                    except AdmissionExhausted:capped=True
                    else:assert edge['key']==root;closed=h._load(root)['summary']['closed']
                elif old['closed']:closed=True
                elif old['leaf']:
                    start=time.perf_counter();variables=list(old['variables'])
                    if mode=='size':
                        for variable in variables:
                            r=split.acquire_record(h,old['leaf'],variable,counts);evidence[split.record_key(r)]=r
                            ranked.append(dict(variable=variable,rank=split.size_rank(h,r,counts)))
                        variables=[min(ranked,key=lambda x:x['rank'])['variable']]
                    elif mode=='first':variables=variables[:1]
                    candidate_seconds+=time.perf_counter()-start
                    for variable in variables:
                        start=time.perf_counter();record=split.acquire_record(h,old['leaf'],variable,counts)
                        candidate_seconds+=time.perf_counter()-start;evidence[split.record_key(record)]=record
                        chosen.append(variable);pending.append(acquire(h,record))
                        closed=compose(h,[root],routes_for(h,evidence.values()),Counter())[0][0]
                        if closed:break
                    capped=any(any(p) for p in pending)
                after=rows(h);fresh=set(after)-set(before)
                assert before.items()<=after.items() and fresh<=h.admitted and len(h.admitted)<=40
                records.append(dict(case=old['case'],group=case['group'],source_sha256=source_id(case['source']),
                    root=root,root_depth=root_depth,closed=closed,capped=capped,chosen=chosen,ranked=ranked,pending=pending,
                    entered=len(h.admitted),stored=len(fresh),admitted_ids=sorted(map(key_sha,h.admitted)),
                    stored_ids=sorted(map(key_sha,fresh)),probes=h.counts['probe_attempts'],
                    counts=dict(h.counts),candidate_counts=dict(counts),admission_counts=dict(h.admission_counts),
                    candidate_seconds=candidate_seconds,seconds=time.perf_counter()-tick))
            elapsed=time.perf_counter()-queries_started;assert initial.items()<=rows(h).items()
            pattern_digest=key_sha(encode(sorted(rows(h).items())));new_patterns=len(rows(h))-len(initial)
        finally:h.close()
        saved=list(evidence.values());cold=replay(path,protocol,records,saved);entry=archive(path,out)
        result=dict(mode=mode,setup_seconds=setup,operation_seconds=elapsed,records=records,evidence=saved,
            covered=sum(r['closed'] for r in records),final_covered=sum(cold['final_closed']),
            entered=sum(r['entered'] for r in records),probes=sum(r['probes'] for r in records),stored=new_patterns,
            fresh_assumptions=sum(r['candidate_counts'].get('bootstrap_fresh_assumptions',0) for r in records),
            pairs=len(saved),pattern_digest=pattern_digest,archive=entry,cold=cold)
        write(out/'report.json',result);return result


def run(out):
    out.mkdir(exist_ok=False);old=load(PARENT/'validation.json');parent=load(PARENT/'protocol.json')
    for p,digest in old['source_fingerprints'].items():assert sha(p)==digest
    protocol=dict(parent=dict(path=str(PARENT/'protocol.json'),sha256=sha(PARENT/'protocol.json')),
        parent_validation_sha256=sha(PARENT/'validation.json'),cases=parent['cases'],options=OPTIONS,
        seed_remaining_depth=0,ordinary_query_depth=1,state_limit=40,candidate_limit=4,
        repetitions=2,orders=[MODES,tuple(reversed(MODES))],source_fingerprints=source_fingerprints(old['source_fingerprints']),
        rationale='Supplemental experiment after depth-zero saved-pair selection found 22 empty candidate pools. All 24 original inputs are reused without filtering.',
        limitations=['The common seed is rebuilt under max_depth=1 and queried initially at depth zero. Its work is charged; old archives are untouched.',
            'Ordinary restarts the whole original at depth one; external splits preserve depth-zero ancestors and expand one selected leaf. This is a workflow comparison, not a pure heuristic ablation.',
            'Recognition has 40 distinct states per query. At most four pairs/eight source assumptions are acquired separately; their propagation, checking and storage are charged.',
            'Only size ranking acquires every candidate before choosing one. First/enumerate acquire their pairs lazily.',
            'Structural coverage and unknown outcomes do not assert SAT/UNSAT truth. Synthetic adaptive data and two orders imply no universal efficiency guarantee.'])
    write(out/'protocol.json',protocol);seed=prepare(out,protocol)
    print(encode(dict(seed_patterns=seed['patterns'],eligible=sum(bool(r['variables']) for r in seed['records']),seed_seconds=seed['seconds'])),flush=True)
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';r=worker(dest,protocol,seed,mode)
            samples.append(dict(mode=mode,repeat=repeat,path=str(dest/'report.json'),sha256=sha(dest/'report.json')))
            print(encode({k:r[k] for k in ('mode','covered','final_covered','entered','stored','probes','fresh_assumptions','pairs','operation_seconds')}),flush=True)
    summary={}
    for mode in MODES:
        a,b=[load(x['path']) for x in samples if x['mode']==mode];assert a['pattern_digest']==b['pattern_digest']
        summary[mode]={**{k:a[k] for k in ('covered','final_covered','entered','stored','probes','fresh_assumptions','pairs')},
            'mean_setup_seconds':(a['setup_seconds']+b['setup_seconds'])/2,'mean_operation_seconds':(a['operation_seconds']+b['operation_seconds'])/2,
            'database_bytes':a['archive']['database_bytes'],'compressed_bytes':a['archive']['compressed_bytes']}
    write(out/'report.json',dict(protocol_sha256=sha(out/'protocol.json'),seed_sha256=sha(out/'seed.json'),samples=samples,summary=summary))
    print(encode(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
