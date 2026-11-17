# Choose an available residual through a different checked guard

Trying one alternative guard after the first residual misses adds one transfer
on 192 fresh queries: expansions fall **142 -> 135 (4.93%)**, and new proof rows
**362 -> 356 (1.66%)**. The saved work belongs to current case 36. Mean complete
time is **1.30% higher**, with large variation and opposite paired signs. This is
a small verified coverage gain, not a demonstrated runtime or memory improvement.

## Policy and proof boundary

The ordinary pipeline first tries a cached whole-query result, a whole-query
support, a SAT witness, and its first valid clause-deletion guard. If that guarded
target has neither a cached answer nor a contained support, the new selector
examines at most one other matching extension proposal. An unavailable or
positive stronger formula consumes the candidate budget too. Index enumeration
and support scans remain charged; a bound on checked candidates does not make
the entire recognition cost constant.

An alternative is selected only if its target already has a checked proof or
model, or contains a checked ready negative support. Pending descriptions are
skipped. Selection performs no fresh SAT search and publishes no proofs. The
ordinary query path then rechecks the selected guard, publishes any required
subset certificate, checks the child and lifts a positive model to the source.
The original guard remains the fallback on a miss. Both support histories and
all proof/query results retain complete cold checking.

This remains an exact guarded decomposition: if a checked stronger formula
G and C is unsatisfiable, every model of G falsifies C. Either valid deletion
guard can therefore be used, with its own checked premise. An available child
alone never establishes the answer for G. The policy does not combine guard
assignments, materialize a pending alternative, or find an optimal decomposition.

## Fresh-query comparison

```sh
python3 experiments/compare_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/validate_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/analyze_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/check_cnf_guard_control.py /tmp/cnf-alternative-guard
```

Both modes start from the same **19,907-key union** and load the 207-entry legacy
and 176-entry causal banks, each with eight-catalog / 389-origin history. The
larger 203-entry causal bank is preserved but remains optional and unloaded.
No new supports are acquired. Selection excludes 2,304 earlier sidecar answers
and cached full roots, then takes 64 new neighbours per template, interleaved.
Four alternating fresh-process pairs visit each query twice. Tests, builds,
profiles and post-hoc checks do not overlap timed workers.

| Measure | First guard | Alternative enabled |
| --- | ---: | ---: |
| Cofactor transfers | 27 | 28 |
| Expansions / splits | 142 / 49 | 135 / 47 |
| Materialization rows | 49 | 49 |
| New proof rows | 362 | 356 |
| Mean query seconds | 2.00774 | 1.51412 |
| Mean complete seconds | 13.60267 | 13.77944 |
| Mean peak RSS, bytes | 520,613,888 | 545,886,208 |
| SQLite bytes | 63,504,384 | 63,496,192 |
| Gzip plus first-trial raw sidecars, bytes | 11,942,205 | 12,207,972 |

All modes answer **100 SAT / 92 UNSAT**. Only case **36**, in template 6, changes
guard: seven expansions become one checked subset publication, requiring no
materialization. No other query regresses in expansion count. Repeated visits
add no rows, but case 36 repeats guard selection: its original target was never
solved, while its selected alternative is now cached.

The selector runs on 15 first-visit misses and once on the repeated visit.
Its 16 additional candidates require 1,729 extension comparisons and 5,709
support-candidate inspections. It makes one ready-support choice, one subsequent
known-target choice and 14 misses, skipping six pending support matches. All
extra recognition, checks and publication are charged. The saved seven nodes
are an observed batch reduction, unlike the previous historical opportunity.

Mean query time falls 24.59%, but total time rises 1.30%. Paired complete changes
are **-28.44%, +36.27%, -28.34%, +48.04%**; their signs track trial order in these
four pairs, with cause untraced. Peak RSS averages 4.85% higher with mixed paired
signs. These measurements establish neither a stable speedup nor a memory win.
Cold audit and compression consume **52.62% / 27.04%** of candidate time. Gzip
plus sidecars grows **2.23%** because selection traces retain the original and
examined guards, despite six fewer proof rows. Historical artifacts and all trial
archives remain additional storage.

Complete time includes preparation, recognition, ordinary checking, publication,
queries, persistence, full cold proof/query and lineage audit, compression and
final digest/report generation. Imports, initial CLI reads and final wrapper
rewrite are excluded. Input selection and old acquisition remain separately
charged. Independent policy reconstruction and the controls below are outside
timed workers.

## Controls and provenance

