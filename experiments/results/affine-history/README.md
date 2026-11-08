# Affine source provenance and recurring expansion work

Runtime checkpoint: `1037595`. This adds native decoded-input and chronological
history contracts, then identifies recurring algebraic work in the preserved
comparison inputs. It makes no new timing or unrestricted-SAT claim.

## Native proof boundary

`parseRow_decoded` recovers exact Boolean coefficients, dimension and right-hand
side. `parseRows_decoded` preserves input order and multiplicity. Fresh definition
certificates record initial widths or actual predecessor-store parent lookups.
Query and eviction responses carry corresponding field/store certificates.
The worker executes `AffineHistory.handle`; `empty_execute_sourced` derives
chronological original-input provenance for every resident node, and
`executed_query_semantics` proves both returned verdicts against that history.
Errors preserve the predecessor store. Trace and origin evidence add no runtime
history snapshots.

A retained child keeps its original history after parent eviction or name reuse.
An exact retry returns that child; a fresh child binds the current parent.
Deleting/redefining the child can therefore change its answer. Retries additionally
check parsed modes, widths or base names, and typed equation lists, so source
agreement does not depend on a theorem about Lean's partial JSON equality.
That comparison has a cost outside the coefficient ledger. Bytes, process
transport, Python hashes/lineage, SQLite and serialized witnesses remain outside
the native proof. No machine-time or whole-process space theorem is claimed.

## Verification and preservation

- **192 tests pass**, including **17 affine / 36 source-update** tests.
- Lean audits **3,794 declarations / 1,836 theorem declarations** without admits
  or added axioms.
- New regressions cover child retries after parent deletion/reuse, new bindings,
  child-name reuse, resets, malformed late equations and atomic eviction rejection.
- **355** earlier generic inputs pass revalidation/audit; five saved source
  versions pass adoption/restart; **268** distinct old affine versions pass source
  replay with four residents and both verdicts pass restart with two residents.
- Every old row across **22 tables** and all **394** previous experiment files
  remains unchanged. Live archive counts are **9,585 results / 3,225 refutations /
  75 source-state rows / 804 affine-state rows** across engine versions.
- All **34** previous manuscript proof blocks remain unchanged, with one new
  affine-history proof. Earlier timing results retain their original binary IDs.

## Expansion pattern diagnostic

`experiments/analyze_affine_reuse.py` replays the six frozen comparison streams,
retains every version in fresh per-case databases, and checks all **108** decisions
against independent elimination of the original systems. It records the actual
ordered parent summary and local equation batch. SHA-256 keys label inputs;
`pattern-check.json` additionally checks full input equality for every match.

| Width / stream | Expansions | Distinct versions | Repeated kernel inputs | Duplicate input rows | Work on repeated inputs / total coefficient work |
|---|---:|---:|---:|---:|---:|
| 2 / repeated | 18 | 18 | 14 | 30 | 2450 / 2793 |
| 2 / novel | 18 | 18 | 0 | 0 | 0 / 2073 |
| 8 / repeated | 18 | 18 | 14 | 120 | 89726 / 100629 |
| 8 / novel | 18 | 18 | 0 | 0 | 0 / 72549 |
| 16 / repeated | 18 | 18 | 14 | 240 | 643566 / 719509 |
| 16 / novel | 18 | 18 | 0 | 0 | 0 / 515509 |

Sorting/deduplicating the local batches produces no additional repeated calls in
these cases. Canonical row-space forms, variable renaming and low-rank changes
are not tested. The 89.4% work share in the width-16 repeated stream identifies
an opportunity, not realized savings. No kernel cache is installed, no timings
are compared, and discovery, checking, cache management and persistence must all
be charged before claiming a gain. The scripts may run alongside preservation
because this is an equality/correctness diagnostic, not a timing experiment.

The next concrete target is to reuse an exact algebraic transition across distinct
source histories. Such reuse must construct the new history certificate instead
of returning an older version's provenance. The per-append coefficient bound
remains O(b^3+b^2 c), summary payload O(b^2), and cold replay sums all earlier
append costs. Exact transition reuse, duplicate compression, then broader
canonical/low-rank patterns are prioritized in `research/implementation-gaps.md`.
The existing hourly automation was updated to this expansion focus.
