"""Reconcile a validated fixed-budget comparison into the manuscript and gaps."""
from pathlib import Path
import json

out = Path('experiments/results/cnf-reuse-expansion')
a = json.loads((out / 'analysis.json').read_text())
assert json.loads((out / 'validation.json').read_text())['passed']
census = json.loads((out / 'support-census.json').read_text())
assert census['passed'] and len(census['records']) == 16
assert all(r['connected_components'] == 1 for r in census['records'])
used_imports = [r['modes']['reuse8000']['used_imported_count'] for r in census['records']]
used_total = sum(used_imports)
imported_total = sum(r['modes']['reuse8000']['imported_derivations'] for r in census['records'])
premise_min = 100 * min(r['modes']['reuse8000']['original_premise_count'] / r['clauses'] for r in census['records'])
premise_max = 100 * max(r['modes']['reuse8000']['original_premise_count'] / r['clauses'] for r in census['records'])
assert all(r['modes']['reuse8000']['supported_variables'] == r['variables'] for r in census['records'])
totals = a['totals']; modes = ('reuse2000', 'fresh8000', 'reuse8000')
solved = lambda mode: sum(n for status, n in a['coverage'][mode].items() if status != 'unresolved')
union = sum(n for status, n in a['union_counts'].items() if status != 'unresolved')
gains = a['gains_over_reuse2000']; reused = a['reuse_only_at_8000']; fresh = a['fresh_only_at_8000']
small, control, large = (totals[m] for m in modes)
ids = lambda values: ', '.join(values) if values else 'none'
summary = f'''[Frozen expansion budgets](reuse-expansion-budget.md) compare the unchanged
watched learner with all surviving knowledge at 2,000 and 8,000 contexts, plus
fresh search at the same 8,000-context cap. The panel remains sixteen exposed
edits of eight refuted parents. All runs start from empty search state.

Checked coverage is **{solved('reuse2000')}/16 → {solved('reuse8000')}/16** with reuse,
versus **{solved('fresh8000')}/16** for fresh search at 8,000 contexts.
There are **{len(gains)} additional reuse answers**, **{len(reused)} reuse-only** and
**{len(fresh)} fresh-only** answers at the larger cap. The historical union covers
**{union}/16**, leaving **{16-union} unresolved**; it is not a measured combined dispatcher.
All completed answers are checked UNSAT refutations. Earlier complete answers
and all earlier derivation prefixes are preserved.

A separate proof census finds all sixteen inputs connected. Their final
refutations reach **{used_total:,}/{imported_total:,}** retained derivation occurrences
and **{premise_min:.2f}–{premise_max:.2f}%** of original clauses, spanning every source
variable. These are stored proof dependencies, not minimal supports or a proof
that every retained ancestor must be active in search.

Mean complete seconds are **{small['complete_seconds']:.5f}** for small reuse,
**{control['complete_seconds']:.5f}** for larger fresh search and
**{large['complete_seconds']:.5f}** for larger reuse. Larger reuse costs
**{a['budget_cost_percent']:+.2f}%** relative to small reuse and
**{a['reuse_vs_fresh_percent']:+.2f}%** relative to equal-cap fresh search.
Proof, acquisition, transport and replay remain charged. These are different
search workloads on exposed inputs, not a uniform speedup or fresh transfer claim.

All **2,689 full and 10 focused tests pass**. Reproduced independent truth checks
cover **47,328 outcomes on 7,888 edited small targets**, including **31,552**
budget-prefix checks. Three fresh workers replay target-only certificates with
search and transport disabled. Validation preserves 253 prior manifests,
84,766 artifact entries, 1,377 scientific sources and all 92 prior proof blocks.
Resume `experiments/results/cnf-reuse-expansion/checkpoint.json`, key
`reuse_expansion`.

**Next priorities:** fresh frozen external transfer, diagnosis of the seven
fresh-search misses, cheaper retained proofs and alternative
supports after premise deletion. Efficient recognition, preprocessing and
unrestricted SAT expansion remain open; no new tractable class is claimed.

'''
for file, old, new in (
    ('research/sat-pattern-discovery.md', '## Latest evidence: watched propagation preserves full-reuse traces', '## Latest evidence: frozen expansion budgets and reuse value'),
    ('research/implementation-gaps.md', '## Latest evidence: watched propagation preserves full-reuse traces', '## Latest evidence: frozen expansion budgets and reuse value'),
    ('research/structural-reuse-priorities.md', '## Current investigation: cheaper full reuse and thirteen remaining targets', '## Current investigation: coverage at a frozen larger expansion budget'),
):
    path = Path(file); text = path.read_text(); assert text.count(old) == 1
    path.write_text(text.replace(old, new + '\n\n' + summary + old.replace('Latest evidence', 'Previous evidence').replace('Current investigation', 'Previous investigation'), 1))

