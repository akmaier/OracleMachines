# Check matched support proofs, then audit the complete lineage

Demand-driven proof checking reduces complete runtime 10.02% against eager
extension and 6.85% against loading the previous index in this matched study.
Every mode still runs the frozen complete proof/query audit and checks all
origins of its support index on the same pinned cold snapshot. Eager and active
extension retain identical proof archives and perform identical SAT search.
The gain comes from avoiding repeated checks of unrelated history before queries.

The index also grows from 151 to 170 retained entries, but this produces **no
additional transfers or saved expansions on the stream**. More entries do not
by themselves establish broader useful coverage. Keep this negative discovery
result alongside the checking improvement.

## Why the active checks suffice

A saved support description is a hint. Bank construction copies it and builds
its raw clause set; it does not read every origin proof or canonicalize every
support. After a target contains a candidate support, the active path checks
its canonical identity and reads its ordinary proof. A checked negative core
already establishes that any containing target is UNSAT, independently of the
guard that originally discovered that core. If the root is missing, the frozen
extractor must derive it from a checked negative origin, and the resulting root
must equal the proposed root. The unchanged subset rule checks and publishes
the target refutation. A positive, missing or misbound core cannot justify UNSAT.

The current query's own guard is still checked online. A negative restricted
child is never substituted for the complete-query identity. Historical discovery
lineage is a separate obligation: an otherwise sound match may have malformed
old provenance, which the complete cold audit must reject before the checkpoint
is accepted. Pending proposals are never persisted as trusted proof-validity flags.
A malformed hint may cause failure; it is not silently treated as a certificate.

Extension discovers the 42 new negative guarded sources normally and merges
their support descriptions with the saved index. It defers old lineage checking,
not new source verification or matched-core verification. The exact merged
frontier agrees with the fully checked extension. Repeated batch identities
still reject, and all old descriptions, origins and proof rows remain preserved.
The live solver is an exclusively owned append-only session. Shared mutable
services and hostile private-connection manipulation are outside this contract.

## A complete audit without repeating the cold proof loads

The joint auditor calls the unchanged frozen complete audit, substituting the
existing read-only snapshot solver. Its close request is held until the same
snapshot has checked every origin, guard, containment relation, dominance
witness and available core of the saved index. The connection closes in a
finally block, including after failures. No proof or query check is removed.
The one pinned view avoids checking lineage against a different database state,
and its already checked proof objects serve both audit phases.

Every mode pays for this complete lineage audit. Its mean cost is 0.20506
seconds in active mode, included in 4.14972 seconds of total cold auditing.
The timed audit boundary is broader than the previous experiment; old runtime
percentages cannot be combined with this result. Independent validation also
replays the ordinary checker and lineage checks without the held-snapshot wrapper.

## Matched results

All workers begin with the current 17,161-key union and saved 151-entry index,
including its pending proposals. Loaded mode checks and reuses that index;
eager mode checks old lineage and extends it; active mode extends it and checks
matched cores on demand. Selection excludes all 1,152 prior sidecar answers and
cached complete roots, then selects another 64 double deletions per original
template. Selection costs 1.64035 seconds separately. Three balanced process
triples visit 192 queries twice, with no concurrent tests, builds or profiles.
These are constructed neighbouring inputs, not an independent arbitrary-SAT sample.

The complete clock charges restoration, bank checks, discovery, matching,
materialization, query handling, complete cold proof/query/lineage audit,
serialization, compression and final digest/report generation. Imports, CLI
reads and the wrapper report rewrite remain excluded. Historical acquisition
stays charged in earlier records.

| Measurement | Loaded index | Eager extension | Active extension |
|---|---:|---:|---:|
| Retained entries | 151 | 170 | 170 |
| Support transfers | 25 | 25 | 25 |
| Fresh expansions / splits | 187 / 64 | 187 / 64 | 187 / 64 |
| New materialization rows | 12 | 13 | 13 |
| All new proof rows | 370 | 371 | 371 |
| Mean preparation seconds | 1.57440 | 1.78958 | 0.51719 |
| Mean two-visit query seconds | 1.05842 | 1.05401 | 1.34819 |
| Mean complete seconds | 11.12815 | 11.52069 | 10.36579 |
| Mean complete cold seconds | 4.08972 | 4.25798 | 4.14972 |
| Mean compression seconds | 3.33575 | 3.34509 | 3.29684 |
| Mean peak RSS, bytes | 535,489,195 | 551,933,269 | 508,368,213 |
| SQLite bytes | 54,427,648 | 54,427,648 | 54,427,648 |
| Gzip bytes | 4,221,922 | 4,222,063 | 4,222,063 |

