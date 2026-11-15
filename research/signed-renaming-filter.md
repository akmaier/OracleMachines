# Excluding signed-renaming reuse before expansion

Case 1120's next residual has 39 variables, 162 clauses and 510 literal
occurrences. Its sixteen saved split pairs produce thirty-two distinct target
keys, all absent from the acquired inventory. Three pairs have matching counts
of variables, clauses and literals. The investigation asks whether these
different keys nevertheless denote the same clause structure after a variable
bijection with independent polarity flips.

## Necessary invariants and their scope

For a normalized clause set F, record its number of active variables, the
multiset of clause widths, and the multiset of pairs

`(min(pos_F(v), neg_F(v)), max(pos_F(v), neg_F(v)))`.

Here `pos_F(v)` and `neg_F(v)` count positive and negative occurrences of v.
A signed variable bijection maps variables bijectively and either preserves
or swaps each variable's positive and negative occurrences. It also maps
distinct clauses bijectively without changing their widths. All three
invariants must therefore agree. A difference certifies that no such renaming
maps one normalized clause set to the other.

The helper first applies the existing normalizer. Duplicate clauses/literals,
tautologies, empty-clause collapse and order-preserving identifier compaction
are charged there. These operations commute with a signed bijection up to
identifier compaction, so they do not invalidate this necessary condition.
The certificate verifier recomputes the profiles from both supplied inputs
and checks the named difference. A digest only binds an archived input; it
does not replace the comparison of actual profiles.

**Equal profiles are inconclusive.** For example, monotone binary clauses
encoding the edges of K3,3 and the triangular prism have the same variable
degrees and clause widths. Their underlying graphs are not isomorphic: one
contains triangles and the other does not. The helper returns no exclusion
for this example and never promotes a profile match to an equivalence.

Likewise, an exclusion is not a SAT or UNSAT answer. Differently structured
formulas may both be satisfiable, and semantic equivalence or a checked
simplification may permit reuse beyond literal renaming. Profiles define an
exact, inexpensive partition by these invariant values; no efficient solver
for every resulting cell follows.

## Candidate audit

The hash-bound, independently reconstructed candidate set yields **32 distinct
profiles**. Every one of its **496 pairs** is excluded from signed-renaming
reuse: 340 first differ in active-variable count, 155 in clause-width counts,
and one requires the paired occurrence invariant. For the variable-5 and
variable-22 true targets, both **37/138/416**,
the paired occurrence counts differ. The other two same-shape pairs already
differ in their clause-width distributions:

- Variable-13 false versus variable-17 false: width counts
  `(2:14, 3:114, 4:24, 5:3)` versus `(2:15, 3:114, 4:21, 5:5)`.
- Variable-13 true versus variable-38 false: width counts
  `(2:19, 3:101, 4:24, 5:3)` versus `(2:17, 3:107, 4:18, 5:5)`.

Preparation takes **0.00306 s**, profiling and comparison **0.01123 s**, and
verification **0.02078 s**. The total before writing the audit is **0.03509 s**;
the producer charges writing and the call overhead separately in
`renaming_audit_seconds`. The discovery counters record **14,796 normalization
literal visits**, **14,796 profile literal visits**, **4,799 clauses** and
**1,188 active-variable records across the 32 inputs**. Verification recomputes
profiles; these discovery counters do not include its additional work.

The profile scan visits each normalized literal once. Normalization, sorting,
dictionary operations, integer arithmetic, allocation and serialization remain
costs. This audit compares all pairs and therefore has a quadratic candidate
pair count; larger catalogs should group exact profile representations first.
Neither the filter nor this experiment implements a complete isomorphism test.

The negative result prevents repeated exploration of these exact-renaming
proposals. It creates no proof edge, closes no original, and changes no
scheduling choice. Expansion continues with the existing first saved pair;
any later convergence after reduction remains a separate reuse opportunity.

## Expansion and remaining interaction

Two independent runs then use the unchanged retained-session worker from the
selected case-1120 residual. Each performs seven advances across two 32-entry
budgets and produces identical per-batch evidence. The first batch stores 31
patterns; its one interrupted input is reentered, charged and stored in the
second batch. The second stores 23 patterns and leaves nine entered inputs
without completed pattern certificates. Total admissions are 64, with 63
distinct entered inputs and **54 newly stored patterns**.

