from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_unit_partition as s
out=Path(__file__).parent
a=s.load(out/'analysis.json');p=s.load(out/'protocol.json');v=s.load(out/'validation.json')
assert v['passed'] and a['remaining']==[] and a['prior_union_gains']==14 and len(a['gains'])==18
assert a['states']==dict(baseline=446191,propagated=58118)
assert a['coverage']['propagated']=={'original':dict(sat=12,unsat=12),'signed-permutation':dict(sat=3,unsat=3),'edit':dict(sat=3,unsat=3)}
assert all(x>0 for x in a['paired_percent'])
d=s.load(out/'gap-diagnostics.json')['records'];assert sum(x['refutation_contexts'] for x in d)==42333 and max(x['diagnostic']['expanded'] for x in d)==7687
full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
assert re.search(r'Ran 2572 tests in .*\n\nOK',full) and re.search(r'Ran 20 tests in .*\n\nOK',focused)
for name in ('latex-reviewed.log','latex-final.log'):
    log=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',log,re.M) and '(365 pages,' in log
supp=s.load(out/'supplemental-checks.json');assert supp['passed'] and supp['semantic_reproduction_equal'] and supp['queries']==8882
supp.update(full_tests=2572,focused_tests=20,full_test_seconds=float(re.search(r'Ran 2572 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=365,visually_inspected_pages=[356,357,358],old_proofs_unchanged=86,added_proofs=1,clean_final_latex_passes=2))
s.write(out/'supplemental-checks.json',supp)
docs=['research/unit-closed-repair-partitions.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Retain exact unit closure under flip and keep commitments: all fourteen retained union misses close, reaching 36/36 exposed inputs. Total cost rises 7.53% with larger root refutations; no complete-workflow speedup or new transfer claim.',coverage=a['coverage'],union_coverage=dict(sat=18,unsat=18,unresolved=0),prior_union_gains=14,comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={file:s.sha(file) for file in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Freeze new larger external sources after the policy change; keep modern-solver reference work and related controls separately denominated.',next_cost_target='Reduce unit-trace storage and replay, and investigate guarded negative reuse across contexts and edits without weakening complete-root or source-checking obligations.'))
print(s.encode(dict(passed=True,exposed_coverage=36,closed_union_gaps=14,full_tests=2572,truth_queries=8882)))
