# Keep reusable leaves when a whole proof has an open frontier

The previous checkpoint leaves one concrete chronological opportunity: fresh
case 69 has a checked refutation before its edit 70 exhausts the common native
budget. The existing complete-cover extractor cannot use that proof. Its
64-node extraction stops at the budget; a larger diagnostic visits 136 proof
nodes but still has nine unsupported endpoints. All 44 extracted unit-support
leaves survive the edit. Rejecting the incomplete cover discards useful work.

## Discovery and exact recomposition

`cnf_partial_proof_plan.py` retains a complete binary branching plan while
marking unsupported endpoints and extraction-budget frontiers as open leaves.
An open leaf makes no SAT/UNSAT claim. Supported leaves retain the existing
source-bound conditional unit certificates. The plan checker verifies every
certificate, all branch assumptions, leaf coverage and the tree bound.

The existing partial composer then operates on the actual target. A supported
leaf is reusable only when its reason clauses remain in that target and its
assumptions follow from the current branch. Open leaves and broken supports
use ordinary native acquisition. One dispatch budget is shared across those
calls. UNSAT requires every reachable branch to close; a positive branch must
lift a model satisfying the entire target. Every published model, unit proof
and split passes the unchanged native verifier. Completed dependency prefixes
survive a later budget stop, while the incomplete root has no verdict.

`WholeProofReuseSolver` discovers an origin from the existing bounded negative
pool after an exact-root miss. It scans canonical clause sets, selects at most
one earlier checked refutation missing exactly one clause from the new source,
and requires some shared clauses. No family label, supplied guard or future
answer selects the proof. Matching uses canonical integer coordinates; it is
not general variable correspondence or semantic-equivalence recognition.
Rank changes can prevent a useful match. Exact clause containment and native
verification prevent an invalid transfer.

The policy extracts at most 64 proof-node occurrences and a cumulative 65,536
literals from those nodes, then attempts recomposition only if a checked leaf survives. Otherwise
it falls back to the preceding whole-input affine/lookahead solver. Plans are
transient hints: native results remain persistent and cold replay needs no plan
or new certificate authority. The optional adapter scopes the existing serial
composer's survival checker to the explicit open-leaf hint format. Exclusive
synchronous use is required; it is not a concurrent in-process interface.

## Resource accounting and limitations

For an extraction bound `B`, the binary plan has at most `2B+1` tree nodes and
`B+1` leaves. A retained template is a subset of the original source, so template
storage is at most `O(B L)` encoded payload, where `L` is the encoded root CNF
length, including clause boundaries and variable identifiers. The source index, copied provenance maps,
branch contexts and recomposition buffers remain additional transient costs.
There is no claim that an open residual is small or easy.

The extraction budgets do not cap total time or memory. A cold native read may
verify the prior proof graph before traversal, and construction of a child
precedes its budget check. Recognition scans the existing bounded pool;
normalization, source matching, copied provenance, template checking, target
restriction, native acquisition, publication and serialization are all charged.
Native dispatch counts exclude direct support and split publications. Selected
retained solver memory excludes transient plans and retained query-log objects;
process RSS and sidecar sizes are reported separately.

The classification is exact as a conditional plan: all branches have a checked
support or an explicit unresolved acquisition obligation. This does not supply
an efficient solution for every resulting leaf, a compact closure for all CNFs,
or a uniform polynomial algorithm for unrestricted SAT.

## Frozen comparison

The previous 72-query holdout at generator sizes 96/120 becomes exposed. Another
72-query stream at sizes 102/126 and seed 202611232256 is frozen before any
comparison. Each has 48 distinct roots and the same six families and
base/edit/repeat schedule. All workers start empty; no archived answers seed
search. Four alternating serial repetitions compare the original binary route,
whole-input affine completion with ordered probing, and that policy with partial
proof reuse, each with an explicit 256-dispatch native budget.

The targeted diagnostic reproduces only the exact prefix through case 69. With
the default extraction bound, 22 of 27 leaves survive, and recomposition refutes
case 70 in 223 native dispatches. Its five other leaves have no template
authority. The fully automatic comparison chooses the same earlier proof from
the pool. Larger extraction and unsupported endpoint handling remain separate
questions; the initial larger diagnostic's nine unsupported endpoints comprise
six subsumption nodes and three implication nodes.

The first exploratory online script accidentally inherited the solver's default
100,000-dispatch budget. Its independently checked proofs are preserved, but
none of its timings or completed-root counts enter the matched comparison. The
frozen protocol and every comparative worker explicitly use 256. This failed
experimental setup is recorded in `exploration/prototype-limit-note.json`.

## Measured coverage and cost

