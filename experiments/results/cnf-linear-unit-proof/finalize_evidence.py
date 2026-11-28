from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_linear_unit_proof as s
out=Path(__file__).parent;a=s.load(out/'analysis.json');p=s.load(out/'protocol.json');v=s.load(out/'validation.json')
assert v['passed'] and a['exposed']['states']==dict(explicit=58118,linear=58118) and a['larger']['states']==dict(explicit=236197,linear=236197)
assert all(x<0 for x in a['exposed']['paired_percent']) and a['larger']['union_counts']==dict(sat=5,unresolved=11)
gaps=a['larger']['unresolved'];assert len(gaps)==11 and sum(x['reference_answer'] is True for x in gaps)==3
assert all(x['component_sizes']==[x['variables']] and x['diagnostic']['expanded']==20000 for x in gaps)
assert a['larger']['reference_counts']==dict(portfolio=dict(unknown=16),z3=dict(sat=8,unsat=8))
full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
assert re.search(r'Ran 2592 tests in .*\n\nOK',full) and re.search(r'Ran 20 tests in .*\n\nOK',focused)
for name in ('latex-reviewed.log','latex-final.log'):
    log=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',log,re.M) and '(367 pages,' in log
old=s.load(out/'explicit-0/report.json')['counts'];new=s.load(out/'linear-0/report.json')['counts'];equal={}
for x,y in [('unit_contexts_checked','linear_contexts_checked'),('unit_deductions_checked','linear_deductions_checked'),('unit_check_literal_charge','linear_check_literal_charge')]:
    assert old[x]==new[y];equal[x]=old[x]
supp=s.load(out/'supplemental-checks.json');assert supp['passed'] and len(supp['signed_transports'])==4 and supp['truth_queries']==8882 and supp['truncated_refutations_rejected']==2709
supp.update(full_tests=2592,focused_tests=20,full_test_seconds=float(re.search(r'Ran 2592 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,equal_logical_checks=equal,manuscript=dict(pages=367,visually_inspected_pages=[358,359,360],old_proofs_unchanged=87,added_proofs=1,clean_final_latex_passes=2))
s.write(out/'supplemental-checks.json',supp)
docs=['research/linear-unit-proofs-and-larger-transfer.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Retain exact preorder refutations: unchanged 36-input coverage/search, 52.63% smaller combined gzip and 1.98% lower complete cost. Frozen larger transfer certifies only five of sixteen inputs; eleven explicit residuals become the primary coverage target.',exposed=a['exposed'],larger=a['larger'],documents={f:s.sha(f) for f in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Investigate larger residual l004 and its related SAT controls, and all eight reference-UNSAT residuals; preserve the 20000-context diagnosis before changing policy or allowance.',next_reuse_target='Reuse checked negative consequences across contexts and edits with exact guards; source-index transport and component conditioning are candidates. Preorder packing does not yet share logical subproofs.'))
print(s.encode(dict(passed=True,exposed=36,new_originals=8,new_controls=8,new_certified=5,new_unresolved=11,full_tests=2592)))
