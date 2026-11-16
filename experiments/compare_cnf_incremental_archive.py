#!/usr/bin/env python3
"""Matched full scans, transactional size ledger, and guarded insertion deltas."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unsat_support as prior
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_incremental_archive import ResidualAppendCursor
from experiments.cnf_unsat_support import CoreBank
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift,clause_set
from experiments.cnf_clause_witness_reuse import reuse_witness
base=prior.base;ResidualSolver=prior.ResidualSolver;rows=prior.rows;binding=prior.binding
PARENT=Path('experiments/results/cnf-unsat-support')
MODES=('scanned','ledger','delta')
FILES=['experiments/cnf_incremental_archive.py','solver/test_cnf_incremental_archive.py',
       'solver/test_cnf_accounted_residuals.py','experiments/compare_cnf_incremental_archive.py','experiments/validate_cnf_incremental_archive.py']


def inputs(solver,protocol):
    templates=base.load(protocol['template_catalog']['path'])['templates']
    known={r['query_root'] for r in base.load(protocol['previous_decisions']['path'])};seen=set();selected=[];selection=[]
    for template in templates:
        clauses=[list(c) for c in sorted(clause_set(template['source'],Counter()))];available=[];previous=cached=duplicates=0
        for a,b in combinations(range(len(clauses)),2):
            source=[c for i,c in enumerate(clauses) if i not in (a,b)];_,_,key=solver._canonical(source)
            if key in known:previous+=1;continue
            if key in seen:duplicates+=1;continue
            seen.add(key)
            if solver.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone():cached+=1;continue
            available.append((base.key_sha('unsat-support-double-deletion-v1:'+key),a,b,key))
        available.sort();assert len(available)>=protocol['per_template']
        selection.append(dict(template_case=template['case'],candidates=len(clauses)*(len(clauses)-1)//2,previous_queries=previous,cached_exclusions=cached,
            duplicates=duplicates,available_digest=base.key_sha(base.encode(available)),selected=protocol['per_template']))
        selected.append([dict(template_case=template['case'],rank=rank,removed=[clauses[a],clauses[b]],source=[c for i,c in enumerate(clauses) if i not in (a,b)],root=key)
                         for rank,(_,a,b,key) in enumerate(available[:protocol['per_template']])])
    cases=[dict(case=rank*len(templates)+ti,**selected[ti][rank]) for rank in range(protocol['per_template']) for ti in range(len(templates))]
    return dict(cases=cases,selection=selection)


def worker(out,protocol,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=base.load(protocol['parent']['path']);records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path)
        solver=(ResidualSolver if mode=='scanned' else AccountedResidualSolver)(path,node_limit=protocol['node_limit']);initial=rows(solver)
        cursor=ResidualAppendCursor(solver) if mode=='delta' else None
        try:
            tick=time.perf_counter();cores=base.load(protocol['cores']['path']);bank=CoreBank(solver,cores)
            extensions=ExtensionBank(base.load(protocol['bank_catalog']['path'])['bank']);bank_seconds=time.perf_counter()-tick
            assert not cursor.take() if cursor else rows(solver)==initial
            setup_seconds=time.perf_counter()-start
            for visit in range(protocol['visits']):
                for case in catalog['cases']:
                    tick=time.perf_counter();before=None if cursor else rows(solver);solver.counts=Counter();counts=Counter()
                    normalized,_,key=solver._canonical(case['source']);known=solver._read(key,normalized,purpose='direct_query')
                    support=bank.reuse(case['source']) if known is None else None
                    witness=reuse_witness(solver,extensions,case['source'],counts) if known is None and support is None else None
                    guard=propose(solver,extensions,case['source'],counts) if known is None and support is None and witness is None else None
                    if guard is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],guard,counts)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None
                    if cursor:added=cursor.take()
                    else:
                        after=rows(solver);assert before.items()<=after.items();added={k:after[k] for k in set(after)-set(before)}
                    records.append(dict(case=case['case'],visit=visit,source=case['source'],guard=guard,witness=witness,core=support,
                        target=[list(c) for c in target],assignment=assignment,child=child,answer=child['answer'],model=model,
                        new_nodes=len(added),new_ids=sorted(map(base.key_sha,added)),counts=dict(counts),premise_counts=premise_counts,seconds=time.perf_counter()-tick))
            final=rows(solver);assert initial.items()<=final.items()
            census=solver.db.execute('SELECT count(*),coalesce(sum(length(id)+length(payload)),0) FROM cnf_residual_v1').fetchone()
            assert solver.archive_storage()==census
            accounting=dict(censuses=getattr(solver,'accounting_censuses',None),cursor={} if cursor is None else dict(cursor.stats),final_nodes=census[0],final_payload_units=census[1],
                full_row_snapshots=(3 if cursor else 4+2*len(records)),final_full_preservation=True)
        except BaseException:
            solver.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:solver.close()
        cold=prior.old.previous.audit(path,records);base.write(out/'queries.json',records);archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(catalog['cases']),visits=protocol['visits'],positive=sum(r['answer'] for r in records if r['visit']==0),
        core_hits=sum(r['core'] is not None for r in records if r['visit']==0),witness_publications=sum(r['witness'] is not None for r in records),
        guard_uses=sum(r['guard'] is not None for r in records if r['visit']==0),nodes=len(final),new_nodes=len(final)-len(initial),
        expanded_nodes=sum(r['child']['metrics'].get('expanded_nodes',0) for r in records),split_nodes=sum(r['child']['metrics'].get('split_nodes',0) for r in records),
        repeat_new_nodes=sum(r['new_nodes'] for r in records if r['visit']),bank_seconds=bank_seconds,setup_seconds=setup_seconds,
        query_seconds=sum(r['seconds'] for r in records),first_query_seconds=sum(r['seconds'] for r in records if r['visit']==0),
        repeat_query_seconds=sum(r['seconds'] for r in records if r['visit']),cold_seconds=cold['seconds'],compression_seconds=archive['seconds'],wall_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=(out/'queries.json').stat().st_size,row_digest=base.key_sha(base.encode(sorted(final.items()))))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),cores=protocol['cores'],archive=archive,cold=cold,accounting=accounting,bank_counts=dict(bank.counts)))
    print(base.encode(summary),flush=True)


def run(out):
    out.mkdir(exist_ok=False);sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});parent=base.load(PARENT/'checkpoint.json')
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,template_catalog=binding('experiments/results/cnf-model-rotation/cases.json'),
        previous_decisions=parent['unsat_support_decisions'],cores=binding(PARENT/'all-0/cores.json'),bank_catalog=binding(PARENT/'cases.json'),
        node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Same salted full-key order over double deletions; exclude all 192 previously answered queries, including guarded answers without direct roots, then exclude any cached full root. Take the next 64 per template and interleave ranks.',
        limitations=['All modes use the full latest 13869-key union and identical persisted 145-core and 260-template banks. Initial core extraction and historical acquisition remain separately charged.',
            'This experiment changes accounting, not search or recognition. Scanned uses the unchanged solver and complete per-query row inventories; ledger uses the existing transactional size ledger; delta additionally reads only guarded committed insertion suffixes.',
            'The delta path requires one exclusively owned append-only connection. Local rewrites and nonmonotone rowids reject; committed external/schema changes invalidate. Conflicting ignored inserts may trigger the inherited ledger full census.',
            'A full initial inventory, final preservation comparison, final independent size census, complete cold replay and compression remain charged. Accounting metadata changes physical archive bytes, not proof rows.',
            'Three balanced fresh-process triples with two visits. No tests/builds/profilers overlap. The worker clock excludes process launch, imports, CLI protocol/catalog reads and final report writing.',
            'Constructed development inputs; no arbitrary-SAT efficiency claim. A delta session is not a durable trust marker and is rebuilt on reopening.'])
    base.write(out/'protocol.json',protocol);start=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'seed';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=inputs(solver,protocol)
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-start,selection=catalog['selection']))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(x['path'])['summary'] for x in samples if x['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
