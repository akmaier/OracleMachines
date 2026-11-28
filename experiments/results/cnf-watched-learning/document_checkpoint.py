"""Reconcile validated equal-trace measurements into the gap record and paper."""
from pathlib import Path
import json
out=Path('experiments/results/cnf-watched-learning');a=json.loads((out/'analysis.json').read_text());b=a['totals']['all'];c=a['totals']['watched'];counts=a['work_counts'];assert a['equal_traces'] and not a['gains'] and not a['losses'];assert a['coverage']['all']==a['coverage']['watched']=={'unresolved':13,'unsat':3};assert b['proof_bytes']==c['proof_bytes']
summary=f'''[Watched propagation with full reuse](watched-propagation-and-full-reuse.md)
keeps all surviving learned clauses active. Two watches replace partial-assignment
occurrence updates, complete-model counts skip values equal to the proposal, and
known list-length charges are accumulated in bulk. Validating the smallest actual
unit/conflict candidate preserves the previous propagation order.

All sixteen exposed edited targets reproduce **byte-identical certificates and identical search
diagnostics**, including all **30,395 contexts** and **3/16 checked refutations**.
There are **no lost answers or new answers**; **13 remain unresolved**. The old
128-clause policy and its two lost answers remain preserved as a separate result.

Across two alternating pairs, mean complete cost changes **{b['complete_seconds']:.5f}
→ {c['complete_seconds']:.5f} seconds ({a['comparison_percent']:+.2f}%)**. Proof JSON remains
**{int(c['proof_bytes']):,} bytes**, with **{c['compressed_bytes']['combined']:,} combined gzip bytes**.
Every retained clause and derivation stays available. Acquisition and proof costs
remain charged; original acquisition is additional. This is a measured processing
change on exposed inputs, not new external coverage or a new tractable class.

All **2,679 full and 20 focused tests pass**. Reproduced independent truth checks
cover **27,414 exact proof/diagnostic comparisons** and **1,024 composed traces**
after edits. Fresh-worker target-only replay disables search and reproduces
answers and checker counters. Validation preserves 252 prior manifests, 84,641
artifacts, 1,372 scientific sources and 91 prior proofs. Resume
`experiments/results/cnf-watched-learning/checkpoint.json`, key `watched_learning`.

**Next priorities:** use a separately frozen budget to investigate the thirteen
remaining edited targets; test fresh external transfer; reduce proof retention
costs; and find alternative supports after premise deletion. Efficient structural
recognition, preprocessing and unrestricted SAT expansion remain open.

'''
for file,old,new in [('research/sat-pattern-discovery.md','## Latest evidence: bounded active knowledge and explicit coverage tradeoffs','## Latest evidence: watched propagation preserves full-reuse traces'),('research/implementation-gaps.md','## Latest evidence: bounded active knowledge and explicit coverage tradeoffs','## Latest evidence: watched propagation preserves full-reuse traces'),('research/structural-reuse-priorities.md','## Current investigation: bounded active knowledge and remaining transfer','## Current investigation: cheaper full reuse and thirteen remaining targets')]:
 p=Path(file);text=p.read_text();assert text.count(old)==1;p.write_text(text.replace(old,new+'\n\n'+summary+old.replace('Latest evidence','Previous evidence').replace('Current investigation','Previous investigation'),1))
