from collections import Counter
from pathlib import Path
import hashlib,json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_selective_learning as s
out=Path('experiments/results/cnf-selective-learning');a=s.load(out/'analysis.json');v=s.load(out/'validation.json');assert v['passed']
assert a['coverage']=={'fresh':{'unresolved':16},'reuse':{'unresolved':13,'unsat':3}} and len(a['gains'])==3 and a['losses']==[] and len(a['remaining'])==13
assert a['transport']['cases']==a['transport']['whole_guard_rejected']==a['transport']['nonempty']==32 and a['transport']['statuses']=={'unknown':32}
assert s.load(out/'semantic-audit.json')==s.load(out/'semantic-audit-reproduced.json')
full=(out/'full-tests.log').read_text();assert re.search(r'Ran 2640 tests in .*\n\nOK',full);assert re.search(r'Ran 22 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
pages=int(sys.argv[1]);inspected=list(map(int,sys.argv[2:]))
for name in ('latex-reviewed.log','latex-final.log'):
 log=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',log,re.M) and f'({pages} pages,' in log
rows=s.source_rows(s.load(out/'protocol.json'));interaction=[]
for row in rows:
 names={abs(v) for c in row['source'] for v in c};parent={v:v for v in names}
 def root(v):
  while parent[v]!=v:v=parent[v]
  return v
 for clause in row['source']:
  if clause:
   r=root(abs(clause[0]))
   for v in clause[1:]:parent[root(abs(v))]=r
 count=len({root(v) for v in names});assert count==1
 interaction.append(dict(id=row['id'],variables=len(names),clauses=len(s.e.canonical(row['source'],Counter())),components=count))
s.write(out/'interaction.json',dict(records=interaction,scope='All 32 edited targets remain connected in the variable incidence graph. This is not a bounded interaction-width certificate.'))
reports={m:{x['id']:x for x in s.load(out/(m+'-0/report.json'))['cases']} for m in ('fresh','reuse')};refs={x['id']:s.bound(x)['result']['answer'] for x in s.load(out/'references.json')['records']}
gaps=[dict(id=x['id'],reference_answer=refs[x['id']],fresh=reports['fresh'][x['id']]['diagnostic'],reuse=reports['reuse'][x['id']]['diagnostic']) for x in a['remaining']];s.write(out/'gap-diagnostics.json',dict(records=gaps))
assert all(x['reference_answer'] is False for x in gaps)
use=[];byid={r['id']:r for r in rows}
for case in reports['reuse'].values():
 if case['status']!='unsat':continue
 row=byid[case['id']];proof=s.load(out/'reuse-0'/(case['id']+'.json'));base=len(s.e.canonical(row['source'],Counter()));kept=len(case['diagnostic']['survival']['retained_indices']);pending=[proof['conclusion']];seen=set()
 while pending:
  index=pending.pop()
  if index in seen:continue
  seen.add(index)
  if index>=base:
   start,steps,_=proof['derivations'][index-base];pending.append(start);pending.extend(parent for _,parent in steps)
 use.append(dict(id=case['id'],retained=kept,retained_used=sum(base<=i<base+kept for i in seen),new=len(proof['derivations'])-kept,new_used=sum(i>=base+kept for i in seen),original_premises_used=sum(i<base for i in seen)))
assert [x['retained_used'] for x in use]==[1400,1600,3037]
s.write(out/'proof-use.json',dict(records=use,scope='Ancestors of the three checked empty-clause conclusions. This diagnoses participation and unused records; no proof-pruning policy or pruned performance was measured.'))

supp=dict(passed=True,full_tests=2640,focused_tests=22,full_test_seconds=float(re.search(r'Ran 2640 tests in ([0-9.]+)s',full)[1]),semantic=s.load(out/'semantic-audit.json')['counts'],old_proofs_unchanged=89,added_proofs=1,manuscript_pages=pages,visually_inspected_pages=inspected,clean_final_latex_passes=2,connected_targets=32,independent_survival_support_unions=32,existing_resource_warnings_retained=True,interaction=s.binding(out/'interaction.json'),gap_diagnostics=s.binding(out/'gap-diagnostics.json'),proof_use=s.binding(out/'proof-use.json'))
s.write(out/'supplemental-checks.json',supp)
docs=['research/selective-learned-knowledge.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Retain selective derivation survival and exact target-only expansion certificates. All 32 old guard failures retain valid negative knowledge; capped expansion adds three refutations, but full reuse is substantially more costly.',coverage=a['coverage'],transport=a['transport'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],documents={f:s.sha(f) for f in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=a['limitations'],next_target='Economical admission/propagation of surviving clauses, alternative proof supports for deleted-premise descendants, and fresh frozen transfer. Preserve all thirteen capped target diagnostics; full valid knowledge retention does not make expansion cheap.'))
print(s.encode(dict(passed=True,whole_guard_failures=32,selective_nonempty=32,new_refutations=3,remaining=13,tests=2640)))
