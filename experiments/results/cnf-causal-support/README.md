# Causal support extraction: more reuse, costly reconstruction

Backward dependency slicing removes unit assignments not required by a conflict
or selected negative child proof. On 192 new constructed queries, nine additional
cofactor transfers reduce expansions 195 -> 100 (48.72%) and query time 27.04%.
Re-extracting all old supports still increases complete runtime 15.87% against
active loading, and derived proofs add more rows. Preserve and load the acquired
frontier before another reconstruction. See [analysis](../../../research/causal-support.md).

Reproduce in fresh directories, with timed workers running alone:

```sh
python3 experiments/probe_cnf_causal_support.py /tmp/cnf-causal-probe
python3 experiments/compare_cnf_causal_support.py /tmp/cnf-causal-support
python3 experiments/validate_cnf_causal_support.py /tmp/cnf-causal-support
python3 experiments/analyze_cnf_causal_support.py /tmp/cnf-causal-support
```

`protocol.json` binds 380 runtime sources, the current 17,947-key union and the
saved 170-entry frontier. Selection excludes all 1,536 prior sidecar answers
and cached complete roots. Three balanced process triples visit each query twice.
Active loads the old bank; extended adds 103 negative origins with the previous
extractor; causal re-extracts all 389 origins with dependency-closed unit slicing.
The historical probe is preserved in `../cnf-causal-support-probe` and publishes
no new certificates. Cases 157/175 acquire new mutual support containment;
cases 123/189 shrink to 26/34 clauses but retain different cores.

Causal extraction removes 5,585 of 14,613 unit steps and reduces retained clause
occurrences 7,385 -> 4,568 against extension. It gives 38 cofactor hits instead
of 29 and uses 100 expansions / 33 splits instead of 195 / 65. All modes return
95 SAT / 97 UNSAT; 52 guards include one positive child. No query regresses in
expansions. Every causal hit still shares its first origin's guard clause.

Mean complete runtime is 10.89172 / 11.63135 / 12.61998 seconds for active /
extended / causal. Causal regresses against both controls in every triple.
Preparation costs 2.33282 seconds, versus 0.08516 / 0.95163. Its 31 matched
missing roots require 275 materialization rows instead of 59 / 65. Total new
rows are 553 versus 423 / 429. The causal trial has 34 ready frontier roots and
142 pending descriptions. Mean peak RSS is 2.36% above active; gzip plus first
trial raw sidecars is 12,152,030 versus 12,164,674 / 12,640,746 bytes. This tiny
space saving is not an asymptotic memory result.

All preparation, lookup, checking, materialization, query work, persistence,
complete cold proof/query and used-index lineage audit, compression, and final
digest/report generation are charged. Imports, initial CLI reads and wrapper
rewrite are excluded. Selection and prior acquisition remain separately charged.
Index-only discovery publishes no proof; a missing support root must be
materialized with the causal extractor and checked before use. A cofactor hit
still requires its complete source query and checked guard. No fresh SAT search
is used in discovery or materialization. Supports are proof-dependent, not
minimum cores, and the acquired proof graph may remain exponential.

The checkpoint preserves earlier fields and adds `causal_support_study`,
`causal_support_decisions`, `causal_support_proposals` and
`extended_support_proposals`. Both new banks use all eight source catalogs in
protocol order; the older 170-entry bank keeps its original six-catalog lineage.
Use `CausalCoreBank` for the causal bank, especially its pending entries. The
older support frontier and optional positive witness bank remain available.
An incremental causal update path is not yet implemented.

The next cost experiment should load this saved frontier without re-extraction
on another novel stream. Remaining coverage targets include negative cases 187,
159, 50 and 60 (20/17/16/16 expansions); SAT case 42 contributes five. All 486
tests pass, and the manuscript builds to 199 pages with 64 unchanged proof blocks.

## Validation and retained authority

Independent validation passes **486 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **1,805 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. The union retains
**18,672 keys / 57,823,232 SQLite / 4,419,183 gzip bytes**, adding 725 keys while
keeping every earlier payload. All **41 alternate certificate occurrences** remain
in trial archives. New decisions comprise **140 direct roots / 52 guards**,
including one positive guarded result.

Resume `experiments/results/cnf-causal-support/checkpoint.json`. Preserve
`causal_support_study`, `causal_support_decisions`, `causal_support_proposals`
and `extended_support_proposals`, along with every inherited field. The causal
frontier has **34 ready roots / 142 pending**; the extended frontier has
**118 / 89**, and the original 170-entry frontier has **119 / 51** in the union.
All three lineage audits pass. Causal pending entries require the causal
materializer; the old materializer is not interchangeable. Both new banks use
eight source catalogs in protocol order; the original bank still uses six.

All prior **375 sources / 4,174 artifacts / 73 manifests** remain unchanged.
Runtime binds 380 sources; the analyzer brings the ledger to 381. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds to **199 pages** without
warnings, preserving all **64 proof blocks**. No new Lean result is claimed.

The new manifest binds **56 artifacts**, including the read-only historical
probe. The next preservation audit inherits **4230 artifacts / 74 manifests**.
