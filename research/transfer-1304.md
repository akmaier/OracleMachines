# Conditioning exposes a refutation and a zero-valid component

On 2026-11-14, two warm advances close original **case 1304, index 52**, raising
structural coverage **60/83 -> 61/83**, also without growth-exception routes.
The original has 48 variables, 204 clauses and 612 literal occurrences. This is
another adaptively reused development case; 22 originals remain uncovered.

## The observed pattern

The selected residual has **34 variables / 148 clauses / 490 literals**. Its last
ordinary candidate, local variable **34**, is clear in both polarities. That
negative result is retained. The configured ordinary pool is then exhausted.
Ranking the seventeen saved cofactor pairs selects local variable **32**, with
rank `[2, 2, 31, 813, 32]`: two distinct unclosed and missing child roots, maximum
support 31, and 813 total cofactor literals. The pair already occurs in the
immutable source record; its unit traces need no fresh discovery.

Both cofactors close under one 32-state allowance, using **ten new states**:

| Branch | Stored reduction chain (variables / clauses / literals) | Outcome |
|---|---|---|
| variable 32 = false | 31/131/410 -> 29/103/306 -> 23/69/194 -> existing empty-clause terminal | UNSAT |
| variable 32 = true | 31/126/403 -> 29/116/354 -> 26/94/274 -> 25/73/206 -> 18/37/90 -> 15/26/63 -> 12/18/40 | SAT |

The false branch uses three failed-literal reductions and reuses an existing
contradiction terminal. In its final 23-variable state, assuming local variable
9 false gives a unit contradiction; setting it true also gives a unit
contradiction. The true branch uses six failed-literal reductions and reaches a
**zero-valid** terminal: assigning every variable false satisfies all eighteen
clauses. This terminal is neither Horn, dual-Horn nor 2-CNF. There is no
elimination or polarity transformation in these new chains. Variable numbers
refer to each separately canonicalized residual, with the saved transports
checked on every edge.

Thus the useful transfer is conditioning followed by renewed failed-literal
inference, which here exposes both a refutation and an easy satisfying component.
The previous two Horn terminals are only one possible outcome of this process.
The independent reference solver confirms UNSAT/SAT for the two cofactors and
SAT for the original; the satisfying child model is lifted and checked against
the complete split source.

There is a precise reuse opportunity in the negative branch. For this source
formula F, the checked refutation of F restricted to variable 32=false establishes
**F entails variable 32=true**. Every model of F must satisfy that value. A future
route could retain this stronger forcing certificate and reference its proof
when reusing the same source. The current implementation preserves the split
and its branch proofs; this run does **not** install a new inferred-unit route.
Structural closure alone is insufficient to create one: the preceding case 1445
had two closed, satisfiable branches. Such a route must bind an actual refutation,
the exact source and variable transport, and must not survive arbitrary source
edits without checking the premises again.

## Work and storage

The first advance makes two new **external** assumption attempts. The nine new
probe nodes also retain **nineteen internal assumption traces**, containing 157
unit deductions, plus 37 deductions in their forced closures. These proof-trace
counts are distinct from total executed operations and from the ten admissions.
All ten admitted states now have completed rows; no earlier completed state is
admitted again and no unfinished state is left pending.

| Operation | Seconds |
|---|---:|
| Authority reconstruction | 41.00845 |
| Initial complete routes | 6.64226 |
| Initial coverage-index audit | 59.13472 |
| Selection, both advances | 0.07601 |
| Acquisition and candidate checking, both advances | 0.20118 |
| Complete route refresh, both advances | 2.01995 |
| Full warm composition and original proof checking | 0.63035 |
| Incremental warm composition and original proof checking | 0.08911 |
| Delta export | 5.79426 |
| Cold check of new records | 0.01919 |
| Cold expanded positive proof | 3.32938 |
| Complete producer, including both composition controls and persistence | 133.16301 |

