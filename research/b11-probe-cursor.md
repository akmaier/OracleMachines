# B11 expansion and B10 continuation find complementary implications

Checkpoint: 26 November 2026. B11 probing finds one new failed assumption at
`(37,39)`; continuing the older B10 schedule finds two different failures at
`(67,63)`. Combining the independently checked implications forces **four new
assignments across two open cases**. Neither case closes. Sampled structural
coverage remains **232/246**, with **14 open**; there is no new native certificate.

## The recognition and reuse condition

B11 appends complements of the checked B10 failures, preserving each reason's
original bank. The source histories use the preceding shared B8 preparation
inside each call. The supplied B11 closure is independently checked to completion.
Only `(37,39)` and `(67,63)` change banks and restart. Twelve other banks reuse
the B10 schedule because their exact clauses, complete closure traces (including
trace order) and trace allowances agree. Full bindings include the source, bank,
closure, deterministic literal order, policy and allowance.

Every old failure proof, cursor binding and schedule is checked. The fresh cold
checker repeats preparation from portable inputs, without trusting discovery's
state. The final audit additionally reconstructs B11 through the frozen B10
feedback implementation, compares every clause/origin tuple and checks new
programs directly against that independently reconstructed bank. Continued B10
programs are separately checked with the frozen B10 checker on bank 10.

Open completions remain scheduling information, not SAT certificates. A source,
closure, bank or allowance change cannot import an old cursor as if it had been
checked on the new bank. Previously valid failure proofs remain usable when
checked on their original bank; this does not justify carrying old open branches
across a strengthening without further checks.

## What the two searches discover

| Local case | New B11 failed assumptions | New continued-B10 failures | Added combined assignments |
| --- | --- | --- | --- |
| `(37,39)` | `-45` | None | `45=true` |
| `(67,63)` | None | `97,129` | `97=false`, `129=false`, `39=true` |

Variable numbers are local bank coordinates. B10 continuation retains the earlier
`-112` failure at `(37,39)` and `66` failure at `(67,63)` too; the table excludes
those previously known failures. B11 alone adds one assignment, while the joint
closure adds four. The latter includes one propagation consequence beyond the
three new failed-assumption complements. Both complete closure traces are saved.

This is a concrete limitation of always preferring a newer bank. A stronger bank
can expose a previously missed implication, as at `(37,39)`, but restarting its
bounded schedule can miss implications reached farther along the older schedule,
as at `(67,63)`. This is a search-budget effect, not weaker logical strength.
Keep both proof sets and unfinished schedules; neither run subsumes the other's
bounded discovery result.

Eleven B11 orders are exhausted and three remain unfinished: `(1,15)`, `(37,39)`
and `(67,63)`. On `(1,15)`, the unchanged bank continues from 64 to 128 completed
assumptions. The changed B11 banks each finish 64 assumptions, while continued
B10 reaches 128 at `(37,39)` and 256 at `(67,63)`. Exhaustion does not certify SAT.

## Charged costs

Two isolated repetitions run in opposite order, with 64 additional probes,
occurrence allowance 262,144 and trace allowance 256. Matched fresh adds the
reusable completion count and scales its occurrence allowance; exact result
equality is checked on this workload. B10 continuation and fixed-budget restart
are separate coverage/cost comparisons, not matched controls.

| Measurement | Continue B10 | B11 restart | Matched fresh | Exact reuse |
| --- | ---: | ---: | ---: | ---: |
| Reconstruction (s) | 0.16628 | 0.16682 | 0.16574 | 0.16576 |
| Discovery including preparation (s) | 0.16694 | 0.19608 | 0.20172 | 0.18930 |
| Independent cold checking (s) | 0.15989 | 0.18371 | 0.18188 | 0.18237 |
| Serialization/reload (s) | 0.00395 | 0.00402 | 0.00362 | 0.00356 |
| Complete census (s) | 0.50319 | 0.55696 | 0.55884 | 0.54683 |
| Fresh probe attempts | 192 | 896 | 2,074 | 192 |
| Occurrence visits | 5,777 | 26,731 | 51,818 | 6,416 |
| Serialized result bytes | 157,305 | 150,613 | 154,676 | 154,676 |

