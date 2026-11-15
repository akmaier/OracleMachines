# Global queries from the maintained expansion catalog

2026-11-15. This comparison continues fresh discovery from
`cnf-original-handoff/report.json`; it does not replay the preceding six-pattern
append. The [report](../experiments/results/cnf-session-catalog/report.json),
[timings](../experiments/results/cnf-session-catalog/timing-summary.json) and
[independent replay](../experiments/results/cnf-session-catalog/reconstruction.json)
preserve the result.

## Result and limits

The same bounded worker closes the selected **40-variable / 158-clause /
467-literal residual of case 1443**, storing **27 patterns** in one advance.
Both repetitions of both methods use identical operations, admissions and
persistent evidence. Overall structural coverage remains **68/83**: completing
this selected conditional residual does not complete every obligation of the
original. No claim about the original's SAT truth follows merely from this
coverage flag.

The two new cofactor chains are informative across categories:

- **38/149/427 -> 35/131/368** uses two new probe nodes and reaches an inherited
  contradiction terminal.
- **37/131/371 -> ... -> 11/14/30** uses 25 new nodes: eight probes, ten
  eliminations, five binary-path reductions, a polarity change and a new family
  terminal. The terminal is both Horn and zero-valid. The chain repeatedly
  interleaves implication-based clause reduction, elimination and probing;
  the polarity change finally exposes the Horn structure.

Exact reuse of the old contradiction is distinct from applying existing
reduction methods to new CNFs. The longer chain is newly certified; it is not
retrieved as an identical old component. Recognition and checking remain
charged. These are particular certified reductions, not a new polynomial
classification of arbitrary SAT or a minimum-cost expansion guarantee.

## Matched costs

Both methods retain the same checked inventory and complete route maintenance,
perform an initial global query, execute the same bounded expansion, then query
all 83 originals again. The baseline rebuilds a second complete route catalog
for that final query; the alternative uses the maintained catalog. Both fully
compose, check the resulting plans and run the original selector. No coverage
index is added. Two repetitions reverse method order.

| Cost in seconds | Rebuild catalog | Use maintained catalog |
| --- | ---: | ---: |
| Initial construction, global query and serialization | 67.34466 | 69.21563 |
| Worker, including preparation, checks and append export | 1.29559 | 1.34665 |
| Updated global query, including both guards | 1.52633 | 0.23719 |
| Query's route construction | 1.10321 | reference reuse |
| Query's full composition and plan checks | 0.33453 | 0.14999 |
| Query's original selection | 0.07996 | 0.07890 |
| Updated query output serialization | 0.33385 | 0.32773 |
| Complete measured sequence | 70.96985 | 71.79572 |

The updated query is **84.46% faster on average**. Individual query times are
**1.31140 / 1.74126** seconds rebuilding and **0.25793 / 0.21646** seconds
maintaining. Composition itself varies, so the full mean difference should not
be attributed solely to the 1.10321-second route rebuild. The entry guard costs
about 0.00414 seconds; the query total also includes the exit guard.

**The complete short sequence regresses by 1.16% in this measurement.** Its
individual times are **69.63884 / 72.30086** seconds rebuilding and
**71.51892 / 72.07253** seconds maintaining. Initial checking variance exceeds the
warm-query saving. Preserve this regression; the experiment does not establish
a total-cost improvement for a single expansion after startup. Longer sessions
are the relevant next measurement. Two observations with shared OS caches are
descriptive, not confidence intervals or holdout performance.

Complete sequence time also charges the seed copy, union merge/check and result
serialization. Independent complete-catalog audits follow each sequence and
are separately timed. Shared parent restoration takes **124.46543 seconds**;
final cold route construction and global coverage take **71.74615 seconds**.
The complete producer, including all four arms and diagnostics, takes
**513.89288 seconds**. These costs are not hidden in the warm query comparison.

## Conditions and resources

`cnf_session_query.query_boundary` holds a SQLite transaction and checks the
session's data/schema versions, local write count, admission ledger, sidecar
snapshot and verifier configurations before and after the query. It preserves
the admission budget, entered states and batch counter. Only acquisition
reported to the existing maintenance object may change the authority between
queries. Checked historical rows, route objects and verifier objects remain
exclusively owned and immutable. The guard does not hash arbitrary in-memory
mutation. A restart reconstructs and checks authority again.

