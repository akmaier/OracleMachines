#!/usr/bin/env python3
"""Matched charged search, resolution knowledge retention and replay."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_resolution_learning as e
from experiments import cnf_linear_unit_proof as baseline
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows
PARENT=Path('experiments/results/cnf-linear-unit-proof')
MODES=('baseline','learning')
FILES=('experiments/cnf_resolution_learning.py','experiments/compare_cnf_resolution_learning.py','experiments/audit_cnf_resolution_learning.py','experiments/validate_cnf_resolution_learning.py','solver/test_cnf_resolution_learning.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');old=load(PARENT/'larger/protocol.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=old['panel'],descriptions=old['descriptions'],baseline_records=binding(PARENT/'larger/linear-0/report.json'),references=binding(PARENT/'larger/references.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','learning'],['learning','baseline']],node_limit=20000,limitations=[
        'Development on the already exposed eight larger originals and eight related controls. No new external transfer or representative coverage claim. Preserve all old models, counterexamples, proof formats and source bytes.',
        'Baseline is unchanged unit propagation/disjoint first-flip search with preorder refutations. Candidate implements standard first-UIP resolution learning, nonchronological backjumping, conflict-based variable activity, phase saving and binary decisions. This bundled policy change is not an isolated learning ablation or new tractability theorem. Both cap entered contexts at 20000, but work per context differs.',
        'Every learned clause has a checked resolution derivation and exact claimed clause; it is globally implied by the source and can prune later contexts. Complete SAT models and derived empty clauses grant authority. A budget-exhausted run remains unknown even though its retained clauses are checked knowledge.',
        'All learned clauses and derivations survive SAT and unknown outcomes and are persisted/rechecked. Input reads and hashes, proposer/index creation, activity and undo work, resolution, acquisition/internal and explicit checks, writes, three compressions, warm and two cold reload/checks are charged. Imports/startup, reporting metadata and independent audits are additional; no search state survives replay and OS caches are not flushed.',
        'Two fresh-process alternating pairs are measured. Prior Z3/portfolio references are preserved audit results, not discovery inputs or matched solver speed comparisons. Old 36-input and constructed panels are separately rechecked.',
        'Guarded knowledge transport permits clause-index changes and deletion of unused original clauses only when every actually referenced original clause survives exactly. It rechecks old and target proofs, never transports SAT authority, and never invokes search. This is same-variable source-premise reuse, not arbitrary semantic equivalence or renaming.',
        'Initial fixed-branch and activity-based development probes and their exact source versions are retained. No production default changes. Learned clause count, width, source guards, proof size, recognition/preprocessing and unrestricted expansion remain explicit obligations.']))


def discover(source,mode,counts):
    proof,diag=(baseline.solve(source,counts) if mode=='baseline' else e.solve(source,counts))
    return dict(engine=mode,proof=proof),None,diag


def check(source,proof,counts=None):
    if type(proof) is not dict or set(proof)!={'engine','proof'}:raise ValueError('Invalid comparison proof')
    if proof['engine']=='baseline':return baseline.check_result(source,proof['proof'],counts)
    if proof['engine']=='learning':return e.check_result(source,proof['proof'],counts)
    raise ValueError('Unknown proof engine')


def check_evidence(source,evidence,counts=None):
    if evidence is not None:raise ValueError('Unexpected evidence sidecar')
    return dict(conditional_exclusions=0)


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=load(out/'protocol.json');rows=source_rows(p);input_seconds=time.perf_counter()-started;cases=[];proofs=[];evidences=[];total=Counter();phases=Counter()
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,evidence,diag=discover(row['source'],mode,counts);acquisition=time.perf_counter()-start;discovery_counts=dict(counts)
        start=time.perf_counter();got=check(row['source'],proof,counts);check_evidence(row['source'],evidence,counts);checking=time.perf_counter()-start
        start=time.perf_counter();write(dest/(str(row['id'])+'.json'),proof);writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],status='unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'),result=got,diagnostic=diag,counts=dict(counts),discovery_counts=discovery_counts,acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);evidences.append(evidence);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    start=time.perf_counter();write(dest/'discovery.json',evidences);phases['writing_seconds']+=time.perf_counter()-start
    start=time.perf_counter();warm=Counter()
    for row,ev in zip(source_rows(p),load(dest/'discovery.json')):check(row['source'],load(dest/(str(row['id'])+'.json')),warm);check_evidence(row['source'],ev,warm)
    warm_seconds=time.perf_counter()-start;start=time.perf_counter();cold=Counter()
    for _ in range(2):
        for row,ev in zip(source_rows(p),load(dest/'discovery.json')):check(row['source'],load(dest/(str(row['id'])+'.json')),cold);check_evidence(row['source'],ev,cold)
    cold_seconds=time.perf_counter()-start;start=time.perf_counter()
    for name,data in (('certificates',proofs),('discovery',evidences),('combined',dict(proofs=proofs,evidence=evidences))):(dest/(name+'.json.gz')).write_bytes(gzip.compress(encode(data).encode(),mtime=0))
    persistence=time.perf_counter()-start
    write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(str(r['id'])+'.json')).stat().st_size for r in rows),evidence_bytes=(dest/'discovery.json').stat().st_size,compressed_bytes={name:(dest/(name+'.json.gz')).stat().st_size for name in ('certificates','discovery','combined')},peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


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
