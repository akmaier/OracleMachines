# Compose checked restrictions before solving the remaining target

On eight historical unresolved cases, one additional checked restriction reduces
fresh expansions and new proof rows from **68 to 29 (57.35%)**. Added native proof
payload falls **57.72%**, while serialized proof deltas plus composition records
fall **13.47%**. Recognition and checking outweigh the child-solve time saved in
these single samples. This establishes less search and retained trial evidence,
with no demonstrated total runtime or peak-memory improvement.

## Exact composition and reuse

Let T be the residual under the original guard. A checked negative core K with
exactly one missing clause C satisfies K ⊆ T ∪ {C}. Hence T ∧ C is UNSAT and every
model of T falsifies C. Fixing every literal of C to false therefore preserves
satisfiability. The implementation checks the negative strengthened premise,
solves the restricted residual, and composes both guards. For SAT, it lifts the
child model through both assignments and checks the original query. For UNSAT,
each guard preserves the absence of a model. Merely deleting C from a negative
proof cannot justify an UNSAT answer; case 155 remains SAT.

The selector takes the first ready overlapping core in legacy/causal order with
one nonempty missing clause using existing target variables and a changed
residual. This is a heuristic, with no minimum-cost or beneficial-restriction
claim. It skips pending cores and makes no fresh SAT search during selection or
premise publication. The existing checked subset rule supplies T ∧ C if needed.
In all six selected cases that strengthened premise is already stored, so no
premise row is added.

Native proof nodes retain their frozen format. The new `checked-guard-chain-v1`
sidecar binds the source, ordered guards, final native child and lifted answer.
`GuardChainBank` verifies these records on load and reuses their conclusions for
identical normalized CNFs, including the renamings admitted by the existing
normalizer. Native root-table lookup alone need not find the composed source.
The sidecars and their checker are required for this reuse. The bank assumes an
exclusively owned immutable or append-only proof session; changed external
storage requires a new checked session. Its lookup is not unrestricted graph
isomorphism or arbitrary formula equivalence recognition.

## Matched historical comparison

Every arm reconstructs the exact persistent prefix immediately before its query
in the preceding terminal-guard stream. Both arms open cold live checkers and
perform the same ordinary preparation. The baseline reproduces the original
proof payloads exactly. The candidate adds at most one guard, solves its remaining
child and retains a checked chain; cases 41 and 179 fall back unchanged.

| Case | Answer | Baseline expansions / new rows | Chain expansions / new rows | Added native payload, baseline → chain |
| --- | --- | ---: | ---: | ---: |
| 41 | UNSAT | 8 | 8 | 16,639 → 16,639 |
| 56 | UNSAT | 17 | 1 | 32,215 → 1,640 |
| 98 | UNSAT | 4 | 1 | 7,120 → 1,879 |
| 107 | UNSAT | 7 | 1 | 12,793 → 1,716 |
| 139 | UNSAT | 1 | 1 | 1,702 → 1,366 |
| 155 | SAT | 3 | 3 | 4,566 → 3,875 |
| 176 | UNSAT | 24 | 10 | 39,410 → 15,680 |
| 179 | UNSAT | 4 | 4 | 9,698 → 9,698 |
| Total | 7 UNSAT / 1 SAT | 68 | 29 | 124,143 → 52,493 |

No case increases expansion or publication count. Cases 56 and 176 together
fall from 41 to 11 expansions. Native payload is identifier plus ASCII JSON
length, not SQLite pages or peak RAM. With the larger composition sidecars,
serialized delta-plus-chain files fall from **251,022 to 217,209 bytes**.
Historical acquisition, retained indices and old proof storage remain additional
costs. The growing union preserves old proofs rather than deleting them to
realize the per-arm saving.

Summed child-solve samples fall from **0.077837 to 0.047904 seconds**. The candidate
also spends 0.065058 seconds selecting near cores and 0.033014 checking premises.
Including composition, this query-phase sum rises from **0.088170 to 0.160206
seconds**. This sum excludes separately reported preparation, serialization,
warm-bank construction, cold replay and prefix reconstruction. Full-row export
and reporting overhead remain in aggregate study time. One sample per arm and
fixed baseline-first order do not establish stable timing estimates. No peak RSS
or downstream stream-sharing effect is measured. Tests and profiling run after
the timed producer.

## Remaining cost and next test

A separate read-only probe restores the same prefixes and prices the six already
selected candidates. Checking only the stored strengthened premise, instead of
first checking the support proof, reduces verified nodes **148 → 57**, checked
literal payload **13,299 → 8,073**, and read bytes **122,683 → 68,141**. The checked
negative strengthened premise alone justifies the restriction. Unverified core
metadata may suggest a clause, but cannot justify an answer. The probe changes
neither discovery nor the deployed selector; it establishes no end-to-end
runtime gain. Missing premises still need the checked-core/subset fallback.

**Next priority:** look up and check the strengthened premise first, reuse prepared
core clause sets or postings for near-containment, then compare on new excluded
inputs. Price setup and cold replay as well as matching. The current scan rebuilds
core clause sets and visits up to all 383 retained entries; six selected cases
still incur separate core and premise checks. Case 176 retains ten expansions,
case 41 eight, and case 179 four. More guards can cost more than the solve avoided;
selection budgets and fresh generalization remain open.

For a chain of d guards, storage includes every retained strengthened premise,
the native child proof and a sidecar containing the source and d guarded CNFs.
With intermediate encodings bounded by L bytes, the sidecar is O(dL) plus model
storage. Checking charges the distinct traversed native proof nodes under the
session cache, formula normalization, each restriction and SAT model lifting.
Child solving remains unrestricted. The warm bank additionally retains normalized
query identities and models; it does not make acquisition, cold checking or
recognition free. No uniform polynomial bound follows for arbitrary SAT.

## Validation and persistent state

All 16 arms pass independent prefix reconstruction, native proof and both-index
lineage checks, guard composition and cold sidecar replay with fresh search
disabled. All **2,957 inherited decisions** and eight composed conclusions replay.
Tests cover two-level SAT lifting, normalized renaming, negative-chain retention,
missing native source roots, tampering, missing children, pending and positive
cores, and exhaustive two-variable truth tables. The full suite passes **1,022
tests**. Older unclosed-SQLite ResourceWarnings remain in its log; the nine focused
chain/condition tests emit none.

Resume `experiments/results/cnf-guard-chain/checkpoint.json`: **20,666 native keys**,
17 added and all 20,649 previous payloads preserved, plus eight bound chain
conclusions. No alternate native certificates occur. The union occupies
64,909,312 SQLite / 4,784,034 gzip bytes; compression changes do not measure live
memory. All prior semantic fields remain; only the parent/union/source bindings
change and two chain fields are added. Structural authority remains 2,614 patterns
/ 259 pairs / 17 missing children, original 17/24 with 999 steps and separate
supplemental 24/24 with 208 steps. There is no fresh source-query coverage, new
Lean result or unrestricted-SAT theorem.

The runtime protocol binds 420 sources; the analyzer and checking-cost probe
bring the final ledger to 422. The preservation audit checks all 416 prior
sources and 4,579 artifacts in 80 manifests. Per-arm deltas, sidecars, phase
reports, unsuccessful cases and reconstruction metadata are retained in
`experiments/results/cnf-guard-chain/`.

New manifest: **70 artifacts**. Next preservation audit: **4649 artifacts / 81 manifests**.
