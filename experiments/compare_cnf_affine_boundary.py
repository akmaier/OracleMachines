#!/usr/bin/env python3
"""Matched full-space and boundary-image completion beside the current solver."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import gzip,json,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_feedback_cofactor_dag as prior
from experiments import cnf_affine_boundary as k
from experiments.cnf_affine_boundary_panel import panel
from experiments.cnf_whole_affine import complete_prepared
from experiments.cnf_affine_negative import check_negative
from experiments.cnf_larger_mixtures import attempt
base=prior.base;old=prior.old;native=k.native
PARENT=Path('experiments/results/cnf-feedback-cofactor-dag')
MODES=('fresh','full','boundary')
FILES=('experiments/cnf_affine_boundary.py','experiments/cnf_affine_boundary_panel.py','experiments/compare_cnf_affine_boundary.py','solver/test_cnf_affine_boundary.py')


def oracle(source):
    """Independent small DPLL audit; no structural recognizers or timing use."""
    nodes=0
    def visit(clauses,fixed):
        nonlocal nodes
        nodes+=1
        while True:
            if any(not c for c in clauses):return None
            if not clauses:return fixed
            units=[c[0] for c in clauses if len(c)==1]
            if not units:break
            lit=units[0];fixed={**fixed,abs(lit):lit>0}
            clauses=[tuple(x for x in c if x!=-lit) for c in clauses if lit not in c]
        lit=min(clauses,key=len)[0]
        for signed in (lit,-lit):
            answer=visit([tuple(x for x in c if x!=-signed) for c in clauses if signed not in c],{**fixed,abs(signed):signed>0})
            if answer is not None:return answer
        return None
    witness=visit([tuple(c) for c in source],{})
    if witness is not None:
        witness={v:witness.get(v,False) for v in {abs(l) for c in source for l in c}}
        assert native.holds(source,witness)
    return dict(answer=witness is not None,model=witness,oracle_nodes=nodes)


def full_discover(source,counts):
    cnf,names=native.normalize(source,counts);n=len(names);root=native.token(cnf,counts)
    limits=k.LIMITS;diagnostic=dict(status='size-cap',variables=n)
    if n>limits['variables'] or len(cnf)>limits['clauses'] or sum(map(len,cnf))>limits['literals']:return None,diagnostic
    a=k.bounded_extract(cnf,counts,limits['xors'])
    if a is None:diagnostic['status']='xor-cap';return None,diagnostic
    s=k.check_affine(cnf,a,counts);diagnostic.update(summary=s,free=n-s['rank'])
    if s['inconsistent']:
        proof=dict(cnf=list(map(list,cnf)),affine=a,decision=dict(kind='linear-conflict',row=next(i for i,r in enumerate(a['reductions']) if (r['mask'],r['rhs'])==(0,1))))
        diagnostic['status']='linear-conflict'
    elif not a['equations']:diagnostic['status']='no-equations';return None,diagnostic
    elif n-s['rank']>8:diagnostic['status']='free-cap';return None,diagnostic
    else:
        witness,e=complete_prepared(cnf,root,a,counts,8);diagnostic['status']=e['status']
        proof=dict(cnf=list(map(list,cnf)),affine=a,decision=(dict(kind='model',model=witness,space=e['space']) if witness is not None else dict(kind='exhaustion',space=e['space'],rejected=e['rejected'])))
    check_full(source,proof,counts);return proof,diagnostic


def check_full(source,proof,counts):
    cnf,names=native.normalize(source,counts)
    if proof['cnf']!=list(map(list,cnf)):raise ValueError('Changed full-space source')
    k.check_affine(cnf,proof['affine'],counts);d=proof['decision']
    if d['kind']=='model':
        k.check_space(len(names),proof['affine'],d['space'],counts);m={int(i):v for i,v in d['model'].items()}
        if not native.holds(cnf,m):raise ValueError('Invalid full-space model')
        return dict(answer=True,model={name:m[i] for i,name in enumerate(names,1)})
    check_negative(cnf,len(names),dict(affine=proof['affine'],decision=d),counts)
    return dict(answer=False,model=None)


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    held,desc=panel();assert held==base.load(out/'heldout.json') and desc==base.load(out/'heldout-descriptions.json')
    freeze=base.load(out/'freeze.json');assert freeze['sha256']==base.sha(out/'heldout.json')
    dev=[]
    for r in base.load(PARENT/'remaining.json')['cases']:
        key='d-'+r['id'];dev.append(dict(id=key,source=r['source']));desc[key]=dict(family='exposed_gap',previous=r['description'])
    rows=dev+held;base.write(out/'panel.json',rows);base.write(out/'descriptions.json',desc)
    base.write(out/'truth.json',{r['id']:oracle(r['source']) for r in rows})
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),freeze=old.binding(out/'freeze.json'),orders=list(map(list,permutations(MODES))),node_limit=256,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limits=k.LIMITS,limitations=[
        'Five exposed bounded-feedback gaps, 24 new generated family controls and four explicit exact repetitions. Descriptions/truth never guide measured solving. Not representative SAT coverage.',
        'Fresh is the current LazyBinaryClosureSolver and already includes affine completion. Full and boundary are explicit acquisition-first policies with exactly the same fallback, not new alternatives to an affine-free baseline.',
        'Full applies the existing eight-free-coordinate completion. Boundary uses rank at most eight of the complete affine basis restricted to leftover support. Both keep source-bound evidence and use full checking on every warm/cold load.',
        'Boundary JSON is a separate authority. Native, equivalence and old affine tables are unchanged. Native cold readers audit fallback records; both cold passes additionally run the same boundary checker, not two independent boundary algorithms.',
        'Every run starts empty and charges source recognition, basis preparation, checking, JSON persistence, SQLite persistence, warm reuse, cold replay and compression. Interpreter startup, report metadata, panel generation and final lineage audit are additional.',
        'Only accepted exact canonical source proofs are reused within a stream. Misses fall back with no verdict. An edited source cannot reuse a proof. No cross-source matrix factor reuse is implemented.',
        'All source/basis work remains charged and retained. Rank reduction can save enumeration without lowering process RSS or beating fresh fallback. No native publication or default-policy change is made.']))


def trial(out,dest,mode):
    dest.mkdir();tick=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);input_seconds=time.perf_counter()-tick
    started=tick;phases=Counter();total=Counter();solvercounts=Counter();cases=[];results=[];stored={};fallback_rows=[];fallback_results=[]
    check=k.check_certificate if mode=='boundary' else check_full
    discover=k.discover if mode=='boundary' else full_discover
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=prior.prior.LazyBinaryClosureSolver(db,node_limit=p['node_limit'])
        try:
            for row in rows:
                cc=Counter();case=dict(id=row['id']);proof=None;diagnostic=None;root=None
                if mode!='fresh':
                    start=time.perf_counter();cnf,_=native.normalize(row['source'],cc);root=native.token(cnf,cc)
                    if root in stored:
                        proof=base.load(dest/stored[root]);cc['boundary_stream_proof_hits']+=1
                        diagnostic=dict(status='exact-proof-reuse')
                    else:proof,diagnostic=discover(row['source'],cc)
                    case['discovery_seconds']=time.perf_counter()-start
                    start=time.perf_counter()
                    if proof is not None and root not in stored:
                        file=base.key_sha(root)+'-proof.json';prior.write(dest/file,proof);stored[root]=file
                    prior.write(dest/(row['id']+'-diagnostic.json'),diagnostic)
                    case['evidence_persistence_seconds']=time.perf_counter()-start
                start=time.perf_counter();solver.counts=Counter()
                if proof is not None:
                    got=check(row['source'],proof,cc);result=dict(answer=got['answer'],model=got['model'],root=root,authority=mode+'-json');case['route']=mode
                else:
                    wrapped=attempt(solver,row['source'])
                    if wrapped['result'] is None:result=dict(answer=None,model=None,root=None,authority='unresolved')
                    else:
                        result={key:wrapped['result'][key] for key in ('answer','model','root','authority')}
                        fallback_rows.append(row);fallback_results.append(result)
                    case['route']='fresh'
                case['solve_check_seconds']=time.perf_counter()-start;case['diagnostic']=diagnostic;case['counts']=dict(cc);case['solver_counts']=dict(solver.counts)
                total.update(cc);solvercounts.update(solver.counts);phases.update({a:b for a,b in case.items() if a.endswith('_seconds')});cases.append(case);results.append(result)
            tables=old.tables(solver.db);start=time.perf_counter();warmcounts=Counter()
            for row,result,case in zip(rows,results,cases):
                if case['route']!='fresh':
                    c=Counter();cnf,_=native.normalize(row['source'],c);root=native.token(cnf,c)
                    got=check(row['source'],base.load(dest/stored[root]),c);assert got['answer']==result['answer'];warmcounts.update(c)
                else:
                    got=attempt(solver,row['source']);assert (None if got['result'] is None else got['result']['answer'])==result['answer']
            warm=time.perf_counter()-start
            # Successful warm calls should publish no new proof; exhausted fallbacks
            # may resume. The workload records whether this happens explicitly.
            warm_changed=old.tables(solver.db)!=tables;tables=old.tables(solver.db)
        finally:solver.close()
        start=time.perf_counter();readers=prior.prior.audit(db,fallback_rows,fallback_results);coldcounts=Counter()
        for _ in range(2):
            for row,result,case in zip(rows,results,cases):
                if case['route']!='fresh':
                    got=check(row['source'],base.load(dest/stored[result['root']]),coldcounts);assert got['answer']==result['answer']
        cold=time.perf_counter()-start
        start=time.perf_counter();archive=base.archive(db,dest)
        evidence={f:base.load(dest/f) for f in sorted(stored.values())};raw=base.encode(evidence).encode();(dest/'certificates.json.gz').write_bytes(gzip.compress(raw,mtime=0));persistence=time.perf_counter()-start
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],results=results,cases=cases,counts=dict(total),solver_counts=dict(solvercounts),warm_counts=dict(warmcounts),cold_counts=dict(coldcounts),
        input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,
        stored=stored,certificate_bytes=sum((dest/f).stat().st_size for f in stored.values()),certificate_compressed_bytes=(dest/'certificates.json.gz').stat().st_size,
        diagnostic_bytes=sum(f.stat().st_size for f in dest.glob('*-diagnostic.json')),records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items()),
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},archive=archive,readers=readers,warm_changed=warm_changed,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for i,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{i}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=i))
        print(base.encode(dict(completed=i)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
