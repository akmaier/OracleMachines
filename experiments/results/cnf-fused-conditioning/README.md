# Checked conditioning edges without full intermediate records

This experiment implements the representation gap identified by the conditioning
study. All 949 inputs are unchanged; this is a matched representation comparison,
not a new holdout or a coverage improvement. The previous independent SAT solver
still makes every decision and retains the same 4,034 residuals in every mode.

## What is stored and checked

A normal OR edge names the full restricted CNF. If that node would immediately
use the existing simplification rule, the new edge instead names its simplified
child and carries the unit/pure certificate. The assumption is supplied by the
OR attempt's variable and the edge's false/true position. Child names compose
through intermediate normalization into parent variable IDs. Full intermediate
clauses, duplicate profile evidence and their node record are omitted when they
have no separate root/component use. Exact parent/source records remain.

The checker reconstructs the restriction and normalization, recomputes the old
profile/component gates, checks the saved reasons, reconstructs the final target
and validates its identity and binding. Recognized families and independent
components keep their original priority. Fusion applies only where the old
planner would choose `simplify`. A pure-enabled policy retains the same complete
global-purity checks as before. An omitted required closure or forged reason,
assumption context, target or binding is rejected.

For a branch value b and remaining child variables Y_b, the edge asserts
`G_b(y) iff exists h, F(x=b,y,h)`. It is an existential relation, not pointwise
equivalence over erased variables. Every child model lifts using the branch
assumption, recorded choices and variable transport, then is checked against the
whole parent CNF. Both branch children are still required for a complete OR
decomposition. No SAT/UNSAT claim is inferred from an unresolved child.

The policy has a separate version field. Existing roots, intermediate records,
archives and solver results are not deleted or migrated. A repeated exact source
uses checked memory or durable nodes. An edited source needs a new identity and
reconstructed reasons; this is not incremental maintenance of arbitrary edits.
The only base-inventory changes are shared storage and conditioning hooks; the
old policies retain their previous serialized records and behavior.

## Matched results

All rows use depth two and four candidates. Coverage excludes the 512 tiny
exhaustive sources, leaving 437. Total time includes recognition, discovery,
checking, serialization, persistence, original-source solving and successful
root lifts. Unlike the earlier study, OR-root lifts are charged to both sides
here. Earlier times should not be directly substituted into this comparison.

| Policy | Closed / 437 | Total s | Discovery s | SQLite bytes | Cold audit s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solver only | n/a | 4.78355 | 0 | 16,404,480 | 0.92615 |
| Frequency, units | 322 | 17.33216 | 12.66311 | 79,118,336 | 6.18338 |
| Fused frequency, units | 322 | 15.97544 | 11.26878 | 62,464,000 | 6.09020 |
| Shortest clauses, units | 330 | 21.16978 | 16.21450 | 96,911,360 | 7.89184 |
| Fused shortest clauses, units | 330 | 17.63829 | 12.98724 | 65,572,864 | 6.93005 |
| Frequency, units+pure | 329 | 18.49975 | 13.54697 | 78,061,568 | 6.91286 |
| Fused frequency, units+pure | 329 | 17.14480 | 12.20739 | 60,809,216 | 6.52549 |

Every paired source has the same root profile, coverage summary and acquired
conditioning-candidate count. The archive analyzer goes further: all 3,999 OR
plans across the three pairs retain the exact alternatives, selected index,
coverage summaries and final child CNF/depth/bindings after contracting the old
simplification node. All non-simplification CNF/depth pairs are preserved. Full
serialized keys differ because the policy version is part of their identity.

| Policy pair | Pattern nodes before -> after | Logical node bytes before -> after | Fused edges | Distinct omitted intermediates |
| --- | ---: | ---: | ---: | ---: |
| Frequency | 9,162 -> 6,102 | 35,730,036 -> 25,366,090 | 3,921 | 3,060 |
| Shortest clauses | 11,224 -> 6,281 | 44,967,792 -> 25,908,912 | 5,428 | 4,943 |
| Combined units+pure | 8,812 -> 5,712 | 34,952,640 -> 24,296,414 | 3,930 | 3,100 |