table = '| Quantity | Reuse, 2,000 | Fresh, 8,000 | Reuse, 8,000 |\n| --- | ---: | ---: | ---: |\n'
for label, fn in (
    ('Checked answers / 16', lambda m: str(solved(m))),
    ('Entered contexts', lambda m: f"{a['states'][m]:,}"),
    ('Mean complete seconds', lambda m: f"{totals[m]['complete_seconds']:.5f}"),
    ('Acquisition including checks, seconds', lambda m: f"{totals[m]['phases']['acquisition_seconds']:.5f}"),
    ('Explicit checks, seconds', lambda m: f"{totals[m]['phases']['checking_seconds']:.5f}"),
    ('Warm reload/check, seconds', lambda m: f"{totals[m]['warm_seconds']:.5f}"),
    ('Two reload/check rounds, seconds', lambda m: f"{totals[m]['cold_seconds']:.5f}"),
    ('Writes, seconds', lambda m: f"{totals[m]['phases']['writing_seconds']:.5f}"),
    ('Three compressions, seconds', lambda m: f"{totals[m]['persistence_seconds']:.5f}"),
    ('Proof JSON bytes', lambda m: f"{int(totals[m]['proof_bytes']):,}"),
    ('Combined gzip bytes', lambda m: f"{totals[m]['compressed_bytes']['combined']:,}"),
    ('Maximum observed RSS bytes', lambda m: f"{a['peak_rss_bytes'][m]:,}"),
): table += '| ' + label + ' | ' + ' | '.join(fn(m) for m in modes) + ' |\n'
note = f'''# Expansion budgets and the marginal value of retained clauses

The faster watched-propagation implementation preserved three checked answers
but left thirteen edited targets at the 2,000-context cap. This experiment asks
whether a fixed larger allowance expands certified coverage, and whether retained
knowledge helps compared with the same watched engine starting fresh.

## Frozen policies and exact composition

Before the runs, `protocol.json` freezes all scientific sources, unchanged panel
bindings, target-only proposal policy, the 2,000/8,000 caps, and two reversed run
orders. All sixteen edits of eight already refuted parents are included; the
other sixteen edits of SAT parents remain separate. No reference label enters
discovery. This is development on exposed inputs, not unseen external transfer.

Reuse reads and checks the original parent proof, retains derivations whose
recorded source-premise paths survive the edit, and activates all surviving
clauses. Search runs on the equivalent augmented CNF. Substituting each learned
premise back into its retained derivation yields a certificate checked against
the target alone. SAT requires a complete target model; UNSAT requires an empty
clause. Unknown retains consequences without asserting a decision. Existing
proofs justify these operations; this checkpoint adds no new tractability theorem.

Every trial starts from empty search state. The 8,000-context run does not resume
the measured 2,000-context run, and its cost is not a suffix cost. Source, seed,
decision order and active-clause policy stay fixed within a reuse pair. Direct
validation checks that every small-budget derivation is a prefix of the larger
proof and every completed small answer survives. Context caps count iterations,
not equal amounts of work, time or memory. Production defaults remain unchanged.

## Coverage and cost

{table}

Additional answers from the larger reuse budget: **{ids(gains)}**.
At 8,000 contexts, reuse-only answers: **{ids(reused)}**; fresh-only answers:
**{ids(fresh)}**. The historical union covers **{union}/16** and leaves
**{16-union} unresolved**. Individual outcomes, exact certificates, retained
knowledge and diagnostics remain in `analysis.json`, `coverage-union.json` and
`remaining.json`. Overlap is reported explicitly; the union has no combined runtime.

Larger reuse changes mean complete cost by **{a['budget_cost_percent']:+.2f}%**
relative to small reuse (paired changes {a['paired_budget_percent'][0]:+.2f}% and
{a['paired_budget_percent'][1]:+.2f}%). Against equal-cap fresh search the change
is **{a['reuse_vs_fresh_percent']:+.2f}%** (paired changes
{a['paired_reuse_vs_fresh_percent'][0]:+.2f}% and {a['paired_reuse_vs_fresh_percent'][1]:+.2f}%).
These policies can enter different contexts and return different sets of answers;
the ratios are workflow-cost comparisons, not equal-answer speedup guarantees.

A separately charged post-hoc census checks all final proofs and traverses the
ancestors of their empty clauses. Every target is connected and has 125–151
variables. Larger-reuse refutations reach {used_total:,} of {imported_total:,}
imported derivation occurrences, ranging from {min(used_imports):,} to
{max(used_imports):,} per target. Their recorded original-premise supports cover
{premise_min:.2f}–{premise_max:.2f}% of canonical source clauses and every source
variable. These counts include proof ancestors: they are not minimum supports,
minimum active sets, or bounds against smaller alternative decompositions.
The full records remain in `support-census.json`; they did not guide the runs.

Complete cost includes source reads/hashing, required parent reads/checks,
transport, proposal preparation, augmentation, search, substitution, checks,
writes, three compressions and replay. Original acquisition and historical
append-only storage remain additional; imports/startup, report encoding and
independent audits are excluded. Maximum RSS is an observed process peak.
Retaining all evidence can grow proof storage and checking even when search
benefits. No end-to-end acquisition amortization is inferred.

The two rounds labelled cold in inherited report fields reread sources and parse
fresh proof objects in the same worker after a warm round. They are not independent
cold-start processes, and OS caches are not flushed. A separate new worker per
policy reproduces target-only answers and checking counters with all search,
expansion and transport disabled; this is additional correctness validation.

## Validation and remaining gaps

All 2,689 full and ten focused tests pass. The independently repeated truth audit
covers 512 two-variable clause sets, 3,304 three-variable clause sets of at most
three clauses and 128 signed sparse mixtures with duplicates and tautologies.
Deletion and shared-variable-addition edits give 7,888 targets. Fresh/reuse at
caps 0, 2 and 8,000 gives 47,328 checked outcomes: 23,240 SAT, 8,918 UNSAT and
15,170 unknown. Independent truth verifies 8,228 consequence occurrences;
31,552 budget-prefix and 23,664 retained-prefix checks pass. These repeated
policies, budgets and edits are not independent problem samples.

The first audit reproduction completed its assertions but failed to write to a
missing output directory. The error log is retained. Creating the directory and
rerunning reproduced the complete audit; frozen scientific sources were unchanged.
All six measured workflows and their operation counters are reproduced, including
exact agreement of the small-budget control with the previous checkpoint.
Lineage validation preserves 253 prior manifests, 84,766 artifact entries, 1,377
scientific sources and all 92 previous proof blocks. Four scientific files are
added; the earlier three published snapshots and their manifests remain unchanged.

The next steps are frozen external transfer and explanation of the seven
fresh-search misses, including alternative supports after deleted premises
and cheaper proof retention. General recognition, preprocessing, compact reusable
interaction descriptions and unrestricted expansion remain open. Raising a fixed
cap and completing finite cases does not establish an efficient class covering
arbitrary CNFs.
'''
Path('research/reuse-expansion-budget.md').write_text(note)

