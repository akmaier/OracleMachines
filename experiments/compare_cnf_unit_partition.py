#!/usr/bin/env python3
"""Matched fresh acquisition, proof persistence and replay for unit partitions."""
from collections import Counter
from pathlib import Path
import gzip,importlib.util,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_unit_partition as e
from experiments import cnf_boundary_repair as boundary
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows
PARENT=Path('experiments/results/cnf-boundary-transfer')
BASELINE=PARENT/'export_root_exclusions.py'
spec=importlib.util.spec_from_file_location('preserved_root_export',BASELINE)
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
MODES=('baseline','propagated')
FILES=('experiments/cnf_unit_partition.py','experiments/compare_cnf_unit_partition.py','experiments/audit_cnf_unit_partition.py','experiments/validate_cnf_unit_partition.py','solver/test_cnf_unit_partition.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=binding(PARENT/'panel.json'),descriptions=binding(PARENT/'descriptions.json'),baseline_records=binding(PARENT/'root-export.json'),baseline_script=binding(BASELINE),previous_union=parent['boundary_transfer']['coverage-union'],source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','propagated'],['propagated','baseline'],['baseline','propagated'],['propagated','baseline']],node_limit=e.NODE_LIMIT,limitations=[
        'Development follow-up on the already exposed 24 external originals and 12 controls. No new transfer or representative generalization claim. Parent labels and reference models stay outside discovery.',
        'Baseline is the unchanged boundary policy plus its preserved full-root recording replay. Candidate propagates source unit clauses under both flip and keep commitments before disjoint first-flip branching, with the same proposer and gain tie-break rule. Both charge at most 20000 entered contexts per source, but contexts have different work.',
        'Candidate shares occurrence lists, fixed-true counts, free-variable counts and full-proposal satisfaction through an iterative undo trail. Unit closure may force keeping a seed value, not merely flipping a currently false clause. This is standard unit propagation and exhaustive DPLL-style search, not a new tractability theorem.',
        'A complete source-bound unit/branch refutation is recorded during search and checked independently. SAT needs a complete original-source witness. Interrupted searches remain unknown. Recording, unit scans, queue selection and restoration cost are explicit; proof size and unrestricted expansion can remain exponential.',
        'All source JSON/DIMACS reads, hashes, proposal/index construction, discovery/internal and explicit checks, proof/evidence writes and three compressions, warm and two cold reload/checks are timed. No search state survives replay; OS caches are not flushed. Imports, reporting metadata and independent audits are additional.',
        'Baseline conditional evidence remains fully persisted and replayed. Candidate has no conditional discovery sidecar beyond its root certificate. Complete workflow costs therefore include their different proof obligations. There is no modern solver speedup ratio or equal completed-work assumption.',
        'All old artifacts, scientific sources, prior coverage unions and counterexamples remain unchanged. Production defaults are unchanged. Fresh transfer after the policy change and unrestricted recognition/preprocessing/expansion obligations remain open.']))


def discover(source,mode,counts):
    if mode=='baseline':
        proof,evidence,diag=baseline.discover(source,counts)
    else:
        proof,diag=e.solve(source,counts);evidence=None
    return dict(engine=mode,proof=proof),evidence,diag


def check(source,proof,counts=None):
    if type(proof) is not dict or set(proof)!={'engine','proof'}:raise ValueError('Invalid comparison certificate')
    if proof['engine']=='baseline':return baseline.check(source,proof['proof'],counts)
    if proof['engine']=='propagated':return e.check_result(source,proof['proof'],counts)
    raise ValueError('Unknown certificate engine')


def check_evidence(source,evidence,counts=None):
    if evidence is None:return dict(conditional_exclusions=0)
    return boundary.check_evidence(source,evidence,counts)


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
