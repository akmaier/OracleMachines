#!/usr/bin/env python3
"""Fresh input transfer with acquired and online feedback controls.

Each run starts with an empty database, shares exact residuals within the frozen
panel, repeats all queries warm, and replays both cold readers before archiving.
Descriptions and exhaustive labels are withheld from every solving workflow.
"""
from collections import Counter
from itertools import permutations
from pathlib import Path
import json,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_strengthened_cross_pivot as prior
from experiments import cnf_source_feedback_native as compiler
from experiments.cnf_fresh_seed_panel import panel,truth
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
base=prior.base;old=prior.old;k=compiler.feedback
PARENT=Path('experiments/results/cnf-strengthened-cross-pivot')
MODES=('fresh','prepared','online')
FILES=('experiments/cnf_fresh_seed_panel.py','experiments/cnf_source_feedback_native.py',
       'experiments/compare_cnf_fresh_seed_feedback.py','solver/test_cnf_source_feedback_native.py')


def write(path,data):
    path.write_text(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    rows,desc=panel();assert rows==base.load(out/'panel.json') and desc==base.load(out/'descriptions.json')
    assert base.sha(out/'panel.json')=='d29e58c65824ca52f58e6b4f7b0ea22a4464c52770e88f01df5392861a84ec95'
    labels={r['id']:truth(r['source']) for r in rows};base.write(out/'truth.json',labels)
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        panel=old.binding(out/'panel.json'),descriptions=old.binding(out/'descriptions.json'),truth=old.binding(out/'truth.json'),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=list(map(list,permutations(MODES))),
        chains={r['id']:old.binding(out/(r['id']+'-chain.json')) for r in rows},fresh_node_limit=256,unit_work_limit=262144,
        discovery_limits=dict(round_limit=2,pivot_limit=16,probe_limit=512,work_limit=2097152,trace_limit=256),
        limitations=[
        '36 fresh synthetic CNFs, frozen before compiler implementation, not a representative SAT distribution. Descriptions and exhaustive truth labels are audit-only.',
        'The existing feedback kernel is unchanged. It is a refutation method, not a SAT decider; every open outcome falls back to the same existing fresh solver.',
        'Fresh performs no feedback discovery. Prepared loads previously acquired chains; their acquisition is additional. Online discovers and persists every chain and search history during this run.',
        'All modes share exact residuals within one initially empty panel archive, then repeat the panel warm. Prepared and online warm calls load and recheck acquired chains before any feedback root hit.',
        'Cold replay uses both source-only readers and checks SAT models against original inputs. Persistence includes SQLite compression. Timing includes loading and hashing; interpreter startup and final lineage audit are additional.',
        'Feedback uses two bounded rounds; fresh retains its different 256-node allowance. Equal elapsed budgets or algorithmic completeness are not claimed.',
        'No historical B13 source inputs, templates, closures or cursor histories are required by the new compiler. Imported helper implementation lineage remains, but prior scientific artifacts are unchanged.',
        'Only exact normalized residual identity is shared; this is not full isomorphism or semantic equivalence recognition. Graph size and total compiler work remain unbounded by the shortcut allowance.']))


def audit(db,rows,results):
    wrapped=[dict(status='sat' if r['answer'] else 'unsat',result=r) for r in results]
    _,readers=prior.previous.audit(db,rows,wrapped)
    return readers


def trial(out,dest,mode):
    dest.mkdir();start=time.perf_counter();p=base.load(out/'protocol.json');rows=old.bound(p['panel'])
    input_seconds=time.perf_counter()-start;results=[];per_case=[];chains={};total=Counter();nc=Counter()
    phases=Counter();warm_counts=Counter();warm_native=Counter();loaded_bytes=0;history_bytes=0
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=LazyBinaryClosureSolver(db,node_limit=p['fresh_node_limit'])
        try:
            for row in rows:
                cc=Counter();record=dict(id=row['id']);chain=None
                if mode=='prepared':
                    tick=time.perf_counter();chain=old.bound(p['chains'][row['id']]);record['load_chain_seconds']=time.perf_counter()-tick
                    loaded_bytes+=Path(p['chains'][row['id']]['path']).stat().st_size
                elif mode=='online':
                    tick=time.perf_counter();chain,search=k.discover(row['source'],cc,**p['discovery_limits']);record['discovery_seconds']=time.perf_counter()-tick
                    tick=time.perf_counter();write(dest/(row['id']+'-chain.json'),chain);write(dest/(row['id']+'-search.json'),search)
                    record['history_persistence_seconds']=time.perf_counter()-tick
                    history_bytes+=sum((dest/(row['id']+'-'+suffix+'.json')).stat().st_size for suffix in ('chain','search'))
                chains[row['id']]=chain;tick=time.perf_counter();solver.counts=Counter()
                if chain is not None and chain['status']=='refuted':
                    root=compiler.compile_program(solver,row['source'],chain,cc,unit_work_limit=p['unit_work_limit'])
                    result=dict(answer=False,root=root,model=None,authority='native');record['route']='feedback'
                else:
                    fresh=solver.solve(row['source']);result={key:fresh[key] for key in ('answer','root','model','authority')};record['route']='fresh'
                record['solve_seconds']=time.perf_counter()-tick;nc.update(solver.counts);total.update(cc)
                record['counts']=dict(cc);record['native_counts']=dict(solver.counts)
                for key,value in record.items():
                    if key.endswith('_seconds'):phases[key]+=value
                results.append(result);per_case.append(record)
            tables=old.tables(solver.db);records=sum(map(len,tables.values()));record_bytes=sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            tick=time.perf_counter()
            for row,result in zip(rows,results):
                cc=Counter();solver.counts=Counter();chain=None
                if mode!='fresh':
                    file=Path(p['chains'][row['id']]['path']) if mode=='prepared' else dest/(row['id']+'-chain.json')
                    chain=base.load(file)
                if chain is not None and chain['status']=='refuted':
                    assert compiler.compile_program(solver,row['source'],chain,cc,unit_work_limit=p['unit_work_limit'])==result['root']
                else:
                    got=solver.solve(row['source']);assert (got['answer'],got['root'])==(result['answer'],result['root'])
                warm_counts.update(cc);warm_native.update(solver.counts)
            warm=time.perf_counter()-tick;assert old.tables(solver.db)==tables
        finally:solver.close()
        tick=time.perf_counter();readers=audit(db,rows,results);cold=time.perf_counter()-tick
        tick=time.perf_counter();archive=base.archive(db,dest);persistence=time.perf_counter()-tick
    # Metadata serialization is reported separately from the completed workflow.
    report=dict(mode=mode,panel=p['panel'],results=results,cases=per_case,input_seconds=input_seconds,phases=dict(phases),warm_seconds=warm,
        cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,counts=dict(total),native_counts=dict(nc),
        warm_counts=dict(warm_counts),warm_native_counts=dict(warm_native),readers=readers,archive=archive,records=records,record_bytes=record_bytes,
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},loaded_chain_bytes=loaded_bytes,new_history_bytes=history_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    base.write(dest/'report.json',report)


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
