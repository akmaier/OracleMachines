#!/usr/bin/env python3
"""Frozen edited inputs and charged selective-knowledge expansion workflows."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_selective_learning as e
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows,parse_dimacs
PARENT=Path('experiments/results/cnf-resolution-learning')
FILES=('experiments/cnf_selective_learning.py','experiments/compare_cnf_selective_learning.py','experiments/audit_cnf_selective_learning.py','experiments/validate_cnf_selective_learning.py','solver/test_cnf_selective_learning.py')
MODES=('fresh','reuse')
LIMIT=2000


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');old=load(PARENT/'protocol.json');rows=[]
    (out/'inputs').mkdir()
    for original in source_rows(old):
        cert=binding(PARENT/'learning-0'/(original['id']+'.json'));proof=bound(cert)['proof'];base=e.canonical(original['source'],Counter());deleted=proof['derivations'][0][0];assert deleted<len(base)
        target=[list(c) for i,c in enumerate(base) if i!=deleted];names=sorted({abs(v) for c in original['source'] for v in c})
        for kind in ('deletion','bridge'):
            key=f"s{len(rows):03d}";edited=target if kind=='deletion' else target+[[names[0],names[-1]+101],[-(names[-1]+101)]]
            raw=out/'inputs'/(key+'.cnf');raw.write_text(f'p cnf {max((abs(v) for c in edited for v in c),default=0)} {len(edited)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in edited))
            rows.append(dict(id=key,source=edited,raw=binding(raw),kind=kind,deleted_index=deleted,parent_id=original['id'],parent_source=original['source'],parent_raw=original['raw'],parent_certificate=cert,parent_kind=proof['kind'],expansion_case=proof['kind']=='unsat'))
    write(out/'panel.json',rows)
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=binding(out/'panel.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['fresh','reuse'],['reuse','fresh']],node_limit=LIMIT,limitations=[
        'All targets are controlled edits of already exposed parents. For each of 16 parents, delete the original clause starting its first stored derivation; the second target also adds a shared-variable bridge and fresh negative unit. No target truth was used to choose edits. This is proof-guided adversarial edit selection, not unseen external transfer.',
        'Transport is audited on all 32 targets. Expansion compares only the 16 edits of eight previously refuted parents, avoiding trivial reuse of old SAT models after pure deletion. Both modes use the unchanged prior learner and the same target-only proposal, capped at 2000 entered contexts. Extra retained clauses alter indexing, propagation and activity; equal budgets do not imply equal work.',
        'Reuse checks the old source proof, retains precisely derivations whose recorded premise paths survive, remaps and rechecks them, then searches an equivalent augmented target and substitutes checked derivations back into a target-only certificate. Missing support drops descendants, not unrelated records. It never inherits SAT authority. This is syntactic proof survival, not complete semantic entailment recognition.',
        'Two fresh-process alternating pairs charge target input/hash reads, candidate parent input/hash/proof reads, old/target checking, filtering, augmentation, expansion, proof substitution, internal/explicit checks, writes, three compressions, warm and two cold target-only reload/checks. Historical parent acquisition is a separately recorded sunk cost; no end-to-end amortization claim. Imports/startup, reporting and independent audits are additional; OS caches are not flushed.',
        'All surviving and newly discovered clauses remain persisted, including SAT and unknown results. No active-index optimization, proof minimization or production default changes. New target reference runs are separate audit results and never search inputs. Z3 SAT models are source checked; negative Z3 output alone grants no project UNSAT authority.',
        'All previous sources, results, refutations, unknowns and proof blocks remain unchanged. Surviving proof support, retained clause growth, target interaction, cold replay, preprocessing and unrestricted expansion remain explicit obligations.']))


def parent_data(row,counts):
    raw=Path(row['parent_raw']['path']).read_bytes();assert sha(row['parent_raw']['path'])==row['parent_raw']['sha256'];source,_=parse_dimacs(raw.decode());assert source==row['parent_source'];counts['selective_parent_input_bytes']+=len(raw)
    cert=bound(row['parent_certificate']);counts['selective_parent_proof_bytes']+=Path(row['parent_certificate']['path']).stat().st_size
    return source,cert['proof']


def discover(row,mode,counts):
    if mode=='fresh':return e.prior.solve(row['source'],counts,node_limit=LIMIT)
    old,proof=parent_data(row,counts);return e.solve(old,proof,row['source'],counts,node_limit=LIMIT)


def check(source,proof,counts=None):return e.prior.check_result(source,proof,counts)


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
