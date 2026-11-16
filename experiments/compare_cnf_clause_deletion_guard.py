#!/usr/bin/env python3
"""Controlled SAT decision experiment; structural coverage remains separate."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift,replay

PARENT=Path('experiments/results/cnf-join-transfer')
MODES=('ordinary','guarded')
FILES=['experiments/cnf_clause_deletion_guard.py','solver/test_cnf_clause_deletion_guard.py',
       'experiments/compare_cnf_clause_deletion_guard.py','experiments/validate_cnf_clause_deletion_guard.py']


def binding(path):return dict(path=str(path),sha256=base.sha(path))
def rows(solver):return dict(solver.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY rowid'))


def audit(path,records):
    before=base.sha(path);start=time.perf_counter();solver=ResidualSolver(path);outputs=[]
    try:
        solver.db.execute('PRAGMA query_only=ON')
        with patch.object(solver,'_expand',side_effect=AssertionError('Fresh cold search')):
            for key in rows(solver):assert solver._read(key) is not None
            checked=len(solver.checked)
            for row in records:
                result=replay(solver,row['source'],row['guard'],row['child'])
                assert result['answer']==row['answer']
                expected=None if row['model'] is None else {int(k):v for k,v in row['model'].items()}
                assert result['model']==expected
                outputs.append(result['answer'])
    finally:solver.close();assert base.sha(path)==before
    return dict(checked_nodes=checked,query_answers=outputs,no_acquisition=True,seconds=time.perf_counter()-start)


def prepare(out,protocol):
    start=time.perf_counter();cases=base.load(protocol['cases']['path']);templates=[];records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';solver=ResidualSolver(path,node_limit=protocol['node_limit'])
        try:
            for case in cases[::2]:
                result=solver.solve(case['source']);templates.append(dict(source=case['source'],root=result['root'],case=case['case']))
                records.append(dict(case=case['case'],source=case['source'],guard=None,child=result,answer=result['answer'],model=result['model']))
            nodes=len(rows(solver))
        except BaseException:
            solver.close();dest=out/'failed-seed';dest.mkdir();base.archive(path,dest);raise
        else:solver.close()
        cold=audit(path,records);dest=out/'seed';dest.mkdir();archive=base.archive(path,dest)
    data=dict(templates=templates,records=records,nodes=nodes,archive=archive,cold=cold,seconds=time.perf_counter()-start)
    base.write(out/'seed.json',data);return data


def worker(out,protocol,seed,mode):
    out.mkdir();start=time.perf_counter();cases=base.load(protocol['cases']['path'])[1::2];results=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(seed['archive'],path)
        solver=ResidualSolver(path,node_limit=protocol['node_limit']);initial=rows(solver);setup=Counter()
        bank=ExtensionBank(seed['templates'],setup) if mode=='guarded' else None
        setup_seconds=time.perf_counter()-start
        try:
            for visit in range(protocol['visits']):
                for case in cases:
                    tick=time.perf_counter();before=rows(solver);counts=Counter();solver.counts=Counter()
                    certificate=propose(solver,bank,case['source'],counts) if bank else None
                    if certificate is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],certificate,counts)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None
                    after=rows(solver);assert before.items()<=after.items()
                    results.append(dict(case=case['case'],visit=visit,source=case['source'],guard=certificate,
                        target=[list(c) for c in target],assignment=assignment,child=child,answer=child['answer'],model=model,
                        new_nodes=len(after)-len(before),new_ids=sorted(map(base.key_sha,set(after)-set(before))),
                        guard_counts=dict(counts),premise_counts=premise_counts,seconds=time.perf_counter()-tick))
            final=rows(solver);assert initial.items()<=final.items()
        except BaseException:
            solver.close();base.write(out/'partial.json',results);base.archive(path,out);raise
        else:solver.close()
        cold=audit(path,results)
        base.write(out/'queries.json',results)
        archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(cases),visits=protocol['visits'],positive=sum(r['answer'] for r in results if r['visit']==0),
        guard_uses=sum(r['guard'] is not None for r in results if r['visit']==0),new_nodes=len(final)-len(initial),nodes=len(final),
        expanded_nodes=sum(r['child']['metrics'].get('expanded_nodes',0) for r in results),
        split_nodes=sum(r['child']['metrics'].get('split_nodes',0) for r in results),
        repeat_new_nodes=sum(r['new_nodes'] for r in results if r['visit']),
        setup_seconds=setup_seconds,query_seconds=sum(r['seconds'] for r in results),cold_seconds=cold['seconds'],
        compression_seconds=archive['seconds'],wall_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=(out/'queries.json').stat().st_size,row_digest=base.key_sha(base.encode(sorted(final.items()))))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),archive=archive,cold=cold,setup_counts=dict(setup)))
    print(base.encode(summary),flush=True)


def run(out):
    out.mkdir(exist_ok=False);previous=base.load(PARENT/'validation.json');sources=dict(previous['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    sources.update({p:base.sha(p) for p in FILES})
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),cases=binding(PARENT/'cases.json'),source_fingerprints=sources,
        node_limit=100000,visits=2,orders=[MODES,tuple(reversed(MODES))],
        limitations=['Optional SAT decision wrapper around the unchanged ResidualSolver; not a structural-coverage policy or new unrestricted complexity claim.',
            'All twelve undeleted templates are solved and checked before either mode. Fresh UNSAT acquisition is charged separately; only actual checked UNSAT can activate a guard.',
            'The query bank matches exact one-clause extensions in shared input coordinates. It does not search arbitrary renamings or hidden logical implications.',
            'Both modes share the identical reference seed; streams are serial fresh processes, with a second query visit. Full archive auditing, sidecar writing and compression are timed.',
            'Whole clock excludes imports and final summary write. Preparation, independent validation and all prior historical costs remain separate.',
            'These twelve edits are constructed development inputs. An absent or satisfiable premise falls back to ordinary solving; budget failure never yields a verdict.'])
    base.write(out/'protocol.json',protocol);seed=prepare(out,protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'seed.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},
                       'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),seed=binding(out/'seed.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
