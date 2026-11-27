#!/usr/bin/env python3
"""Charge online discovery, memo recognition, proof checking and cold replay."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_fresh_seed_feedback as prior
from experiments import cnf_feedback_cofactor_dag as kernel
from experiments.cnf_conditioning_transfer_panel import panel,truth
base=prior.base;old=prior.old;write=prior.write
PARENT=Path('experiments/results/cnf-fresh-seed-feedback')
MODES=('fresh','flat','tree','memo')
FILES=('experiments/cnf_conditioning_transfer_panel.py','experiments/cnf_feedback_cofactor_dag.py',
       'experiments/compare_cnf_feedback_cofactor_dag.py','solver/test_cnf_feedback_cofactor_dag.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json');freeze=base.load(out/'freeze.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    held,desc=panel();assert held==base.load(out/'heldout.json') and desc==base.load(out/'heldout-descriptions.json')
    assert base.sha(out/'heldout.json')==freeze['heldout_sha256']
    development=base.load(out/'development.json');rows=development+held
    for r in base.load(PARENT/'remaining.json')['cases']:desc['d-'+r['id']]=r['description']
    base.write(out/'panel.json',rows);base.write(out/'descriptions.json',desc);base.write(out/'truth.json',{r['id']:truth(r['source']) for r in rows})
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),freeze=old.binding(out/'freeze.json'),
        panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES[i:]+MODES[:i]) for i in range(4)],
        limits=freeze['policy'],fresh_node_limit=256,unit_work_limit=262144,limitations=[
        'Six exposed feedback gaps and 24 separately frozen synthetic held-out inputs. Descriptions and exhaustive truth are audit-only; this is not a representative SAT distribution.',
        'Flat runs depth zero; tree and memo allow two additional conditioning levels and the same 64-state ceiling. Only memo uses exact residual plus remaining-depth discovery reuse within each call.',
        'All workflows start empty, share native residuals within one panel order, repeat all queries warm, use both cold authority readers, and compress their archives.',
        'Discovery, normalization, lookup, evidence serialization, checking and fallback search are charged. Online methods retain complete diagnostic searches separately; open internal search histories are omitted only from certificates.',
        'Warm calls load and validate entire saved certificates before negative-root reuse; unresolved states are never SAT authority and fall back to the same existing fresh solver.',
        'Every source compilation shares a single direct-unit allowance across all leaf compilers. The allowance does not bound other construction, verifier, stack or memory work.',
        'Matched tree/memo comparisons test discovery reuse; native archives may already share the same exact residual graph. Any coverage improvement over flat also spends more conditioning work.',
        'Interpreter startup, report-metadata serialization and the final preservation audit are additional. Short workload timings are machine-specific. No default policy or unrestricted SAT guarantee changes.']))


def trial(out,dest,mode):
    dest.mkdir();start=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel']);input_seconds=time.perf_counter()-start
    results=[];records=[];total=Counter();native_counts=Counter();phases=Counter();cert_bytes=0;search_bytes=0
    limits={**p['limits'],'depth_limit':0 if mode=='flat' else p['limits']['depth_limit']}
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=prior.LazyBinaryClosureSolver(db,node_limit=p['fresh_node_limit'])
        try:
            for row in rows:
                cc=Counter();record=dict(id=row['id']);certificate=None
                if mode!='fresh':
                    tick=time.perf_counter();certificate,attempts=kernel.discover(row['source'],cc,reuse=mode=='memo',**limits);record['discovery_seconds']=time.perf_counter()-tick
                    tick=time.perf_counter();write(dest/(row['id']+'-certificate.json'),certificate);write(dest/(row['id']+'-searches.json'),attempts)
                    record['history_persistence_seconds']=time.perf_counter()-tick
                    cert_bytes+=(dest/(row['id']+'-certificate.json')).stat().st_size;search_bytes+=(dest/(row['id']+'-searches.json')).stat().st_size
                tick=time.perf_counter();solver.counts=Counter()
                if certificate is not None and certificate['status']=='refuted':
                    root=kernel.compile_program(solver,row['source'],certificate,cc,unit_work_limit=p['unit_work_limit'])
                    result=dict(answer=False,model=None,root=root,authority='native');record['route']='feedback'
                else:
                    if certificate is not None:kernel.validate(row['source'],certificate,cc)
                    got=solver.solve(row['source']);result={key:got[key] for key in ('answer','model','root','authority')};record['route']='fresh'
                record['solve_check_seconds']=time.perf_counter()-tick;record['counts']=dict(cc);record['native_counts']=dict(solver.counts)
                total.update(cc);native_counts.update(solver.counts);phases.update({k:v for k,v in record.items() if k.endswith('_seconds')})
                results.append(result);records.append(record)
            tables=old.tables(solver.db);wc=Counter();wn=Counter();tick=time.perf_counter()
            for row,result in zip(rows,results):
                cc=Counter();solver.counts=Counter();certificate=None if mode=='fresh' else base.load(dest/(row['id']+'-certificate.json'))
                if certificate is not None and certificate['status']=='refuted':
                    assert kernel.compile_program(solver,row['source'],certificate,cc,unit_work_limit=p['unit_work_limit'])==result['root']
                else:
                    if certificate is not None:kernel.validate(row['source'],certificate,cc)
                    got=solver.solve(row['source']);assert (got['answer'],got['root'])==(result['answer'],result['root'])
                wc.update(cc);wn.update(solver.counts)
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();readers=prior.audit(db,rows,results);cold=time.perf_counter()-tick
        tick=time.perf_counter();archive=base.archive(db,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(mode=mode,panel=p['panel'],results=results,cases=records,counts=dict(total),native_counts=dict(native_counts),warm_counts=dict(wc),warm_native_counts=dict(wn),
        input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,
        certificate_bytes=cert_bytes,search_bytes=search_bytes,records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items()),
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},archive=archive,readers=readers,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
