#!/usr/bin/env python3
"""Matched occurrence versus watched propagation with all retained clauses active."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_watched_learning as e
from experiments import compare_cnf_selective_learning as previous
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows
PARENT=Path('experiments/results/cnf-admitted-learning')
FILES=('experiments/cnf_watched_learning.py','experiments/compare_cnf_watched_learning.py','experiments/audit_cnf_watched_learning.py','experiments/validate_cnf_watched_learning.py','solver/test_cnf_watched_learning.py')
MODES=('all','watched')
LIMIT=2000


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');old=load(PARENT/'protocol.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=old['panel'],baseline_records=binding(PARENT/'all-0/report.json'),references=old['references'],transport=old['transport'],source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['all','watched'],['watched','all']],node_limit=LIMIT,limitations=[
        'Exposed-policy development on the same 16 edited targets from eight previously refuted parents. No target bytes or labels change; no fresh external transfer or representative sample.',
        'Both modes activate all surviving clauses with the same target-only proposal and 2000 entered contexts. Candidate replaces per-occurrence partial-assignment bookkeeping with two watches, retaining minimum actual clause order. Complete-model counts update only when values differ from the proposal. Trace equality is checked, not assumed.',
        'All surviving derivations remain checked, copied and persisted. No admission cap, proof pruning, restart, activity or production default change. Watch initialisation, movement, candidate scanning, complete-model updates and proof composition are charged.',
        'Two alternating fresh-process pairs charge input/hash reads, parent reads/checks, selective transport, augmentation, search, substitution, checks, writes, three compressions and replay. Historical parent acquisition, imports/startup, reports and independent audits are additional.',
        'Warm and two rounds labelled cold deserialize fresh objects within the same worker; these are not independent cold-start processes and do not flush OS caches. Additional fresh-worker replay validates target-only checking separately.',
        'Coverage, remaining interactions, proof sizes and replay are retained alongside time and memory. Equal finite traces are not an efficient decomposition of every CNF or a polynomial unrestricted-SAT guarantee.']))



def discover(row,mode,counts):
    source,proof=previous.parent_data(row,counts)
    return (e.selective.solve if mode=='all' else e.solve)(source,proof,row['source'],counts,node_limit=LIMIT)


def check(source,proof,counts=None):return e.check_result(source,proof,counts)


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=load(out/'protocol.json');rows=[r for r in source_rows(p) if r['expansion_case']];input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter()
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,diag=discover(row,mode,counts);acquisition=time.perf_counter()-start;discovery_counts=dict(counts)
        start=time.perf_counter();got=check(row['source'],proof,counts);checking=time.perf_counter()-start
        start=time.perf_counter();write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],kind=row['kind'],parent_id=row['parent_id'],status='unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'),result=got,diagnostic=diag,discovery_counts=discovery_counts,counts=dict(counts),acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    start=time.perf_counter();warm=Counter()
    for row in source_rows(p):
        if row['expansion_case']:check(row['source'],load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;start=time.perf_counter();cold=Counter()
    for _ in range(2):
        for row in source_rows(p):
            if row['expansion_case']:check(row['source'],load(dest/(row['id']+'.json')),cold)
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();evidence=[None]*len(proofs)
    for name,data in (('certificates',proofs),('discovery',evidence),('combined',dict(proofs=proofs,evidence=evidence))):(dest/(name+'.json.gz')).write_bytes(gzip.compress(encode(data).encode(),mtime=0))
    persistence=time.perf_counter()-start
    write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(r['id']+'.json')).stat().st_size for r in rows),compressed_bytes={name:(dest/(name+'.json.gz')).stat().st_size for name in ('certificates','discovery','combined')},peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    samples=[]
    for i,order in enumerate(load(out/'protocol.json')['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**binding(dest/'report.json'),mode=mode,repeat=i));print(mode,i,load(dest/'report.json')['complete_seconds'],flush=True)
    write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
