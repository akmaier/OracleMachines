# Prior progress guides B12 ordering, but does not dominate source order

Checkpoint: 26 November 2026. The same combined B12 bank is searched with two
orders. Source order finds failed assumption **`-68`** at `(67,63)`;
untested-first finds **`83`**. Their joint closure forces **68=true and 83=false**,
but no case closes. Coverage remains **232/246**, with **14 open**. This is a
checked experimental ordering policy, not a new production default or certificate.

The comparison supplies a concrete counterexample to permanently skipping old
open assumptions after strengthening: source order's new `-68` failure was
previously completed without a failure in the supplied older histories. Revisiting
it is useful. Untested-first finds a different implication within the same
allowance, so neither bounded result subsumes the other.

## Bank construction and the ordering invariant

B12 combines the retained B11 failures and continued B10 failures. Both histories
are independently checked on their original banks. Their common B10 source and
provenance must agree. Duplicate clauses keep their earlier valid origins; new
origins identify either the B10 comparison or the B11 program. The supplied joint
closure is checked to completion before any search.

For a changed bank, let `R` be the existing deterministic source-derived order of
active signed literals and `S` the union of the two supplied completion lists.
The experimental order is the stable concatenation
`[r in R where r not in S] + [r in R where r in S]`. It contains every active
literal exactly once. Existing opposite-literal promotion after a checked failure
is unchanged. “Untested” means absent from these two lists, not never tried on
any earlier bank.

Old completions affect priority only: none is imported as a new-bank completion
when the bank changes. Every newly completed assumption is actually probed on
B12. As before, claimed old open completions are scheduling information, not
independent evidence of satisfiability or absence of a contradiction. Soundness
of returned failure proofs does not depend on their honesty.

Twelve banks are exactly unchanged. They retain source order and import B11
completions only when their clauses, full closure traces and trace bounds agree.
The other two banks, `(37,39)` and `(67,63)`, start fresh under the chosen order.
Bindings include policy, ordering selection, source, bank, closure, complete
derived literal order and trace bound. Cross-policy cursor replay is rejected,
including where the two orders happen to be identical.

Cold validation reconstructs from owned portable inputs. The final audit separately
uses the frozen B10 feedback path, checks B11 and B10 comparison proofs on their
original banks, constructs B12 without the new preparation function, derives the
expected order and checks the result through the frozen cursor engine. Every bank
and origin tuple agrees. No checked object or trusted marker crosses calls.

## Equal-budget discovery and the preserved negative result

Each policy receives 64 new probes per case. On the changed banks:

| Case and order | Completed | Absent from supplied old lists | Present in old lists | New failure |
| --- | ---: | ---: | ---: | --- |
| `(37,39)`, source | 64 | 0 | 64 | None |
| `(37,39)`, untested-first | 64 | 64 | 0 | None |
| `(67,63)`, source | 64 | 0 | 64 | `-68` |
| `(67,63)`, untested-first | 64 | 28 | 36 | `83` |

The heuristic reaches 92 assumptions absent from the selected older lists, but
does not close more cases or find more failed assumptions than source order.
The result rejects a general dominance claim for prioritizing novelty. In local
bank coordinates, the two B12 proofs force 68=true and 83=false. Combining them
consumes **both** search budgets; it is not a single 64-probe achievement.

Continuing B11 separately finds failure `-39` at `(67,63)`, a direct proof of
39=true. The combined B12 closure already implies that value from older B10
failures, so it adds no new B12 assignment. This alternative proof is preserved
as a possible cheaper provenance route; no native reconstruction saving has been
measured. Neither B12 policy nor B11 continuation produces a new native refutation.

Three orders remain unfinished, `(1,15)`, `(37,39)` and `(67,63)`, and eleven are
exhausted. All source-order, untested-first and continued-B11 histories remain.
Exhaustion is not a SAT certificate.

## Full costs, including the regression

Two isolated repetitions run in opposite mode order. `matched fresh` uses the
untested-first policy but extends its probe/occurrence budget instead of importing
unchanged histories; its full result equals the reuse result on every case.
All arms charge reconstruction, owned preparation/recognition, discovery, fresh
independent cold checking, serialization and reload.

