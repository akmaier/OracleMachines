#!/usr/bin/env python3
"""Matched full versus bounded active admission on retained edited CNFs."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_admitted_learning as e
from experiments import compare_cnf_selective_learning as previous
from experiments.compare_cnf_boundary_transfer import sha,load,encode,write,binding,bound,source_rows
PARENT=Path('experiments/results/cnf-selective-learning')
FILES=('experiments/cnf_admitted_learning.py','experiments/compare_cnf_admitted_learning.py','experiments/audit_cnf_admitted_learning.py','experiments/validate_cnf_admitted_learning.py','solver/test_cnf_admitted_learning.py')
MODES=('all','admitted')
LIMIT=2000


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json');old=load(PARENT/'protocol.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=old['panel'],baseline_records=binding(PARENT/'reuse-0/report.json'),references=binding(PARENT/'references.json'),transport=binding(PARENT/'transport.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['all','admitted'],['admitted','all']],node_limit=LIMIT,clause_limit=e.CLAUSE_LIMIT,limitations=[
        'Policy development on the exposed 16 edited targets from eight previously refuted parents. All previous target bytes, labels, references and unknowns remain unchanged. This is not new external transfer or a representative sample.',
        'Baseline activates every surviving learned clause. Candidate admits at most 128 distinct non-source clauses, ranked by smaller width then more recent retained derivation; duplicate clauses use their most recent record. The rule uses proof syntax, not target truth or new trial outcomes. The same target-only proposal and unchanged learner are used with 2000 entered contexts.',
        'Every surviving derivation is still checked, copied, retained and persisted, including inactive clauses and ancestors. Only active augmented input changes; no proof pruning, watched-literal propagation or production defaults change. Clauses discovered by new search are not subject to this initial admission cap.',
        'Any admitted subset is implied by the target, so augmentation preserves its entire model set. Exact proof substitution produces an unchanged-format target certificate. SAT requires a full source model; UNSAT requires a checked empty clause; capped runs remain unknown.',
        'Two fresh-process alternating pairs charge input/hash reads, parent proof reads and checks, selective transport, ranking, augmentation, search, substitution, checks, writes, three compressions, warm and two cold target-only reload/checks. Historical parent acquisition is additional. Imports/startup, reports and independent audits are additional; OS caches are not flushed.',
        'The historical union preserves answers if bounded admission loses a baseline answer. A union is not a measured combined dispatcher. Per-policy misses, novel gains, retained evidence, replay costs and unresolved interactions are recorded separately. No polynomial arbitrary-CNF efficiency claim.']))


def discover(row,mode,counts):
    source,proof=previous.parent_data(row,counts)
    return (e.prior.solve if mode=='all' else e.solve)(source,proof,row['source'],counts,node_limit=LIMIT)


def check(source,proof,counts=None):return e.prior.prior.check_result(source,proof,counts)


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
