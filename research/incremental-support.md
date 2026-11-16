# Incremental discovery from newly acquired negative results

The saved support index can now be extended without re-extracting every old
proof support. Adding 99 newly acquired negative guarded results to the previous
145 yields exactly the same frontier as full reconstruction: 168 distinct raw
supports and 151 retained entries, up from 112 and 104. On a new 192-query stream,
the enlarged bank certifies four more targets and reduces expansions 199 -> 162.
However, incremental discovery only improves complete time 0.45% over rebuilding,
and costs 4.12% more than reusing the old ready bank. Keep extension optional;
repeated evidence checking remains the main acquisition cost to address.

## Exact merge and validity conditions

The old index retains every raw support and origin, including entries dominated
by a smaller support. New discovery uses only the new source catalogs. Identical
raw clause sets keep their first origin and stable index; new raw supports are
appended, and new origins are remapped to those indices. A repeated catalog/case
identity is rejected, even for a positive result, so reapplying a batch cannot
silently acquire it twice. Callers should load the resulting checkpoint on resume.

For each new support C, an existing retained subset already covers every target
containing C, so C need not enter the frontier. Otherwise C enters and replaces
retained supersets of C. Those supersets remain in history, and every target
matching one still matches C. No other pair becomes comparable. Induction over
the additions leaves precisely the inclusion-minimal raw supports of the union.
The final frontier is sorted by the same size/lexicographic rule as a complete
rebuild; dominance witnesses are recomputed against that order. Thus both
procedures retain the same containment matches and choose the same first match.
This is a property of a finite support family, not an efficient partition of SAT.

Loading the old index checks its source identities, guard compositions, negative
origin proofs, support containment and dominance witnesses. Every already-present
core proof must check as negative. Missing derived roots remain proposals, not
certificates. A matched pending proposal invokes the frozen materializer; the
checked derived root must equal the proposed root before the unchanged subset
rule may publish UNSAT. A malformed proposal can be rejected or miss reuse; it
cannot supply an unchecked negative answer. Sound answers still depend on the
ordinary verifier, not a persisted validation flag. Pending proposals survive
JSON serialization, restart and further extension without eager materialization.

This initial implementation still scans old provenance on load, builds clause
sets, copies the old index and recomputes all dominance witnesses. It does not
make cold preparation proportional only to the delta. Recognition remains raw
clause containment in common coordinates; arbitrary variable-renaming search is
not performed. A restricted negative result still needs its complete source,
stronger negative premise and checked deletion guard for full-query recomposition.

## Measured comparison

Every worker begins with the current **16,760-key union** and its already-ready
104-core bank. The ready mode checks and loads that bank; rebuild discovers
supports from all 244 negative guarded results; incremental checks the old index
and discovers only the 99 new negatives. All modes use the same deferred
materializer, so only a match can trigger a missing derived proof. This control
includes complete old provenance checking: it is not the cheapest possible
loader of independently checked negative cores.

Selection excludes all 960 previous sidecar answers, including guarded records,
and all cached complete roots. It costs 1.78046 seconds separately. A fixed salted
order selects the next 64 double deletions per original template. Three balanced
fresh-process triples visit the 192 inputs twice, without concurrent tests,
builds or profiles. These constructed neighbours are development inputs, not an
independent arbitrary-SAT benchmark.

The complete clock charges restoration, bank checking, discovery, matching,
materialization, query work, full cold audit, sidecars, compression and final
row digest/report generation. Imports, CLI protocol reads and the wrapper's
report rewrite remain excluded. Prior acquisition stays charged in historical
records. Percentages from different streams or timing boundaries cannot be
multiplied into a cumulative saving.

| Measurement | Ready bank | Full rediscovery | Incremental discovery |
|---|---:|---:|---:|
| Negative origins | 145 | 244 | 244 |
| Retained supports/proposals | 104 | 151 | 151 |
| Discovery proof-node visits | 0 | 1,697 | 715 |
| Support transfers | 14 | 18 | 18 |
| Fresh expansions | 199 | 162 | 162 |
| Split nodes | 64 | 53 | 53 |
| Materialized proof rows | 0 | 39 | 39 |
| All new proof rows | 362 | 368 | 368 |
| Mean preparation seconds | 1.27181 | 1.82786 | 1.78856 |
| Mean two-visit query seconds | 1.22946 | 1.14185 | 1.18675 |
| Mean complete seconds | 11.17962 | 11.69363 | 11.64076 |
| Mean cold audit seconds | 4.12820 | 4.12858 | 4.06629 |
| Mean compression seconds | 3.39409 | 3.45767 | 3.46246 |
| Mean peak RSS, bytes | 428,856,661 | 423,799,467 | 429,599,403 |
| SQLite bytes | 52,887,552 | 52,858,880 | 52,858,880 |
| Gzip bytes | 4,143,717 | 4,142,183 | 4,142,183 |

