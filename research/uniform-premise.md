# Uniform completion of conditioned residuals

## Implemented pattern

`cnf_uniform_premise.select` extends saved-premise recovery to nonterminal
residuals. It preserves earlier accepted choices and the existing probe budget.
Before fallback, it binds each retained nonconflicting premise to the exact
target-plus-assumption, checks its unit reasons, reconstructs the residual and
tests both uniform completions. A complete source model is transported and
checked before direct native SAT publication. No new propagation or search is
performed by completion. Earlier discovery still runs to its previous stopping
point, and its costs remain charged.

All-false satisfies a residual exactly when every clause contains a negative
literal; all-true satisfies it exactly when every clause contains a positive
literal. These predicates give four disjoint outcomes: false only, true only,
both, and neither. Three outcomes supply explicit witnesses. The fourth remains
unresolved, containing both satisfiable and unsatisfiable formulas.

This directly covers Horn and dual-Horn residuals after consistent full unit
closure. A nonempty Horn clause with no negative literal would be a positive
unit, which closure has already eliminated; the dual argument is symmetric.
The sign predicates also cover formulas outside these syntactic families.
For example, `(a OR b OR NOT c OR NOT d)` accepts both uniform assignments
while being neither Horn, dual-Horn nor two-CNF. This broader case is tested;
the measured fresh successes below are all within Horn or overlapping families.

The unresolved cell still encodes general SAT. For any unit-free CNF F, add
fresh variables a,b and conjoin `(a OR b) AND (NOT a OR NOT b)`. The result is
satisfiable exactly when F is, remains unit-free, and rejects both uniform
assignments. For arbitrary F, first apply unit closure: a conflict can map to
a fixed unit-free UNSAT formula rejecting both assignments; otherwise apply
the same fresh-variable construction to the residual. This is a polynomial
conversion preserving satisfiability. Classifying the four cells therefore
does not supply an efficient solver for the unresolved cell. An independent
finite audit checks all 256 subsets of the eight full-width three-variable
clauses, including the unsatisfiable subset, with the fresh-variable pair.

## Matched evidence

Seventeen exact-prefix contexts retain earlier positive controls and difficult
misses. The new nonterminal control, binary-probe stream case 14, changes from
three acquired nodes / 2,439 native bytes to one model node / 1,363 bytes. Its
delta/record sidecars shrink 7,992 -> 6,848 bytes. Evaluation times are
3.568 -> 3.023 ms and 3.462 -> 2.851 ms in opposite policy orders; complete
arms have opposite timing signs. All sixteen other contexts retain their
earlier payloads and records. There are 36 control arms including the repeat.

The fresh study uses sixty excluded queries: twelve per finite family plus
twelve same-template neighbours. All 48 family targets remain unfamiliar after
preparation; the twelve neighbours become known. All modes answer 43 SAT and
17 UNSAT queries. Nine further gated-Horn targets accept uniform completion;
three already accepted positive-terminal recovery. All twelve gated targets
therefore publish one model each, with no fresh acquisition expansion.

| Fresh-stream quantity | Native baseline | Previous recovery | Uniform completion |
|---|---:|---:|---:|
| New native nodes | 457 | 452 | 434 |
| New native payload bytes | 539,808 | 535,908 | 521,248 |
| Expanded nodes | 445 | 437 | 410 |
| Direct model publications | 0 | 3 | 12 |
| Discovery/acquisition propagation visits | 71,086 | 174,679 | 169,529 |
| Mean query seconds | 0.39352 | 0.44913 | 0.44780 |
| Mean complete worker seconds | 22.86422 | 23.10989 | 22.81393 |
| Mean full cold replay seconds | 11.22115 | 11.27781 | 11.18068 |

The additional eighteen-node / 14,660-byte saving is about 3.98% / 2.74% of
new acquisition. Query differences are -0.00855 and +0.00587 seconds, so there
is no consistent query-time gain. Both complete-worker differences are
negative, -0.22305/-0.36887 seconds, but the two trials do not establish general
scaling or isolate these differences from setup, replay and compression noise.
Native baseline still uses less query time and propagation.

