"""Render the validated measurement summary without changing frozen policies."""
from pathlib import Path
import json
out=Path('experiments/results/cnf-admitted-learning');a=json.loads((out/'analysis.json').read_text());b=a['totals']['all'];c=a['totals']['admitted'];solved=lambda m:sum(n for k,n in a['coverage'][m].items() if k!='unresolved');union=sum(n for k,n in a['union_counts'].items() if k!='unresolved');cost='falls' if c['complete_seconds']<b['complete_seconds'] else 'rises'
summary=f'''[Bounded active knowledge](bounded-active-knowledge.md) admits at most 128 distinct
non-source learned clauses, ranked by shorter width and then recency. Every
surviving derivation remains checked and persisted; inactive proof ancestors
are available for exact substitution without entering the propagation input.
This preserves the target model set for every admission subset.

On the same sixteen exposed edited targets at 2,000 contexts, full admission
certifies **{solved('all')}/16** and bounded admission **{solved('admitted')}/16**.
There are **{len(a['gains'])} new answers and {len(a['losses'])} baseline answers lost** by the
bounded policy. The historical union certifies **{union}/16**, leaving
**{len(a['remaining'])} unresolved**. The union preserves earlier answers and is not
a measured combined dispatcher. The bounded policy is not a replacement for full admission: it produces no new
answer here and loses two earlier ones. This is exposed-policy development, not
fresh external transfer or a new tractable SAT class.

Initial imported clauses fall **{a['initial_active']['all']:,} → {a['initial_active']['admitted']:,}**.
Mean complete measured cost {cost} **{b['complete_seconds']:.5f} → {c['complete_seconds']:.5f}
seconds ({a['comparison_percent']:+.2f}%)**. Assignment occurrence updates change
**{a['assignment_occurrences']['all']:,} → {a['assignment_occurrences']['admitted']:,}**.
Proof JSON changes **{int(b['proof_bytes']):,} → {int(c['proof_bytes']):,} bytes**;
two reload/check rounds change **{b['cold_seconds']:.5f} → {c['cold_seconds']:.5f} seconds**.
Those rounds parse fresh objects in the same worker; a separate fresh-worker
validation reproduces all target answers and checking counters without search.
Retained-proof reads, checks and writes are charged; old acquisition is additional. The
128 cap does not limit newly learned clauses or general expansion.

All **2,659 full and 19 focused tests pass**. Reproduced small-case checks cover
13,624 edited targets and 40,872 complete model-set comparisons at admission
budgets 0, 1 and 128. Validation preserves 251 manifests, 84,515 artifacts,
1,367 scientific sources and 90 prior proofs; five scientific files and one
proof are added. Resume `experiments/results/cnf-admitted-learning/checkpoint.json`,
key `admitted_learning`.

**Largest remaining gaps:** the {len(a['remaining'])} unresolved edited targets; cheaper
propagation with broader clause access or admission informed by proof use; fresh
frozen external transfer; retained-proof cost; and alternative supports after
source deletions. The active import cap
preserves exactness, but does not bound unrestricted SAT complexity.

'''
for file,old,new in [('research/sat-pattern-discovery.md','## Latest evidence: selective knowledge survives edits, with costly expansion','## Latest evidence: bounded active knowledge and explicit coverage tradeoffs'),('research/implementation-gaps.md','## Latest evidence: selective knowledge survives edits, with costly expansion','## Latest evidence: bounded active knowledge and explicit coverage tradeoffs'),('research/structural-reuse-priorities.md','## Current investigation: selective survival and economical expansion','## Current investigation: bounded active knowledge and remaining transfer')]:
 p=Path(file);text=p.read_text();assert text.count(old)==1;previous=old.replace('Latest evidence','Previous evidence').replace('Current investigation','Previous investigation');p.write_text(text.replace(old,new+'\n\n'+summary+previous,1))
