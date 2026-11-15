#!/usr/bin/env python3
"""Frozen new-input comparison of size ranking, lookahead and bank reuse."""
from collections import Counter,defaultdict
import gzip
import json
from pathlib import Path
import random
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_lookahead_bank import LookaheadInventory,scout_candidates,TABLE
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted,FrontierIndex
from experiments.cnf_trace_split import candidates,verify,attach
from experiments.cnf_route_composition import compose
from experiments.cnf_expanded_coverage import expand,owner
from experiments.cnf_projection_bridge import verify_positive
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_subsumption_transfer import sha,load,key_sha,source_id,no_acquisition
from experiments.compare_cnf_complete_admission import write,rows,archive
from experiments.continue_cnf_transfer_split import restore_archive

OPTIONS=dict(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
MODES=('size','lookahead_recompute','lookahead_reuse','enumerate')
SEED=20261115214950
FILES=['experiments/cnf_lookahead_bank.py','experiments/compare_cnf_lookahead.py','solver/test_cnf_lookahead_bank.py']


def corpus():
    rng=random.Random(SEED);cases=[]
    def random_cnf(n,density):
        return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(n*density))]
    for n in (24,36,48,60):
        for density in (3.8,4.1,4.25,4.4,4.6):
            cases.append(dict(group='random_3cnf',size=n,density=density,source=random_cnf(n,density)))
    for i in range(4):
        n=(36,48,48,60)[i];source=random_cnf(n,4.25)
        source.extend([[-n-j,n+j+1] for j in range(1,9)])
        if i%2:source.extend([[1,n+1],[-n-9,2],[-2,n+4,3]])
        cases.append(dict(group='connected_binary_mixture' if i%2 else 'disjoint_binary_mixture',size=n,source=source))
    assert len({source_id(x['source']) for x in cases})==24
    return cases


def prepare(out,protocol):
    tick=time.perf_counter();records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'seed';h=CompleteAdmissionInventory(path,**OPTIONS)
        for table in ('cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            h.db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit()
        try:
            for i,case in enumerate(protocol['cases']):
                began=time.perf_counter();h.set_admission_budget(256);h.counts=Counter();root=None;ranked=[];leaf=None
                try:root=h._edge(case['source'],0)['key']
                except AdmissionExhausted:pass
                closed=root is not None and h._load(root)['summary']['closed']
                if root is not None and not closed:
                    frontier=FrontierIndex(h).frontier(root)
                    leaf=max(frontier,key=lambda k:(h._load(k)['profile']['shape']['literals'],k))
                    ranked=candidates(h,leaf,SimpleNamespace(by_source=defaultdict(list)),Counter(),candidate_limit=4)
                records.append(dict(case=i,root=root,closed=closed,leaf=leaf,ranked=ranked,
                    entered=len(h.admitted),probes=h.counts['probe_attempts'],counts=dict(h.counts),seconds=time.perf_counter()-began))
            nodes=len(rows(h))
        finally:h.close()
        entry=archive(path,out)
    result=dict(records=records,archive=entry,patterns=nodes,seconds=time.perf_counter()-tick)
    write(out/'seed.json',result);return result


def routes_for(h,records):
    routes=SimpleNamespace(by_source=defaultdict(list))
    for record in records:attach(h,routes,record,Counter())
    return routes


def acquire(h,record):
    targets,_=verify(h,record,Counter());pending=[]
    for target,edge in zip(targets,record['edges'],strict=True):
        try:actual=h._edge(target,h._load(record['source'])['depth'])
        except AdmissionExhausted:pending.append(True)
        else:
            assert actual==edge;pending.append(False)
    return pending


def replay(path,protocol,seed,records,evidence):
    tick=time.perf_counter();before=sha(path);h=LookaheadInventory(path,**OPTIONS);h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')):
            for key in rows(h):assert owner(h,key)._load(key) is not None
            bank=list(h.db.execute(f'SELECT id,payload FROM {TABLE}'))
            for key,payload in bank:h.check_bank_row(key,payload)
            routes=routes_for(h,evidence)
            roots=[]
            for i,(case,old,row) in enumerate(zip(protocol['cases'],seed['records'],records,strict=True)):
                assert row['case']==old['case']==i and row['source_sha256']==source_id(case['source'])
                if old['root'] is None:assert not row['closed'];continue
                assert h._canonical(case['source'],0)[2]==old['root']
                # Later cases can add shared closure; a previous positive must persist.
                now,plan=compose(h,[old['root']],routes,Counter())
                if row['closed']:assert now==[True];roots.append(old['root'])
            _,plan=compose(h,roots,routes,Counter());proof=expand(h,plan,roots,routes,Counter())
            checked=verify_positive(h,proof,roots,[[],[],[],evidence,[]],[],Counter())
            return dict(seconds=time.perf_counter()-tick,patterns=len(rows(h)),bank_entries=len(bank),
                queries=len(records),positive_steps=len(checked.justified),no_acquisition=True)
    finally:h.close();assert sha(path)==before


def worker(out,protocol,seed,mode):
    out.mkdir();tick=time.perf_counter();records=[];evidence=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';restore_archive(seed['archive'],path);h=LookaheadInventory(path,**OPTIONS);h.set_admission_budget(0)
        initial=rows(h)
        try:
            # All arms pay the same cold history check before querying.
            for key in initial:assert owner(h,key)._load(key) is not None
            setup=time.perf_counter()-tick;began=time.perf_counter()
            for case,old in zip(protocol['cases'],seed['records'],strict=True):
                start=time.perf_counter();h.set_admission_budget(40);h.counts=Counter();h.prepared.counts=Counter()
                h.reuse_probe_bank=True;before=rows(h);ranked=old['ranked'];observations=[];chosen=[];pending=[]
                closed=old['closed'];scout_counts={};scout_seconds=0
                if ranked and not closed:
                    if mode.startswith('lookahead'):
                        st=time.perf_counter();observations=scout_candidates(h,ranked);scout_seconds=time.perf_counter()-st
                        scout_counts=dict(h.counts);chosen=[observations[0]['record']]
                        h.reuse_probe_bank=mode=='lookahead_reuse'
                    elif mode=='size':chosen=[ranked[0]['record']]
                    else:chosen=[r['record'] for r in ranked]
                    attempted=[]
                    for record in chosen:
                        pending.append(acquire(h,record));attempted.append(record);evidence.append(record)
                        routes=routes_for(h,evidence)
                        closed=compose(h,[old['root']],routes,Counter())[0][0]
                        if closed:break
                    chosen=attempted
                after=rows(h);fresh=set(after)-set(before)
                assert before.items()<=after.items() and fresh<=h.admitted and len(h.admitted)<=40
                records.append(dict(case=old['case'],group=case['group'],source_sha256=source_id(case['source']),
                    closed=closed,eligible=bool(ranked),chosen=chosen,observations=observations,pending=pending,
                    entered=len(h.admitted),stored=len(fresh),admitted_ids=sorted(map(key_sha,h.admitted)),
                    probes=h.counts['probe_attempts'],scout_seconds=scout_seconds,scout_counts=scout_counts,
                    counts=dict(h.counts),admission_counts=dict(h.admission_counts),seconds=time.perf_counter()-start))
            elapsed=time.perf_counter()-began;assert initial.items()<=rows(h).items()
            patterns=len(rows(h));bank=h.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0]
            pattern_digest=key_sha(encode(sorted(rows(h).items())))
        finally:h.close()
        cold=replay(path,protocol,seed,records,evidence);entry=archive(path,out)
        result=dict(mode=mode,setup_seconds=setup,operation_seconds=elapsed,records=records,evidence=evidence,
            covered=sum(r['closed'] for r in records),entered=sum(r['entered'] for r in records),
            probes=sum(r['probes'] for r in records),stored=patterns-len(initial),bank_entries=bank,
            pattern_digest=pattern_digest,archive=entry,cold=cold)
        write(out/'report.json',result);return result


