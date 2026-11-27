#!/usr/bin/env python3
"""Matched one-way forcing and shared implication-edge evidence."""
from collections import Counter
from pathlib import Path
import gzip,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_relation_buckets as prior
from experiments import cnf_forcing_buckets as k
from experiments.cnf_forcing_bucket_panel import panel
base=prior.base;old=prior.old;native=k.native;oracle=prior.oracle
FALLBACK=prior.FALLBACK
PARENT=Path('experiments/results/cnf-relation-buckets')
MODES=('fresh','relations','paths','shared')
FILES=('experiments/cnf_forcing_buckets.py','experiments/cnf_forcing_bucket_panel.py','experiments/compare_cnf_forcing_buckets.py','solver/test_cnf_forcing_buckets.py')


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
        'Twenty-seven exposed unique sources, 24 frozen synthetic constructions and four repeats. Labels/descriptions are audit-only; not a representative external benchmark.',
        'Relations wraps the preceding shared relation-cofactor policy without one-way forcing. Paths adds capped binary reachability from each signed variable, retains each supported path separately, and propagates the derived units. Shared has identical discovery and forcing but interns directed clause-supported edges and checks each pooled edge once per incoming forcing proof.',
        'Both forcing modes make one pass after the preceding unit/conflict/equivalence stage. Later unit consequences can expose further binary paths which are not searched again. Every accepted path starts at the negation of its forced literal and ends at that literal. A cap-exhausted search is a partial transformation, never a refutation.',
        'The existing work_limit value independently caps forcing traversal edges per incoming cofactor and reserved bucket probes per node. Graph setup, start enumeration, queues, path assembly, lookup, normalization, checking, persistence, time and RAM remain additional. Shared evidence requires every pooled edge to be source-supported, unique and used; path walks and endpoints are checked individually.',
        'All structural arms retain root folding, one binary equivalence block per edge, depth two, width eight and identical unit/bucket limits. Full normalized final residual plus remaining depth is the local memo key under fixed policy. Every incoming relation/forcing/renaming transport remains separate and checked.',
        'Source edits invalidate evidence. Policy/depth changes invalidate reuse. Unknown is not UNSAT and binary splits retain both exact children. One-way forcing does not assert a general small quotient or efficient arbitrary-SAT partition.',
        'Four cyclic process orders start empty with one common fallback. Complete time charges preparation, recognition, checking, evidence/SQLite persistence, warm reuse, cold reconstruction and compression. Startup, report metadata, generation, post-hoc diagnostics, history and lineage audit are additional.',
        'Both native cold readers audit fallback; two additional JSON passes use the same forcing/bucket checker, not independent JSON implementations. Native/equivalence/affine/Lean formats are unchanged. Relations is the preceding policy in this wrapper, not a historical timing rerun.',
        'Independent paths and shared edges have identical logical coverage and discovery order; count reductions in support checks do not by themselves establish lower runtime or total storage. All regressions and missed recognitions are retained; no production default changes.']))



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
                    wrapped=prior.prior.prior.prior.prior.prior.attempt(solver,row['source']);case['route']='fresh'
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
                    wrapped=prior.prior.prior.prior.prior.prior.attempt(solver,row['source']);assert (None if wrapped['result'] is None else wrapped['result']['answer'])==result['answer']
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
