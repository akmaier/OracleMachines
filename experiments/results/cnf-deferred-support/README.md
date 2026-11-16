# Support proofs constructed only after a match

Deferred construction produces the same 23 checked transfers and 177 expansions
as eager construction on the further unseen 192-input stream. It constructs
209 support-proof nodes instead of 1,310, reducing all new nodes 1,648 -> 547.
Complete time improves 9.96% against eager construction, but is still 9.21%
higher than the old-bank control. Keep the mode optional; discovery costs more
than this stream saves. See [analysis](../../../research/deferred-support.md).

Run the timed producer alone, into a fresh directory:

```sh
python3 experiments/compare_cnf_deferred_support.py /tmp/cnf-deferred-support
python3 experiments/validate_cnf_deferred_support.py /tmp/cnf-deferred-support
python3 experiments/analyze_cnf_deferred_support.py /tmp/cnf-deferred-support
```

The three commands must run in order; no tests/builds/profiles overlap timed
workers. `protocol.json` binds 357 runtime sources, the historical 14,630-key
construction seed and latest 16,320-key authority. Selection excludes 768 prior
sidecar answers and all cached complete roots in the latest authority. The
latest complete 104-core bank stays preserved. This is a construction-policy
ablation, not a comparison against loading that already-ready bank.

Three balanced fresh-process triples visit 192 new constructed neighbours twice.
All modes answer 93 SAT / 99 UNSAT, with 54 negative guards. The candidate has
19 materialization calls and 23 hits; every published target needs a checked
negative core. Unmaterialized support proposals are not certificates. Eager and
deferred frontiers agree exactly, and within-mode repetitions have identical
logical/physical archives. All 177 remaining expansions occur on 21 negatives.
All measured hits share their first origin's guard clause; broader cross-category
coverage remains open. Historical acquisition and selection are separately charged.

The outer complete clock includes final row digest and report generation,
which the frozen worker's `wall_seconds` excludes. Imports, CLI protocol reads
and the wrapper report rewrite remain excluded. Primary timing uses
`complete_worker_seconds` and memory uses `complete_peak_rss_bytes`. Timings from
earlier streams/boundaries cannot be multiplied into a cumulative saving.

`cost-attribution.json` records every query, paired timing comparisons, remaining
expansions, proof liveness and pending roots. All 209 deferred materialization
nodes are needed by this stream's query proof closure. The eager archive has
1,101 further preparation nodes outside that closure. This is not a proof that
the online policy always constructs a minimum graph. Mean RSS improves 3.78%
against eager but paired differences are noisy; no robust memory gain follows.
Against the old bank, RSS rises 1.87% and complete time regresses in every triple.

`checkpoint.json` preserves all inherited fields and adds
`deferred_support_study`, `deferred_support_decisions` and
`deferred_support_proposals`. The reference union retains **16,760 keys /
51,294,208 SQLite / 4,046,593 gzip bytes**, 440 keys beyond the latest authority.
Earlier payloads win overlaps; 46 alternate certificate occurrences remain in
trial archives. The new decisions have 138 direct roots and 54 guarded negatives.
The earlier 104-core ready bank remains complete in this union. The 83 pending
roots apply only to the historical deferred trial, not the final union.

All 442 tests, nine ordinary-solver archive audits and 3,456 trial query replays,
every union node, 1,037 inherited decisions and all new decisions pass. Fresh
validation search is disabled. Original structural authority remains 2,614
patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps and
separate supplemental 24/24 / 208; original case 7 retains its discovery pointer.
All 353 prior sources and 3,923 artifacts / 69 manifests remain unchanged.
The analyzer brings the final source ledger to 358; 64 manuscript proof blocks
are unchanged. There is no new Lean or unrestricted-SAT claim.

`fixture-failure.txt` preserves an initial test-fixture failure: adding an
independent two-literal clause reused an already cached root under canonical
variable renaming, so `inserted=False` was correct. The corrected test uses a
two-clause connected extension and passes; this was not a false solver answer.
`tests.txt` retains inherited resource warnings and the successful 442-test run.

The manuscript builds to 195 pages without warnings. All 64 proof blocks are unchanged.
