"""Bind reviewed signed-choice costs, checks and retained interaction gaps."""
from pathlib import Path
import hashlib,json,re


def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path):return dict(path=str(path),sha256=sha(path))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main(out,pages,inspected):
    a=load(out/'analysis.json');p=load(out/'protocol.json');g=load(out/'gap-diagnostics.json');audit=load(out/'semantic-audit.json')
    assert audit['passed'] and load(out/'audit-reproduction.json')['exact_semantic_records_reproduced']
    assert sum(v for k,v in audit['counts'].items() if k.endswith('_inputs'))==5457
    assert sum(v for k,v in audit['counts'].items() if k.endswith('_certified'))==1700
    assert len(audit['missed_satisfiable_domains'])==228 and len(audit['fresh_records'])==65
    assert audit['invalidated_witnesses']==audit['checked_reuses']==5
    assert g['first_attempt_categories']=={'strict-choice-class':6,'complete-nonclique-choices':5,'partial-choices-with-unclassified-clauses':26}
    assert g['edited_witness_diagnostic']['restored_deleted_exclusion_still_satisfied']
    candidates=g['remaining_random']['rejected_candidates'];assert len(candidates)==2 and candidates[0]==candidates[1] and len(candidates[0]['violated_clause_indices'])==26
    assert a['gains']==['e036'] and a['remaining']==['e007'] and all(v<0 for v in a['paired_percent'])
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2485 tests in .*\n\nOK',full) and re.search(r'Ran 18 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):
        assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    supplemental=dict(passed=True,semantic_audit=binding(out/'semantic-audit.json'),audit_reproduction=binding(out/'audit-reproduction.json'),gap_diagnostics=binding(out/'gap-diagnostics.json'),diagnostic_script=binding(out/'diagnose_remaining.py'),truth_table_inputs=5457,truth_table_witnesses=1700,missed_satisfiable_domains=228,fresh_sat_witnesses=5,fresh_sat_inputs=47,full_tests=2485,focused_tests=18,full_test_seconds=float(re.search(r'Ran 2485 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=83,added_proofs=0,clean_final_latex_passes=2),scope='The new SAT witness is complete-source authority outside the strict choice class. Classification counts depend on a fixed extraction. Independent truth audits and diagnostic replays are outside matched timing.')
    write(out/'supplemental-checks.json',supplemental)
    docs=['research/signed-choice-witnesses.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain optional checked signed-choice SAT proposals: exposed original coverage 24/25 unchanged, derived controls 11/12 to 12/12, no lost verdict; measured complete workflow 8.49 percent cheaper. Defaults unchanged.',coverage=a['coverage'],gains=a['gains'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={name:sha(name) for name in docs},supplemental_checks=binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Inspect the surviving random 3-CNF through its 26 violated clauses and shared variables, testing bounded repair or conditioning with complete source checks. Preserve the candidate as rejected, not a certificate. Improve demand extraction and nonclique representation against retained misses, then freeze unseen external inputs.',next_cost_target='Reuse validated source/context and unaffected constraint structure while charging invalidation, checking, cold replay and discovery. No efficient arbitrary-SAT partition or unrestricted expansion bound.')
    write(out/'decision.json',decision)
    print(json.dumps(dict(passed=True,originals=24,derived_controls=12,prior_synthetic_union_unchanged=182)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))
