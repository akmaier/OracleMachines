"""Bind transfer limits and independently verified post-transfer root export."""
from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_boundary_transfer as s


def main(out,pages,inspected):
    a=s.load(out/'analysis.json');p=s.load(out/'protocol.json');v=s.load(out/'validation.json');export=s.load(out/'export-validation.json');report=s.load(out/'root-export.json');interaction=s.load(out/'interaction-audit.json')
    assert v['passed'] and export['passed'] and s.bound(export['report'])==report
    assert a['gains']==a['losses']==[] and a['states']==dict(baseline=430480,boundary=422860)
    expected={'original':{'sat':8,'unresolved':16},'signed-permutation':{'sat':2,'unresolved':4},'edit':{'sat':2,'unresolved':4}}
    assert a['coverage']==dict(baseline=expected,boundary=expected) and a['union_coverage']==dict(sat=12,unsat=10,unresolved=14)
    assert a['reference_counts']==dict(portfolio=dict(sat=9,unsat=10,unknown=17),z3=dict(sat=18,unsat=18))
    assert any(v>0 for v in a['paired_percent']) and any(v<0 for v in a['paired_percent'])
    assert export['coverage']==dict(sat=12,unsat=6,unknown=18) and export['extra_states']==23331 and export['total_states']==446191
    assert export['negative_exports']==export['already_certified_by_portfolio']==['t004','t005','t006','t007','t026','t027']
    assert interaction['remaining']==14 and sum(r['reference_answer'] for r in interaction['records'])==6
    assert all(r['component_sizes']==[r['variables']] for r in interaction['records'])
    assert s.load(out/'export-audit.json')['counts']==dict(sat=95,unsat=417)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2552 tests in .*\n\nOK',full) and re.search(r'Ran 6 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    checks=('input-audit','overlaps','references','gap-diagnostics','interaction-audit','export-policy','root-export','export-audit','export-validation','whitespace-audit')
    supplemental=dict(passed=True,evidence={k:s.binding(out/(k+'.json')) for k in checks},full_tests=2552,focused_tests=6,full_test_seconds=float(re.search(r'Ran 2552 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,export_truth_tables=512,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=86,added_proofs=0,clean_final_latex_passes=2),scope='Frozen transfer has identical SAT sets and mixed time signs. Root export is a separately frozen, charged follow-up; its six negatives overlap older portfolio coverage. Z3 negative results remain trusted audit output.')
    s.write(out/'supplemental-checks.json',supplemental)
    docs=['research/boundary-transfer-and-root-exclusions.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain negative transfer evidence and the six independently checked exported root refutations. No SAT coverage gain or reliable matched speedup on this sample; storage and replay grow sharply. The combined portfolio union remains 22/36, with fourteen explicit residual gaps.',coverage=a['coverage'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],union_coverage=a['union_coverage'],export_coverage=export['coverage'],documents={file:s.sha(file) for file in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Investigate the six known-SAT and eight reference-UNSAT misses, especially the connected 100-variable originals; use new frozen inputs after any policy change.',next_cost_target='Reuse or compress checked conditional negative evidence and export completed full-support refutations without repeating acquisition. Preserve all outside-context and source-edit obligations.')
    s.write(out/'decision.json',decision)
    cp=s.load(out/'checkpoint.json')
    cp['boundary_transfer'].update({k:s.binding(out/(k+'.json')) for k in ('export-policy','root-export','export-audit','export-validation','interaction-audit')})
    s.write(out/'checkpoint.json',cp);v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    print(s.encode(dict(passed=True,original_union=15,control_union=7,remaining=14,new_kernel_negatives=6)))


if __name__=='__main__':main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))
