#!/usr/bin/env python3
"""Read-only next-gap diagnosis: one missing clause can justify a forced guard.

If checked UNSAT core K is contained in T union {C}, every model of T falsifies
C. This logical condition does not itself supply a published composed proof.
Only prior keys and the exact per-query append prefix are used for endpoints.
"""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_guard as study
from experiments.cnf_clause_deletion_guard import clause_set,check_guard,lift
from experiments.cnf_residual_dag import restrict
from experiments.validate_cnf_unsat_support import bound
base=study.base


def probe(out):
    tick=time.perf_counter();p=base.load(out/'protocol.json');parent=bound(p['parent']);trial=base.load(out/'ready-0/report.json')
    records=bound(trial['queries']);indices={n:bound(p[f]) for n,f in [('legacy','support_index'),('causal','causal_index')]};counts=Counter()
    cores=[(name,i,c,clause_set(c['source'],counts)) for name,b in indices.items() for i,c in enumerate(b['cores'])]
    items=[];inventory={}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'final';base.restore_archive(trial['archive'],path);s=study.ResidualSolver(path)
        try:
            s.db.execute('PRAGMA query_only=ON');all_keys=set(study.rows(s));inserted={h for r in records for h in r['new_ids']}
            available={base.key_sha(k) for k in all_keys}-inserted
            def read(key):return s._read(key) if base.key_sha(key) in available else None
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh diagnostic search')),patch.object(s,'_store',side_effect=AssertionError('Diagnostic publication')):
                for name,bank in indices.items():
                    pending=[(i,c) for i,c in enumerate(bank['cores']) if read(c['root']) is None]
                    terminal=[i for i,c in pending if (n:=read(c['origin'])) is not None and n['proof']['kind']=='units' and n['proof'].get('conflict') is not None]
                    inventory[name]=dict(pending=len(pending),terminal_pending_indices=terminal)
                for row in records:
                    if not row['visit'] and row['child']['metrics'].get('expanded_nodes',0):
                        target=row['target'];members=clause_set(target,counts);candidates=[];distances=[]
                        for name,i,core,wanted in cores:
                            if not wanted&members:continue
                            node=read(core['root'])
                            if node is None:continue
                            assert node['answer'] is False;missing=wanted-members;distances.append(len(missing))
                            if len(missing)!=1:continue
                            clause=next(iter(missing))
                            if not clause:continue
                            fixed={abs(l):l<0 for l in clause};child=restrict(target,fixed,counts)
                            if clause_set(child,Counter())==members:continue
                            small,names,root=s._canonical(child);known=read(root);ready=None;pending=[]
                            if known is not None:
                                assert known['answer']==row['answer']
                                if known['answer']:lift(target,fixed,dict(zip(names,known['model'])))
                            else:
                                child_members=clause_set(child,counts)
                                for bn,ci,c,w in cores:
                                    if not w<=child_members:continue
                                    proof=read(c['root'])
                                    if proof is None:pending.append(dict(bank=bn,index=ci))
                                    else:assert proof['answer'] is False;ready=dict(bank=bn,index=ci);break
                            if ready is not None:assert row['answer'] is False
                            candidates.append(dict(bank=name,index=i,missing_clause=list(clause),forced_literals=[-l for l in clause],
                                residual_root_sha256=base.key_sha(root),known_answer=None if known is None else known['answer'],ready_support=ready,pending_supports=pending,
                                endpoint_ready=known is not None or ready is not None,residual_clauses=len(child),residual_literals=sum(map(len,child))))
                        items.append(dict(case=row['case'],answer=row['answer'],expansions=row['child']['metrics']['expanded_nodes'],
                            target_clauses=len(target),target_literals=sum(map(len,target)),minimum_missing_ready_clauses=min(distances,default=None),candidates=candidates))
                    available.update(row['new_ids'])
        finally:s.close();assert base.sha(path)==trial['archive']['database_sha256']
    result=dict(protocol=study.binding(out/'protocol.json'),trial=study.binding(out/'ready-0/report.json'),probe=study.binding(__file__),inventory=inventory,cases=items,
        endpoint_ready_cases=[r['case'] for r in items if any(c['endpoint_ready'] for c in r['candidates'])],counts=dict(counts),seconds=time.perf_counter()-tick,
        limitations=['Post-hoc diagnosis, no publication or fresh SAT search. Core availability and endpoint reads are restricted to the exact pre-query append prefix, never later solved targets.',
            'A near support is never accepted as UNSAT by dropping its missing clause. Its checked UNSAT proof justifies falsifying that clause when all remaining core clauses are in the target.',
            'Nonempty overlap, one nonempty missing clause and a changed residual are required; an empty-clause core is excluded as vacuous.',
            'Endpoint readiness does not publish a checked nested-guard result. Exact proof composition, recognition costs, fresh-input testing and fallback remain future work. No minimum-cost or unrestricted-SAT theorem.'])
    base.write(out/'missing-clause-probe.json',result)
    print(base.encode(dict(inventory=inventory,endpoint_ready_cases=result['endpoint_ready_cases'],cases=[dict(case=r['case'],expansions=r['expansions'],nearest=r['minimum_missing_ready_clauses'],candidates=len(r['candidates']),ready=sum(c['endpoint_ready'] for c in r['candidates'])) for r in items])))


if __name__=='__main__':probe(Path(sys.argv[1]))
