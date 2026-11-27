# Completing only the visible affine boundary

Date: 27 November 2026. Parent: `22cb7992`. Evidence: `experiments/results/cnf-affine-boundary/`.

## Why this is the next gap

The preceding five feedback-unresolved inputs are **already solved by the current solver’s affine path**: four have contradictory extracted equations and the bridge has seven free coordinates. They are not unresolved SAT instances or new coverage wins in this checkpoint. The useful remaining restriction is the existing completion gate’s limit of eight total free coordinates. Earlier exact projection can also re-encode boundary equations as CNF, but this experiment keeps the affine basis and does not enumerate a new parity encoding.

## Exact reuse and certificate

Extract the existing complete parity-half groups from normalized CNF and leave all other clauses intact. Check the extraction and Gaussian rows, then construct and check a complete affine space `x = a + Vt`. Let `B` be the variables mentioned in leftover clauses. Select original basis directions whose restrictions to `B` form a basis of the projected image. The verifier checks independence with descending pivots and checks that every original direction projects into their span; discovery uses ascending pivots. Merely dropping zero projections is insufficient: a retained test has six nonzero projections of rank five.

If the image has rank `b`, the selected full vectors lift all `2^b` distinct boundary assignments. Every full affine solution has one of these boundaries, and leftover clauses depend only on that boundary. Therefore one representative per boundary suffices. A satisfying representative is checked against every original source clause. For UNSAT, each boundary representative carries a falsified leftover clause. The checker reconstructs binary coefficient vectors and uses inverse Gray indexing, independently of the producer’s incremental Gray traversal. No assignment table or new boundary CNF is materialized.

The versioned certificate `cnf-affine-boundary-v1` is a separate JSON authority. Existing native, equivalence and affine-negative tables and readers are unchanged; no native proof silently depends on this new format. Every cold and warm load rechecks the full source, affine basis, image completeness and verdict. The two native cold readers audit fallback records, and each cold pass also runs the same boundary checker. They are not two independently implemented boundary checkers.

Reuse requires an exactly equal normalized source. A stream stores one accepted proof per exact source; changed clauses or variable relationships invalidate it. Open results carry no verdict and use the same existing fallback. No persistent reuse of a changed matrix or support is implemented. The discovery policy retains the existing source-size and XOR limits and caps image rank at eight. A full basis is still constructed before the rank test; normalization, basis space, verification and misses remain charged. The `2^b` term can still be exponential for unrestricted inputs.

## Frozen controls and measured result

Before implementing the kernel, freeze 24 synthetic constructions and four exact repeated queries. The unique panel contains 15 SAT and 9 UNSAT inputs: connected affine extensions of mixed-CNF cores, growing parity prisms, crossing edits, a parity-clause deletion and random three-CNFs. No normalized input duplicates the preceding panel, but these are designed structural controls, not a representative external benchmark. All descriptions and independent DPLL truth labels are withheld from workflows. Exhaustive small-case tests and signed sparse renamings provide separate correctness controls.

On the 24 unique constructions, direct full-space completion covers **14/24**, and boundary completion covers **18/24**. Four new direct cases exceed the old cap: three connected mixtures (including one crossing edit) and a pure consistent parity input. Their free dimension is eleven; boundary ranks are five, six or zero. One additional stream repeat reuses the new negative certificate. The current fallback already decides all 33 queries including the five development cases. Thus coverage here means the certified acquisition family, not extra SAT decisions beyond the whole solver.

For the unsatisfiable connected core with three attached pairs, measured enumeration falls **256 → 32**. With six pairs, the old gate refuses dimension eleven and falls back; the new method checks 32 representatives. Comparing 32 with `2^11 = 2048` describes the avoided full-space enumeration, not an observed 2048-candidate baseline run. The pure consistent 30-variable parity case has eleven free coordinates but rank-zero boundary and needs one representative.

Six process-order permutations compare the current solver (`fresh`, which already contains affine recognition), the explicit existing full-space acquisition plus fallback, and boundary acquisition plus the same fallback. Every run starts empty; all accepted proof reuse is exact and all cold/warm proof verification is charged. Timings include recognition, preparation, JSON persistence, fallback, archive compression and cold replay. Interpreter startup, report metadata, panel generation and final preservation audit are additional.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | SQLite record bytes | JSON certificate bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0.00000 | 0.04989 | 0.00870 | 0.03694 | 0.11470 | 102,523 | 0 | 53,755,904 |
| full | 0.01194 | 0.03783 | 0.00937 | 0.03538 | 0.11800 | 71,965 | 26,327 | 53,084,160 |
| boundary | 0.01303 | 0.02149 | 0.00926 | 0.03110 | 0.09216 | 38,144 | 33,626 | 52,297,728 |

Boundary completion saves **19.66% complete time against fresh** and **21.90% against explicit full-space completion**. Savings against fresh range from 16.38% to 23.93% across the six paired orders. This is a modest workload-specific gain, not the 64-fold theoretical enumeration ratio applied to total runtime. Discovery itself increases from 0.01194 to 0.01303 seconds versus full-space acquisition, because projection and checking cost work.

Combined SQLite-record plus JSON-proof bytes fall **102,523 → 71,770** versus fresh (30.00%). Their combined compressed size falls **24,436 → 16,798** bytes (31.26%). The boundary workflow additionally retains 9,317 diagnostic bytes; full-space retains 6,386. These figures exclude the repeated experiment reports, preserved failed runs, historical archives and SQLite/container overhead. Peak RSS decreases only about 2.7%; it is whole-process high-water memory and no asymptotic memory improvement is inferred. Certificates retain the full affine basis even when few directions are visible.

## Preserved failures and limits

The first test incorrectly assumed a kernel direction would have zero boundary projection. Its failure exposed the nonzero-but-dependent case now tested explicitly. The initial timing driver used the full canonical CNF key as a filename and hit the filesystem name-length limit; that run and driver are retained, and the corrected driver uses a digest for filenames while retaining full source bindings. A first audit compared integer-keyed in-memory models with string-keyed JSON serialization by textual key order; its log and script are preserved, and the final audit compares normalized JSON values. None of these failed controls is included in the matched timing averages.

## Next target

The six distinct remaining acquisition misses are random three-CNFs with no extracted complete parity halves; their two repeats do not add structural gaps. All are decided by the existing fallback. Investigate useful non-affine boundary relations or hidden affine structure only with exact extraction/recomposition and full discovery costs. The current experiment extends the affine dimension gate; it does not explain those non-affine cores. Increasing the enumeration cap alone is a separate, exponential approach.

For performance, rank-zero/pure affine handling and reusable checked basis preparation are now concrete supporting targets. A production integration would also need explicit authority dispatch and tests; this checkpoint keeps the separate experimental certificate route and leaves defaults unchanged. The full affine basis, image recognition and cold proof checks remain material costs.

Resume `experiments/results/cnf-affine-boundary/checkpoint.json`, key `affine_boundary.remaining`. All prior 223 manifests, 35,068 artifact entries and 1,228 source fingerprints are preserved; five new source/test files raise the ledger to 1,233. All 65 earlier proof blocks remain unchanged and one restricted boundary-completeness proof is added. General compact coverage and polynomial acquisition/expansion for arbitrary SAT remain open.

Validation: **2,234 full tests and 37 focused tests pass**. The independent audit replays all 18 comparison arms and the three unique SQLite archives, checks every accepted JSON certificate and every input against an independent DPLL oracle, and verifies all parent artifact/source hashes. Existing unclosed-SQLite ResourceWarnings remain in the full-suite log; focused tests have none.
