"""Bind supplementary audits and reviewed documents after checks finish."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,json,re
from experiments import cnf_factor_conditioning as f
from experiments.compare_cnf_factor_conditioning import base,old


def main(out,pages,inspected):
    audit=base.load(out/'semantic-audit.json');payload=gzip.decompress(Path(audit['archive']['path']).read_bytes())
    assert base.sha(audit['archive']['path'])==audit['archive']['sha256'] and hashlib.sha256(payload).hexdigest()==audit['uncompressed_sha256']
    records=json.loads(payload);counts=Counter()
    for record in records:
        got=f.check(record['source'],record['prefix'],record['proof'])
        assert json.loads(base.encode(got))==record['result']
        assert got['answer']==record['truth'];counts[record['proof']['status']]+=1
    assert len(records)==632 and dict(counts)=={'sat':212,'unsat':420}
    a=base.load(out/'analysis.json');p=base.load(out/'protocol.json');union=base.load(out/'coverage-union.json')
    assert len(union['records'])==182 and all(r['answer'] is not None for r in union['records'])
    for values in a['paired_percent'].values():assert all(x>0 for x in values)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2431 tests in .*\n\nOK',full) and re.search(r'Ran 16 tests in .*\n\nOK',focused)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    supplemental=dict(passed=True,semantic_audit=old.binding(out/'semantic-audit.json'),semantic_archive=audit['archive'],semantic_archive_rechecked=True,semantic_records=len(records),semantic_results=dict(counts),audit_reproduction=old.binding(out/'audit_cutsets.py'),coverage_union=old.binding(out/'coverage-union.json'),retained_diagnostic_screen=old.binding(out/'cutset-screen.json'),development_failures=[old.binding(out/x) for x in ('preflight-source-before-fix.py','validator-before-json-key-fix.py')],development_failure_explanations=['JSON-list/tuple concatenation fixed before benchmark protocol; no accepted timing used the initial source.','JSON integer/string dictionary keys compared as parsed values after validation-only correction; measured code and evidence unchanged.'],full_tests=2431,focused_tests=16,full_test_seconds=float(re.search(r'Ran 2431 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=81,added_proofs=1,clean_latex_passes=2),scope='Independent audits and previous-root acquisition are outside matched incremental timing. Root union completion is restricted to the retained synthetic panel.')
    base.write(out/'supplemental-checks.json',supplemental)
    docs=['research/factor-conditioning.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain checked cutset conditioning and exact original-root witness transport. Adds both remaining SAT roots, completing the retained 182-query structural certificate union. Higher incremental cost; no default change or unrestricted/external-coverage claim.',retained_root_coverage=180,union_root_coverage=182,root_panel_size=182,new_roots=a['new_roots'],branches=a['branches'],cost_comparisons_percent=a['comparisons_percent'],paired_percent=a['paired_percent'],documents={x:base.sha(x) for x in docs},supplemental_checks=old.binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Freeze new graph structures and external CNFs before tuning cutset recognition. Record overlaps, interaction and unresolved cases; the old synthetic panel is now saturated. The third frontier and twenty-five open branches remain concrete stress cases.',next_cost_target='Measure selective/adaptive branching and stopping after a checked root witness, together with exact validated source contexts. Charge discovery, construction, invalidation, replay and all necessary UNSAT branch obligations. No savings from those unimplemented policies claimed.')
    base.write(out/'decision.json',decision);print(base.encode(dict(passed=True,audit_records=len(records),root_union=len(union['records']),documents=len(docs))))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))
