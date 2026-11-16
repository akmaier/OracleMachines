#!/usr/bin/env python3
"""Post-hoc guard attribution, surviving hardness and checked SAT reuse leads."""
from pathlib import Path
from collections import Counter
from itertools import product
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_deletion_guard as study
from experiments.cnf_clause_deletion_guard import removed_clause,check_guard,ExtensionBank,propose
from experiments.cnf_residual_dag import holds,restrict
from experiments.cnf_simplification import discover_simplification,check_simplification
base=study.base


def run(out):
    start=time.perf_counter();report=base.load(out/'report.json');reconstruction=base.load(out/'reconstruction.json')
    protocol=base.load(report['protocol']['path']);cases=base.load(protocol['cases']['path']);seed=base.load(report['seed']['path'])
    witness_checks=[]
    for old,case in zip(seed['records'],cases[1::2],strict=True):
        if old['answer']:
            model={int(k):v for k,v in old['model'].items()};removed_clause(old['source'],case['source'])
            assert holds(old['source'],model) and holds(case['source'],model)
            witness_checks.append(dict(case=case['case'],template_case=old['case'],model_satisfies_edited_input=True))
    # A cheap UNSAT premise need not leave an easy exceptional cofactor.
    clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in product((-1,0,1),repeat=2)]
    solver=study.ResidualSolver();checked=0
    try:
        for mask in range(1<<len(clauses)):
            g=[c for i,c in enumerate(clauses) if mask>>i&1];weak=g+[(-3,)];strong=weak+[(3,)]
            old=solver.solve(strong);assert old['answer'] is False
            cert=propose(solver,ExtensionBank([dict(source=strong,root=old['root'])]),weak)
            fixed,target=check_guard(solver,weak,cert)
            assert fixed=={3:False} and target==tuple(g);checked+=1
    finally:solver.close()
    parent=base.load(protocol['parent']['path']);diagnostic=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'history';base.restore_archive(parent['archive'],path);h=base.CompleteAdmissionInventory(path,**base.OPTIONS);h.set_admission_budget(0)
        try:
            original,edited=cases[12]['source'],cases[13]['source'];clause=removed_clause(original,edited);prefix={}
            for i,lit in enumerate(clause+[None]):
                assignment=dict(prefix)
                if lit is not None:assignment[abs(lit)]=lit>0
                target=restrict(edited,assignment);cert=discover_simplification(target,Counter(),units=True,pure=False)
                target,_=check_simplification(target,cert,Counter(),units=True,pure=False);key=h._canonical(target,0)[2]
                diagnostic.append(dict(cell=i,assignment=assignment,clause_satisfied=lit is not None,
                    shape=[len({abs(l) for c in target for l in c}),len(target),sum(map(len,target))],
                    root=key,present=h._load(key) is not None))
                if lit is not None:prefix[abs(lit)]=lit<0
        finally:h.close();assert base.sha(path)==parent['archive']['database_sha256']
    a,b=report['summary']['ordinary'],report['summary']['guarded']
    result=dict(report=study.binding(out/'report.json'),reconstruction=study.binding(out/'reconstruction.json'),
        analyzer=study.binding(__file__),case13_partition=diagnostic,sat_witness_checks=witness_checks,
        conditional_hardness_check=dict(examples=checked,construction='For arbitrary G and fresh x: weaker=G AND NOT x, stronger=weaker AND x. Stronger has a unit contradiction; deleting x and applying the guard leaves exactly G.'),
        reductions_percent={k:100*(a[k]-b[k])/a[k] for k in ['new_nodes','split_nodes','mean_query_seconds','mean_wall_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes']},
        archive_plus_raw_sidecar_bytes={m:[report['summary'][m]['compressed_bytes']+x for x in report['summary'][m]['sidecar_bytes']] for m in study.MODES},
        seconds=time.perf_counter()-start)
    base.write(out/'analysis.json',result);print(base.encode(dict(witnesses_checked=len(witness_checks),counterexample_family_checks=checked,seconds=result['seconds'])))


if __name__=='__main__':run(Path(sys.argv[1]))
