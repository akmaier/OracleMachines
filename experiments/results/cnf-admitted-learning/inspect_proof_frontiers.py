from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_admitted_learning as s
out=Path('experiments/results/cnf-admitted-learning')
rows=s.source_rows(s.load(out/'protocol.json'));byid={r['id']:r for r in rows};cases=s.load(out/'admitted-0/report.json')['cases']
# Post-hoc explanation, using clause identity rather than a duplicate record's index.
frontiers=[];candidate={c['id']:c for c in cases}
for case in s.load(out/'all-0/report.json')['cases']:
 if case['status']!='unsat':continue
 row=byid[case['id']];proof=s.load(out/'all-0'/(row['id']+'.json'));n=len(s.e.prior.canonical(row['source'],Counter()));k=case['diagnostic']['expansion']['reused'];chosen=candidate[row['id']]['diagnostic']['expansion']['admitted'];active_clauses={tuple(proof['derivations'][i][2]) for i in chosen};pending=[proof['conclusion']];seen=set();frontier=set()
 while pending:
  i=pending.pop()
  if i in seen:continue
  seen.add(i)
  if i>=n:
   first,steps,_=proof['derivations'][i-n];parents=[first]+[parent for _,parent in steps]
   if i>=n+k:frontier.update(parent-n for parent in parents if n<=parent<n+k)
   pending.extend(parents)
 clauses={tuple(proof['derivations'][i][2]) for i in frontier};overlap=clauses&active_clauses
 frontiers.append(dict(id=row['id'],candidate_status=candidate[row['id']]['status'],retained_frontier_indices=sorted(frontier),distinct_frontier_clauses=len(clauses),admitted_frontier_clauses=len(overlap),omitted_frontier_clauses=len(clauses-overlap),frontier_widths=dict(Counter(map(len,clauses))),omitted_widths=dict(Counter(map(len,clauses-overlap)))))
s.write(out/'baseline-proof-frontiers.json',dict(records=frontiers,scope='Post-hoc reachable edges from new baseline derivations to retained clauses, matched by clause identity. This diagnoses the recorded proof route, not the necessity of any clause for SAT solving or a causal explanation of candidate failure. No policy was retuned.'))
for row in frontiers:print(row['id'],row['distinct_frontier_clauses'],row['admitted_frontier_clauses'],row['omitted_frontier_clauses'])