| Measurement | Continue B11 | B12 source | B12 untested-first | Matched fresh |
| --- | ---: | ---: | ---: | ---: |
| Reconstruction (s) | 0.16277 | 0.16320 | 0.16324 | 0.16409 |
| Discovery with preparation (s) | 0.18400 | 0.36720 | 0.36773 | 0.38699 |
| Independent cold checking (s) | 0.17911 | 0.36125 | 0.36346 | 0.36877 |
| Serialization/reload (s) | 0.00388 | 0.00499 | 0.00533 | 0.00554 |
| Complete census (s) | 0.54725 | 0.90776 | 0.90850 | 0.93416 |
| Fresh probe attempts | 192 | 192 | 192 | 2,138 |
| Occurrence visits | 5,359 | 5,650 | 6,686 | 54,284 |
| Result bytes | 156,073 | 154,254 | 154,210 | 154,210 |

Untested-first is **0.08% slower** than source order, effectively tied at the
resolution of these two repetitions. It makes more occurrence visits and has
nine discovery and eleven checking case-level regressions versus source order.
All are preserved. Neither the 44-byte result difference nor process RSS of about
98 MB establishes a useful memory improvement.

Exact unchanged-bank reuse avoids **1,946 probes** and improves matched total time
**2.75%**. That is distinct from the ordering experiment. B12 untested-first is
**66.01% slower than continuing B11**, largely because construction/checking again
rebuilds a common history through two paths. Discovery plus checking takes **80.48%**
of total B12 time; the heuristic's two changed cases inspect 512 old completion
slots to partition 552 active literal entries. No general speedup is established.

Running both B12 censuses costs **1.81626 s**, before separately measured feedback.
The audit's independent reconstruction and three-way feedback diagnostic takes
**2.74026 s** and overlay publication/reload **0.01270 s**. Those diagnostic times
were collected while regression tests were running; they are not an isolated
production compilation benchmark. Startup/loading, historical acquisition, pilots,
native compilation and the remaining lineage audit are additional.

## Persistence, limits and next target

The new **13,386-byte** overlay references **3,560,471 bytes in 134 transitive
frontier files**, plus itself. All earlier source-order results, proofs and native
archives remain. Diagnostic artifacts add more storage. References avoid a new
duplicate parent export; they do not remove dependencies or bound lifetime growth.

Resume `experiments/results/cnf-b12-progress-order/checkpoint.json` with
`compare_cnf_b12_progress_order.load_frontier(checkpoint['b12_progress_order']['remaining'])`.
New fields retain `b12_source_result`, `b12_unseen_result`,
`b11_continuation_result`, each B12 policy's feedback closure and
`b12_joint_closure`. The loader checks parent bindings, exact keys and non-overwrite.
Decode and semantically check results before reuse; a matching hash is not proof
authority. Choose the ordering explicitly when validating a B12 result.

**Highest measured cost target:** share the repeated common B10 preparation inside
B12 discovery/checking, preserving independent checks for the distinct original
and comparison programs. The census records 28 context preparations for either
B12 policy, versus 14 for B11 continuation. This is another instance of a proof-history graph being
traversed as a tree. Reusing checked common nodes within one owned call is a more
credible runtime target than replacing source order with the heuristic. A generic
checked history representation should make source bindings, bounds, original-bank
origins and invalidation explicit before reusing a node.

For coverage, preserve both newly forced units and both schedules at `(67,63)`.
The unchanged exhausted cases still require stronger interactions or another
decomposition. A complete ordering is not an efficient solution of every CNF;
history construction, ownership copies, canonicalization, indexing and old proof
checking lie before or outside the bounded probe-occurrence budget. Uniform SAT
efficiency, native context growth and lifetime-space bounds remain open.

All **2,118 full tests** and **43 focused tests** pass. Nine new tests cover exact
unchanged reuse, frozen bank/origin equality, policy-bound replay, complete order
partitioning, actual probing on changed banks, corruption rejection, cold and
interrupted continuation, private ownership and overlay validation. Exhaustive
signed unit/binary formulas on two variables plus seventy generated five-variable
formulas are unit-simplified before applicable open histories are built; both
orders' returned implications/refutations agree with exhaustive model checking.
All **1,167 prior sources**, **30,430 artifact entries in 209 manifests**, earlier
reference/cumulative/native bindings and **64 original manuscript proof blocks**
are unchanged. The final source ledger has 1,171 entries. Existing SQLite
ResourceWarnings remain in the full suite; no new native records are added.

For new timings, copy `pilot.json`, `pilot-source.py` and
`b11-comparison-pilot.json` to a new directory before running
`compare_cnf_b12_progress_order.py prepare`, then `run_census` and
`validate_cnf_b12_progress_order.py validate`. Save tests/build logs and a decision
record before `seal`. Preserve this checkpoint's frozen reports.
