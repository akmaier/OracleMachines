# Choose a checked available proof before deriving another support

The combined frontier preserves the causal bank's 30 target transfers while
reducing support materialization **137 -> 57 rows (58.39%)** on 192 new queries.
Total new proof rows fall **351 -> 271 (22.79%)**. This is a reproducible storage
and derivation improvement on this workload. Complete runtime and peak memory
need separate accounting: mean time improves, paired timing signs are mixed,
and peak RSS increases.

## Policy and correctness boundary

`ProofChoiceBank` loads the acquired legacy and causal frontiers. For each
uncached guarded target, it checks contained supports in legacy-then-causal
order and selects the first whose ordinary negative proof is available. If no
matching root is ready, it materializes the first legacy match, or otherwise the
first causal match, using that bank's original extractor. Failed containment
falls through to the unchanged solver. All current-query guards remain checked.

Soundness uses the existing subset rule: a checked unsatisfiable clause subset
makes the target unsatisfiable. The ready probe checks the actual canonical root
and negative proof; a saved description alone never certifies an answer. A
pending description must reproduce its advertised root through the matching
checked materializer. Cofactor UNSAT still needs the full query's guard. No
whole-query result is inferred from child identity alone.

The policy searches both retained frontiers, preserving their syntactic match
coverage. It is a heuristic, not a minimum-cost algorithm. Checking an already
stored proof can be expensive; a different pending proof might be cheaper to
derive. Legacy-first fallback is not optimal, and earlier choices can change
later sharing. Ready status is checked against the current archive, never saved
as an unchecked validity flag.

The composite stores 383 retained entries and references both immutable index
histories: 421 raw-core references and 778 origin references correspond to only
**389 distinct acquired sources**. These references avoid copying full historical
metadata into another sidecar; they do not remove the original artifacts. The
complete frozen proof/query audit is followed by both full lineage audits on
the same pinned read-only snapshot. An unused corrupted origin still rejects.

For K entries and total retained clause volume L across both banks,
constructor space is O(K + L), in addition to descriptions, proof-check caches and the archive. A miss
scans both banks. A hit pays containment and canonicalization for candidates
visited, ordinary checking for each matched root probed, and possibly a second
scan plus materialization. The observed ready-first advantage does not bound
these costs polynomially for every growing family of arbitrary CNFs.

## Matched fresh-query experiment

Run the producer, validator and analyzer in a new directory:

```sh
python3 experiments/compare_cnf_proof_choice.py /tmp/cnf-proof-choice
python3 experiments/validate_cnf_proof_choice.py /tmp/cnf-proof-choice
python3 experiments/analyze_cnf_proof_choice.py /tmp/cnf-proof-choice
```

Each mode starts from the same **19,091-key union**. Selection excludes 1,920
prior sidecar answers and cached whole-query roots, then takes the next 64
neighbours per template, interleaved. Selection costs 1.69644 seconds separately.
Three balanced fresh-process triples visit each query twice. No tests, builds or
profilers overlap timed workers. Historical acquisition remains separately
charged. All modes load the same acquired eight-catalog, 389-origin history;
the two newer catalogs' 94 guarded negative outcomes are not added to discovery.

| Measure | Legacy | Causal | Combined |
| --- | ---: | ---: | ---: |
| Retained entries | 207 | 176 | 383 |
| Cofactor transfers | 26 | 30 | 30 |
| Fresh expansions | 56 | 35 | 35 |
| Split nodes | 16 | 11 | 11 |
| Materialization rows | 85 | 137 | 57 |
| Total new rows | 316 | 351 | 271 |
| Mean query seconds | 1.90344 | 1.52964 | 1.51620 |
| Mean complete seconds | 13.45278 | 12.42048 | 11.08200 |
| Mean peak RSS, bytes | 513,032,192 | 566,635,179 | 597,961,387 |
| Final SQLite bytes | 60,624,896 | 60,600,320 | 60,534,784 |
| Gzip plus first-trial raw sidecars, bytes | 12,752,455 | 12,261,039 | 11,727,695 |

All modes answer **102 SAT / 90 UNSAT**. Repeated visits add no rows. Four
additional causal/combined hits account for the 21 saved expansions against
legacy; no query regresses in expansion count. All transfers still share their
first origin's guard. This remains a constructed neighbouring workload, not a
blind sample establishing arbitrary-SAT coverage.

The combined policy selects 25 ready proofs (21 legacy, four causal) and makes
five materializations (four legacy, one causal). Its readiness scan visits 7,445
candidates, charges 224,718 candidate-clause containment units and reads 45
matching roots. On the 26 targets all modes cover, materialization rows are
**85 / 121 / 41**. Four additional hits require 16 further combined
materialization rows. The 80-row saving against causal-only reuse therefore
comes from overlapping targets; it is not the previous stream's post-hoc
41-row estimate carried forward.

Mean complete time falls **10.78% against causal** and **17.62% against legacy**,
but each comparison has one regression among three pairs. Against causal the
paired changes are -15.05%, -17.85%, +3.28%; against legacy +2.06%, -28.03%,
-21.43%. Preserve that variability; three runs do not establish a stable speedup.
Query time differs only -0.88% against causal. Combined lineage checking costs
0.53090 seconds versus 0.38002 for causal: checking both histories is charged.
Complete time includes restoration, preparation, lookup, checking, derivation,
persistence, full cold replay, compression and final digest/report generation.
Imports, initial CLI reads and the final wrapper rewrite are excluded.

Combined peak RSS rises **5.53% against causal / 16.55% against legacy**, in all
three pairs. Keeping both indices adds live state, but the measured allocation
cause has not been traced. The smaller proof-row delta barely changes the full
SQLite file (-0.11% versus causal). Gzip plus sidecars falls 4.35%, while all
historical artifacts, nine trials and the union remain additional retained data.
No general memory improvement follows from fewer materialization rows.

## Next investigation

Complete cold replay and compression consume **43.69% / 31.96%** of combined
time. Both-lineage checking is only part of cold replay, so removing one small
check cannot explain away this dominant cost. Keep full checks until an equally
strong, measured replacement exists. The combined policy remains an explicit
option because it trades extra live memory for fewer new proof rows.

For broader discovery, all **35 remaining expansions are negative**. Current
cases **46 / 48** require seven each, case **27** six, cases **7 / 101 / 156**
four each, and case **86** three. Templates 6/8/12 contribute 17/11/7. These
current-stream IDs are not the original structural cases. The next coverage
experiment should acquire causal supports incrementally from the preserved
new guarded negatives and compare these seven residual structures, including
changes of guard. Charge acquisition and both live-state and complete replay
costs; do not repeatedly rebuild the unchanged historical frontier.

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
