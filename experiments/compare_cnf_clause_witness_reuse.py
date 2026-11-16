#!/usr/bin/env python3
"""Matched SAT witness publication with ordinary and UNSAT-guard controls."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift,replay
from experiments.cnf_clause_witness_reuse import reuse_witness,check_witness
from experiments import compare_cnf_clause_deletion_guard as previous

PARENT=Path('experiments/results/cnf-clause-deletion-guard')
MODES=('ordinary','guarded','witness')
FILES=['experiments/cnf_clause_witness_reuse.py','solver/test_cnf_clause_witness_reuse.py',
       'experiments/compare_cnf_clause_witness_reuse.py','experiments/validate_cnf_clause_witness_reuse.py']


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
                if row.get('witness') is not None:
                    assert row['guard'] is None
                    transferred=check_witness(solver,row['source'],row['witness'])
                    expected={int(k):v for k,v in row['model'].items()}
                    assert transferred==expected
                result=replay(solver,row['source'],row['guard'],row['child'])
                assert result['answer']==row['answer']
                expected=None if row['model'] is None else {int(k):v for k,v in row['model'].items()}
                assert result['model']==expected
                outputs.append(result['answer'])
    finally:solver.close();assert base.sha(path)==before
    return dict(checked_nodes=checked,query_answers=outputs,no_acquisition=True,seconds=time.perf_counter()-start)


def worker(out,protocol,seed,mode):
    out.mkdir();start=time.perf_counter();cases=base.load(protocol['cases']['path'])[1::2];results=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(seed['archive'],path)
        solver=ResidualSolver(path,node_limit=protocol['node_limit']);initial=rows(solver);setup=Counter()
        bank=ExtensionBank(seed['templates'],setup) if mode!='ordinary' else None
        setup_seconds=time.perf_counter()-start
        try:
            for visit in range(protocol['visits']):
                for case in cases:
                    tick=time.perf_counter();before=rows(solver);counts=Counter();solver.counts=Counter()
                    witness=reuse_witness(solver,bank,case['source'],counts) if mode=='witness' else None
                    certificate=propose(solver,bank,case['source'],counts) if bank and witness is None else None
                    if certificate is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],certificate,counts)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None
                    after=rows(solver);assert before.items()<=after.items()
                    results.append(dict(case=case['case'],visit=visit,source=case['source'],guard=certificate,witness=witness,
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
        guard_uses=sum(r['guard'] is not None for r in results if r['visit']==0),
        witness_publications=sum(r['guard_counts'].get('published_witness_roots',0) for r in results),new_nodes=len(final)-len(initial),nodes=len(final),
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
    out.mkdir(exist_ok=False);prior=base.load(PARENT/'validation.json');sources=dict(prior['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    sources.update({p:base.sha(p) for p in FILES});old_protocol=base.load(PARENT/'protocol.json')
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),prior_report=binding(PARENT/'report.json'),
        cases=old_protocol['cases'],seed=binding(PARENT/'seed.json'),source_fingerprints=sources,
        node_limit=100000,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        limitations=['Optional SAT decision experiment on the same twelve constructed edits, not a structural-coverage increase or an unrestricted-SAT result.',
            'All modes start from the same previously acquired 613-node reference seed; its original acquisition/check/compression cost remains separately charged.',
            'Witness mode alone tries checked SAT witness publication before the unchanged UNSAT guard. Both use the same exact one-clause extension bank, in common coordinates.',
            'A publication stores one ordinary independently verifiable query SAT node. New stored nodes and fresh search expansions are reported separately.',
            'Three fresh-process triples balance mode position; each stream visits all twelve queries twice. No tests or builds run during measurements.',
            'Whole time includes restoration, bank preparation, matching, premise checking, solving, model checks, bookkeeping, cold replay, sidecar writing and compression; imports and final summary write excluded.',
            'The active structural checkpoint and every earlier reference archive remain preserved. A checked union later retains all distinct reference keys; alternate valid payloads stay in trial archives.'])
    base.write(out/'protocol.json',protocol);start=time.perf_counter();seed=base.load(protocol['seed']['path'])
    assert base.sha(protocol['seed']['path'])==protocol['seed']['sha256']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'seed';base.restore_archive(seed['archive'],path);cold=previous.audit(path,seed['records'])
        assert {k:v for k,v in cold.items() if k!='seconds'}=={k:v for k,v in seed['cold'].items() if k!='seconds'}
    base.write(out/'preflight.json',dict(seed=protocol['seed'],original_acquisition_seconds=seed['seconds'],
        checked=cold,seconds=time.perf_counter()-start))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),protocol['seed']['path'],mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},
                       'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),seed=protocol['seed'],samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
