#!/usr/bin/env python3
"""Matched incremental comparison of checked frontier cutsets and root lift."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_factor_clause_width as prior
from experiments import cnf_factor_conditioning as f
base=prior.base;old=prior.old;verified=prior.verified
PARENT=Path('experiments/results/cnf-factor-refinement')
MODES=('wide','cut0','cut2','cut4')
FILES=('experiments/cnf_factor_conditioning.py','experiments/compare_cnf_factor_conditioning.py','solver/test_cnf_factor_conditioning.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for name,h in parent['source_fingerprints'].items():assert base.sha(name)==h,name
    roots={r['id']:r for r in base.load('experiments/results/cnf-selective-width-buckets/remaining.json')['cases']}
    rows=[]
    for r in base.load(PARENT/'panel.json'):
        root=roots[r['root_id']];rows.append(dict(**r,root_source=root['source'],context=root['proof']))
    base.write(out/'panel.json',rows)
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(out/'panel.json'),screen=old.binding(out/'cutset-screen.json'),source_fingerprints={**parent['source_fingerprints'],**{name:base.sha(name) for name in FILES}},orders=[list(MODES[i%4:]+MODES[:i%4]) for i in range(8)],limits=dict(clause_width=4,clause_budget=65536,max_cutset=4,cache_entries=4096,cache_bytes=4194304),limitations=[
        'Exploratory screen-guided policy on the same three exposed frontiers; cutset size four was selected after the retained screen. IDs, descriptions and truth labels do not enter graph ranking. This is not held-out external generalization.',
        'Wide continues the original checked factor prefix at width ten. Cut0, cut2 and cut4 rebuild exact width-four covers and condition zero, two or four graph-degree-ranked variables before width-nine elimination. Every Boolean branch is retained, including failures and work exhaustion.',
        'Original prefix projection work is charged once and deducted from a single 262144-unit projection allowance across all branches of each frontier. Cover search has a separate 65536 candidate/completion cap. Graph ranking, normalization, restriction, bit operations and all verification are additional charged work.',
        'Each acquisition includes internal checking. Explicit, warm and each of two cold passes independently validate the old whole-root context, cover/branch certificates and root SAT witness transport. Only an actual complete source witness upgrades a root. Warm and cold start with empty bounded verified-operator banks; operating-system file caches are not flushed.',
        'The same three frontiers are attempted in every mode, even when an earlier frontier already supplies a model of the same root. This deliberately retains the unresolved third-frontier cost; no conditional early-stopping saving is claimed.',
        'Charged incremental stage includes input/context loading, discovery/internal checks, explicit checking/root recomposition, writes, compression, warm and two cold replays. Historical root acquisition, startup, final report metadata and independent audits remain additional; no full 182-query pipeline or fresh-solver speedup is claimed.',
        'All previous 180 structural certificates remain retained. Adding original-source models for the two exposed roots completes only this finite synthetic 182-query panel. One active frontier can stay unresolved beneath a SAT root; arbitrary SAT, new distributions and efficient unrestricted partitioning remain open.']))


def acquire(row,mode,counts):
    if mode=='wide':
        proof,diag,_=prior.continuation.discover(row['source'],row['prefix'],counts);return proof,diag
    return f.discover(row['source'],row['prefix'],counts,cut_limit=int(mode[-1]))


def check(row,context,mode,proof,counts):
    got=prior.continuation.check(row['source'],row['prefix'],proof,counts) if mode=='wide' else f.check(row['source'],row['prefix'],proof,counts)
    root=f.lift_root(row['root_source'],context,row['node'],row['source'],row['prefix'],got,counts)
    return dict(leaf=got,root=root)


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);contexts={r['root_id']:old.bound(r['context']) for r in rows};input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter();sessions=[]
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:
            counts=Counter();start=time.perf_counter();proof,diag=acquire(row,mode,counts);acquisition=time.perf_counter()-start
            start=time.perf_counter();got=check(row,contexts[row['root_id']],mode,proof,counts);checking=time.perf_counter()-start
            start=time.perf_counter();base.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
            cases.append(dict(id=row['id'],status=proof['status'],result=got,diagnostic=diag,counts=dict(counts)));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    sessions.append(bank.stats());start=time.perf_counter();warm=Counter()
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:check(row,contexts[row['root_id']],mode,base.load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;sessions.append(bank.stats());start=time.perf_counter();cold=Counter()
    for _ in range(2):
        with verified.installed(bank:=verified.VerifiedOperators()):
            for row in rows:check(row,contexts[row['root_id']],mode,base.load(dest/(row['id']+'.json')),cold)
        sessions.append(bank.stats())
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();(dest/'certificates.json.gz').write_bytes(gzip.compress(base.encode(proofs).encode(),mtime=0));persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence,complete_stage_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(r['id']+'.json')).stat().st_size for r in rows),compressed_bytes=(dest/'certificates.json.gz').stat().st_size,cache_sessions=sessions,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


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
