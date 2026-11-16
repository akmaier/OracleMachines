# Incremental support discovery

The extended index has 151 retained entries instead of 104 and certifies four
additional targets on a further unseen stream. Expansions fall 199 -> 162.
Processing only the 99 new negative sources visits 715 extraction nodes instead
of 1,697, with exactly the same frontier and proof archives as full reconstruction.
But complete time improves only 0.45% against reconstruction and regresses 4.12%
against loading the ready bank. No practical total-time or memory gain is established.
See [analysis](../../../research/incremental-support.md).

Reproduce into fresh directories, with the timed producer running alone:

```sh
python3 experiments/compare_cnf_incremental_support.py /tmp/cnf-incremental-support
python3 experiments/validate_cnf_incremental_support.py /tmp/cnf-incremental-support
python3 experiments/analyze_cnf_incremental_support.py /tmp/cnf-incremental-support
python3 experiments/profile_cnf_incremental_support.py /tmp/cnf-incremental-support-profile
```

`protocol.json` binds 363 runtime sources, the current 16,760-key seed and the
saved 104-core bank. Selection excludes all 960 previous sidecar answers and
cached complete roots. Three balanced fresh-process triples query each of the
192 constructed neighbouring inputs twice; no tests/builds/profiles overlap.
Complete time includes final row digest/report generation. Imports, CLI reads
and the wrapper report rewrite are excluded. Acquisition history and selection
remain separately charged; no cumulative cross-stream speedup is claimed.

The ready control checks old provenance and available cores. Rebuild extracts
from all 244 negative guarded sources. Incremental checks the old index and
extracts only the 99 new negatives. New raw supports deduplicate against old
entries, and smaller supports replace frontier supersets without deleting them
from history. Full and incremental results agree on every raw support, origin,
dominance witness and first-match order. Repeated batch identities reject.
Pending proposals persist across restart and extension. A proposal is not a
certificate: the frozen materializer and proof checker must accept the negative
core before subset publication. Source/guard/child binding remains necessary
for every complete guarded query.

All modes return 105 SAT / 87 UNSAT, including one guarded SAT case. Candidate
transfers rise 14 -> 18; cases 53, 121, 163 and 190 account for all 37 avoided
expansions. The extended frontier has 104 available roots and 47 pending roots.
These available roots differ from the original 104 ready cores, all of whose
proofs remain stored. Remaining work is 154 expansions on 18 negatives and eight
on guarded SAT case 188. Every measured support hit shares its first origin's
guard clause; cross-category and arbitrary-SAT coverage remain open.

The preparation diagnostic is retained in `../cnf-incremental-support-profile/`.
It overlapped the correctness suite, not the timed workers: use its call counts
and call structure, not elapsed-time comparisons. Incremental checking makes
7,216 proof reads and 14,281 canonicalizations, more than the 6,783 and 13,518
of rebuilding. Repeated old-evidence checking offsets the reduced extraction.
The next target separates active matching proof requirements from complete
historical provenance audit while keeping both checks and correct invalidation.

`cost-attribution.json` records every query, the paired changes, pending roots
and remaining expansion work. Full and incremental archives are byte-identical.
Mean incremental peak RSS is 1.37% above rebuild and 0.17% above ready. Gzip plus
sidecars increases 11,064,817 -> 11,617,440 bytes versus ready. Keep extension
optional and preserve the measured regression.

`checkpoint.json` retains inherited fields and adds `incremental_support_study`,
`incremental_support_decisions` and `incremental_support_proposals`. Resume from
that extended index, with the five old catalogs in order and only a new batch;
do not rediscover the acquired supports. The union preserves 17,161 keys /
52,809,728 SQLite / 4,124,643 gzip bytes, adding 401 keys. Eight alternative
certificate occurrences remain in trials. New decisions have 149 direct roots
and 43 guards (42 negative, one positive).

All 451 tests, nine ordinary-solver archive checks / 3,456 query replays, every
union node, 1,229 inherited decisions and all new decisions pass with fresh
validation search disabled. All 358 prior sources and 3,979 artifacts / 70
manifests remain unchanged. The analyzer brings the final source ledger to 364.
Structural authority stays original 17/24 / 999 steps and separate supplemental
24/24 / 208, with 2,614 patterns / 259 pairs / 17 missing children and the original
case 7 discovery pointer unchanged. No new Lean or unrestricted-SAT result.

The manuscript builds to 196 pages without warnings; all 64 proof blocks are unchanged.
