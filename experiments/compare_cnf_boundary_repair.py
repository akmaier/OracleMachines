#!/usr/bin/env python3
"""Matched fresh-process repair runs with conditional evidence persistence charged."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_boundary_repair as e
from experiments.compare_cnf_partition_repair import sha,load,encode,write,binding,bound,check
PARENT=Path('experiments/results/cnf-partition-repair')
MODES=('baseline','boundary')
FILES=('experiments/cnf_boundary_repair.py','experiments/compare_cnf_boundary_repair.py','experiments/audit_cnf_boundary_repair.py','experiments/validate_cnf_boundary_repair.py','solver/test_cnf_boundary_repair.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=binding('experiments/results/cnf-hamming-repair/constructed-inputs.json'),truth=binding('experiments/results/cnf-hamming-repair/constructed-audit-witnesses.json'),baseline=binding(PARENT/'partition-0/report.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','boundary'],['boundary','baseline'],['baseline','boundary'],['boundary','baseline']],node_limit=e.NODE_LIMIT,prefix_limit=e.PREFIX_LIMIT,max_rounds=e.MAX_ROUNDS,limitations=[
        'Exploratory follow-up on 32 exposed constructed planted-SAT sources, not fresh external transfer. Policy selected after probes on retained near models; timed discovery reacquires them from raw CNF. Audit truth witnesses and IDs never enter search.',
        'Kernel-only comparison, unchanged production portfolio. Both arms collect near models with identical disjoint traversal. Baseline uses 20000 states; candidate uses an initial 10000 and shares the remaining allowance across at most eight conditional rounds. All prefix and local states count toward 20000.',
        'Free all variables in currently false clauses, preserving all constraints induced by the fixed outside assignment. Rebuild local search per round; retain one incremental source projection index. Checked exclusion supports select outside variables to release; prefix flip/keep commitments are discarded on recentering.',
        'Conditional UNSAT excludes one outside context only. All SAT answers require full original-source witnesses; no incomplete search or conditional proof is promoted to global UNSAT. A cap or stalled boundary returns unknown.',
        'Time includes source JSON reads, proposals, acquisition, index construction and updates, local solver restarts, conditional checking, explicit model/evidence checking, proof and evidence writes/compression, and warm/two cold reloads. Discovery sidecars persist all conditional proofs. No search state survives replay; OS caches are not flushed. Imports, reporting metadata and independent audits are additional.',
        'Equal state budgets do not imply equal work or a universal ordering guarantee. Wide neighborhoods may approach the whole input. No new tractability, compact arbitrary refutations or efficient unrestricted SAT expansion claim.',
        'Prior external 37/37, synthetic 182/182, all historical artifacts and sources remain preserved and separate. Constructed panel completion alone is not general efficient coverage.']))


def source_rows(p):return bound(p['panel'])


def discover(source,mode,counts):
    if mode=='boundary':
        result=e.repair(source,counts); witness=result['witness']; evidence=result['evidence']; diag=result['diagnostic']
    else:
        seed=e.proposal(source,counts);result=e.collect(source,seed,len(seed['names']),counts,node_limit=e.NODE_LIMIT)
        witness=result['witness'];evidence=dict(format=e.EVIDENCE,seed=result['near_model'],rounds=[])
        diag=dict(prefix=result['diagnostic'],rounds=[],expanded=result['diagnostic']['expanded'],reason='sat' if witness else 'unknown')
    return dict(format='cnf-repair-model-result-v1',witness=witness),evidence,diag


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=load(out/'protocol.json');rows=source_rows(p);input_seconds=time.perf_counter()-started;cases=[];proofs=[];evidences=[];total=Counter();phases=Counter()
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,evidence,diag=discover(row['source'],mode,counts);acquisition=time.perf_counter()-start;discovery_counts=dict(counts)
        start=time.perf_counter();got=check(row['source'],proof,counts);e.check_evidence(row['source'],evidence,counts);checking=time.perf_counter()-start
        start=time.perf_counter();write(dest/(str(row['id'])+'.json'),proof);writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],status='unresolved' if got['answer'] is None else 'sat',result=got,diagnostic=diag,counts=dict(counts),discovery_counts=discovery_counts,acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);evidences.append(evidence);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    start=time.perf_counter();write(dest/'discovery.json',evidences);phases['writing_seconds']+=time.perf_counter()-start
    start=time.perf_counter();warm=Counter()
    for row,ev in zip(source_rows(p),load(dest/'discovery.json')):check(row['source'],load(dest/(str(row['id'])+'.json')),warm);e.check_evidence(row['source'],ev,warm)
    warm_seconds=time.perf_counter()-start;start=time.perf_counter();cold=Counter()
    for _ in range(2):
        for row,ev in zip(source_rows(p),load(dest/'discovery.json')):check(row['source'],load(dest/(str(row['id'])+'.json')),cold);e.check_evidence(row['source'],ev,cold)
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
