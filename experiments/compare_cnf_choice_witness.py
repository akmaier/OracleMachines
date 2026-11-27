#!/usr/bin/env python3
"""Paired full-workflow comparison of checked signed-choice witnesses."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import gzip,hashlib,json,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_choice_witness as e
from experiments import cnf_verified_operators as verified
from experiments.cnf_external_cutsets import parse_dimacs
PARENT=Path('experiments/results/cnf-capacity-core')
EXTERNAL=Path('experiments/results/cnf-external-cutsets')
MODES=('baseline','choice')
FILES=('experiments/cnf_choice_witness.py','experiments/compare_cnf_choice_witness.py','experiments/audit_cnf_choice_witness.py','solver/test_cnf_choice_witness.py')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def write(path,value):Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def binding(path):return dict(path=str(path),sha256=sha(path))
def bound(entry):
    assert sha(entry['path'])==entry['sha256'],entry['path']
    return load(entry['path'])
base=SimpleNamespace(sha=sha,load=load,encode=encode,write=write)
old=SimpleNamespace(binding=binding,bound=bound)


def source(row):
    assert sha(row['raw']['path'])==row['raw']['sha256']
    cnf,_=parse_dimacs(Path(row['raw']['path']).read_text());assert cnf==row['source']
    return cnf


def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=binding(EXTERNAL/'panel.json'),descriptions=binding(EXTERNAL/'descriptions.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','choice'],['choice','baseline'],['baseline','choice'],['choice','baseline']],matching_allowance=e.MATCHING_ALLOWANCE,limitations=[
        'Exploratory follow-up on the already exposed 25 original SATLIB inputs and 12 derived controls. The edited hole10 case motivated constructive choices. No fresh external holdout or representative coverage estimate.',
        'Algorithms receive only CNFs. Two fixed greedy variable-disjoint selections, connected exclusion components, and the unchanged native matching helper propose a complete signed assignment. Every original clause is checked; matching success is not proof authority.',
        'A connected component is conservatively capacity one even when it is not a clique. Failed matching or rejected witnesses supply no UNSAT certificate. Strict-class diagnostics are distinct from the more general full-source witness authority.',
        'Baseline is the previous capacity/expanded pipeline. Choice arm attempts the SAT witness gate first, then calls that unchanged pipeline. No fallback general SAT solver and no changed production defaults.',
        'All initial raw parsing, preparation, discovery/internal and explicit checks, JSON writes, compression, warm and two cold reloads are charged. Every replay reparses source and reloads proof. Verified-operator banks start empty per phase; OS caches are not flushed. Startup, final metadata and independent audits are additional.',
        'D*E admission reserves a matching edge-visit bound across the two selections; source scans, sorting, component construction, copies, verification and memory are outside that allowance but timed. No unrestricted SAT bound or globally complete structure recognition follows.',
        'All old sources, certificates and synthetic 182/182 union remain unchanged. Recognition failures and nonclique false-negative controls are retained. Reusing a SAT witness requires complete current-source validation, including changed constraints.']))


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);sources=[source(r) for r in rows];input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter();sessions=[]
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row,cnf in zip(rows,sources):
            counts=Counter();start=time.perf_counter();proof,diag=e.pipeline(cnf,counts,enabled=mode=='choice');acquisition=time.perf_counter()-start
            start=time.perf_counter();got=e.check_pipeline(cnf,proof,counts);checking=time.perf_counter()-start
            start=time.perf_counter();base.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
            cases.append(dict(id=row['id'],status='unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'),result=got,diagnostic=diag,counts=dict(counts),acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing));print(mode,row['id'],cases[-1]['status'],round(acquisition,3),flush=True)
    sessions.append(bank.stats());start=time.perf_counter();warm=Counter()
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:e.check_pipeline(source(row),base.load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;sessions.append(bank.stats());start=time.perf_counter();cold=Counter()
    for _ in range(2):
        with verified.installed(bank:=verified.VerifiedOperators()):
            for row in rows:e.check_pipeline(source(row),base.load(dest/(row['id']+'.json')),cold)
        sessions.append(bank.stats())
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();(dest/'certificates.json.gz').write_bytes(gzip.compress(base.encode(proofs).encode(),mtime=0));persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(r['id']+'.json')).stat().st_size for r in rows),compressed_bytes=(dest/'certificates.json.gz').stat().st_size,cache_sessions=sessions,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    samples=[]
    for i,order in enumerate(base.load(out/'protocol.json')['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=i))
        print(base.encode(dict(completed=i)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
