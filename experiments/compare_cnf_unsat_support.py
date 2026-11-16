#!/usr/bin/env python3
"""Checked proof supports on a fixed sample of unseen double deletions."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_model_rotation as old
from experiments.cnf_unsat_support import SupportExtractor,CoreBank
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift,clause_set
from experiments.cnf_clause_witness_reuse import reuse_witness
base=old.base;ResidualSolver=old.ResidualSolver;rows=old.rows;binding=old.binding
PARENT=Path('experiments/results/cnf-model-rotation')
MODES=('guarded','three','all')
FILES=['experiments/cnf_unsat_support.py','solver/test_cnf_unsat_support.py',
       'experiments/compare_cnf_unsat_support.py','experiments/validate_cnf_unsat_support.py']


def inputs(solver,parent,count):
    prior=base.load(PARENT/'cases.json');templates=prior['templates'];selected=[];selection=[];seen=set()
    for template in templates:
        clauses=[list(c) for c in sorted(clause_set(template['source'],Counter()))];available=[];excluded=0;duplicates=0
        for a,b in combinations(range(len(clauses)),2):
            source=[c for i,c in enumerate(clauses) if i not in (a,b)];_,_,key=solver._canonical(source)
            if key in seen:duplicates+=1;continue
            seen.add(key)
            if solver.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone():excluded+=1;continue
            available.append((base.key_sha('unsat-support-double-deletion-v1:'+key),a,b,key))
        available.sort();assert len(available)>=count
        selection.append(dict(template_case=template['case'],candidates=len(clauses)*(len(clauses)-1)//2,cached_exclusions=excluded,duplicates=duplicates,
            available_digest=base.key_sha(base.encode(available)),selected=count))
        chosen=[]
        for rank,(_,a,b,key) in enumerate(available[:count]):
            chosen.append(dict(template_case=template['case'],rank=rank,removed=[clauses[a],clauses[b]],source=[c for i,c in enumerate(clauses) if i not in (a,b)],root=key))
        selected.append(chosen)
    cases=[dict(case=rank*len(templates)+ti,**selected[ti][rank]) for rank in range(count) for ti in range(len(templates))]
    single=prior['cases']+prior['excluded'];bank=[dict(source=x['source'],root=x['root']) for x in single]
    sources=[dict(source=t['source'],label='template-'+str(t['case'])) for t in templates]
    sources += [dict(source=r['source'],label='deletion-'+str(r['case'])) for r in base.load(parent['model_rotation_decisions']['path']) if not r['answer']]
    return dict(cases=cases,selection=selection,bank=bank,support_sources=sources)


def prepare(solver,catalog,mode):
    if mode=='guarded':return [],{},0.0
    start=time.perf_counter();extractor=SupportExtractor(solver);sources=catalog['support_sources'][:3] if mode=='three' else catalog['support_sources']
    unique={}
    with patch.object(solver,'_expand',side_effect=AssertionError('Fresh support extraction')):
        for source in sources:
            core=extractor.source_core(source['source']);unique.setdefault(base.encode(core['source']),dict(label=source['label'],**core))
    cores=sorted(unique.values(),key=lambda c:(len(c['source']),c['source']))
    return cores,dict(extractor.counts),time.perf_counter()-start


def worker(out,protocol,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=base.load(protocol['parent']['path']);records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path,node_limit=protocol['node_limit']);initial=rows(solver)
        try:
            cores,extraction_counts,extraction_seconds=prepare(solver,catalog,mode)
            setup=Counter();extensions=ExtensionBank(catalog['bank'],setup);bank=CoreBank(solver,cores) if cores else None
            setup_ids=sorted(map(base.key_sha,set(rows(solver))-set(initial)));setup_seconds=time.perf_counter()-start
            for visit in range(protocol['visits']):
                for case in catalog['cases']:
                    tick=time.perf_counter();before=rows(solver);solver.counts=Counter();counts=Counter()
                    normalized,_,key=solver._canonical(case['source']);known=solver._read(key,normalized,purpose='direct_query')
                    support=bank.reuse(case['source']) if known is None and bank else None
                    witness=reuse_witness(solver,extensions,case['source'],counts) if known is None and support is None else None
                    guard=propose(solver,extensions,case['source'],counts) if known is None and support is None and witness is None else None
                    if guard is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],guard,counts)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None
                    after=rows(solver);assert before.items()<=after.items()
                    records.append(dict(case=case['case'],visit=visit,source=case['source'],guard=guard,witness=witness,core=support,
                        target=[list(c) for c in target],assignment=assignment,child=child,answer=child['answer'],model=model,
                        new_nodes=len(after)-len(before),new_ids=sorted(map(base.key_sha,set(after)-set(before))),
                        counts=dict(counts),premise_counts=premise_counts,seconds=time.perf_counter()-tick))
            final=rows(solver);assert initial.items()<=final.items()
        except BaseException:
            solver.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:solver.close()
        cold=old.previous.audit(path,records);base.write(out/'queries.json',records);base.write(out/'cores.json',cores)
        archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(catalog['cases']),visits=protocol['visits'],positive=sum(r['answer'] for r in records if r['visit']==0),
        cores=len(cores),core_hits=sum(r['core'] is not None for r in records if r['visit']==0),
        witness_publications=sum(r['witness'] is not None for r in records),guard_uses=sum(r['guard'] is not None for r in records if r['visit']==0),
        nodes=len(final),new_nodes=len(final)-len(initial),preparation_new_nodes=len(setup_ids),
        expanded_nodes=sum(r['child']['metrics'].get('expanded_nodes',0) for r in records),split_nodes=sum(r['child']['metrics'].get('split_nodes',0) for r in records),
        repeat_new_nodes=sum(r['new_nodes'] for r in records if r['visit']),extraction_seconds=extraction_seconds,setup_seconds=setup_seconds,
        query_seconds=sum(r['seconds'] for r in records),first_query_seconds=sum(r['seconds'] for r in records if r['visit']==0),
        repeat_query_seconds=sum(r['seconds'] for r in records if r['visit']),cold_seconds=cold['seconds'],compression_seconds=archive['seconds'],wall_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=sum((out/p).stat().st_size for p in ('queries.json','cores.json')),row_digest=base.key_sha(base.encode(sorted(final.items()))))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),cores=binding(out/'cores.json'),archive=archive,cold=cold,setup_ids=setup_ids,
        extraction_counts=extraction_counts,bank_counts={} if bank is None else dict(bank.counts),extension_setup_counts=dict(setup)))
    print(base.encode(summary),flush=True)


def run(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,screen=binding(out/'screen.json') if (out/'screen.json').exists() else None,
        node_limit=100000,visits=2,per_template=64,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='For each of three templates enumerate all double deletions, exclude already cached full roots and duplicates; select 64 smallest SHA256(salt+full canonical key), then interleave ranks. No support containment or prospective answer used.',
        limitations=['Constructed development neighbors of three known UNSAT templates, not an arbitrary-CNF efficiency guarantee or independent holdout.',
            'All arms inherit the full 9104-key reference union and all 260 known single-deletion templates. Positive witness transfer and exact negative guards remain common controls.',
            'three extracts cores from the original three templates; all also extracts the 185 saved UNSAT single deletions. Deduplicate raw clause sets. Every derived node is checked by the frozen residual checker.',
            'Each fresh process pays extraction, recognition, publication, search, full archive cold checking and compression. Earlier acquisition and selection costs remain separately reported.',
            'No minimality claim. Exact subset matching uses common coordinates. Cold proof certificates work without the extraction algorithm or source template.',
            'Three balanced process triples, two query visits; no tests, builds or profilers alongside timed workers. All previous rows and failed cost comparisons remain retained.'])
    base.write(out/'protocol.json',protocol);start=time.perf_counter();parent=base.load(protocol['parent']['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=inputs(solver,parent,protocol['per_template'])
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-start,selection=catalog['selection'],peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
