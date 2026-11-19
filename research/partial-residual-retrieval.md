# Partial-search proofs need better variable correspondence

The optional `PartialResidualSolver` admits bounded hints from committed negative
residual proofs, including proofs left by budget-stopped searches. It finds a few
checked matches but **increases mean query time 5.88% exposed and 4.27% on a fresh
size holdout**. Outcomes and recorded native expansion counts are unchanged.
Keep `InputSafeAffineProbeSolver` as the performance baseline. This experiment
rejects the current admission/index policy as a net improvement on these streams.

## What the policy checks

After a completed query or native budget stop, admission examines at most 64
newest committed native records. It skips key/payload pairs over 256 KiB before
fetching and decoding them, and admits nonterminal negative proofs with at most
1,024 literal occurrences. Terminal contradictions are cheap to rediscover;
split, component and unit proofs with dependencies are the intended candidates.
This filter was chosen before freezing the comparison. The earlier policy and
its passing tests remain in `initial-policy/`.

The pool retains at most 64 entries under a conservative 512 KiB charge for
entries, index containers and independently charged anchors. Two longest source
clauses, with lexical ties, index each hint in its own compact variable coordinates.
A query makes at most 32 residual probes and considers four candidates per probe.
Whole-source containment qualifies; one missing clause may trigger one causal
support plan, limited to 32 nodes, 8,192 source literals and a 128 KiB accepted-plan
charge. The original native verifier checks the origin, derived support and target
containment. Candidate hints never carry authority. A conditional residual
refutation is not a refutation of its unconditioned source.

Admission requires committed, idle, healthy storage. Failed publication cannot
seed pending records. On restart, the same bounded tail seeds hints; this does
not restore the previous pool order or recover source-variable maps. All native
and affine proofs remain in their existing independently checked archives.

The caps bound retained hints and selected discovery work, not total solver cost.
SQL length inspection can touch oversized payloads before they are rejected.
Decoding, insertion/eviction transients, proof prerequisite checking, publication,
native fallback and the full checked graph are outside the retained byte caps.
An empty pool reports zero, excluding its empty container shells.
Every probe still visits target clauses; a small candidate count does not make
recognition constant-time in input length. Persistent proof storage is uncapped.

## Frozen comparison and measured regression

Both policies start empty, use the same 256-native-expansion cap, and retain all
preceding witness, negative-plan and affine features. Eight serial workers use
two opposite mode orders. Exposed sizes are 96/108/120; fresh holdout sizes are
126/132/138. Each stream has 108 attempts and 72 roots, with six generators,
two samples and base/edit/repeat variants. The solver receives no generator or
donor labels. These designed workloads are not a representative external corpus.

| Measurement | Exposed baseline | Exposed pool | Holdout baseline | Holdout pool |
|---|---:|---:|---:|---:|
| Mean query seconds | 11.84740 | 12.54410 | 22.14798 | 23.09321 |
| Mean complete worker seconds | 23.16265 | 23.87504 | 43.69728 | 44.62639 |
| Recorded native expansions | 4,982 | 4,982 | 8,450 | 8,450 |
| Native records | 5,655 | 5,655 | 8,825 | 8,840 |
| SQLite bytes | 77,430,784 | 77,430,784 | 145,874,944 | 145,825,792 |
| Checked graph and candidate bytes | 210,148,387 | 210,350,129 | 398,449,606 | 398,704,123 |
| Mean cold proof seconds | 4.69563 | 4.71909 | 9.00763 | 9.03188 |

Query and complete times regress in both orders. Complete time rises 3.08% /
2.13%. Warm time rises 3.56% / 1.14%. Holdout SQLite storage falls only 0.034%,
while compressed storage grows 0.011%; fifteen extra native records arise in the
changed proof graph. Checked objects grow 0.096% / 0.064%. There is no substantial
space gain. Complete time includes setup, misses, hint maintenance, proof checks,
publication, retained-object measurement, warm/cold replay, reconstruction,
sidecars and compression. Preparation and posthoc audits are separate.

Outcomes remain 50 SAT / 43 UNSAT / 15 unresolved exposed and 42 SAT / 39 UNSAT /
27 unresolved on holdout. Every matched completed verdict agrees; no formerly
completed attempt becomes stopped. Exhaustive tests cover all 512 two-variable
formulas, and regressions check conditional-proof misuse, deleted premises,
tampered storage, stale hints, publication failure and byte/work caps.

There are two exposed hits from 999 probes and 48 candidates, and one holdout hit
from 1,346 probes and 37 candidates. Holdout admission reads 28,147,556 key/payload
bytes, admits 993 hints and evicts 985. Peak retained charge is 524,270 bytes.
Posthoc profiling reproduces every query counter, result and native/affine digest.
Instrumented admission takes 1.863 seconds and retrieval 0.341 seconds; charge
computation takes 1.269 seconds inclusive within admission. These overlapping,
instrumented times diagnose overhead; use the frozen workers for comparisons.

## Checked blind spot and next experiment

The diagnostic stores the eight ternary clauses excluding all assignments on
variables 1,2,3. The target contains those clauses on variables 4,5,6, plus
`(1,4,7)`, `(2,5,8)` and `(3,6,9)`. Both formulas are UNSAT. The retained
literal-valued anchors miss the target. Supplying the injective order-preserving
map 1→4, 2→5, 3→6 lets the unchanged subset checker publish the target proof
without fresh solving; independent cold replay validates it. This establishes
a representation blind spot. The mapping is supplied, and its prevalence in
the timed workloads is unknown. It is not an automatic discovery result.

The next primary experiment should retain bounded **root-variable correspondence
for committed residuals**, then propose transport into later residuals of the
same source or edits retaining variable identities. Compose checked normalization
maps, require an injection, test actual transported clause containment, and retain
the original proof checker as authority. Renamed unrelated inputs require an
additional mapping-discovery algorithm; arbitrary isomorphism search must not
be hidden in lookup. Cold map persistence/reconstruction and invalidation also
need explicit costs. Freezing a fresh holdout prevents tuning away this regression.

Admission should be selective and incremental if this transport finds useful
matches: maintaining almost a thousand hints for one hit is not worthwhile.
The larger bottleneck remains acquisition. Random and shared mixtures consume
86.02% of first-order holdout query time; the 27 stops consume 19.463 of 23.074
seconds. Better correspondence alone does not establish a small reusable core
or efficient arbitrary-SAT closure. Alternative supports, separator discovery
and representative external workloads remain separate gaps.

Resume `experiments/results/cnf-partial-residual-pool/checkpoint.json` for the
preserved evidence union, while keeping the preceding affine policy as the
performance baseline. `checks.json` binds the source ledger, prior artifacts,
all chronological and historical audits, test/build results and unchanged proof
blocks. No new tractability theorem or P-versus-NP result is claimed.
