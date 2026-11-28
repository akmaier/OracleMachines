#!/usr/bin/env python3
"""Untuned transfer of frozen repair kernels to new SATLIB sources and controls."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_boundary_repair as e
from experiments.compare_cnf_boundary_repair import sha,load,encode,write,binding,bound,check,discover
from experiments.cnf_external_cutsets import parse_dimacs
PARENT=Path('experiments/results/cnf-boundary-repair')
MODES=('baseline','boundary')
FILES=('experiments/acquire_cnf_boundary_transfer.py','experiments/compare_cnf_boundary_transfer.py','experiments/audit_cnf_boundary_transfer.py','experiments/validate_cnf_boundary_transfer.py','solver/test_cnf_boundary_transfer.py')


def source_rows(p):
    rows=bound(p['panel'])
    for row in rows:
        assert sha(row['raw']['path'])==row['raw']['sha256']
        cnf,_=parse_dimacs(Path(row['raw']['path']).read_text())
        assert cnf==row['source'];row['source']=cnf
    return rows


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');selection=load(out/'selection.json')
    assert selection['parent']==binding(PARENT/'checkpoint.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    for file,h in selection['policy_files'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=selection['parent'],parent_manifest=selection['parent_manifest'],panel=binding(out/'panel.json'),selection=binding(out/'selection.json'),acquisition=binding(out/'acquisition.json'),descriptions=binding(out/'descriptions.json'),transports=binding(out/'transports.json'),overlaps=binding(out/'overlaps.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','boundary'],['boundary','baseline'],['baseline','boundary'],['boundary','baseline']],policy=selection['policy'],reference_policy=dict(portfolio='unchanged cnf_hamming_repair.pipeline',per_input_process_timeout_seconds=30,z3_timeout_ms=10000,z3_random_seed=0),limitations=[
        'Frozen policy transfer to 24 previously unused SATLIB originals in six size/truth groups, plus six signed permutations and six edits. Selection indices and controls were frozen before acquiring new contents. This is size-limited nonrepresentative sampling, not a competition or all-history novelty claim.',
        'No tuning or new solving algorithm. Compare unchanged full 20000-state disjoint traversal with the frozen 10000-state prefix plus proof-guided local repair, sharing 20000 total states and at most eight rounds. Publisher labels, file names and truth results never enter discovery.',
        'Repair kernels provide SAT witnesses or unknown. A finished local or prefix exclusion is not promoted by these frozen wrappers to global UNSAT. UNSAT publisher labels and Z3 results are audit data, not new portfolio certificates.',
        'All raw DIMACS rereads, input hashing, proposal/index preparation, search and conditional checks, evidence/model writes and three compressions, warm and two cold reload/checks are measured. No search state survives replay; OS caches are not flushed. Download, import/startup, final reports and independent reference runs are additional.',
        'Separate one-shot fresh-process reference runs use the unchanged full portfolio and Z3 with fixed timeouts. Portfolio certificates receive independent project checks; Z3 SAT models receive full-source checks. Z3 UNSAT is trusted reference output, not a project-checkable refutation. Reference times do not include the matched persistence/replay workload and are not used for a speedup ratio.',
        'Exact normalized overlap is checked against the retained external 37, constructed 32 and synthetic 182 panels. Controls are related inputs. No semantic-isomorphism or general distribution coverage claim.',
        'Prior sources, artifacts and coverage unions are immutable. Remaining gaps include unrestricted preprocessing, conditional interaction width, guarded negative reuse and compact acquisition; finite holdout success would not prove a polynomial SAT method.']))


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
