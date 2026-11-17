# Bounded partition screening and reuse of unit traces

The optional selector now chooses plans without solving every candidate and
reuses the unit traces it computes when publishing checked native proofs. The
historical controls improve, but the fresh comparison exposes a cost regression:
an all-terminal partition can be worse than an already terminal unsplit target.
Keep this policy optional until that gate is repaired.

## Recognition and exact reuse

After ordinary reuse and one additional premise-first guard both miss, prepared
clause postings identify overlapping acquired cores missing two or three clauses.
Candidates are ordered by missing-clause count and bank position. At most eight
core proofs are read and four forward/reverse plans screened. Every used core
must have a checked negative native proof. A pending core is skipped.

Each plan is the existing exact first-false partition. The frozen unit propagator
checks the unsplit target and all candidate children without SAT search or proof
publication. Admit a plan when all children conflict, or at least two conflict
and exactly one remaining residual has fewer literals than the propagated unsplit
target. Rank admitted plans by remaining children, remaining literal payload,
branch count, core index and order. These are heuristics, not lower bounds on
solving cost or a minimum-cost certificate. The four-plan budget bounds neither
posting discovery nor all preprocessing.

For a selected branch, bind the saved trace to its canonical root and check each
forced literal. Reuse a terminal conflict directly, or solve only the residual
below a nonterminal forced prefix and lift its model/proof. The frozen native
verifier checks every published node. A branch with no forced literals falls
back to the ordinary solver; an already checked native child is reused. Existing
proof formats are unchanged. Partition conclusions still need their bound
sidecars and a checked `PartitionBank`; the native source root need not exist.

## Matched evidence

Six historical arms restore exact pre-query prefixes, repeat ordinary
preparation, and compare the original single-clause policy with screening:

| Historical case | Selected plan | Baseline / screened expansions | Trace publications | Baseline / screened new rows | Baseline / screened added native bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| 6 | Core 240, reverse | 7 / 0 | 3 | 7 / 4 | 11,296 / 6,122 |
| 68 | Core 258, reverse | 27 / 8 | 3 | 27 / 12 | 32,827 / 16,605 |
| 135 | Core 209, reverse | 7 / 3 | 3 | 7 / 7 | 10,761 / 10,036 |

Each selected plan also publishes one strengthened-premise row. Bypassing a
unit-parent expansion does not eliminate its proof: nine saved-trace
publications replace nine expansion calls across these controls. Row counts
**41 -> 23** and native payload **54,884 -> 32,763 bytes** are more informative
than the expansion counter alone. Neither is peak live memory or full retained
history. Candidate screening and verification remain additional work.

Case 135 rejects the previously tested two-clause orders, then considers a
three-clause core within its four-plan budget. Its rows do not improve. This
illustrates why nearest-core distance alone is an incomplete plan search.
The first control harness stopped because it incorrectly assumed every selected
plan's native keys already existed in the union. Its five completed arms, source
and failure log are retained. The complete rerun preserves seven newly exposed
keys, checks all six arms and merges those keys append-only. This was a harness
assumption failure, not an invalid SAT conclusion.

The fresh comparison uses **192 excluded neighbouring inputs**, a fixed acquired
bank, and two reversed-order pairs in separate processes. Both policies agree on
all answers (94 SAT), repeat without publication, and pass cold replay. Six of
seven unresolved queries accept an extra single-clause guard. Only case 176
reaches partition screening. The baseline unit propagator already finds a
conflict there, but the selector still examines four plans and accepts two
terminal branches.

Consequently, total expansions fall **27 -> 26**, while new native rows increase
**247 -> 249** and added native payload increases **495,506 -> 499,414 bytes**
(**0.79% worse**). Case 176 itself changes from one proof row to three: two
children plus a strengthened premise. Child propagation visits fall 8,190 ->
7,080, but screening adds 5,289; combined propagation visits rise to **12,369**,
with 68 further explicit trace-check literal visits. This is a concrete
counterexample to using terminal child count or fewer expansions as a savings
certificate.

Mean query time rises 1.243 -> 1.306 seconds. Complete worker means are
14.225 / 14.178 seconds, a small 0.34% difference dominated by other phases;
cold replay and compression average 6.83 / 3.90 seconds in the screened arm.
Both paired query differences are positive. The two complete-time differences
are negative but smaller than between-repeat variation. Process peak RSS is
recorded, with substantial variation. No stable total-runtime or live-memory
improvement is established. Diagnostic sidecars also increase retained size.

## Resource limits and next target

Let K be the acquired core count, S its stored clause/literal payload, P the
posting incidences touched by a target, and L bound the target and each branch
encoding. Prepared storage is O(S) in addition to the existing native archive.
Discovery visits P incidences and can sort O(K) candidates, costing
O(L + S + P + K log K) elementary operations, including candidate clause
set differences; literal/key comparisons and normalization also need accounting.
The fixed read/plan budget does not make arbitrary proof reads constant-cost:
cold dependency verification can traverse retained proofs.

For at most b screened plans with at most k=3 branches and v variables, the
frozen repeated-scan propagator costs O((v+1)L) per probe, hence
O((1+bk)(v+1)L) for baseline plus branch propagation, excluding canonicalization,
recognition and proof checking. Retained per-call trace/key diagnostics can use
O(bk(L+v)) space. Only selected prefixes are published, but every screened probe
is paid. Remaining residual search keeps the original solver's worst-case
assignment dependence. No unrestricted-SAT polynomial or new Lean claim follows.

1. **Before discovering partition plans, reuse a terminal unsplit trace.** Case
   176 needs no partition. Charge its initial propagation and publish the checked
   native proof once. This is a direct guard against the observed regression.
2. **Inspect residuals after the extra guard, with a bounded stopping rule.**
   Fresh cases 43 and 172 account for **19/26 expansions** (10 and 9, three splits
   each); case 70 adds four. All accept a known strengthened premise, so the
   current policy never screens their remaining interaction. Restore their exact
   prefixes and compare checked decompositions before extending the stream policy.
3. Keep all recognition, verification and cold replay costs visible. Wider
   screening can cost more than the work saved. Neighbouring-input improvements
   still do not establish coverage of unrelated or arbitrary CNFs.

Resume [expanded checkpoint](../experiments/results/cnf-partition-screen/expanded-checkpoint.json).
The fresh checkpoint and historical additions are separately retained. Reuse all
ordinary catalogs, both earlier chain catalogs, earlier partitions, the 192 new
mixed decisions and six historical control records. Do not pass mixed schemas
to the ordinary catalog checker. The result directory contains independent
selection reconstruction, every trial archive, deltas, regressions and cold audits.