Reuse avoids **1,882 probes**, reducing matched discovery time **6.16%** and total
time **2.15%** in these two repetitions. Discovery improves on thirteen case-level
means and regresses on `(67,63)`; checking regresses on seven. All measured
regressions remain. The small total reduction is not a universal or statistically
established speedup. B11 reuse costs **8.67% more** than continued B10 and finds a
different implication rather than strictly greater coverage.

Source reconstruction, discovery and checking consume **30.31%, 34.62% and
33.35%** of B11 reuse time. Prefix/history validation still dominates the cost
left after probe reuse. Peak process RSS ranges from 97,927,168 to 98,025,472
bytes; there is no meaningful memory reduction. Input loading/startup, historical
acquisition, pilots, native compilation and final lineage auditing are additional.
Independent original-bank checking and individual/joint feedback construction
cost **0.88537 s** separately; overlay publication/reload costs **0.01281 s**.
The feedback diagnostic uses frozen reconstruction for comparison and is not an
optimized production feedback timing.

## Persistence and remaining obligations

The **8,654-byte** resume overlay references **3,087,280 bytes across 91 transitive
frontier files**, plus itself. Older overlays retain solved cases and both older
and newer histories. Flattening the fourteen rows and inlining just this pass's
two result sets would take 2,106,602 bytes; older result bindings would still
remain. References avoid another duplicate export when dependencies are already
stored, not the retained dependency set or lifetime growth. Native archives and
diagnostic evidence are additional to these frontier-data totals.

Resume `experiments/results/cnf-b11-probe-cursor/checkpoint.json` with
`compare_cnf_b11_probe_cursor.load_frontier(checkpoint['b11_probe_cursor']['remaining'])`.
New fields are `b11_result`, `b10_comparison_result`, `b11_feedback_closure` and
`b11_joint_closure`. The loader checks parent bindings, exact keys and non-overwrite;
results must still be decoded and semantically checked before use. Hash agreement
is not proof authority.

The next coverage step is to use the joint closures for the same two changed
cases while retaining the farther-progressed B10 schedule. A useful experiment
is to prioritize previously untested assumptions after a bank change, treating
old progress only as an ordering hint. Every selected assumption must still be
checked on the new bank. This could avoid spending the entire next allowance
repeating the start of an old order; it is a hypothesis, not an implemented gain.
The eleven exhausted unchanged cases need stronger interaction or another
decomposition. Uniform efficient arbitrary-SAT coverage remains open.

The fixed-bank schedule has at most twice the source-variable count, but that
does not bound inherited proof size, reconstruction or context expansion.
Ownership copying, canonicalization, index preparation and old proof checking
precede or fall outside the occurrence cap. No polynomial construction,
unrestricted runtime or lifetime-space guarantee follows from the bounded pass.

All **2,109 full tests** and **43 focused tests** pass. Nine new tests cover exact
reuse, source-bank provenance, changed bounds, cold/interrupted continuation,
caller mutation, malformed proofs/bindings, overlay corruption and complementary
search results. Exhaustive signed unit/binary formulas on two variables and
seventy generated five-variable formulas are unit-simplified before applicable
open histories are built; returned implications/refutations agree with exhaustive
model checking. All **1,163 prior source fingerprints**, **30,211 artifact entries
in 208 manifests**, existing native/reference/cumulative bindings and **64 original
manuscript proof blocks** remain unchanged. The final source ledger has 1,167
entries. Existing SQLite ResourceWarnings remain in the full suite.

To rerun, copy `pilot.json`, `pilot-source.py` and `b10-comparison-pilot.json` to a
new output directory before `compare_cnf_b11_probe_cursor.py prepare`. Then run
`run_census`, followed by `validate_cnf_b11_probe_cursor.py validate`; supply test
and build logs plus a decision record before `seal`. Do not overwrite this
checkpoint's frozen results.
