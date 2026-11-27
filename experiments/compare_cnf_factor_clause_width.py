#!/usr/bin/env python3
"""Charged lifecycle study of the three unresolved source-bound factor frontiers."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_verified_operators as prior
from experiments import cnf_factor_clause_width as f
from experiments import cnf_bucket_continuation as continuation
base=prior.base;old=prior.old;verified=prior.verified
PARENT=Path('experiments/results/cnf-verified-operators')
FRONTIER=Path('experiments/results/cnf-selective-width-buckets/remaining-profile.json')
MODES=('hold','wide','clause3','clause4')
FILES=('experiments/cnf_factor_clause_width.py','experiments/compare_cnf_factor_clause_width.py','solver/test_cnf_factor_clause_width.py')


def acquire(row,mode,counts):
    if mode=='hold':f.checked_prefix(row['source'],row['prefix'],counts);return dict(status='unresolved'),dict(reason='retained-prefix')
    if mode=='wide':
        proof,diag,_=continuation.discover(row['source'],row['prefix'],counts);return proof,diag
    return f.discover_prefix(row['source'],row['prefix'],int(mode[-1]),65536,counts)


def check(row,mode,proof,counts):
    if mode=='hold':
        if proof!={'status':'unresolved'}:raise ValueError('Invalid retained prefix')
        f.checked_prefix(row['source'],row['prefix'],counts);return dict(answer=None,model=None)
    if mode=='wide':return continuation.check(row['source'],row['prefix'],proof,counts)
    return f.check_prefix(row['source'],row['prefix'],proof,counts)


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for name,h in parent['source_fingerprints'].items():assert base.sha(name)==h,name
    rows=[dict(id=r['id']+':'+str(r['node']),root_id=r['id'],node=r['node'],source=r['source'],prefix=r['prefix']) for r in base.load(FRONTIER)['records']]
    base.write(out/'panel.json',rows)
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),frontier=old.binding(FRONTIER),panel=old.binding(out/'panel.json'),source_fingerprints={**parent['source_fingerprints'],**{name:base.sha(name) for name in FILES}},orders=[list(MODES[i%4:]+MODES[:i%4]) for i in range(8)],limits=dict(clause_budget=65536,cache_entries=4096,cache_bytes=4194304),limitations=[
        'The three saved unresolved active-factor frontiers of two SAT roots. Input is source CNF plus its previously checked width-nine projection prefix. Historical acquisition and full root preparation are additional, not included in this incremental-stage comparison.',
        'Hold retains the same source-bound prefix and reconstructs active factors. Wide continues at width ten. Clause3 and clause4 classify all active tables as exact same-variable CNF covers, certified width obstructions, or budget-unresolved; only complete covers permit a new width-nine bucket continuation.',
        'The old projection work remains charged against the total 262144 allowance before any continuation. Clause candidate/completion search has a separate 65536-unit cap per frontier; mask construction, subsumption, checking and bit-operation costs are additional measured work. These caps are not total runtime or unrestricted SAT bounds.',
        'Each new terminal CNF is the exact conjunction of all checked covers. Its model is lifted through the full old prefix choices and checked against the source; no auxiliary variables or unchecked replacements are accepted. A leaf certificate is not automatically a whole-root verdict.',
        'All modes use the previous bounded verified-operator bank across each phase. Warm and each cold pass start empty. Eight cyclic process orders charge input, recognition, prefix preparation, internal/explicit checking, writes, warm/cold replay and compression. Startup, final report metadata, earlier acquisition and independent audits are extra.',
        'This is a focused stage study, not a complete end-to-end 182-query comparison or external generalization. Same-variable clause-width obstructions are representation lower bounds, not time lower bounds or obstructions to auxiliary encodings, conditioning or contextual simplification.']))


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);input_seconds=time.perf_counter()-started;cases=[];proofs=[];total=Counter();phases=Counter();sessions=[]
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:
            counts=Counter();start=time.perf_counter();proof,diag=acquire(row,mode,counts);acquisition=time.perf_counter()-start
            start=time.perf_counter();got=check(row,mode,proof,counts);checking=time.perf_counter()-start
            start=time.perf_counter();base.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
            cases.append(dict(id=row['id'],status=proof['status'],result=got,diagnostic=diag,counts=dict(counts),acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing));proofs.append(proof);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
    sessions.append(bank.stats());start=time.perf_counter();warm=Counter()
    with verified.installed(bank:=verified.VerifiedOperators()):
        for row in rows:check(row,mode,base.load(dest/(row['id']+'.json')),warm)
    warm_seconds=time.perf_counter()-start;sessions.append(bank.stats());start=time.perf_counter();cold=Counter()
    for _ in range(2):
        with verified.installed(bank:=verified.VerifiedOperators()):
            for row in rows:check(row,mode,base.load(dest/(row['id']+'.json')),cold)
        sessions.append(bank.stats())
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();payload=base.encode(proofs).encode();(dest/'certificates.json.gz').write_bytes(gzip.compress(payload,mtime=0));persistence=time.perf_counter()-start
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