The two extension modes have identical logical and physical proof archives.
Incremental discovery visits 57.87% fewer support nodes, but preparation improves
only 2.15% and complete time 0.45%. Paired complete-time differences range from
0.009% to 1.01%; three trials do not establish a practically robust speedup.
Mean peak RSS is 1.37% higher than rebuilding and 0.17% higher than loading the
ready bank. There is no demonstrated memory improvement.

Relative to the ready bank, extension reduces fresh expansions 18.59%, but
complete time regresses 3.65–4.57% in every matched triple. Query time improves
3.47%. Gzip is only 1,534 bytes smaller; first-trial gzip plus raw sidecars grows
from 11,064,817 to 11,617,440 bytes. Counting only proof-database size would hide
that increase. No historical row or previous trial is removed.

## Coverage and the next investigation

All modes answer 105 SAT / 87 UNSAT, with 104 witness publications, 45 old
full-query core hits and 43 guards. Of the guards, 42 are negative and one is
positive. Six targets are cached. The enlarged bank uses 15 supports for 18
transfers; newly covered cases 53, 121, 163 and 190 account for all 37 saved
expansions. Three materializations add 39 proof nodes. At the end of each
extension trial, 104 of the 151 retained roots exist and 47 remain pending.
The saved bank's original 104 roots are a different set: three older frontier
entries are superseded, and their records and proofs remain preserved.

The new batch contributes 84 distinct raw supports; 28 duplicate old entries,
56 are new, and three old frontier entries are superseded. The resulting 151-entry
frontier preserves all old matches. Every measured transfer still shares the
guard clause of its first origin. These results extend reuse within the tested
families; they do not demonstrate broad cross-guard or cross-category coverage.

Nineteen queries still expand: 18 negatives require 154 expansions, and guarded
SAT case 188 needs eight. Template 8 contributes 66 expansions, template 6 adds
51, and template 12 adds 45. Largest negative cases are 61 (19), 72 and 142
(18 each), and 19 (14). These IDs refer to this new catalog, not the original
structural cases. Preserve the guarded SAT example when studying negative reuse.

The preparation diagnostic explains why fewer extractions did not deliver a
large total saving. Incremental load/checking calls `_read` 7,216 times versus
6,783 for rebuilding, and canonicalization 14,281 versus 13,518. Avoided
extraction is offset by checking the saved provenance and ready cores. This
instrumented diagnostic overlapped the correctness suite; use its call counts
and structure, not elapsed-time comparisons. It did not overlap timed workers.

The next high-value target is to distinguish the evidence needed for a current
support match from a complete historical provenance audit, while retaining
both kinds of verification. In particular, a checked negative core can justify
subset reuse independently of the guard that originally discovered it. Pending
proposals still require checked materialization before use. Investigate whether
an owned append-only session or demand-driven active checks can avoid repeatedly
normalizing unrelated historical evidence, with complete cold audit still
charged separately. Do not introduce persisted unchecked trust marks. The
remaining negative cases above and cross-guard transfer are the next coverage
probes once this cost is controlled. Cold audit and compression remain 34.93%
and 29.74% of complete incremental time.

The method still depends on the acquired proof DAG and the retained support
family. New traversal can revisit old subgraphs shared by new sources; the
extractor memo is session-local. Clause-set construction, exact containment,
antichain maintenance, materialization, retained space and cold reconstruction
remain explicit costs. Graph size and acquisition can be exponential in input
length. No minimum-work, uniform-polynomial SAT, new structural-closure or Lean
claim follows.

## Validation and persistent authority

Resume `experiments/results/cnf-incremental-support/checkpoint.json`. Preserve
all inherited fields plus `incremental_support_study`, `incremental_support_decisions`
and `incremental_support_proposals`. The latter stores the complete extended
index (including all raw supports, origins and dominance), not just ready cores.
For the next extension, supply the five old decision catalogs in their existing
order and only genuinely new batches. Repeated batch identities reject. Use the
extended index to preserve acquired discovery rather than returning to the old
104-entry frontier. Match-time proof checks still apply to every pending root.

The union retains **17,161 keys / 52,809,728 SQLite / 4,124,643 gzip bytes**, adding
401 keys while keeping every earlier payload. Eight alternate certificate
occurrences remain in trial archives. The new catalog has **149 direct roots /
43 guarded decisions** (42 negative, one positive). All 104 original ready cores
remain in history; the extended frontier has 104 available roots and 47 pending
proposals in the union as well as the candidate trials.

All **451 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,229 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **358 sources / 3,979 artifacts /
70 manifests** remain unchanged. Runtime binds 363 sources; the post-hoc analyzer
brings the ledger to 364. Structural authority remains 2,614 patterns / 259 pairs /
17 missing children, original 17/24 / 999 steps, separate supplemental 24/24 /
208, and original case 7's discovery pointer. No new Lean or unrestricted-SAT claim.
Checkpoint SHA-256: `6c60e95e1a8f0f0dc12fc2e24dba38178cc35ae5e13a07a28d43b30d0180700c`.
Report SHA-256: `c5c12f205dd77b370d4120ce0baf06e33ab0ecc1268e2fa7d8ac14fbd4ef5275`.

The manuscript builds to 196 pages without warnings; all 64 proof blocks are unchanged.
