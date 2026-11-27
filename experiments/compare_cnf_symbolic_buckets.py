#!/usr/bin/env python3
"""Matched symbolic preprocessing before conditioned bucket acquisition."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_buckets as prior
from experiments import cnf_symbolic_buckets as k
from experiments.cnf_symbolic_bucket_panel import panel
base=prior.base;old=prior.old;native=k.native;oracle=prior.oracle
FALLBACK=prior.FALLBACK
PARENT=Path('experiments/results/cnf-conditioned-buckets')
MODES=('fresh','base','units','fold')
FILES=('experiments/cnf_symbolic_buckets.py','experiments/cnf_symbolic_bucket_panel.py','experiments/compare_cnf_symbolic_buckets.py','solver/test_cnf_symbolic_buckets.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    held,desc=panel();assert held==base.load(out/'heldout.json') and desc==base.load(out/'heldout-descriptions.json')
    freeze=base.load(out/'freeze.json');assert base.sha(out/'heldout.json')==freeze['sha256']
    dev=[]
    for row in base.load(PARENT/'remaining.json')['cases']:
        if 'repeat_of' in row['description']:continue
        key='d-'+row['id'];dev.append(dict(id=key,source=row['source']));desc[key]=dict(family='exposed_gap',previous=row['description'])
    rows=dev+held;base.write(out/'panel.json',rows);base.write(out/'descriptions.json',desc);base.write(out/'truth.json',{r['id']:oracle(r['source']) for r in rows})
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),freeze=old.binding(out/'freeze.json'),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limits=freeze['policy'],node_limit=256,orders=[list(MODES[i:]+MODES[:i]) for i in range(4)],limitations=[
        'Twelve unique exposed acquisition misses, 24 frozen synthetic constructions and four separate repeats. Descriptions and independent truth labels do not guide solving. This is not a representative external benchmark.',
        'Base wraps the preceding memoized depth-two bucket method with an identity preprocessing program. Units adds indexed unit propagation; fold adds exact complementary-clause folding with unit consequences. All use the same conditioned kernel and fallback. No per-branch symbolic preprocessing is added.',
        'Folding requires identical clause remainders and opposite pivot literals. General resolution cannot replace both parents. Every incoming program checks parent membership and exact remainders; units use a separate full-scan verifier.',
        'Occurrence and deletion-signature indexes update only affected clauses; stale heap candidates are revalidated. Removed parents invalidate signatures. Exact canonical root programs reuse within each stream, and source or policy changes invalidate them.',
        'Preprocessing permits 512 steps and 262144 reserved index-maintenance work units; its unit clause reads, candidate handling, normalization and verification are outside that allowance. A partial transformation remains exact. Old per-node width-eight/probe262144 and depth-two conditioning limits remain fixed.',
        'The separate symbolic JSON authority retains its transformation and a full old conditioned proof. SAT lifts unit assignments and inverse residual renaming, then checks the original source. UNSAT requires the checked terminal verdict. Unknown is not UNSAT.',
        'All workers start empty, share exact root programs, use the same fallback, replay all programs warm and twice cold, and compress JSON/SQLite archives. Both native readers check fallback records; additional passes use the same symbolic/conditioned checker, not independent JSON checkers.',
        'Complete time charges preparation, recognition, checking, index maintenance, persistence, warm reuse, cold replay and compression. Interpreter startup, report metadata, panel generation, history and lineage audit are additional.',
        'Base is the old acquisition policy in the new wrapper, not a timing rerun of the old artifact. Worst-case distinct residuals and bucket width remain exponential. No production default, native format, Lean refinement or unrestricted SAT efficiency claim changes.']))


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
                    wrapped=prior.prior.prior.attempt(solver,row['source']);case['route']='fresh'
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
                    wrapped=prior.prior.prior.attempt(solver,row['source']);assert (None if wrapped['result'] is None else wrapped['result']['answer'])==result['answer']
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
