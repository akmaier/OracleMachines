# Completing a retained split without repeating its closed branch

On 2026-11-14, resuming the pending true cofactor of case **1445** raises checked
structural coverage from **59/83 to 60/83**, including the view without
growth-exception routes. This is another completed decomposition of a reused
development input, not a new tractability class or a fresh holdout result.

## What was reused and what was reconstructed

The preceding comparison retained a split of a **27-variable, 93-clause,
287-literal** source on local variable **4**. Its false cofactor was already
closed; its true **23 / 70 / 196** cofactor had no completed root record. The
continuation checks and resumes that exact saved split. It does not rerank the
parent or acquire new external probe blocks or split records.

One advance uses **20/32 admissions**, all on the true branch. The closed false
branch uses zero admissions. Four of those twenty identities had been entered
before the previous allowance expired, but had no completed rows. They are
recomputed and charged again. All twenty now have completed records, and no
previously completed identity is admitted again. This distinction prevents
claiming that the interrupted recognizer's entire partial computation was saved.

The true branch follows this chain, in canonical residual coordinates:

| Rule | Variables | Clauses | Literal occurrences |
|---|---:|---:|---:|
| probe | 23 | 70 | 196 |
| probe | 22 | 64 | 180 |
| probe | 21 | 59 | 164 |
| binary paths | 19 | 56 | 158 |
| elimination | 19 | 43 | 114 |
| elimination | 18 | 40 | 106 |
| binary paths | 17 | 39 | 103 |
| elimination | 17 | 38 | 100 |
| binary paths | 16 | 36 | 98 |
| elimination | 16 | 34 | 90 |
| elimination | 15 | 33 | 88 |
| probe | 14 | 32 | 86 |
| elimination | 12 | 28 | 76 |
| binary paths | 11 | 25 | 69 |
| elimination | 11 | 24 | 65 |
| elimination | 10 | 21 | 57 |
| elimination | 9 | 18 | 50 |
| elimination | 8 | 14 | 39 |
| polarity transformation | 7 | 9 | 22 |
| recognized family | 7 | 9 | 22 |

There are four probe reductions, four binary-path deletions, ten eliminations,
one polarity transformation and one family terminal. The terminal is **Horn and
zero-valid, not 2-CNF**. Both children of the saved split therefore now have Horn
routes, reaching six and seven variables respectively. This continues the
observed interaction between restriction, implication-based deletion, bounded
elimination and polarity changes. These operations need not expose such a short
chain on an arbitrary CNF.

All sixteen retained split sources are closed, with no pending or open retained
leaf. This is not global completion: **23 original inputs remain uncovered**.
The completed original is index 74 / case 1445, with 48 variables, 204 clauses and
612 literal occurrences. Its independent saved reference result is SAT.

## Charged costs

| Operation | Seconds |
|---|---:|
| Restore accumulated authority | 36.84684 |
| Initial complete routes | 6.91416 |
| Initial full coverage-index audit | 59.49625 |
| Select retained obligation | 0.01473 |
| Resume and acquire true branch | 0.05998 |
| Refresh complete routes | 0.98680 |
| Full warm composition and original proof checking | 0.12095 |
| Incremental warm composition and original proof checking | 0.04477 |
| Export additive delta | 5.28912 |
| Cold check new delta records | 0.02210 |
| Cold check expanded positive proof | 3.24254 |
| Whole producer pipeline, including both warm controls and persistence | 127.60236 |

Initial reconstruction and preparation total **103.25725 seconds**. Warm route
refresh still exceeds acquisition by about sixteen times. The two composition
methods agree on all 83 flags in both views. Incremental maintenance checks six
option sources across the two graphs and propagates 142 newly justified nodes;
full recomposition visits 25,659 sources. These are one matched update, with full
composition first, not a stable speedup estimate. No peak-RAM measurement is made.

The additive archive contains **20 patterns and no new external probe records**:
**11,805 compressed bytes / 327,680 SQLite bytes**. Full SQLite grows by
**249,856 bytes**, from 771,342,336 to **771,592,192 bytes**, retaining all
**41,815** older patterns and adding twenty. The positive proof grows from 2,828
to **2,948 steps**. The reference archive retains all 2,115 earlier nodes and now
has **2,135**, including the checked original result. Cached key and JSON payloads
reported by the producer are serialized payload counts, not Python heap or peak
resident memory.

## Validation and next obligation

The independent validator disables fresh structural recognition, reconstructs the
checkpoint, checks the exact resumed split and admission identities, and recomputes
all original coverage flags and the next selection from complete routes. It also
replays every saved reference node, checks both branch answers without reference
expansion, and lifts their models back to the split source. The producer checks
new records, the expanded positive proof, conflict-free reconstruction, idempotent
merge and unchanged prior rows. All **181 relevant tests pass**. Independent
reconstruction and full cold checking take **105.82498 seconds**, including
**63.60740 seconds** for complete route preparation and coverage checking.
All **229 artifacts** in eleven preceding manifests are unchanged. The manuscript
builds to 153 pages with all 64 existing proof blocks unchanged and no overfull
boxes or undefined references. No new core recognition rule or Lean refinement
is introduced.

The next smallest selected original leaf is **34 variables / 148 clauses / 490
literals**, belonging to **case 1304, index 52**. Its next ordinary offset is 12
and only local variable **34** remains in the configured ranked pool. Its key
SHA-256 is `bef0f0de793f31155199f7c6a8dba7819495f90e23de8817a9967edc55880f35`.
Test the saved-pair options and that final ordinary candidate; preserve a failed
recognition attempt as evidence rather than treating this heuristic pool as a
complete SAT classifier. Prefer useful sequences within a retained checked
session to amortize the dominant cold preparation.

A separate persistence gap is now measured: four unfinished states were entered
twice. Persisting checked local reductions before their descendants complete could
avoid that repeated work, but requires a separate pending-obligation format and
checker. An unfinished row must never masquerade as a completed proof. Longer
chains may also exhaust the same allowance repeatedly; this run does not prove
bounded progress or polynomial expansion for all inputs.

Resume `experiments/results/cnf-pending-warm/report.json` through
`experiments.continue_cnf_pending_warm.restore_checkpoint`, retaining evidence
counts **(1, 42, 156, 16, 1)**. The producer is
`python3 experiments/continue_cnf_pending_warm.py OUTPUT --parent REPORT`;
the saved run's independent validator is
`python3 experiments/validate_cnf_pending_warm.py experiments/results/cnf-pending-warm`.
Do not rerun into the preserved output directory or reuse an older graph snapshot
as authority for this newer catalog.
