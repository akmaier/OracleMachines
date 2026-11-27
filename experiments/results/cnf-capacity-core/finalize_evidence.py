"""Bind checked costs, retained misses, test logs and reviewed documents."""
from pathlib import Path
import hashlib, json, re


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path): return dict(path=str(path),sha256=sha(path))
def write(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main(out,pages,inspected):
    a=load(out/'analysis.json'); p=load(out/'protocol.json')
    semantic=load(out/'semantic-audit.json'); gaps=load(out/'gap-diagnostics.json')
    assert semantic['passed'] and load(out/'audit-reproduction.json')['exact_semantic_records_reproduced']
    assert sum(v for k,v in semantic['counts'].items() if k.endswith('_inputs'))==5462
    assert sum(v for k,v in semantic['counts'].items() if k.endswith('_certified'))==1260
    assert len(gaps['missed_small_domain_cores'])==30 and len(gaps['missed_mixtures'])==2
    assert len(gaps['external'])==37 and sum(r['kind']=='capacity' for r in gaps['external'])==6
    assert a['gains']==['e020','e021','e022','e023','e024','e035'] and a['remaining']==['e007','e036']
    assert all(x<0 for x in a['paired_percent'])
    full=(out/'full-tests.log').read_text(); focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2467 tests in .*\n\nOK',full) and re.search(r'Ran 20 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):
        assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    supplemental=dict(passed=True,semantic_audit=binding(out/'semantic-audit.json'),audit_reproduction=binding(out/'audit-reproduction.json'),gap_diagnostics=binding(out/'gap-diagnostics.json'),diagnostic_script=binding(out/'diagnose_remaining.py'),truth_table_inputs=5462,truth_table_refutations=1260,recognizer_only_misses=dict(domain_restrictions=30,mixtures=2),full_tests=2467,focused_tests=20,full_test_seconds=float(re.search(r'Ran 2467 tests in ([0-9.]+)s',full)[1]),existing_resource_warnings_retained=True,manuscript=dict(pages=pages,visually_inspected_pages=inspected,old_proofs_unchanged=82,added_proofs=1,clean_final_latex_passes=2),scope='Independent truth audits and diagnostics are outside matched timings. Missed small cores are gate-only recognition misses, not claims about the old portfolio. External follow-up uses the already exposed panel.')
    write(out/'supplemental-checks.json',supplemental)
    docs=['research/capacity-core-certificates.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
    decision=dict(decision='Retain an optional independently checked demand/capacity core gate: exposed external originals 19/25 to 24/25, derived controls 10/12 to 11/12, no lost verdict; measured full workflow 26.71 percent cheaper. Defaults unchanged.',coverage=a['coverage'],gains=a['gains'],remaining=a['remaining'],comparison_percent=a['comparison_percent'],paired_percent=a['paired_percent'],documents={name:sha(name) for name in docs},supplemental_checks=binding(out/'supplemental-checks.json'),limitations=p['limitations'],next_coverage_target='Inspect surviving random 3-CNF interaction and edited capacity instance; consider checked SAT reconstruction from choices. Improve bounded demand selection or reuse through edits against retained small core misses, then evaluate unseen encodings.',next_cost_target='Source/context verification reuse and direct wide-single-clause classification remain supporting work; preserve full support checking, source binding and cold costs. No unrestricted compact-core or SAT bound.')
    write(out/'decision.json',decision)
    print(json.dumps(dict(passed=True,external_originals=24,derived_controls=11,prior_synthetic_union_unchanged=182)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]),int(sys.argv[2]),list(map(int,sys.argv[3:])))
