# Native histories and bounded affine residency

Runtime checkpoint: `88f26a8`. All earlier results, proofs and experiments remain.
The checkpoint adds native eventwise source-CNF composition, removes literal
ancestor retention from affine native states, and evaluates reuse against matched
reconstruction. It does not establish unrestricted SAT tractability.

## Proof and implementation

`SourceHistory.handle` is the source dispatcher executed by the worker.
`handle_valid` derives raw-initial, current-CNF and exact-patch response contracts
on success and predecessor-state equality on failure. `execute_valid` and
`trace_meaning` compose them across arbitrary finite interleavings, including
administrative operations. `trace_query_semantics` yields the actual root's full
original-CNF decision. `earlier_event_retained` preserves prior observations under
continuation. Observations have event-specific store identities; a deleted name
can later be reused with different meaning. The worker does not store the
mathematical trace. Python content-addressed lineage, bytes, witnesses and SQLite
remain outside the proof.

The earlier affine `State` held its entire original history at runtime. Evicting
map entries would therefore leave ancestors reachable from resident children.
`AffineResident` now uses Mathlib `Erased` to preserve exact original-history
semantics in proofs without carrying ancestor values in the compiled state.
Generated C contains a single state field for the summary. Current node request
JSON and metadata remain additional runtime data. The algebra, summary-size bound
and coefficient charges are unchanged. `dropNames_preserves` proves exact lookup
preservation for all other names. A checked child requires no live ancestor name.

`native_affine_versions` bounds resident versions to 2..4,096, default 256. Before
an append, the service protects its parent and evicts an older resident node.
Original source records remain durable; cold replay reads batches individually
and evicts earlier native versions. Its Python plan and cycle check still retain
O(T) identifiers. Failed transactions preserve old rows and mark residency uncertain;
the next request resets only the affine store and reconstructs checked state.
Native 4,096-version capacity limits simultaneous residency, not history length.
No byte/RSS or complete Python-retention theorem follows from a version count.

## Verification

- **190 tests pass**, including **15 affine tests / 36 source-update tests**.
- Lean audits **3,625 declarations / 1,766 theorem declarations**, without admits
  or added axioms.
- A source test interleaves initial binding, partial-batch failures, failed deletion,
  patching, old-root queries, name reuse and layout reset. Rejected mutations do
  not leak intermediate nodes or delete an earlier root.
- An affine history grows to **4,101 appends**, queries an evicted historical
  version, and restarts with only **two resident versions**. All answers agree.
- Tests cover child survival after parent eviction, failure recovery, invalid caps,
  and exhaustive small-system parity-to-CNF conversion, including auxiliary names.
- All **355** earlier generic inputs pass revalidation/audit; five source versions
  pass adoption/restart; all **268** older affine versions pass source replay under
  a four-version cap. Positive and negative archived versions also pass restart
  under a two-version cap.
- After this work, every old row in **22 tables** and all **233 prior experiment
  files** remains unchanged. The live archive has **9,230 generic results /
  3,096 refutations / 70 source-state rows / 536 affine-state rows**. The latter
  includes 268 versions adopted under the new engine fingerprint.
- All **33 earlier manuscript proof blocks** remain verbatim, with one new native
  history proof. Earlier timing artifacts are unchanged.

## Matched comparison

72 fresh-process/database runs cover widths 2/8/16 and repeated/novel equations,
with three sequential repetitions and rotated mode order. Every stream has 16
appends, a contradictory successor and a satisfiable historical branch. All
**1,296 decisions**, including **72 negative decisions**, agree with independent
elimination of the original equations. No run fails or times out.

Median stream times in milliseconds:

| Width / equations | Resident | Full parent replay | Service restart | Checked CDCL |
|---|---:|---:|---:|---:|
| 2 / repeated | 151.41 | 147.41 | 776.96 | 261.05 |
| 2 / novel | 132.78 | 145.38 | 796.87 | 289.33 |
| 8 / repeated | 138.42 | 223.97 | 863.05 | 364.72 |
| 8 / novel | 154.37 | 188.22 | 790.12 | 1001.17 |
| 16 / repeated | 166.47 | 474.98 | 1091.72 | 698.34 |
| 16 / novel | 155.53 | 357.77 | 966.19 | 3196.47 |

Totals include service setup, conversion, requests, restart and shutdown; raw
worker-process totals also include Python bootstrap. Resident and full-replay
modes use identical deltas, archives and native algebra. At width 16, resident
reuse improves stream time by **2.85 / 2.30** relative to full replay. The smallest
repeated stream shows no gain; small differences have no significance claim.
All modes retain results. CDCL pays a different representation, unary encoding
and proof-checking pipeline, so its column cannot isolate solver algorithm speed.
The six synthetic streams do not establish general SAT performance.

An earlier overlapping adoption/timing pass is preserved in `pilot/`; its timings
are excluded. The final comparison uses identical compressed input bytes and runs
after archive adoption, with no simultaneous repository builds, tests or replay.
Raw worker JSON files, `comparison.json`, frozen inputs, per-run database paths,
phase metrics, caps and binary/source fingerprints are retained. Databases remain
in ignored `solver/.cache/` locations, not replaced by summaries alone.

## Remaining obligations

Native source trace composition and affine ancestor erasure/eviction are now
concrete. Remaining work is complete Python/SQLite and affine named-protocol
refinement, serialized/full-history witnesses, broader separator decompositions
and mixed CNF/XOR backdoors, end-to-end machine/resource accounting, workload-based
dispatch, and the general relation/factor store invariants. Their existing
correctness restrictions remain. This checkpoint does not prove compact closure
or efficient acquisition for unrestricted CNF.
