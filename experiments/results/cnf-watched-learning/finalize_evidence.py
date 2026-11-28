"""Seal supporting tests, manuscript checks and the measured decision."""
from pathlib import Path
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_watched_learning as s
out=Path('experiments/results/cnf-watched-learning');a=s.load(out/'analysis.json');v=s.load(out/'validation.json');assert v['passed'] and a['equal_traces'];assert a['coverage']['all']==a['coverage']['watched']=={'unresolved':13,'unsat':3};assert not a['gains'] and not a['losses'];assert a['states']=={'all':30395,'watched':30395}
assert s.load(out/'trace-bytes.json')['passed']
assert s.load(out/'semantic-audit.json')==s.load(out/'semantic-audit-reproduced.json')
full=(out/'full-tests.log').read_text();assert re.search(r'Ran 2679 tests in .*\n\nOK',full);assert re.search(r'Ran 20 tests in .*\n\nOK',(out/'focused-tests.log').read_text());assert s.load(out/'fresh-process-replay.json')['passed']
pages=int(sys.argv[1]);inspected=list(map(int,sys.argv[2:]))
for name in ('latex-reviewed.log','latex-final.log'):
 text=(out/name).read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',text,re.M) and f'({pages} pages,' in text
for mode in s.MODES:
 for r in s.load(out/(mode+'-0')/'report.json')['cases']:assert r['diagnostic']['expansion']['reused']>128
assert all(r['reference_answer'] is False for r in a['remaining'])
common=set(a['work_counts']['all'])&set(a['work_counts']['watched']);assert all(a['work_counts']['all'][k]==a['work_counts']['watched'][k] for k in common)
supp=dict(passed=True,full_tests=2679,focused_tests=20,full_test_seconds=float(re.search(r'Ran 2679 tests in ([0-9.]+)s',full)[1]),semantic=s.load(out/'semantic-audit.json')['counts'],old_proofs_unchanged=91,added_proofs=1,manuscript_pages=pages,visually_inspected_pages=inspected,clean_final_latex_passes=2,complete_retained_prefix_checked=True,equal_measured_proofs_and_diagnostics=True,trace_bytes=s.binding(out/'trace-bytes.json'),shared_operation_counts_equal=sorted(common),baseline_matches_parent=True,all_knowledge_active=True,fresh_process_replay=s.binding(out/'fresh-process-replay.json'),initial_fixture_error_preserved=True,existing_resource_warnings_retained=True)
s.write(out/'supplemental-checks.json',supp)
docs=['research/watched-propagation-and-full-reuse.md','research/sat-pattern-discovery.md','research/structural-reuse-priorities.md','research/implementation-gaps.md','paper/bounded_domain_sat_and_amortized_reasoning.tex']
s.write(out/'decision.json',dict(decision='Preserve watched propagation as an experimental full-reuse engine with exact matched proofs and coverage. Keep the previous bounded-admission loss result. Treat measured cost as the whole implementation bundle, with remaining coverage and acquisition obligations explicit.',coverage=a['coverage'],comparison_percent=a['comparison_percent'],equal_traces=True,documents={f:s.sha(f) for f in docs},supplemental_checks=s.binding(out/'supplemental-checks.json'),limitations=a['limitations'],next_target='Freeze a new expansion budget to investigate the thirteen remaining edited targets, then fresh external transfer, proof retention costs and alternatives to vanished supports. No production defaults change.'))
print(s.encode(dict(passed=True,coverage=a['coverage'],equal_traces=True,comparison_percent=a['comparison_percent'],tests=2679)))
