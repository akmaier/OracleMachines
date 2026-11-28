#!/usr/bin/env python3
"""Paired complete repair-kernel workflows on the retained constructed panel."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import gzip,hashlib,json,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_partition_repair as e
PARENT=Path('experiments/results/cnf-hamming-repair')
MODES=('baseline','partition')
FILES=('experiments/cnf_partition_repair.py','experiments/compare_cnf_partition_repair.py','experiments/audit_cnf_partition_repair.py','solver/test_cnf_partition_repair.py')


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

def prepare(out):
    assert not (out/'protocol.json').exists();parent=load(PARENT/'checkpoint.json')
    for file,h in parent['source_fingerprints'].items():assert sha(file)==h,file
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),panel=binding(PARENT/'constructed-inputs.json'),truth=binding(PARENT/'constructed-audit-witnesses.json'),baseline_records=binding(PARENT/'constructed-results.json'),source_fingerprints={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}},orders=[['baseline','partition'],['partition','baseline'],['baseline','partition'],['partition','baseline']],node_limit=e.NODE_LIMIT,limitations=[
        'Exploratory follow-up on 32 already exposed constructed planted-SAT inputs, not fresh external generalization. Truth witnesses are read only by independent audits, never discovery or branch selection.',
        'Repair-kernel comparison only. Baseline is the unchanged previous Hamming search; the candidate partitions false-clause extensions by the first flipped available variable, fixing earlier candidates at seed values. Both use the same proposer, ranking rule, radius and 20000-state cap.',
        'A flip/keep context is stronger than a flip mask. Equal state caps do not imply equal work; full measured preparation, discovery, checking, writes, compression and replay are charged. No production default or existing portfolio changes.',
        'SAT requires a complete original-source model check. Unknown results contain no negative authority. Independently checked exclusion trees certify only their stated ball; the root must have empty flip and keep masks.',
        'Initial source JSON parsing, proposal construction, occurrence indexing, search/internal checks, explicit checking, JSON writes, compression and warm/two cold reloads are timed. Every replay reloads source and certificates. No search state is reused between phases; OS caches are not flushed. Imports, final metadata, audits and auxiliary minimum-distance diagnosis are additional.',
        'Disjoint branches avoid overlapping extension spaces but need not have polynomial total size or uniformly outperform another ordering. Unrestricted expansion, transfer and compact proof obligations remain open.',
        'All prior artifacts, scientific sources, the synthetic 182/182 union and external 37/37 union remain unchanged and distinct from this constructed repair-only panel.']))


def source_rows(p):return bound(p['panel'])


def discover(source,mode,counts):
    seed=e.proposal(source,counts)
    engine=e.baseline.search if mode=='baseline' else e.search
    result=engine(source,seed,len(seed['names']),counts,node_limit=e.NODE_LIMIT)
    assert result['exclusion'] is None  # SAT witnesses or explicitly unknown on this timed panel.
    return dict(format='cnf-repair-model-result-v1',witness=result['witness']),dict(seed=seed,search=result)


def check(source,proof,counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','witness'} or proof['format']!='cnf-repair-model-result-v1':raise ValueError('Invalid repair result')
    if proof['witness'] is None:
        e.previous.capacity.canonical(source,counts)
        return dict(answer=None,model=None)
    return e.previous.check(source,proof['witness'],counts)


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=load(out/'protocol.json');rows=source_rows(p);input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter()
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,diag=discover(row['source'],mode,counts);acquisition=time.perf_counter()-start;discovery_counts=dict(counts)
        start=time.perf_counter();got=check(row['source'],proof,counts);checking=time.perf_counter()-start
        start=time.perf_counter();write(dest/(str(row['id'])+'.json'),proof);writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],status='unresolved' if got['answer'] is None else 'sat',result=got,diagnostic=diag,counts=dict(counts),discovery_counts=discovery_counts,acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    start=time.perf_counter();warm=Counter()
    for row in source_rows(p):check(row['source'],load(dest/(str(row['id'])+'.json')),warm)
    warm_seconds=time.perf_counter()-start;start=time.perf_counter();cold=Counter()
    for _ in range(2):
        for row in source_rows(p):check(row['source'],load(dest/(str(row['id'])+'.json')),cold)
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();(dest/'certificates.json.gz').write_bytes(gzip.compress(encode(proofs).encode(),mtime=0));persistence=time.perf_counter()-start
    write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(str(r['id'])+'.json')).stat().st_size for r in rows),compressed_bytes=(dest/'certificates.json.gz').stat().st_size,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


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
