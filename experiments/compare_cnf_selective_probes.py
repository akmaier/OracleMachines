#!/usr/bin/env python3
"""Selective continuation versus unchanged probing, uniform allowance and repeated clear prefixes."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import gzip,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_relations as prior
from experiments import cnf_selective_probes as k
from experiments.cnf_selective_probe_panel import panel
base=prior.base;old=prior.old;native=k.native;oracle=prior.oracle
FALLBACK=prior.FALLBACK
PARENT=Path('experiments/results/cnf-probe-relations')
MODES=('fresh','base','eager','restart','resume')
FILES=('experiments/cnf_selective_probes.py','experiments/cnf_selective_probe_panel.py','experiments/compare_cnf_selective_probes.py','solver/test_cnf_selective_probes.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    held,desc=panel();assert held==base.load(out/'heldout.json') and desc==base.load(out/'heldout-descriptions.json')
    freeze=base.load(out/'freeze.json');assert base.sha(out/'heldout.json')==freeze['sha256']
    previous=base.load(PARENT/'panel.json');previous_desc=base.load(PARENT/'descriptions.json')
    dev=[dict(id='d-'+r['id'],source=r['source']) for r in previous]
    for r in previous:desc['d-'+r['id']]=dict(family='previous_panel',previous=previous_desc[r['id']])
    frontier=base.load(PARENT/'frontier-inputs.json')
    dev.extend(dict(id='f-'+r['id'],source=r['source']) for r in frontier)
    for r in frontier:desc['f-'+r['id']]=dict(family='exposed_frontier',variables=r['variables'])
    rows=dev+held;base.write(out/'panel.json',rows);base.write(out/'descriptions.json',desc);base.write(out/'truth.json',{r['id']:oracle(r['source']) for r in rows})
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),freeze=old.binding(out/'freeze.json'),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limits=freeze['policy'],node_limit=256,orders=[list(MODES[i:]+MODES[:i]) for i in range(5)],limitations=[
        'Previous 76 queries and six exposed frontier inputs plus 24 new unlabelled synthetic cases and four exact normalized repeats. This is not representative external SAT evidence. Metadata and labels are audit-only; recurring families and exact overlaps are reported.',
        'Base translates exactly to the previous 128-probe relations engine. Eager translates to the same engine with 256 probes. Selective modes run the initial 128, one relation tail, then a charged bucket gate; only capped unresolved nonconstant edges receive 128 more probes, without another relation tail. Ordering differs from eager.',
        'Restart and resume use identical acquisition schedules and produce identical proofs modulo mode. Restart rebuilds the occurrence index and repeats completed clear prefixes on unchanged CNFs. Resume retains that exact index and prefix only within one visit. Any source change invalidates it. No cursor or clear probe is cold authority.',
        'Depth two permits at most seven edges. Initial plus continuation attempts are at most 256 per edge, 1792 per root, and share eight accepted probe rounds. Restart repeats at most another 128 per edge. Binary/unit/bucket quotas are separate; occurrence visits, recognition, checking and reconstruction are charged. No wall-time or unrestricted polynomial bound.',
        'Five cyclic process orders use empty stores and one common fallback. Total time charges input, discovery with its internal check, explicit checking, writes, warm/cold replay and compression. Startup, labels, lineage audit and post-hoc diagnostics are separate. Both native cold readers audit archives; two JSON passes share one implementation.',
        'Unresolved means unknown, not UNSAT. Source-bound failed-assumption traces and exact transport certify consequences. No production default changes or arbitrary SAT efficiency claim.']))


def trial(out,dest,mode):
    dest.mkdir();started=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);input_seconds=time.perf_counter()-started
    phases=Counter();total=Counter();sc=Counter();cases=[];results=[];stored={};fallback_rows=[];fallback_results=[]
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=FALLBACK.LazyBinaryClosureSolver(db,node_limit=p['node_limit'])
        try:
            for row in rows:
                cc=Counter();case=dict(id=row['id']);proof=None;diag=None
                if mode!='fresh':
                    start=time.perf_counter();cnf,_=native.normalize(row['source'],cc);root=native.token(cnf,cc)
                    if root in stored:
                        proof=base.load(dest/stored[root]);diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                    else:proof,diag=k.discover(row['source'],cc,mode=mode,**p['limits'])
                    case['discovery_seconds']=time.perf_counter()-start;start=time.perf_counter()
                    if root not in stored:
                        file=base.key_sha(root)+'-proof.json';base.write(dest/file,proof);stored[root]=file
                    base.write(dest/(row['id']+'-diagnostic.json'),diag);case['evidence_persistence_seconds']=time.perf_counter()-start
                start=time.perf_counter();solver.counts=Counter();got=None if proof is None else k.check_certificate(row['source'],proof,cc)
                if got is not None and got['answer'] is not None:
                    result=dict(answer=got['answer'],model=got['model'],root=root,authority=k.FORMAT);case['route']='bucket'
                else:
                    wrapped=prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.attempt(solver,row['source']);case['route']='fresh'
                    if wrapped['result'] is None:result=dict(answer=None,root=None,model=None,authority='unresolved')
                    else:
                        result={key:wrapped['result'][key] for key in ('answer','model','root','authority')};fallback_rows.append(row);fallback_results.append(result)
                case['solve_check_seconds']=time.perf_counter()-start;case.update(diagnostic=diag,counts=dict(cc),solver_counts=dict(solver.counts))
                total.update(cc);sc.update(solver.counts);phases.update({key:value for key,value in case.items() if key.endswith('_seconds')});cases.append(case);results.append(result)
            tables=old.tables(solver.db);start=time.perf_counter();wc=Counter()
            for row,result,case in zip(rows,results,cases):
                if mode!='fresh':
                    cnf,_=native.normalize(row['source'],wc);root=native.token(cnf,wc);got=k.check_certificate(row['source'],base.load(dest/stored[root]),wc)
                    if case['route']=='bucket':assert got['answer']==result['answer']
                if case['route']=='fresh':
                    wrapped=prior.prior.prior.prior.prior.prior.prior.prior.prior.prior.attempt(solver,row['source']);assert (None if wrapped['result'] is None else wrapped['result']['answer'])==result['answer']
            warm=time.perf_counter()-start;assert tables==old.tables(solver.db)
        finally:solver.close()
        start=time.perf_counter();readers=FALLBACK.audit(db,fallback_rows,fallback_results);coldcounts=Counter()
        for _ in range(2):
            if mode!='fresh':
                for row,result,case in zip(rows,results,cases):
                    cnf,_=native.normalize(row['source'],coldcounts);root=native.token(cnf,coldcounts)
                    got=k.check_certificate(row['source'],base.load(dest/stored[root]),coldcounts)
                    if case['route']=='bucket':assert got['answer']==result['answer']
        cold=time.perf_counter()-start;start=time.perf_counter();archive=base.archive(db,dest)
        payload=base.encode({f:base.load(dest/f) for f in sorted(stored.values())}).encode();(dest/'certificates.json.gz').write_bytes(gzip.compress(payload,mtime=0))
        persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],cases=cases,results=results,counts=dict(total),solver_counts=dict(sc),warm_counts=dict(wc),cold_counts=dict(coldcounts),input_seconds=input_seconds,phases=dict(phases),
        warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,stored=stored,certificate_bytes=sum((dest/f).stat().st_size for f in stored.values()),certificate_compressed_bytes=(dest/'certificates.json.gz').stat().st_size,
        diagnostic_bytes=sum(f.stat().st_size for f in dest.glob('*-diagnostic.json')),
        records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items()),digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},archive=archive,readers=readers,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for i,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=i))
        print(base.encode(dict(completed=i)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