The new patterns include 20 probe, 15 elimination, 10 binary-path, six
unresolved, one polarity, one conjunction and one family node. The family
terminal is **5 variables / 4 clauses / 9 literals**, Horn and zero-valid,
outside dual-Horn, 2-CNF and one-valid. The selected focus remains open;
**coverage stays 66/83**. Reaching one conditional terminal does not complete
all interactions in that focus or its original.

Renaming failure does not prevent reuse after reduction. The true branch of
the **36/147/461** source reaches an inherited **2/1/2** retained plan after
eight new prefix nodes. The false branch of the **30/117/366** source reaches
the inherited empty-CNF plan after two new probe nodes; its true branch reaches
the new Horn terminal. The cold structural findings mark these nodes as
inherited, rather than counting recognition of a familiar family as reuse of
an existing certificate.

The next saved pair has source **25/96/309** and targets **23/89/277** and
**22/73/215**, both pending. Resume the exact saved pair before inventing a new
split. The nine interrupted states require renewed admissions under the
current worker; there is no stored certificate for an unfinished recursive
frame. A continuation mechanism would have to retain and check these frames,
not merely exempt their repeated work from accounting.

The means over the two independent runs, summing both batches, are:

| Phase | Seconds |
| --- | ---: |
| Complete workers | 18.01738 |
| Preparation | 16.81073 |
| Expansion | 0.91088 |
| Selection within expansion | 0.38584 |
| Acquisition within expansion | 0.43381 |
| Route maintenance within expansion | 0.08798 |
| Coverage within expansion | 0.00324 |
| Append delta export | 0.03405 |

Preparation includes initial checking; the second batch retains the checked
session. The complete producer costs **236.02832 s**, charging **105.00548 s**
for historical restoration and **68.70599 s** for final route preparation and
global coverage. These are costs of repeated discovery runs, not comparisons
against a changed worker. The remaining preparation and cold authority costs
are much larger than fresh acquisition on this bounded workload.

History grows by **749,568 bytes** to **777,986,048 bytes / 42,268 patterns**.
The union delta is **831,488 SQLite bytes / 38,073 compressed bytes**; six new
split sidecars and no external probe rows are retained. The reference archive
grows **3,830 -> 4,114 nodes**; every old payload is unchanged. The global
positive certificate is byte-identical and still has 3,360 steps. The live
index has **707 routes / two missing-target links**. These are persistent sizes
and logical counters, not peak RAM measurements or a compact-storage bound.

Resume `experiments/results/cnf-original-1120/report.json` through
`continue_cnf_original_1120.restore_checkpoint`, report SHA-256
`d0ffd584ce79e219103ec891f04b7a038aff42cc9b9b86221bbf0c0b41f4fb8e`.
Preserve evidence **(1, 42, 156, 54, 1)** and **two bridges**. Read the bound
`next_selection` archive; the pending source key hash is
`7187942ac65244a2700f4c0e912ca876ca046144695d4392d2b006913ac98bd7`.
The original focus remains case 1120, retained index 22; pending-split selection
does not itself repeat that original index.

## Validation and reproduction

Independent cold reconstruction passes in **419.43195 s**, reproducing every
intermediate catalog and both complete sequences with fresh discovery and
reference search disabled. All **4,114 reference nodes** verify; all **3,830
previous reference payloads** and **1,361 artifacts across 27 prior manifests**
remain unchanged. All **238 regression tests** pass, including the five new
tests below. The manuscript builds to **163 pages**, with no overfull boxes or
undefined references and all **64 prior proof blocks** unchanged. Validation
commands, fingerprints and concurrency notes are in the new checkpoint's
`validation.json`; its manifest binds the preserved evidence and logs.

The five unit tests enumerate all **512 clause sets over two variables** and
their **eight signed permutations**, including sparse target identifiers.
They also check tampering, normalization edge cases, invalid literals, a
same-shape exclusion, and the equal-profile nonisomorphic example above.
The textual invariant proof does not claim a Lean refinement of Python.

The frozen candidate source is
`experiments/results/cnf-session-frontier/structural-findings.json`, bound by
its previous manifest. The new producer writes `renaming-audit.json`; its cold
validator recomputes every profile and checks all pair exclusions before
reconstructing the expansion. Run from the repository root with a fresh
output directory:

```sh
python3 -m unittest solver.test_cnf_renaming_invariant
python3 experiments/continue_cnf_original_1120.py /tmp/cnf-original-1120
python3 experiments/validate_cnf_original_1120.py /tmp/cnf-original-1120
```