Untimed replay of the previous frozen worker produces a byte-identical database
and identical semantic query records to the new first-guard baseline, after
removing the new null diagnostic field. This checks that copying the query loop
did not silently improve or weaken the baseline.

Historical case **121** is restored from its original **19,543-key snapshot**.
With fresh SAT search disabled, the new selector finds the diagnosed alternative,
and the ordinary subset rule publishes one proof row. Its child solves with zero
expansions, and complete cold proof/query and both-lineage audits pass. The old
20-expansion number belongs to the historical stream; this control is not a new
isolated matched runtime comparison. The regression proof and result are retained
in a separate archive, not counted as a new fresh-query case or amortized gain.

First-origin guard comparisons also need care. Fresh case **101** uses a guard
different from its selected core's first origin, in both policies. The core's
second recorded origin already uses that guard. Across all recorded origins,
**no hit uses an unseen removed-clause assignment**. Case 36 changes the chosen
guard for its query, but its selected support already has that guard in its
provenance. This is useful decomposition choice without evidence of general
transfer across previously unobserved guards.

## Next cost and coverage targets

All **135 remaining expansions are negative**. Largest current cases are
**2 (18), 120 (17), 66/67/180 (14 each), 7 (13), 23/155 (11 each)**.
Templates 6/8/12 account for 55/34/46 expansions. These IDs belong to this stream.

Three cases have pending supports under an alternative guard: **23 (11 current
expansions)**, **85 (six)** and **103 (one)**. They account for the six skipped
matches; several descriptions match case 103. Price checked materialization on
23 and 85 before enabling it, and keep 103 as a low-cost fallback control.
Deriving a small support can cost more than solving its target. Use the original
pre-query state for controlled probes and fresh inputs for generalization; these
cases are now retained in the new union. Record partial reusable derivations,
recognition cost and later-sharing effects if testing a derivation budget.

Full cold replay remains the dominant complete cost, and timing variation needs
explanation before asserting a net speedup. Neither bounded candidate selection
nor these acquired frontiers provide a uniform polynomial solution of arbitrary
SAT, a minimum-cost expansion theorem, or a compact-closure construction.

## Validation and retained authority

Independent validation passes **518 tests**, eight complete fresh-trial
archive checks / **3,072 query replays**, every union node, **2,573 inherited
decisions** and all 192 new decisions. Archive validation disables fresh search
and reconstructs guard selection and proof choice from pre-query append history.
Separate untimed frozen-worker replay recomputes the baseline, matching semantic
queries and proof bytes. The historical regression adds one proof row without
fresh SAT search and passes full cold proof/query and both-lineage checks.

The fresh-query union retains **20,270 keys / 63,492,096 SQLite / 4,704,611 gzip
bytes**, adding 363 keys and preserving every prior payload. There are no
alternate certificates. New decisions have **144 direct roots / 48 negative
guards**. The historical regression's additional target proof is not in this
union; its complete archive and guarded result remain separately retained in
`experiments/results/cnf-alternative-guard/historical-control/` and bound by
`control-check.json`. It is not counted as a fresh-query coverage gain.

Resume `experiments/results/cnf-alternative-guard/checkpoint.json`. It preserves
all prior semantic fields and adds `alternative_guard_study` and
`alternative_guard_decisions`. The measured banks retain the same eight-catalog /
389-origin history, with **132/75 legacy** and **67/109 causal** ready/pending
entries. The original 170-entry frontier has **126/44**; the optional 203-entry
expanded causal frontier has **67/136**, retaining its eleven-catalog / 526-origin
lineage. All four lineage checks pass. The two newest catalogs contain 98
negative guarded records not acquired into that larger optional frontier.

All prior **397 sources / 4,406 artifacts / 77 manifests** remain unchanged.
Runtime binds 401 sources; analyzer and control checker bring the ledger to 403.
Structural authority stays **2,614 patterns / 259 pairs / 17 missing children**,
original **17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The paper builds cleanly to **202 pages** with
**64 unchanged proof blocks**. No new Lean or unrestricted-SAT resource theorem.
The full test log retains 24 unclosed-SQLite ResourceWarnings from older tests;
eight focused new tests emit none with warnings enabled. Allocation origins
remain untraced.

Checkpoint SHA-256: `ff7c124f610f1a7e11207b6f248d8f420d7bd0272ff91df0c9c9d75d4e8b729d`.
Report SHA-256: `4f15e41ec39a67b7df6172cb64eba7b9c863c492655fdc1b44d9ee674d766909`.
