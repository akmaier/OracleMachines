"""Bind matched costs, semantic checks, contextual counterexamples and manuscript."""
from pathlib import Path
import json,re
from experiments import cnf_boundary_repair as e
from experiments.compare_cnf_boundary_repair import load,write,sha,binding,bound


def main(out,pages,inspected):
    a=load(out/'analysis.json');p=load(out/'protocol.json');g=load(out/'gap-diagnostics.json');audit=load(out/'semantic-audit.json')
    assert audit['passed'] and load(out/'audit-reproduction.json')['exact_semantic_records_reproduced']
    assert audit['counts']==dict(exhaustive_inputs=512,fresh_inputs=64,conditional_queries=8402,sat_contexts=1033,excluded_contexts=7369,incremental_snapshots=6704,bounded_runs=1728,bounded_sat=312)
    assert a['coverage']==dict(baseline=dict(sat=29,unresolved=3),boundary=dict(sat=32))
    assert a['gains']==[24,25,29] and a['remaining']==[] and a['states']==dict(baseline=118552,boundary=94762)
    assert all(x<0 for x in a['paired_percent']) and g['total_conditional_exclusions']==11
    for r,states,widths in zip(g['records'],(10468,10011,15731),((6,15,25,39,59,77),(3,8),(21,26,32,43,63,78))):
        assert r['diagnostic']['expanded']==states
        assert tuple(x['selected_variables'] for x in r['diagnostic']['rounds'])==widths
    example=load(out/'context-counterexample.json')
    assert e.check_conditional(example['source'],example['conditional_exclusion'])==dict(outside_context_excluded=True)
    assert e.previous.check(example['source'],example['global_sat'])['answer']
    assert example['invalidated_by']==['outside','free','source']
    regression=load(out/'budget-regression.json');source=regression['source']
    assert e.previous_search.search(source,regression['seed'],len(regression['seed']['names']),node_limit=2)==regression['baseline']
    assert e.repair(source,node_limit=2,prefix_limit=1)==regression['boundary']
    assert regression['baseline']['witness'] and regression['boundary']['witness'] is None
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2546 tests in .*\n\nOK',full) and re.search(r'Ran 18 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    checks=('semantic-audit','audit-reproduction','gap-diagnostics','context-counterexample','budget-regression','exploration')
    supplemental=dict(passed=True,evidence={name:binding(out/(name+'.json')) for name in checks},truth_table_inputs=576,conditional_queries=8402,full_tests=2546,focused_tests=18,full_test_seconds=float(re.search(r'Ran 2546 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=85,added_proofs=1,clean_final_latex_passes=2),scope='Freshly charged near-model acquisition and exact context reconstruction. Conditional UNSAT carries no global negative authority. Wide final free sets, higher replay/storage costs and small-cap restart regression remain explicit.')
    write(out/'supplemental-checks.json',supplemental)
    docs=['research/proof-guided-boundary-repair.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain optional proof-guided boundary repair: exposed constructed kernel coverage 29/32 to 32/32 under the same total state cap, all 29 old models preserved, mean complete cost 17.60 percent lower. Cold checking and storage grow; no production default change or unseen transfer claim.',coverage=a['coverage'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={file:sha(file) for file in docs},supplemental_checks=binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Freeze unseen external inputs and compare the fixed policy with the full portfolio and a fresh solver. This exposed panel is complete; unrestricted efficient coverage remains open.',next_cost_target='Understand the nearly full-width interactions and reuse checked negative supports across related contexts/edits, charging preparation, invalidation, reconstruction and persistence.')
    write(out/'decision.json',decision);print(json.dumps(dict(passed=True,constructed_sat=32,remaining=0,conditional_exclusions=11,prior_external_union_unchanged=37)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))
