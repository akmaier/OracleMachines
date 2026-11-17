# Checked proof choice across acquired support frontiers

The combined policy preserves the causal bank's 30 target hits while reducing
materialization **137 -> 57 rows** and total new rows **351 -> 271**. Mean complete
time improves 10.78% versus causal-only reuse, but paired signs are mixed and
peak RSS rises 5.53%. See [analysis](../../../research/proof-choice.md).

Reproduce in a fresh directory, with timed workers running alone:

```sh
python3 experiments/compare_cnf_proof_choice.py /tmp/cnf-proof-choice
python3 experiments/validate_cnf_proof_choice.py /tmp/cnf-proof-choice
python3 experiments/analyze_cnf_proof_choice.py /tmp/cnf-proof-choice
```

The protocol binds 390 runtime sources and the 19,091-key starting union.
Selection excludes 1,920 prior sidecar decisions and cached roots. Three balanced
fresh-process triples compare legacy, causal and combined policies on 192 new
neighbours, each visited twice. The combined index contains 383 retained entries
and references both immutable histories of 389 distinct sources. Both complete
lineages are audited on the same frozen snapshot. New support discovery and
historical cold construction are outside this comparison; all their previous
costs and artifacts remain retained.

The combined policy checks ready roots first and uses legacy-first fallback.
Canonical roots, ordinary negative proofs, exact clause containment, matching
materializers and current-query guards remain required. An index description is
not a certificate. Independent replay reconstructs selection from available keys
before each query, in addition to checking every final proof and result.

All modes answer 102 SAT / 90 UNSAT. Combined and causal expand 35 nodes versus
56 for legacy; four extra targets account for the difference. No repeated visit
adds rows. Combined chooses 25 ready proofs and five materializations. Remaining
35 expansions are all negative, on seven cases. Broader cross-guard coverage,
incremental acquisition and unrestricted polynomial bounds remain open.

Mean complete seconds are 13.45278 / 12.42048 / 11.08200. Combined improves the
mean against both baselines but regresses in one pair against each. Peak RSS is
597,961,387 bytes, 5.53% above causal and 16.55% above legacy, with all paired
increases; allocation cause is untraced. Full cold replay and compression cost
43.69% / 31.96% of combined runtime. All preparation, checks, derivation,
persistence, replay, compression and final digest/report generation are charged;
imports, initial CLI reads and final wrapper rewrite are excluded. Selection
and historical acquisition are separately charged. Ready-first is a heuristic,
not a minimum-cost proof selection guarantee.

## Validation and retained authority

Independent validation passes **502 tests**, nine complete archive checks /
**3,456 trial query replays**, every union node, **2,189 inherited decisions** and
all 192 new decisions, with fresh validation search disabled. Every combined
selection is reconstructed from the archive's append history before that query.
The union retains **19,543 keys / 60,649,472 SQLite / 4,567,169 gzip bytes**,
adding 452 keys while preserving every earlier payload. All **38 alternate
certificate occurrences** remain in trial archives. New decisions have
**149 direct roots / 43 negative guards**.

Resume `experiments/results/cnf-proof-choice/checkpoint.json`. It preserves
all prior semantic fields and adds `proof_choice_study`, `proof_choice_decisions`
and `proof_choice_portfolio`. The composite references the original immutable
legacy and causal banks. Their union readiness is **129/78** and **60/116**
(ready/pending); the original 170-entry frontier has **125/45**. All three
complete lineage checks pass. The fixed measured banks still use eight catalogs;
**137 guarded-negative origin records** from the three subsequent catalogs now
remain available for incremental acquisition. These are source records, not a
claim of 137 distinct residual structures.

All prior **386 sources / 4,286 artifacts / 75 manifests** remain unchanged.
Runtime binds 390 sources; the analyzer brings the ledger to 391. Structural
authority stays **2,614 patterns / 259 pairs / 17 missing children**, original
**17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The manuscript builds cleanly to **201 pages** with
**64 unchanged proof blocks**. No new Lean or unrestricted-SAT resource bound.
The full suite retains 24 unclosed-SQLite ResourceWarnings during older tests;
10 focused new tests emit none with warnings enabled. Their allocation origins
remain untraced.

Checkpoint SHA-256: `dc35b10ea9a53856e6d1b906aac4d629cf247bdc60c888f1ea01f56b8fc714fa`.
Report SHA-256: `4dfdbc24d4b76325aaf98ce14231849ee1f18ad6a84a66dc50d190ef15d2b228`.

The new manifest binds **59 artifacts**. The next preservation audit inherits
**4345 artifacts / 76 manifests**.
