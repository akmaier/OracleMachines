#!/usr/bin/env python3
"""Matched per-cofactor unit closure and shared closed residual acquisition."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_symbolic_buckets as prior
from experiments import cnf_closed_buckets as k
from experiments.cnf_closed_bucket_panel import panel
base=prior.base;old=prior.old;native=k.native;oracle=prior.oracle
FALLBACK=prior.FALLBACK
PARENT=Path('experiments/results/cnf-symbolic-buckets')
MODES=('fresh','root','tree','closed')
FILES=('experiments/cnf_closed_buckets.py','experiments/cnf_closed_bucket_panel.py','experiments/compare_cnf_closed_buckets.py','solver/test_cnf_closed_buckets.py')


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
        'Twenty unique exposed misses, 24 frozen synthetic constructions and four separate repeats. Labels/descriptions do not guide acquisition; not a representative external benchmark.',
        'Root applies the previous root-folding policy with exact raw-cofactor memoization, expressed in the new proof wrapper. Tree adds indexed unit closure before each bucket but does not share nodes. Closed adds exact normalized post-unit residual plus remaining-depth sharing.',
        'All arms use the same root folding, depth two, width eight and per-node reserved bucket work. Unit closure uses the preceding indexed preprocessor with its per-edge step/index-work caps. No additional folds are applied after conditioning.',
        'Incoming edges retain their exact raw cofactor, unit derivation and renaming to a shared closed residual. Forced assignments cannot be reused as if they were a shared residual model. Every incoming edge and every stored node is checked.',
        'Closed cache identity includes full canonical residual and remaining depth under a fixed policy. Source edits and policy changes invalidate root reuse. Different raw cofactors may share a closed node only after separate exact unit proofs and transport. Unknown results remain unknown.',
        'Both split children are explored. At depth d there are at most 2^(d+1)-1 transport requests; sharing can avoid descendant requests. Per-edge closure work, source normalization and lookup still occur on memo hits. No unrestricted small-state bound is established.',
        'All workers start empty, use the same current fallback, replay exact root programs warm and twice cold, and compress JSON/SQLite evidence. The separate closed-bucket authority does not alter native, affine, equivalence or Lean formats. Both native cold readers audit fallback; the additional JSON passes use the same checker.',
        'Complete timing includes preparation, closure recognition/maintenance, edge checks, bucket work, persistence, warm replay, cold replay and compression. Interpreter startup, report metadata, panel generation, history and preservation audit are additional.',
        'Root is the previous policy in a new wrapper, not a historical artifact timing rerun. Discovery/index probe quotas do not bound planning, normalization, all verification, runtime or RAM. No production default or unrestricted SAT efficiency claim changes.']))


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
                    wrapped=prior.prior.prior.prior.attempt(solver,row['source']);case['route']='fresh'
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
                    wrapped=prior.prior.prior.prior.attempt(solver,row['source']);assert (None if wrapped['result'] is None else wrapped['result']['answer'])==result['answer']
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
