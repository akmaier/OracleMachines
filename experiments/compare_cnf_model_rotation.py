#!/usr/bin/env python3
"""Fixed unseen deletion stream: ordinary, guarded, and bounded model rotation."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_witness_reuse as previous
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift,clause_set
from experiments.cnf_clause_witness_reuse import reuse_witness
from experiments.cnf_model_rotation import ModelRotation
base=previous.base;ResidualSolver=previous.ResidualSolver;binding=previous.binding;rows=previous.rows
PARENT=Path('experiments/results/cnf-clause-witness-reuse')
MODES=('ordinary','guarded','rotation')
FILES=['experiments/cnf_model_rotation.py','solver/test_cnf_model_rotation.py',
       'experiments/compare_cnf_model_rotation.py','experiments/validate_cnf_model_rotation.py']


def select_cases(solver,original,template_ids):
    templates=[dict(case=i,source=original[i]['source'],root=solver._canonical(original[i]['source'])[2]) for i in template_ids]
    ordered=[[list(c) for c in sorted(clause_set(t['source'],Counter()))] for t in templates]
    cases=[];excluded=[];seen=set()
    for ci in range(max(map(len,ordered))):
        for ti,clauses in enumerate(ordered):
            if ci>=len(clauses):continue
            source=[c for j,c in enumerate(clauses) if j!=ci];_,_,key=solver._canonical(source)
            reason='duplicate' if key in seen else ('cached' if solver.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone() else None)
            seen.add(key)
            item=dict(template=ti,template_case=template_ids[ti],removed_index=ci,removed_clause=clauses[ci],source=source,root=key)
            if reason:excluded.append(dict(**item,reason=reason))
            else:cases.append(dict(case=len(cases),**item))
    seeds=[dict(source=original[i+1]['source'],root=solver._canonical(original[i+1]['source'])[2]) for i in template_ids]
    return dict(cases=cases,excluded=excluded,templates=templates,seeds=seeds)


def worker(out,protocol,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=base.load(protocol['parent']['path']);cases=catalog['cases'];results=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path)
        solver=ResidualSolver(path,node_limit=protocol['node_limit']);initial=rows(solver);setup=Counter()
        bank=ExtensionBank(catalog['templates'],setup) if mode!='ordinary' else None
        engine=ModelRotation(solver,catalog['templates'],catalog['seeds'],flip_limit=protocol['flip_limit']) if mode=='rotation' else None
        if engine:engine.drain()
        setup_ids=sorted(map(base.key_sha,set(rows(solver))-set(initial)));setup_seconds=time.perf_counter()-start
        try:
            for visit in range(protocol['visits']):
                for case in cases:
                    tick=time.perf_counter();before=rows(solver);counts=Counter();solver.counts=Counter()
                    witness=reuse_witness(solver,bank,case['source'],counts) if bank else None
                    certificate=propose(solver,bank,case['source'],counts) if bank and witness is None and not counts.get('witness_query_already_known') else None
                    if certificate is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],certificate,counts)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None
                    if engine and model is not None:
                        engine.observe(case['source'],model,dict(kind='query',index=len(results)));engine.drain()
                    after=rows(solver);assert before.items()<=after.items()
                    results.append(dict(case=case['case'],visit=visit,source=case['source'],guard=certificate,witness=witness,
                        target=[list(c) for c in target],assignment=assignment,child=child,answer=child['answer'],model=model,
                        new_nodes=len(after)-len(before),new_ids=sorted(map(base.key_sha,set(after)-set(before))),
                        guard_counts=dict(counts),premise_counts=premise_counts,seconds=time.perf_counter()-tick))
            final=rows(solver);assert initial.items()<=final.items()
            state=engine.state() if engine else None
        except BaseException:
            state=engine.state() if engine else None;solver.close();base.write(out/'partial.json',results);base.write(out/'rotation.json',state);base.archive(path,out);raise
        else:solver.close()
        cold=previous.audit(path,results)
        base.write(out/'queries.json',results);base.write(out/'rotation.json',state)
        archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(cases),visits=protocol['visits'],positive=sum(r['answer'] for r in results if r['visit']==0),
        guard_uses=sum(r['guard'] is not None for r in results if r['visit']==0),new_nodes=len(final)-len(initial),nodes=len(final),
        expanded_nodes=sum(r['child']['metrics'].get('expanded_nodes',0) for r in results),
        split_nodes=sum(r['child']['metrics'].get('split_nodes',0) for r in results),
        repeat_new_nodes=sum(r['new_nodes'] for r in results if r['visit']),
        rotation_publications=0 if state is None else state['counts'].get('rotation_publications',0),
        rotation_attempts=0 if state is None else state['counts'].get('rotation_flip_attempts',0),
        setup_new_nodes=len(setup_ids),setup_seconds=setup_seconds,query_seconds=sum(r['seconds'] for r in results),cold_seconds=cold['seconds'],
        compression_seconds=archive['seconds'],wall_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=sum((out/p).stat().st_size for p in ('queries.json','rotation.json')),row_digest=base.key_sha(base.encode(sorted(final.items()))))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),rotation=binding(out/'rotation.json'),
        archive=archive,cold=cold,setup_counts=dict(setup),setup_ids=setup_ids))
    print(base.encode(summary),flush=True)


def run(out):
    out.mkdir(exist_ok=False);prior=base.load(PARENT/'validation.json');sources=dict(prior['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    sources.update({p:base.sha(p) for p in FILES})
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),prior_report=binding(PARENT/'report.json'),
        original_cases=binding('experiments/results/cnf-join-transfer/cases.json'),screen=binding(PARENT/'rotation-screen.json'),source_fingerprints=sources,
        template_ids=[6,8,12],node_limit=100000,flip_limit=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='All exact single-clause deletions of sorted clause sets, round-robin clause index then template order; deduplicate full canonical roots and exclude roots already in the latest reference union, before any solving.',
        limitations=['Constructed development inputs include two known rotation positives; this is not a blind or independent holdout.',
            'All modes inherit the full latest 1169-node reference union. Earlier acquisition costs remain sunk and separately documented, not erased.',
            'Rotation is established transition-clause witness reuse. Three checked UNSAT templates and three checked SAT deletion seeds are supplied.',
            'One witness per deleted clause, FIFO exploration, at most 64 flips per template over the entire stream; budgets never reset per query. Every flip scans the full template.',
            'Runtime matching uses only exact CNF clause sets, not case labels. Both bank modes check the direct query cache first, then checked SAT witness transfer and the existing UNSAT guard.',
            'Three process triples balance mode position. Whole time includes restoration, discovery, checks, search, bookkeeping, cold checking, sidecar writing and compression; imports/final report write excluded.',
            'Failed and unprocessed rotations remain stored. Failure or budget exhaustion never certifies UNSAT. Original structural coverage and all previous archives remain unchanged.'])
    base.write(out/'protocol.json',protocol);start=time.perf_counter();parent=base.load(protocol['parent']['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'seed';base.restore_archive(parent['reference_union'],path);cold=previous.audit(path,[])
        solver=ResidualSolver(path)
        try:catalog=select_cases(solver,base.load(protocol['original_cases']['path']),protocol['template_ids'])
        finally:solver.close()
    screen=base.load(protocol['screen']['path']);selected={c['root'] for c in catalog['cases']}
    assert len(screen['candidates'])==2
    for c in screen['candidates']:assert c['root'] in selected
    base.write(out/'cases.json',catalog)
    base.write(out/'preflight.json',dict(parent=protocol['parent'],checked=cold,selected=len(catalog['cases']),excluded=len(catalog['excluded']),seconds=time.perf_counter()-start))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