measure=f'''Full admission certifies **{solved('all')}/16** targets; the 128-clause policy
certifies **{solved('admitted')}/16**. It adds {len(a['gains'])} checked answers and loses
{len(a['losses'])} baseline answers within the cap. The preserved historical union is
**{union}/16**, with **{len(a['remaining'])} unresolved**. All sixteen targets have earlier
trusted reference-UNSAT outcomes, kept separate from project-certified coverage.
New gains: {', '.join(a['gains']) or 'none'}. Lost baseline answers:
{', '.join(a['losses']) or 'none'}. These individual cases remain in the record.

| Quantity | All surviving clauses active | At most 128 imports |
| --- | ---: | ---: |
| Initial imported clauses across 16 targets | {a['initial_active']['all']:,} | {a['initial_active']['admitted']:,} |
| Entered contexts | {a['states']['all']:,} | {a['states']['admitted']:,} |
| Assignment occurrence updates | {a['assignment_occurrences']['all']:,} | {a['assignment_occurrences']['admitted']:,} |
| Mean complete seconds | {b['complete_seconds']:.5f} | {c['complete_seconds']:.5f} |
| Mean acquisition including internal checks, seconds | {b['phases']['acquisition_seconds']:.5f} | {c['phases']['acquisition_seconds']:.5f} |
| Mean explicit checking, seconds | {b['phases']['checking_seconds']:.5f} | {c['phases']['checking_seconds']:.5f} |
| Mean warm reload/check, seconds | {b['warm_seconds']:.5f} | {c['warm_seconds']:.5f} |
| Mean two cold reload/checks, seconds | {b['cold_seconds']:.5f} | {c['cold_seconds']:.5f} |
| Mean writes, seconds | {b['phases']['writing_seconds']:.5f} | {c['phases']['writing_seconds']:.5f} |
| Mean three compressions, seconds | {b['persistence_seconds']:.5f} | {c['persistence_seconds']:.5f} |
| Proof JSON bytes | {int(b['proof_bytes']):,} | {int(c['proof_bytes']):,} |
| Combined gzip bytes | {b['compressed_bytes']['combined']:,} | {c['compressed_bytes']['combined']:,} |
| Maximum observed process RSS bytes | {a['peak_rss_bytes']['all']:,} | {a['peak_rss_bytes']['admitted']:,} |

Mean complete cost changes **{a['comparison_percent']:+.2f}%**; paired changes are
{a['paired_percent'][0]:+.2f}% and {a['paired_percent'][1]:+.2f}%. Search choices and outcomes can change,
so this is not an equal-search representation comparison. The complete prior
proof prefix remains identical in both modes; final size differences come from
new expansion records. The active cap is not a proof-size cap.
'''
p=Path('research/bounded-active-knowledge.md');text=p.read_text();assert 'ADMISSION_RESULTS' in text;p.write_text(text.replace('ADMISSION_RESULTS',measure))
tex=fr'''On the same sixteen exposed edited targets, full admission certifies
{solved('all')}/16 and bounded admission {solved('admitted')}/16 within the fixed cap.
There are {len(a['gains'])} newly certified answers and {len(a['losses'])} lost baseline answers.
The preserved historical union certifies {union}/16, leaving {len(a['remaining'])} unresolved.
All target reference outcomes are trusted UNSAT claims; only checked project
refutations contribute to certified coverage.  Gains, losses and remaining
case diagnostics are recorded separately.  The historical union is not a
measured combined dispatcher, and these exposed inputs are not fresh transfer.

Imported active clauses fall from {a['initial_active']['all']:,} to
{a['initial_active']['admitted']:,} across the sixteen runs.  Entered contexts change
from {a['states']['all']:,} to {a['states']['admitted']:,}, and assignment occurrence updates
from {a['assignment_occurrences']['all']:,} to {a['assignment_occurrences']['admitted']:,}.
Across two fresh-process alternating pairs, mean complete cost {cost} from
{b['complete_seconds']:.5f} to {c['complete_seconds']:.5f} seconds ({a['comparison_percent']:+.2f}\%).
Paired changes are {a['paired_percent'][0]:+.2f}\% and {a['paired_percent'][1]:+.2f}\%.
Mean acquisition including checks changes from {b['phases']['acquisition_seconds']:.5f}
to {c['phases']['acquisition_seconds']:.5f} seconds, explicit checking from
{b['phases']['checking_seconds']:.5f} to {c['phases']['checking_seconds']:.5f}, warm replay from
{b['warm_seconds']:.5f} to {c['warm_seconds']:.5f}, and two cold reload/checks from
{b['cold_seconds']:.5f} to {c['cold_seconds']:.5f} seconds.  Proof JSON changes from
{int(b['proof_bytes']):,} to {int(c['proof_bytes']):,} bytes and combined gzip from
{b['compressed_bytes']['combined']:,} to {c['compressed_bytes']['combined']:,} bytes.
Maximum observed process RSS changes from {a['peak_rss_bytes']['all']:,} to
{a['peak_rss_bytes']['admitted']:,} bytes.

The measured workload includes target and parent input/hash reads, parent proof
checks, selective transport, ranking, augmentation, expansion, substitution,
checks, writes, three compressions and replay.  The two reload/check rounds
called cold in the counters deserialize fresh objects in the same worker, after
its warm round; they are not independent cold-start processes.  Separate fresh
workers reproduce every target answer and checker counter with search, expansion
and transport disabled; this validation is outside benchmark costs.  Old acquisition is separately
recorded and additional.  Imports/startup, reports and independent audits are
additional; cold replay does not flush operating-system caches.  Search choices
and answers can change, so the comparison is not equal-search proof packing.
Both modes retain the identical complete prior proof prefix, including inactive
ancestors.  Final proof-size differences reflect newly acquired records.
'''
p=Path('paper/bounded_domain_sat_and_amortized_reasoning.tex');text=p.read_text();marker=r'\section{System 1, System 2, and the reuse of computation}';assert text.count(marker)==1 and r'\label{sec:admitted-learning}' not in text;section=(out/'manuscript-section-template.tex').read_text().replace('ADMISSION_MEASUREMENTS',tex);p.write_text(text.replace(marker,section+'\n'+marker,1))
print('Wrote bounded-admission research checkpoint')