Active preparation normalizes 517,355 literal occurrences versus 1,904,438 for
eager extension, and makes 1,563 database lookups versus 6,625. Checking some
premises during the query makes query time 27.91% higher than eager extension,
but complete time improves in every triple, by 9.21–10.87%. It also improves
5.78–8.30% against the loaded control. This does not establish that extension
itself is profitable: the loaded control still uses eager upfront checks, and
an active loader without extension is not compared here.

Mean peak RSS is 7.89% below eager and 5.06% below loaded. The eager comparison
changes sign across triples, so do not infer a robust memory improvement over
eager extension. All three loaded comparisons are lower, by 4.44–6.56%, but
there is no improved asymptotic memory bound. Proof archives are byte-identical
between extension modes. Gzip plus raw sidecars increases from 11,657,158 bytes
for loaded to 11,894,676 for active; no persistent-space saving is established.

## Coverage limits and next targets

The 42 new negative sources yield 40 distinct supports: 17 duplicate old entries,
23 are new, and four old frontier entries are superseded without deletion.
There are 191 raw supports and 170 retained descriptions. Both extension modes
use 22 supports for 25 transfers, materializing four roots through 13 new proof
rows. They end with 106 available retained roots and 64 pending ones. Repeated
query visits add no rows. Every measured transfer still shares the guard clause
of its first origin; broader cross-guard and cross-category coverage remains open.

All modes answer 97 SAT / 95 UNSAT, with 95 witness publications, 51 old full-query
core hits and 46 guards. The guards include 44 negatives and two positives;
four restricted targets are cached. Seventeen queries still expand: 15 negatives
need 145 expansions, and guarded SAT cases 137 and 2 need 26 and 16. Template 12
accounts for 169 of 187 expansions, template 8 for 18 and template 6 for none.
Largest negatives are cases 29 (23), 140 (18), 116 (17) and 149 (15). These are
new-catalog IDs, not the original structural cases.

The next coverage work should inspect these unresolved template-12 residuals,
including whether retained SAT witnesses can repair or transfer to the two
positive cases, rather than equating index growth with coverage. Test whether
different guards expose shared supports or summaries; retain exact recomposition.
For the next cost ablation, load the now-acquired 170-entry index with active
checks before paying for more discovery. This run has already paid for those
entries; do not rebuild them to claim savings. Complete cold auditing and
compression now occupy 40.03% and 31.81% of active worker time, so further
large total-cost claims need to address those phases explicitly.

Active matching still scans raw clause sets. Successful matches pay for
canonicalization and verification; pending ones may require large derivations.
Complete auditing remains dependent on the acquired graph and provenance size.
That graph and its construction can be exponential in input length. No uniform
polynomial SAT algorithm, minimum-work bound, new original structural closure
or additional Lean verification is established.

## Validation and persistent authority

Resume `experiments/results/cnf-active-support/checkpoint.json`. Preserve all
inherited fields plus `active_support_study`, `active_support_decisions` and
`active_support_proposals`. Load this complete 170-entry index, including pending
entries and its raw-support/origin history. Its six source catalogs stay in their
existing order; a subsequent extension must supply only a genuinely new batch.
The union contains **17,532 keys / 54,337,536 SQLite / 4,206,056 gzip bytes**,
adding 371 keys while retaining every old payload. Two alternate certificate
occurrences remain in trial archives. New decisions comprise **146 direct roots /
46 guards**, including the two SAT cases. The union also has 106 available retained
roots and 64 pending ones; pending entries cannot justify UNSAT before verification.

All **461 tests**, nine complete archive checks / **3,456 trial query replays**,
every union node, **1,421 inherited decisions** and all new decisions pass with
fresh validation search disabled. Prior **364 sources / 4,042 artifacts /
71 manifests** remain unchanged. Runtime binds 368 sources; the analyzer brings
the ledger to 369. Structural authority stays 2,614 patterns / 259 pairs / 17
missing children, original 17/24 / 999 steps, separate supplemental 24/24 / 208,
and original case 7's discovery pointer. No new Lean claim.
Checkpoint SHA-256: `ddab750444c8546722ca5d15acee2abbda32455e9dd2dcc785715ebdcfaa62b1`.
Report SHA-256: `9b616b087f471249cebe07ea6c29a864980c46d3736425e613b6cfa1de556b70`.

The manuscript builds to 197 pages without warnings; all 64 proof blocks are unchanged.