def run(out):
    out.mkdir(exist_ok=False);old=load('experiments/results/cnf-transfer-split/validation.json')
    for p,digest in old['source_fingerprints'].items():assert sha(p)==digest
    cases=corpus();legacy='experiments/results/cnf-retained-plans-full/report.json'
    known={source_id(c['source']) for c in load(legacy)['cases']}
    previous='experiments/results/cnf-subsumption-transfer/protocol.json'
    known.update(source_id(c['source']) for c in load(previous)['cases'])
    assert all(source_id(c['source']) not in known for c in cases)
    protocol=dict(seed=SEED,cases=cases,options=OPTIONS,pipeline_state_limit=40,seed_state_limit=256,
        parent_validation_sha256=sha('experiments/results/cnf-transfer-split/validation.json'),
        novelty_parents={p:sha(p) for p in (legacy,previous)},
        source_fingerprints={**old['source_fingerprints'],**{p:sha(p) for p in FILES}},
        modes=MODES,repetitions=2,orders=[MODES,tuple(reversed(MODES))],
        score='One profile per cofactor: unresolved component count, maximum support, literal sum, then prior rank.',
        limitations=['All 24 sources and the score are frozen before acquisition; synthetic random and binary mixtures only.',
            'Seed acquisition and its retained evidence are shared preprocessing costs, not free work.',
            'Lookahead and acquisition share 40 distinct admissions; count reentries, verification, serialization and I/O separately.',
            'No new SAT/UNSAT verdict, uniform efficiency claim or peak-RAM measurement. Recognition outcomes are policy-relative.'])
    write(out/'protocol.json',protocol);seed=prepare(out,protocol)
    print(json.dumps(dict(seed_covered=sum(r['closed'] for r in seed['records']),eligible=sum(bool(r['ranked']) for r in seed['records']),seed_patterns=seed['patterns'],seed_seconds=seed['seconds'])),flush=True)
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';r=worker(dest,protocol,seed,mode)
            samples.append(dict(mode=mode,repeat=repeat,path=str(dest/'report.json'),sha256=sha(dest/'report.json')))
            print(json.dumps({k:r[k] for k in ('mode','covered','entered','stored','probes','bank_entries','operation_seconds')}),flush=True)
    summary={}
    for mode in MODES:
        arms=[load(x['path']) for x in samples if x['mode']==mode];a,b=arms
        assert a['pattern_digest']==b['pattern_digest']
        summary[mode]={**{k:a[k] for k in ('covered','entered','stored','probes','bank_entries')},
            'mean_setup_seconds':(a['setup_seconds']+b['setup_seconds'])/2,
            'mean_operation_seconds':(a['operation_seconds']+b['operation_seconds'])/2,
            'database_bytes':a['archive']['database_bytes'],'compressed_bytes':a['archive']['compressed_bytes']}
    a=load(out/'lookahead_reuse-0/report.json');b=load(out/'lookahead_recompute-0/report.json')
    assert a['pattern_digest']==b['pattern_digest']
    assert [r['chosen'] for r in a['records']]==[r['chosen'] for r in b['records']]
    write(out/'report.json',dict(protocol_sha256=sha(out/'protocol.json'),seed_sha256=sha(out/'seed.json'),samples=samples,summary=summary))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
