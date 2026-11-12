#!/usr/bin/env python3
"""Read-only growth-budget diagnostic after checked subsumption fallback."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_variable_elimination import opportunity
from experiments.compare_cnf_retained_plans import sha


def main(output):
    if output.exists(): raise FileExistsError(output)
    reports=[]
    for suite in ('remaining','originals'):
        path=Path('experiments/results/cnf-subsumed-elimination-'+suite+'/report.json')
        report=json.loads(path.read_text()); result=next(r for r in report['results'] if r['mode']=='subsumed')
        leaves=[]
        for leaf in result['frontier']:
            cnf=leaf['cnf']; row=opportunity(cnf)
            # Same candidate ordering/budget as the implementation. The observer
            # alone also retains the complete all-variable candidate list.
            candidates=sorted(row['candidates'],key=lambda c:(c['pairs'],c['variable']))[:64]
            eligible=[c for c in candidates if c['retained_subsumption_clause_delta']<=0]
            minima=min((c['retained_subsumption_literal_delta'] for c in eligible),default=None)
            n=len({abs(l) for c in cnf for l in c}); m=len(cnf); L=sum(map(len,cnf))
            assert L<=m*n
            leaves.append(dict(key_sha256=leaf['key_sha256'],variables=n,clauses=m,literals=L,
                width=max(map(len,cnf),default=0),initial_clause_variable_product=m*n,
                min_extra_literals_with_nongrowing_clauses=minima,
                runtime_budget_candidates=candidates,all_variable_opportunity=row))
        reports.append(dict(suite=suite,report_sha256=sha(path),leaves=leaves,
            selected_leaves=len(leaves),current_rule_available=sum(r['min_extra_literals_with_nongrowing_clauses'] is not None and r['min_extra_literals_with_nongrowing_clauses']<=0 for r in leaves),
            clause_only_candidates_available=sum(r['min_extra_literals_with_nongrowing_clauses'] is not None for r in leaves),
            extra_literal_thresholds={str(t):sum(r['min_extra_literals_with_nongrowing_clauses'] is not None and 0<r['min_extra_literals_with_nongrowing_clauses']<=t for r in leaves) for t in (1,2,4,8,16,32,64)}))
    data=dict(script_sha256=sha(Path(__file__)),opportunity_helper_sha256=sha('experiments/analyze_cnf_variable_elimination.py'),reports=reports,
        limitations=['Read-only candidate opportunities; no new integrated policy, closure or performance result.',
            'The per-CNF bound L <= m*n requires normalized non-tautological clauses with no repeated literals; it is not a bound on the accumulated proof graph.',
            'Non-growing clause counts and decreasing variables bound intermediate CNF size on an accepted elimination chain, not existence of such a chain for every SAT input.',
            'Runtime candidate cap and opposing-pair cap are retained; all-variable diagnostics are recorded separately.'])
    output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='leaves'} for r in reports]))


if __name__=='__main__': main(Path(sys.argv[1]))