measure=f'''Both policies certify **3/16**, leaving **13 unresolved**. All sixteen output
certificates are byte-identical and search diagnostics are identical, as are all **30,395 entered
contexts**, proof sizes, compression bytes and checking/replay counters. The
baseline reproduces the parent checkpoint exactly. The candidate improves
full-admission cost without discarding clauses; it does not increase coverage
beyond full admission.

| Quantity | Full occurrence index | Full clauses with watches |
| --- | ---: | ---: |
| Mean complete seconds | {b['complete_seconds']:.5f} | {c['complete_seconds']:.5f} |
| Acquisition including checks, seconds | {b['phases']['acquisition_seconds']:.5f} | {c['phases']['acquisition_seconds']:.5f} |
| Explicit checks, seconds | {b['phases']['checking_seconds']:.5f} | {c['phases']['checking_seconds']:.5f} |
| Warm reload/check, seconds | {b['warm_seconds']:.5f} | {c['warm_seconds']:.5f} |
| Two reload/check rounds, seconds | {b['cold_seconds']:.5f} | {c['cold_seconds']:.5f} |
| Writes, seconds | {b['phases']['writing_seconds']:.5f} | {c['phases']['writing_seconds']:.5f} |
| Three compressions, seconds | {b['persistence_seconds']:.5f} | {c['persistence_seconds']:.5f} |
| Proof JSON bytes | {int(b['proof_bytes']):,} | {int(c['proof_bytes']):,} |
| Combined gzip bytes | {b['compressed_bytes']['combined']:,} | {c['compressed_bytes']['combined']:,} |
| Maximum observed RSS bytes | {a['peak_rss_bytes']['all']:,} | {a['peak_rss_bytes']['watched']:,} |

Mean complete cost changes **{a['comparison_percent']:+.2f}%**, with paired changes
{a['paired_percent'][0]:+.2f}% and {a['paired_percent'][1]:+.2f}%. The baseline makes
{counts['all']['learning_assignment_occurrences']:,} assignment and
{counts['all']['learning_undo_occurrences']:,} undo occurrence visits. The candidate
makes {counts['watched']['watch_model_assignment_occurrences']:,} complete-model assignment
visits and {counts['watched']['watch_model_undo_occurrences']:,} complete-model undo visits,
plus {counts['watched']['watch_visits']:,} watch visits,
{counts['watched']['watch_candidate_literals']:,} replacement-literal inspections and
{counts['watched']['watch_agenda_literals']:,} candidate-validation literal inspections.
These categories perform different work and should not be summed as equivalent
operations. Watch construction, moves and stale candidates are retained in the
full counter ledger. No proof material is removed.
'''
p=Path('research/watched-propagation-and-full-reuse.md');text=p.read_text();assert 'WATCHED_MEASUREMENTS' in text;p.write_text(text.replace('WATCHED_MEASUREMENTS',measure))
tex=fr'''Both policies certify 3/16, with thirteen targets still unknown under the
cap.  Every certificate is byte-identical and each search diagnostic identical, including all
30,395 entered contexts; the baseline also reproduces its previous checkpoint.
There are no newly solved or lost targets.  Mean complete cost changes from
{b['complete_seconds']:.5f} to {c['complete_seconds']:.5f} seconds ({a['comparison_percent']:+.2f}\%),
with paired changes {a['paired_percent'][0]:+.2f}\% and {a['paired_percent'][1]:+.2f}\%.
Mean acquisition including checks changes from {b['phases']['acquisition_seconds']:.5f}
to {c['phases']['acquisition_seconds']:.5f} seconds; explicit checks from
{b['phases']['checking_seconds']:.5f} to {c['phases']['checking_seconds']:.5f}; warm replay
from {b['warm_seconds']:.5f} to {c['warm_seconds']:.5f}; and two reload/check rounds from
{b['cold_seconds']:.5f} to {c['cold_seconds']:.5f}.  Proof JSON remains
{int(c['proof_bytes']):,} bytes and combined gzip {c['compressed_bytes']['combined']:,}
bytes.  Maximum observed process RSS changes from {a['peak_rss_bytes']['all']:,} to
{a['peak_rss_bytes']['watched']:,} bytes.

The old engine makes {counts['all']['learning_assignment_occurrences']:,} assignment
and {counts['all']['learning_undo_occurrences']:,} undo occurrence visits.  The
candidate makes {counts['watched']['watch_model_assignment_occurrences']:,} complete-model
assignment visits and {counts['watched']['watch_model_undo_occurrences']:,} undo visits,
plus {counts['watched']['watch_visits']:,} watch visits,
{counts['watched']['watch_candidate_literals']:,} replacement-literal inspections and
{counts['watched']['watch_agenda_literals']:,} candidate-validation inspections.
These categories do different work; their totals are not interchangeable
operation counts.  Full counters retain construction, movement and stale-entry
costs.  All derivations and their checking obligations remain unchanged.
'''
p=Path('paper/bounded_domain_sat_and_amortized_reasoning.tex');text=p.read_text();marker=r'\section{System 1, System 2, and the reuse of computation}';assert text.count(marker)==1 and r'\label{sec:watched-learning}' not in text;section=(out/'manuscript-section-template.tex').read_text().replace('WATCHED_MEASUREMENTS',tex);p.write_text(text.replace(marker,section+'\n'+marker,1))
print('Updated watched-propagation checkpoint documents')