Maintained and rebuilt ordered route catalogs agree after every replayed
advance. This is the invariant supporting identical finite-catalog closure and
selection. Missing targets remain explicit until verified insertion activates
their routes; no unknown input is inferred closed. Both methods end with
**710 indexed external routes**, no pending targets, and identical cache counts:
**20,297 checked pattern objects plus 2,916 prepared checked objects**.

Sharing the existing catalog adds no persistent index and avoids a transient
second catalog. The final cold inventory separately encodes **60,884,728 bytes of keys** and
**195,276,573 bytes of node JSON**, with 23,213 unique checked nodes and no
duplicate keys across its two policy views. These are logical serialized
payloads, not resident memory or a measured compression saving. Both methods store exactly
the same expansion: history grows **372,736 bytes**, from **778,899,456** to
**779,272,192 bytes**, and **42,341 -> 42,368 patterns**. The delta occupies
**438,272 SQLite bytes / 20,280 compressed bytes**. Reference evidence grows
**4,413 -> 4,481 nodes**; the positive original-coverage certificate remains
**3,564 steps**. Old payloads and previous experiment artifacts are preserved.

In the first maintained worker, preparation costs **1.04254 seconds**, including
**0.48173 seconds** scanning all eight tables and 66,622 rows; local expansion
costs **0.22849 seconds**. The full-history seed copy also remains in preparation.
The earlier guarded-digest regression is preserved: unchanged-read savings
do not establish an append-time benefit. Avoiding a redundant seed copy under
the checked append boundary is a candidate, not an implemented saving.

The guard still serializes the roughly **1.535 MB** sidecar snapshot. Its cost
grows with that evidence; it is not constant-time validation. Full graph
composition and selection remain, as do acquisition, certificate checking,
serialization, and cold restoration. Cheap queries do not bound fresh
expansion or stored-state growth for unrestricted SAT.

## Resume and next gaps

Resume **`experiments/results/cnf-session-catalog/report.json`**, SHA-256
`f856409b5a58b402ccf6f545dc8570cae22952a79b2b06460a8f68ab2635e10b`, using
**`experiments.compare_cnf_session_catalog.restore_checkpoint`**. Retain evidence
**(1, 42, 156, 57, 1)** and **two bridges**. Resume `next_selection`, not the
report's completed `source`. Next is **40/163/490**, original **case 1190**,
retained index **31**, no pending split; source SHA-256
`da6fb7faa72f03147efaa6102dee5733767a901a2a4fc79f471c435d070ee0d1`.
Case 1443 still has other structural obligations; coverage remains 68/83.

1. Continue original-bound discovery with this retained inventory and catalog
   across several selected residuals. Compare complete multi-expansion sequences
   so startup amortization is measured rather than presumed.
2. Investigate the repeated binary-path / elimination / probing chain as a
   structural description across unresolved cases. Exact keys and checked
   reductions must justify reuse; matching sizes or operation counts is
   insufficient. Keep both conditional branches and recomposition explicit.
3. Cold restoration and initial global semantic checking dominate complete cost.
   Test avoiding repeated historical checks while retaining complete authority
   for unresolved cases. A saved positive certificate alone cannot certify the
   selector's unresolved frontier. Warm query composition and output
   serialization remain measurable smaller costs.

Validation checks all eight saved global queries, every acquisition prefix,
identical operations and logical results, and all 4,481 reference nodes with
fresh discovery and reference expansion disabled. All **259 tests** pass,
including five new guard/ledger tests. The manuscript build preserves all
**64 existing proof blocks**. The validation record records elapsed times,
artifact hashes and preservation counts; validation jobs overlap, so their
elapsed times are not a performance comparison.

Cold validation passes in **611.73501 seconds**. All **1,666 prior artifacts
across 32 manifests**, **101 historical source files**, and all **4,413 previous
reference payloads** remain unchanged. The new manifest binds **79 artifacts /
8,977,136 bytes**; the manuscript builds to **166 pages**. This experiment
archive size includes repeated comparison outputs and the reference snapshot,
separately from the solver-history growth above.
