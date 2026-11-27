#!/usr/bin/env python3
"""Matched full workflow costs for the optional checked capacity gate."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_external_cutsets as prior
from experiments import cnf_capacity_core as e
base=prior.base;old=prior.old;verified=prior.verified
PARENT=Path('experiments/results/cnf-external-cutsets')
MODES=('baseline','capacity')
FILES=('experiments/cnf_capacity_core.py','experiments/compare_cnf_capacity_core.py','solver/test_cnf_capacity_core.py','experiments/audit_cnf_capacity_core.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json')
    for name,h in parent['source_fingerprints'].items():assert base.sha(name)==h,name
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(PARENT/'panel.json'),descriptions=old.binding(PARENT/'descriptions.json'),source_fingerprints={**parent['source_fingerprints'],**{name:base.sha(name) for name in FILES}},orders=[['baseline','capacity'],['capacity','baseline'],['baseline','capacity'],['capacity','baseline']],work_limit=e.WORK_LIMIT,limitations=[
        'Exploratory follow-up on the already exposed external panel: 25 original SATLIB inputs and 12 related controls. Capacity rule motivated by its five unresolved pigeonhole originals. This is not a fresh holdout or representative coverage estimate.',
        'Fixed capacity rule receives CNF clauses only. Two greedy demand selections, a greedy conflict clique partition, and an augmenting-path deficiency proposal. Checker uses exact source clause containment, disjoint demand literals, full exclusion pairs, exact partition, and strict deficiency. Failed recognition gives no verdict.',
        'Baseline is the unchanged expanded external pipeline. Capacity arm first attempts a whole-source refuting core and otherwise runs that same pipeline. No fallback SAT solver. There are no lost prior certificates, and incomplete inputs remain unresolved.',
        'All initial raw input parsing, search, internal and explicit checks, writes, compression, warm and two cold replays are charged. Every replay reparses source and reloads JSON. Verified-operator banks start empty per phase; operating-system caches are not flushed. Startup, final metadata and independent audits are extra.',
        'Search probe limit excludes input scanning, sorting, adjacency creation, checking, persistence and total retained memory. Nothing here bounds arbitrary SAT solving or assures a useful compact cover for every CNF.',
        'Certificates are reusable under source changes only after exact current-source demand/exclusion containment checks. They certify an inconsistent subset, not semantic equivalence or a full factorization. Their complements and overlaps with previous recognizers remain unrestricted.']))


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);sources=[prior.source(r) for r in rows];input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter();sessions=[]
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row,cnf in zip(rows,sources):
            counts=Counter();start=time.perf_counter();proof,diag=e.pipeline(cnf,counts,enabled=mode=='capacity');acquisition=time.perf_counter()-start
            start=time.perf_counter();got=e.check_pipeline(cnf,proof,counts);checking=time.perf_counter()-start
            start=time.perf_counter();base.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
            cases.append(dict(id=row['id'],status='unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'),result=got,diagnostic=diag,counts=dict(counts),acquisition_seconds=acquisition,checking_seconds=checking));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing));print(mode,row['id'],cases[-1]['status'],round(acquisition,3),flush=True)
    sessions.append(bank.stats());start=time.perf_counter();warm=Counter()
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:e.check_pipeline(prior.source(row),base.load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;sessions.append(bank.stats());start=time.perf_counter();cold=Counter()
    for _ in range(2):
        with verified.installed(bank:=verified.VerifiedOperators()):
            for row in rows:e.check_pipeline(prior.source(row),base.load(dest/(row['id']+'.json')),cold)
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