Diagnostic sidecars grow about 2.83%, from 1.942 to 1.997 MB. Trial database /
compressed sizes fall 77,463,552/5,675,680 -> 77,434,880/5,670,546 bytes. Mean
process RSS falls about 2.02 MB (740.098 -> 738.075 MB), a small two-run
observation with no memory-scaling claim. The preservation union includes
earlier and comparator payloads; it is not the smallest policy's live state.

## Complete cost and validation

The extension examines 105 saved attempts, accepts nine and retains 96 misses.
It copies 12,529 premise literals, checks reason clauses containing 703 literals,
reconstructs 3,381 residual clauses, visits 7,226 residual literals in the
single-pass sign test, and verifies 2,449 original premise literals for accepted
models. All 96 misses belong to graph-colouring inputs in this stream.
Normalization, full-key creation, transport and native publication are also
included in measured selection/publication time and counters.

For k checked attempts, L input literal occurrences and n variables, the
additional trace checking, restriction and sign recognition take
O(k(L+n)) expected dictionary operations, plus the canonicalizations and full
keys for each attempt. A valid reason clause cannot recur after becoming
satisfied, so its trace-checking payload is bounded by premise length. One
accepted model adds O(L+n) verification/transport work. Temporary working state
is O(L+n), with O(k) additional diagnostic descriptors, excluding the already
retained screens. Input integer bit lengths, publication, archive census,
serialization and inherited replay remain separate charges. This is not a bound
on earlier discovery or unrestricted SAT acquisition.

Nine new tests include 1,024 attempted small clause-set/assumption/coordinate
combinations, malformed evidence, misleading residual counters, baseline-prefix
transport, native search disabled, cold replay, broader uniform families and
satisfiable misses. Conflicting combinations are rejected before completion.
Posthoc attribution independently audits 138 counter records and checks the
256-formula embedding experiment. Full independent reconstruction and the
existing native certificate checks retain the proof boundary; no new Lean
theorem or proof schema is claimed.

## Next targets

The retained misses expose **twenty two-CNF conditions on five graph queries**.
Posthoc SCC solving supplies four positive models for fresh case 39, and source
transport verifies each against the original target-plus-assumption. Case 39
currently acquires three nodes / 1,444 native bytes. Implement and price checked
mixed two-CNF model transport at this exact prefix without repeating unit
propagation.

Sixteen other conditions, on fresh graph cases 43/51/55/59, have checked
contradictory implication paths. These conditions alone do not refute their
parents. Their parents currently acquire 52 nodes in total. Investigate native
conditional refutation publication, the existing guard interface, complementary
branches and checked symmetry transport. Charge every remaining branch and
certificate; do not equate one negative condition with a negative parent.
SCC diagnosis is posthoc, not a timed solver feature in this checkpoint.

Gated-Horn discovery remains a large avoidable cost: **74,194 propagation visits
despite zero acquisition propagation after completion**. Early positive stopping
and reusing bound canonical forms are the next computation targets, preserving
the current full-discovery policy as comparator. Random three-CNF and coupled
parity still require 320 acquisition nodes / 54,301 propagation visits. The
binary filter supplies no saved uniform-completion attempts there. Positive
discovery outside that filter, wider conditioning and arbitrary-CNF compact
closure remain open. Full cold replay continues to dominate complete workers.

Evidence and reproduction:
[`experiments/results/cnf-uniform-premise/`](../experiments/results/cnf-uniform-premise/).


All **1,129 tests**, 23 focused tests, 138 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-uniform-premise/checkpoint.json`:
**24,444 native keys**, preserving all 23,987 prior payloads, with 216 new
composed records alongside 3,581 inherited records, 2,957 ordinary decisions
and six projections. The union uses 77,484,032 database bytes / 5,677,574
compressed bytes. Five alternate model payloads remain preserved (fourteen
occurrences). Ready/pending banks are 132/38, 141/66, **87/89** and **87/116**.
The two gains refer to one 568-byte negative certificate acquired by shared
ordinary preparation for neighbour case 1 in every mode: causal core 46 and
incremental-causal core 51. This activation is not a uniform-policy gain.
All 514 earlier sources, 5,918 artifacts and 96 manifests remain unchanged.
The paper builds at 212 pages with all 64 existing proof blocks unchanged;
structural authority and original coverage remain unchanged. No new Lean theorem
or unrestricted-SAT resource bound is claimed.