Initial reconstruction and preparation total **106.78542 seconds**. Selection,
acquisition, route refresh and incremental checking total **2.38625 seconds**;
complete route refresh accounts for most of that warm work. The two full-control
samples differ substantially, so this is not a stable speedup estimate. The
incremental view checks six changed/new option sources across both graphs and
propagates 118 new justifications after acquisition. Both methods agree on all
83 original flags in both views.

Early closed-child search misses on both advances. It ranks sixteen pairs before
the last ordinary probe, then seventeen before discovering exhaustion; ordinary
fallback ranks the same seventeen again. That is **50 pair checks**. Avoiding
the duplicate final ranking is a specific maintenance opportunity, but its cost
is already included in acquisition above and is much smaller than cold checking.
The unchanged graph after a clear probe also needs no new coverage-rule checks,
yet complete route refresh still costs about a second.

The delta adds **ten patterns and one continuation**, plus one separate split
sidecar: **9,914 compressed bytes / 200,704 SQLite bytes**. Full SQLite grows by
**122,880 bytes** to **771,715,072 bytes / 41,845 patterns**, preserving all older
rows. The expanded positive proof has **3,043 steps**. The reference archive has
**2,259 nodes**, retaining all 2,135 earlier nodes. These are retained storage
measurements, not peak RAM; shorter live obligations do not imply shrinking
history or polynomial storage across arbitrary inputs. The delta excludes the
separately retained positive-proof and reference snapshots, case data, diagnostics
and logs: the complete new results directory occupies **3,115,928 logical file
bytes**, including its manifest. That excludes the reconstructed working database
and source/documentation edits.

## Validation and continuation

The independent replay disables fresh structural recognition. It checks source
bindings, admission identities, saved split proofs, all 83 coverage flags in both
views and the exact next selection. It checks both reference branch answers and
model lifting without new reference expansion, and verifies every retained
reference node. Cold reconstruction and checking take **109.00529 seconds**.
All **181 relevant regression tests pass**. All **249 artifacts** in twelve
preceding manifests are unchanged. The manuscript builds to **154 pages**, with
all **64 existing proof blocks** unchanged, no overfull boxes and no undefined
references.
The producer also checks the new delta, expanded positive proof, unchanged
parent rows and idempotent merging. No new recognizer or Lean refinement is added.

All seventeen retained splits are closed. The next smallest selected residual
belongs to **case 1299 / index 48**, with **36 variables / 162 clauses / 517
literals**. Its next ordinary candidates are **33, 34 and 36**, at offset 12.
No currently saved candidate has a present or closed child root. The best saved
pair splits on variable **17**, with rank `[2, 2, 34, 927, 17]`; this is a size
heuristic, not proof of minimum cost. There is a concrete alternative:

| Next source's split variable | False cofactor | True cofactor | Total literals |
|---|---|---|---:|
| 17, first by current rank | 34/152/485 | 32/144/442 | 927 |
| 1, third by current rank | 16/46/111 | 35/158/502 | 617 |

Variable 1 leaves a larger maximum support but exposes one much smaller
cofactor and about a third fewer total literal occurrences. Neither cofactor has
been acquired, so that is an opportunity, not a measured runtime or coverage
gain. After the remaining probes, compare these balanced and asymmetric choices
on matched snapshots under the same admission allowance, charging failed
recognition as well as successful reuse. This tests the rank's implicit cost
model instead of assuming that minimizing maximum support minimizes expansion.

Resume **`experiments/results/cnf-transfer-1304/report.json`** through
`experiments.continue_cnf_pending_warm.restore_checkpoint`, preserving evidence
counts **(1, 42, 156, 17, 1)**. The next source SHA-256 is
`6b9b95c54e6bc4dcab8c537abb5c636401c87ad995a9ae5957fa2c821c19f1b0`.
Reproduce into a fresh directory with
`python3 experiments/continue_cnf_pending_warm.py OUTPUT --parent experiments/results/cnf-pending-warm/report.json`;
replay this result with
`python3 experiments/validate_cnf_warm_transfer.py experiments/results/cnf-transfer-1304`.
No short chain, cheap pattern discovery, or polynomial expansion bound for
unrestricted SAT follows from this additional completed case.
