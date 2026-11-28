#!/usr/bin/env python3
"""Matched proof representation costs and frozen larger transfer."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_linear_unit_proof as e
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows
PARENT=Path('experiments/results/cnf-unit-partition')
MODES=('explicit','linear')
FILES=('experiments/cnf_linear_unit_proof.py','experiments/compare_cnf_linear_unit_proof.py','experiments/audit_cnf_linear_unit_proof.py','experiments/validate_cnf_linear_unit_proof.py','experiments/acquire_cnf_linear_unit_proof.py','solver/test_cnf_linear_unit_proof.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');old=load(PARENT/'protocol.json');larger=out/'larger'
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    for file,h in load(larger/'selection.json')['policy_files'].items():assert sha(file)==h,file
    write(larger/'protocol.json',dict(panel=binding(larger/'panel.json'),descriptions=binding(larger/'descriptions.json'),transports=binding(larger/'transports.json'),orders=[['explicit','linear']],node_limit=20000,selection=binding(larger/'selection.json')))
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=old['panel'],descriptions=old['descriptions'],baseline_records=binding(PARENT/'propagated-0/report.json'),larger_protocol=binding(larger/'protocol.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['explicit','linear'],['linear','explicit'],['explicit','linear'],['linear','explicit']],node_limit=20000,limitations=[
        'Representation comparison on the exposed 36-input panel: identical frozen search, seed, order, cap and result sets. Unit search records the same full proof; candidate packs it afterward. Packing and checking are charged, including simultaneous old/new proof retention. No search novelty or production default change.',
        'Linear preorder nodes omit explicit context keys. Independent checking reconstructs every context using a partial-assignment undo trail, source-clause unit deductions and complete first-flip branch orders. All expected children and exactly all supplied nodes must be consumed. Packing alone grants no authority.',
        'Four fresh-process alternating pairs on exposed inputs; one separately denominated pair on eight frozen new 125/150-variable originals plus four signed and four edited controls. Selection and both search/encoding source hashes were frozen before acquisition. The small size-limited sample is not representative, and exact normalized nonoverlap is not all-history semantic novelty.',
        'Input reads/hashes, preparation, acquisition/internal and explicit checks, conversion, persistence, three compressions, warm and two cold source/proof reloads are timed. No search state survives replay; OS caches are not flushed. Imports/startup, reporting metadata, downloads and independent audits are additional.',
        'Source publisher bytes are preserved exactly in gzip. Workflow DIMACS is a whitespace-normalized re-emission, checked for parsed equality. Labels and reference models never enter search. Z3 UNSAT remains a trusted reference unless a project certificate independently certifies it.',
        'Complete evidence can remain exponential. Finite coverage and exact recomposition do not imply efficient recognition, preprocessing or unrestricted expansion. Guarded negative reuse across different contexts/edits remains open.']))


def discover(source,mode,counts):
    proof,diag=(e.prior.solve(source,counts) if mode=='explicit' else e.solve(source,counts))
    return dict(engine=mode,proof=proof),None,diag


def check(source,proof,counts=None):
    if type(proof) is not dict or set(proof)!={'engine','proof'}:raise ValueError('Invalid comparison proof')
    if proof['engine']=='explicit':return e.prior.check_result(source,proof['proof'],counts)
    if proof['engine']=='linear':return e.check_result(source,proof['proof'],counts)
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
