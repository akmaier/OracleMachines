from collections import Counter
from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_admitted_learning as s
out=Path('experiments/results/cnf-admitted-learning');a=s.load(out/'analysis.json');v=s.load(out/'validation.json');assert v['passed']
assert a['coverage']['all']=={'unresolved':13,'unsat':3};assert sum(a['union_counts'].values())==16
assert s.load(out/'semantic-audit.json')==s.load(out/'semantic-audit-reproduced.json')
assert a['initial_active']=={'all':59480,'admitted':2048}
full=(out/'full-tests.log').read_text();assert re.search(r'Ran 2659 tests in .*\n\nOK',full);assert re.search(r'Ran 19 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
pages=int(sys.argv[1]);inspected=list(map(int,sys.argv[2:]))
for name in ('latex-reviewed.log','latex-final.log'):
 log=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',log,re.M) and f'({pages} pages,' in log
rows=s.source_rows(s.load(out/'protocol.json'));byid={r['id']:r for r in rows};cases=s.load(out/'admitted-0/report.json')['cases'];admissions=s.load(out/'admission.json')['records'];assert all(len(r['admitted'])==128 for r in admissions)
for case in cases:
 assert case['diagnostic']['expansion']['reused']>128 and len(case['diagnostic']['expansion']['admitted'])==128
assert all(r['reference_answer'] is False for r in a['remaining'])
# Preserve proof-use diagnostics for any certified admitted outcome.
use=[]
for case in cases:
 if case['status']!='unsat':continue
 row=byid[case['id']];proof=s.load(out/'admitted-0'/(row['id']+'.json'));n=len(s.e.prior.canonical(row['source'],Counter()));k=case['diagnostic']['expansion']['reused'];active=set(case['diagnostic']['expansion']['admitted']);active_clauses={tuple(proof['derivations'][i][2]) for i in active};pending=[proof['conclusion']];seen=set()
 while pending:
  i=pending.pop()
  if i in seen:continue
  seen.add(i)
  if i>=n:
   first,steps,_=proof['derivations'][i-n];pending.append(first);pending.extend(parent for _,parent in steps)
 use.append(dict(id=row['id'],retained=k,active=len(active),retained_ancestors=sum(n<=i<n+k for i in seen),active_ancestors=sum(n<=i<n+k and tuple(proof['derivations'][i-n][2]) in active_clauses for i in seen),inactive_ancestors=sum(n<=i<n+k and tuple(proof['derivations'][i-n][2]) not in active_clauses for i in seen),new_ancestors=sum(i>=n+k for i in seen),original_premises=sum(i<n for i in seen)))
s.write(out/'proof-use.json',dict(records=use,scope='Reachability from checked empty-clause conclusions; inactive proof ancestors do not have to be active propagation clauses. No proof pruning was performed.'))
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
supp=dict(passed=True,full_tests=2659,focused_tests=19,full_test_seconds=float(re.search(r'Ran 2659 tests in ([0-9.]+)s',full)[1]),semantic=s.load(out/'semantic-audit.json')['counts'],old_proofs_unchanged=90,added_proofs=1,manuscript_pages=pages,visually_inspected_pages=inspected,clean_final_latex_passes=2,complete_retained_prefix_checked=True,admission_cases=32,initial_active=a['initial_active'],proof_use=s.binding(out/'proof-use.json'),initial_fixture_errors_preserved=True,existing_resource_warnings_retained=True)
assert s.load(out/'fresh-process-replay.json')['passed'];supp['fresh_process_replay']=s.binding(out/'fresh-process-replay.json')
supp['baseline_proof_frontiers']=s.binding(out/'baseline-proof-frontiers.json');s.write(out/'supplemental-checks.json',supp)
docs=['research/bounded-active-knowledge.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Do not replace full admission with this 128-clause policy: it loses two baseline answers and provides no new answer on this exposed panel. Preserve the cheaper experimental policy, all evidence, and the historical union as evidence for the next admission/propagation investigation.',coverage=a['coverage'],union_counts=a['union_counts'],gains=a['gains'],losses=a['losses'],comparison_percent=a['comparison_percent'],documents={f:s.sha(f) for f in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=a['limitations'],next_target='Remaining edited-input interactions, frozen external transfer of the admission policy, retained-proof costs and alternatives to vanished proof supports. The historical union is not a measured dispatcher.'))
print(s.encode(dict(passed=True,coverage=a['coverage'],gains=a['gains'],losses=a['losses'],remaining=len(a['remaining']),tests=2659)))