| Mean or retained measure | Exposed completion | Exposed partial reuse | Fresh completion | Fresh partial reuse |
|---|---:|---:|---:|---:|
| Solve seconds | 14.2601 | 14.4798 | 12.3606 | 12.8598 |
| Complete-worker seconds | 27.1048 | 27.9854 | 23.9247 | 25.5030 |
| Native dispatches | 4,521 | 4,501 | 3,311 | 3,400 |
| Native records | 6,405 | 6,401 | 5,101 | 4,954 |
| Native key + payload bytes | 56,272,305 | 57,064,578 | 48,558,525 | 51,885,888 |
| Selected retained Python bytes | 238,234,983 | 241,566,362 | 206,528,898 | 220,309,248 |
| SQLite bytes | 90,734,592 | 91,828,224 | 75,780,096 | 80,752,640 |
| Compressed SQLite bytes | 6,400,539 | 6,446,138 | 5,689,433 | 5,932,827 |

Exposed distinct-root coverage grows from **38/48 to 39/48**. Case 70 changes
from an 874.18 ms unresolved attempt to an 802.23 ms checked refutation on
average. These are different outcomes, not two completed-solve timings.
The full exposed solve mean nevertheless regresses **1.54%**, and complete-worker
mean **3.25%**, with all four pairs slower. Extra matching and extraction on
other inputs are charged. Stored native payload grows **1.41%** and selected
retained Python state **1.40%**, despite four fewer native records.

Fresh coverage remains **42/48** for both completion and partial reuse; the
original binary route covers 40/48. The earlier solver already provides that
two-root gain. Partial reuse adds no fresh coverage, regresses solve mean
**4.04%** and complete-worker mean **6.60%**, with all four pairs slower. Native
payload grows **6.85%** and selected retained Python state **6.67%**, despite
147 fewer records. Fewer stored nodes need not mean less stored data.

Fresh positive edit 61 improves from 20 to nine dispatches and 165.80 to 125.11 ms.
Fresh negative edit 70 drops from 115 to 89 dispatches, but its mean attempt
increases from 501.89 to 507.60 ms. The strongest regressions are shared-mixture
edits 31/34: one dispatch each becomes 57/58, and combined solve time rises by
329.33 ms. This accounts for about two thirds of the stream's 499.15 ms increase.
The mechanism reuses valid partial evidence while displacing a cheaper complete
solution path. It therefore remains optional.

Cold checking rises from 5.4627 to 5.5730 exposed seconds and 4.7078 to 5.1261
fresh seconds; reconstruction rises from 0.8013 to 1.2090 and 0.9786 to 1.1978
seconds. Mean peak RSS rises from 807,620,608 to 814,182,400 exposed bytes and
742,924,288 to 773,971,968 fresh bytes. All are measured costs, not general
space bounds. Query sidecars also retain successful plans and grow; selected
solver-graph sizes do not include those log objects. Complete-worker time
includes serialization, warm reuse, cold checking, reconstruction and compression.
Study preparation and cumulative validation are separate.

**Next target: prioritize an already available complete reusable result before
extracting a partial plan.** Use the existing `cnf_pool_priority.try_pools`, and
check the exact new-policy prefix for edits 31/34 before claiming those cheap
results remain available. Keep the useful exposed case-70 transfer and charge
pool misses on fresh inputs. Random-three still consumes **73.74%** of fresh
solve time, but these two edit regressions give a specific avoidable cost.

Independent reconstruction of the new policy's exact prefix confirms a complete
negative-pool hit on both edits 31/34 with zero fresh expansion. The exposed
case-70 probe misses. The diagnostic calls take 126.80, 146.71 and 127.87 ms,
respectively, including canonicalization and pool work. These posthoc timings
are outside the serial matched comparisons and establish no improved-policy
speedup. In particular, the failed case-70 check would add cost before the useful
partial transfer. The next policy must price that miss as well as its two hits.

## Reproduction

The checkpoint and raw records live in
`experiments/results/cnf-whole-proof-reuse/`. The matching compare, validate and
finalize scripts preserve all previous authority, raw trial alternatives and
stopped prefixes. Focused tests check all 256 subsets of a small cube against
exhaustive truth, invalid plans and assumptions, budget stops, automatic source
matching, sparse-label positive witnesses and independent cold readers.

Validation: 1,648 tests pass, including 57 focused tests without warnings. The
full suite retains 44 existing SQLite resource warnings. The 252-page manuscript
builds without warnings and preserves all 64 earlier proof environments.

The cumulative audit passes for 1,728 matched query records, 142 exploratory
query records and 40 successful partial plans. Two independent readers check
all six persistent tables in 31 archives, and all 342 earlier partition records
remain valid. The 154 earlier manifests and 13,713 artifacts are unchanged.

The merged archive adds 25,356 native records and eight affine records, including
valid results from the larger-budget exploratory run. These totals are
preservation counts, not matched-workload coverage gains. It now holds 121,030
native records, 107 affine records, 117 equivalence records across three formats
and 34 binary-discovery records. All previous authoritative payloads remain
unchanged; 670 alternative-payload observations remain in the raw trial archives.
The cumulative SQLite database is 1,425,793,024 bytes and its compressed archive
101,864,913 bytes. Full validation takes 786.97 seconds, including 74.09 seconds
to archive the union; this preparation cost is separate from online query times.