section = rf'''\subsection{{Expansion budgets and the marginal value of retained clauses}}
\label{{sec:reuse-expansion-budget}}

The watched implementation preserves three checked answers on the sixteen edited
targets, leaving thirteen at its 2,000-context cap.  A separately frozen comparison
raises that cap to 8,000 and adds a fresh-search control at 8,000.  The original
target bytes, proposal policy, watched learner, active-clause policy and two
reversed process orders are fixed before execution.  All sixteen targets remain
edits of eight already exposed refuted parents.  The other sixteen edits of SAT
parents remain separate.  Neither publisher labels nor reference answers enter
discovery; this is exposed-policy development, not fresh external transfer.

Reuse checks the original parent proof, filters surviving recorded derivations,
and searches the equivalent target with all surviving clauses active.  Exact
proof substitution removes the augmented premises from the final target-only
certificate.  The previous propositions justify this composition.  The larger
run starts from an empty search state, not the measured smaller run's live state;
its time is not a continuation cost.  Direct validation establishes that every
smaller-budget derivation is an exact prefix of the larger proof and that all
previously completed answers survive.  No production default changes.

Checked coverage is {solved('reuse2000')}/16 at 2,000 contexts with reuse,
{solved('fresh8000')}/16 at 8,000 with fresh search, and
{solved('reuse8000')}/16 at 8,000 with reuse.  The larger reuse run supplies
{len(gains)} additional answers.  At the larger cap there are {len(reused)}
reuse-only and {len(fresh)} fresh-only answers.  Their historical union covers
{union}/16 and leaves {16-union} unresolved; it is not a measured combined
dispatcher.  Complete target models or target refutations alone grant authority.
All completed outputs are checked UNSAT refutations.  Unfinished searches
remain unknown, even when a trusted reference says UNSAT.

A separately charged post-hoc census finds every target connected, with 125--151
variables.  Final reused refutations reach {used_total:,} of {imported_total:,}
retained derivation occurrences, ranging from {min(used_imports):,} to
{max(used_imports):,} per target.  Their recorded original-premise supports cover
{premise_min:.2f}--{premise_max:.2f}\% of source clauses and all source variables.
These are ancestors in the stored proof, not minimum supports, minimum active
clause sets or lower bounds on alternative decompositions.  This census does not
guide the frozen acquisition policy.

Mean complete seconds in that order are {small['complete_seconds']:.5f},
{control['complete_seconds']:.5f} and {large['complete_seconds']:.5f}.
Larger reuse changes cost by {a['budget_cost_percent']:+.2f}\% against smaller
reuse and {a['reuse_vs_fresh_percent']:+.2f}\% against equal-cap fresh search.
The corresponding entered-context totals are {a['states']['reuse2000']:,},
{a['states']['fresh8000']:,} and {a['states']['reuse8000']:,}; equal caps do not
imply equal work or equal solved sets.  These are workflow costs, not a universal
speedup or an end-to-end acquisition-amortization result.

Proof JSON bytes are {int(small['proof_bytes']):,}, {int(control['proof_bytes']):,}
and {int(large['proof_bytes']):,}; combined gzip bytes are
{small['compressed_bytes']['combined']:,}, {control['compressed_bytes']['combined']:,}
and {large['compressed_bytes']['combined']:,}.  Maximum observed process RSS is
{a['peak_rss_bytes']['reuse2000']:,}, {a['peak_rss_bytes']['fresh8000']:,} and
{a['peak_rss_bytes']['reuse8000']:,} bytes.  Mean acquisition including checks is
{small['phases']['acquisition_seconds']:.5f}, {control['phases']['acquisition_seconds']:.5f}
and {large['phases']['acquisition_seconds']:.5f} seconds; explicit checking is
{small['phases']['checking_seconds']:.5f}, {control['phases']['checking_seconds']:.5f}
and {large['phases']['checking_seconds']:.5f}.  The two reload/check rounds cost
{small['cold_seconds']:.5f}, {control['cold_seconds']:.5f} and {large['cold_seconds']:.5f}
seconds.  Source reads/hashes, required parent reads/checks, transport, proposals,
augmentation, search, substitution, writes, compression and replay are charged.
Historical acquisition/storage, imports/startup, report encoding and independent
audits are additional.  Reload rounds deserialize in the same worker and do not
flush OS caches; separate fresh workers check target-only answers with search
and transport disabled.

All 2,689 full and ten focused tests pass.  Independent truth audits are reproduced
on 7,888 edited small targets, giving 47,328 outcome checks: 23,240 SAT, 8,918
UNSAT and 15,170 unknown.  They cover all two-variable clause sets, three-variable
sets of at most three clauses and 128 signed sparse mixtures, with deletions and
shared-variable additions.  All 31,552 budget-prefix checks, 23,664 retained-prefix
checks and 8,228 consequence-occurrence checks pass.  Related budgets and edits
are not independent samples.  A missing output directory interrupted the first
audit reproduction only at its final write; the error is retained and no frozen
policy changed.  Validation preserves 253 previous manifests, 84,766 artifact
entries, 1,377 scientific sources, all 92 earlier proof blocks and the three
published snapshots.  Four scientific files are added.  No new tractability
theorem is claimed.  Frozen external transfer, remaining interactions,
alternative premise supports, proof retention cost and unrestricted SAT
expansion remain separate obligations.

'''
path = Path('paper/bounded_domain_sat_and_amortized_reasoning.tex'); text = path.read_text()
marker = r'\section{System 1, System 2, and the reuse of computation}'
assert text.count(marker) == 1 and r'\label{sec:reuse-expansion-budget}' not in text
path.write_text(text.replace(marker, section + marker, 1))
print('Recorded validated budget comparison in gap records and manuscript.')
