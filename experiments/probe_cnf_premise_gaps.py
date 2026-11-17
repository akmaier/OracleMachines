#!/usr/bin/env python3
"""Read-only readiness/missing-clause diagnosis of the largest fresh misses."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as study
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
base=study.base


def probe(out):
    p=base.load(out/'protocol.json');parent=bound(p['parent']);trial=base.load(out/'premise-first-0/report.json');records=bound(trial['queries'])
    cores=bound(p['support_index'])['cores']+bound(p['causal_index'])['cores'];selected=sorted([r for r in records if r['eligible'] and r['choice'] is None],key=lambda r:-r['child_metrics'].get('expanded_nodes',0));results=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:initial=set(map(base.key_sha,study.rows(s)))
        finally:s.close()
        path=Path(td)/'final';base.restore_archive(trial['archive'],path);s=SnapshotResidualSolver(path)
        try:
            available=set(initial);prefixes={}
            for r in records:prefixes[r['case']]=available|set(r['early_ids']);available.update(r['new_ids'])
            for r in selected:
                target=r['chain']['source']
                for guard in r['chain']['guards']:_,target=check_guard(s,target,guard)
                members=clause_set(target,Counter());groups={'ready':[],'pending':[]}
                for i,core in enumerate(cores):
                    wanted=clause_set(core['source'],Counter());overlap=wanted&members
                    if not overlap:continue
                    missing=sorted(wanted-members);root=core['root'];assert s._canonical(core['source'])[2]==root
                    status='ready' if base.key_sha(root) in prefixes[r['case']] else 'pending'
                    if status=='ready':assert s._read(root)['answer'] is False
                    groups[status].append(dict(core=i,missing_clauses=[list(c) for c in missing],missing_count=len(missing),overlap=len(overlap)))
                minima={}
                for status,candidates in groups.items():
                    size=min((x['missing_count'] for x in candidates),default=None)
                    minima[status]=dict(minimum_missing=size,examples=[x for x in candidates if x['missing_count']==size][:5],matching_minimum=sum(x['missing_count']==size for x in candidates))
                results.append(dict(case=r['case'],template_case=r['template_case'],expansions=r['child_metrics'].get('expanded_nodes',0),answer=r['chain']['answer'],target_clauses=len(members),target_literals=sum(map(len,members)),minima=minima))
        finally:s.close()
    result=dict(protocol=study.binding(out/'protocol.json'),trial=study.binding(out/'premise-first-0/report.json'),probe=study.binding(__file__),cases=results,
        limitations=['Read-only diagnosis on the three fresh unresolved misses after the completed experiment; proof availability is masked to each exact pre-query prefix. No publication or SAT search.',
            'Minimum missing clause count is a structural distance, not a bound on derivation or solving work. For several missing clauses the known negative conjunction only forces at least one clause to be false, not every clause. Exact branching/composition and its cost remain unimplemented.'])
    base.write(out/'remaining-gaps.json',result);print(base.encode(results))


if __name__=='__main__':probe(Path(sys.argv[1]))
