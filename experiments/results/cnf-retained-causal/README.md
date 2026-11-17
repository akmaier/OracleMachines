# Retained causal frontiers: avoid rediscovery, preserve complete checks

Loading the acquired causal frontier cuts complete runtime 16.56% versus
rebuilding it and produces identical frontier files and proof archives. Against
loading the legacy frontier, it saves 22.5% of expansions but total runtime is
effectively flat and measured peak memory is higher. See
[analysis](../../../research/retained-causal.md).

Reproduce in a fresh directory, with timed workers running alone:

```sh
python3 experiments/compare_cnf_retained_causal.py /tmp/cnf-retained-causal
python3 experiments/validate_cnf_retained_causal.py /tmp/cnf-retained-causal
python3 experiments/analyze_cnf_retained_causal.py /tmp/cnf-retained-causal
```

The protocol binds 385 runtime sources and the current 18,672-key union. Selection
excludes 1,728 prior sidecar answers and cached complete roots, then chooses 192
new two-deletion neighbours, visited twice in three balanced process triples.
Legacy loads the 207-entry old-rule frontier; rebuilt re-extracts the 176-entry
causal frontier; retained loads that saved causal frontier. Both use the same
389 origins in eight ordered catalogs. The latest 51 negative origins remain
preserved but are not added in this comparison.

The loader checks the file fingerprint and explicit causal/deferred policy,
preserves saved fields, and selects the matching causal materializer. These are
identity checks, not UNSAT certificates. Every matched core still needs ordinary
proof checking; pending roots require checked materialization. Current-query
guards and full cold proof/query and index-lineage audit remain charged. No
persistent unchecked validity flag is accepted.

Mean complete seconds are 10.56570 / 12.74826 / 10.63701 for legacy / rebuilt /
retained. Loading avoids 2,851 discovery-node visits and cuts preparation
2.29443 -> 0.08099 seconds. Complete time improves in all three pairs versus
rebuild. Query time rises 46.39% because reconstruction had warmed proof checks.
Against legacy, complete time is 0.67% higher with mixed paired signs; no net
speedup is established. Six additional target hits reduce expansions 120 -> 93
and splits 37 -> 30. All modes answer 99 SAT / 93 UNSAT; 45 guards include two
positive children. Every causal hit still shares its first origin's guard.

Retained causal matches add 100 materialization rows versus 33 for legacy; total
new rows are 365 versus 319. On the 19 overlapping targets, materialization costs
74 versus 33 rows. The six extra hits require another 26 rows and six publications.
Test cheaper-proof selection on overlaps before claiming that this apparent
41-row opportunity survives different sharing/cache histories.

Mean peak RSS rises 14.56% against legacy and 11.24% against rebuild, with
positive paired differences. The allocation cause is untraced. Gzip plus
first-trial raw sidecars is 12,173,774 versus 12,657,545 for legacy. The retained
frontier has 48 ready roots / 128 pending in the trials. Complete cold audit and
compression cost 41.29% and 33.65% of retained runtime.

All setup, preparation, lookup, checking, derivation, queries, persistence,
complete cold audit, compression and final digest/report generation are charged.
Imports, initial CLI reads and wrapper rewrite are excluded. Historical acquisition
and selection are separately charged. This is a current-union comparison on
novel queries, not evidence that original discovery was free or has amortized.

The 492-test suite passes with unclosed-SQLite ResourceWarnings during older
tests. The focused six new tests pass with warnings enabled and none emitted;
both logs are retained. Allocation origins of the older-test warnings are not
traced. The manuscript builds cleanly to 200 pages with 64 unchanged proof blocks.

The next cost target is choosing among available proofs on overlapping matches.
The remaining 93 expansions comprise 74 negative and 19 positive. Current negative
cases 14/161 cost 19/15; SAT cases 45/91 cost 14/five. Broader cross-guard transfer,
incremental causal discovery and unrestricted polynomial guarantees remain open.

## Validation and retained authority

Independent validation passes **492 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,997 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**19,091 keys / 59,228,160 SQLite / 4,491,457 gzip bytes**, adding 419 keys while
preserving every earlier payload. All **48 alternate certificate occurrences**
remain in trial archives. New decisions have **147 direct roots / 45 guards**,
including two positive guarded results.

Resume `experiments/results/cnf-retained-causal/checkpoint.json`. It preserves
all inherited semantic fields, adding `retained_causal_study` and
`retained_causal_decisions`; the saved frontiers themselves are unchanged. Load
`causal_support_proposals` with the fingerprinted causal loader and matching
materializer. In the union, the causal frontier has **48 ready roots / 128 pending**;
the extended legacy frontier has **121 / 86**, and the original 170-entry frontier
has **120 / 50**. Both measured banks keep the same eight-catalog, 389-origin
lineage. The ninth catalog is excluded from selection but not added to discovery.
The original frontier retains its six-catalog lineage. All three union audits pass.

All prior **381 sources / 4,230 artifacts / 74 manifests** remain unchanged.
Runtime binds 385 sources; the analyzer brings the ledger to 386. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **200 pages** without warnings,
with **64 unchanged proof blocks**. No new Lean result or unrestricted-SAT bound.
The full test log retains 24 unclosed-SQLite ResourceWarnings during older tests;
the six focused new tests emit none with warnings enabled. Their allocation
origins remain untraced; this is not a failed proof check.

The new manifest binds **56 artifacts**. The next preservation audit inherits
**4286 artifacts / 75 manifests**.