The shortest-clause archive retains only 25 explicit simplification nodes,
compared with 4,968 before fusion. Fused traces themselves take 430,620 JSON bytes
over 5,428 edges, including 25,127 unit-reason entries. Frequency traces use
324,851 bytes, and combined traces 325,206 bytes, including 1,626 pure assignments.
These costs are already included in the new OR payload. Each policy's exact
source payload increases by 123,370 bytes from the new policy metadata.

## Runtime and memory limits

Savings do not come from skipping recognition or checks. Frequency classification
calls increase from 18,324 to 20,046 and propagation visits from 5,318,896 to
6,073,100; shortest-clause classification calls increase from 22,448 to 23,418.
Incoming fused edges can repeat work previously attached to one shared node.
Normalization payload decreases, and fewer full records are checked, serialized
and retained. The initial 48-case in-memory pilot actually regresses in time,
2.17463 -> 2.24521 s, while reducing logical node bytes. It is preserved in
`pilot.json`. The full-database savings are single sequential samples, not a
uniform runtime guarantee or statistical significance result.

The original six easy-case allocation diagnostic slightly increases with the
new metadata (shortest-clause peak 153,294 -> 153,994 bytes). A separate diagnostic
on six explicitly named branch-heavy sources, including a 32-variable source,
gives the following traced Python peaks:

| Policy pair | Peak traced bytes before -> after |
| --- | ---: |
| Frequency | 6,058,671 -> 4,614,558 |
| Shortest clauses | 5,682,777 -> 3,756,516 |
| Combined units+pure | 5,428,612 -> 4,234,777 |

Both diagnostics exclude native SQLite memory and RSS and are not full-corpus
peak measurements. They run separately from the timed comparison. Warm
reinspection is 116.73 -> 111.53 ms for frequency, 104.57 -> 105.95 ms for
shortest clauses, and 105.20 -> 127.91 ms for combined processing. Warm timing
regressions and the small diagnostic increase are retained.

For A incoming fused edges and U distinct intermediates, fusion replaces U full
node records with A edge traces and final-child bindings/references. Repeated
trace copies, recognition, restriction and validation remain charged. High fan-in
can make those repeated costs significant; no universal space or time reduction
follows. This transformation changes neither the search-depth obligation nor
the number of unresolved semantic problems.

## Remaining discovery gap and validation

The shortest-clause mode still leaves 107 non-tiny sources open, and all policies
still miss the 32 fresh 3-CNFs on 20/32 variables. Its remaining logical payload
is dominated by unresolved nodes (12,124,411 bytes) and OR nodes (11,510,391 bytes).
The next discovery experiment should use bounded, checked probing on conditioned
residuals containing binary clauses: a unit-conflict proof under one assumption
can justify the opposite forced value without treating it as an arbitrary choice.
Use the compact closure representation, retain every failed probe, and compare
with the same existing depth/candidate policies while charging probe work. Pure
3-CNF roots have no immediate unit cascade after only one assignment; account
for when conditioning first creates useful binary interactions. No small probe
budget or complete coverage for every CNF is guaranteed. Avoiding repeated
recognition remains supporting work if its measured cost dominates probing.

All 312 Python tests pass. New checks cover exhaustive tiny inputs, every branch
fiber and model lift on unlabelled mixtures, renamings, edits, terminal/component
priority, forged and omitted traces, source transport, cold corruption and
coexistence. Seven new and five previous archives replay without byte changes
or fresh solver expansion. The unchanged Lean build/audit passes (4,087
declarations / 1,946 theorem declarations). Existing conditioning and
simplification semantics compose here; no new Python/SQLite refinement or
unrestricted polynomial-time SAT result is claimed.

```sh
python3 experiments/compare_cnf_fused_conditioning.py --output /tmp/cnf-fused-new
python3 experiments/analyze_cnf_fused_conditioning.py /tmp/cnf-fused-new
python3 experiments/profile_cnf_fused_memory.py /tmp/cnf-fused-new
python3 -m unittest discover -s solver -p 'test_*.py' -q
```

Use a new output directory. Run allocation profiling after timing completes.
Exact inputs, fingerprints, per-source records, original/fused archives, full
plan checks and both allocation diagnostics are retained. Generation, exhaustive
truth tables, summary walks, initialization and gzip are outside operation time;
full cold verification is reported separately.
