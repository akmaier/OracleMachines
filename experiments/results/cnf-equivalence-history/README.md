# Checked simultaneous repair for explicit equivalence blocks

The matched comparison removes all **120 unsigned-chain** and **32 signed-chain**
fallback acquisitions. The largest chain history reduces acquisition/update time
from **2.4689 s to 0.06676 s**, logical archive payload from **3,792,631 to 98,663
bytes**, and peak traced Python allocations from **45,575,163 to 1,925,402 bytes**.
These are synthetic single-run measurements, not general SAT performance bounds.

## What changed

`EquivalenceRepairHistory` first tries the existing affected-clause scalar repair.
On failure, it lazily recognizes connected variable blocks from complementary
binary clause pairs in the exact base. For example, `(-x OR y)` and `(x OR -y)`
force equality; `(x OR y)` and `(-x OR -y)` force inequality. Complementing all
variables in a connected block preserves these pairs, including mixed signs.
Recognition uses union-find and runs once per recognized base in a warm session.
It is unnecessary on compatible additions or successful scalar repairs.

The proposal is only a candidate. A generic `append-joint` record supplies the
new clause and a sorted, distinct list of variables to complement. Its checker
reconstructs the full parent occurrence/count indexes, aggregates all changes
to each affected clause's count, and accepts only if every count remains positive
and the new clause holds. Earlier additions and external couplings are included.
Internal zero-net count changes require no count-map writes. Intermediate scalar
states need not be valid. No serialized block, count or affected-clause list is
trusted. Older versions retain their models and roots.

Lean proves the semantic joint preservation and extension rules. It does not
verify Python discovery, count/index maintenance, integer parsing or SQLite.

## Matched results

Both modes receive identical exact sources and additions. Timing includes base
acquisition, lazy discovery, candidate failure, independent checking, state
maintenance, JSON/SQL persistence and any full-source fallback. Optional witness
exports, diagnostics, offline compression, row digests and archive audits are
outside acquisition timing. DB initialization and cold/warm queries are separate.

| Case | Baseline / joint fallbacks | Baseline / joint seconds | Baseline / joint logical bytes |
| --- | ---: | ---: | ---: |
| 32 equivalence blocks, width 2 | 32 / 0 | 0.10142 / 0.01041 | 127,127 / 5,249 |
| 32 equivalence blocks, width 8 | 32 / 0 | 0.41601 / 0.02110 | 824,739 / 23,132 |
| 32 equivalence blocks, width 32 | 32 / 0 | 2.46892 / 0.06676 | 3,792,631 / 98,663 |
| 32 signed-equivalence blocks, width 8 | 32 / 0 | 0.48960 / 0.02153 | 822,755 / 23,004 |
| Coupled blocks with repeated changes | 2 / 0 | 0.00318 / 0.00157 | 1,252 / 558 |
| One block, width 256 | 1 / 0 | 0.06349 / 0.01374 | 44,768 / 23,448 |
| One block, width 1,024, default budget | 1 / 1 | 0.78859 / 0.78141 | 189,168 / 189,168 |
| 32 parity blocks, width 3 | 32 / 32 | 0.18276 / 0.17662 | 326,256 / 326,256 |
| 32 matching blocks, 4 choices each | 32 / 32 | 0.93411 / 1.00234 | 2,267,324 / 2,267,324 |

For the largest chain case, SQLite shrinks from 6,668,288 to 204,800 bytes and
retained bases from 33 to one. The last joint update visits 32 variables and 124
postings in discovery, then independently visits them again during checking.
It allocates 342 trie nodes, changes no old clause counts and invokes no residual
solver. This is still work proportional to the block, not constant-time repair.

Preparation is comparable (47.42 versus 45.55 ms), since block discovery is lazy.
Cold final query increases from 40.88 to 44.42 ms. Repeating the last known update
from its parent in a fresh engine takes 88.32 versus 45.98 ms, including resumed
recognition; the archive already contains the result in both modes. This is a
restart/reuse measurement, not a new cold solve. All cold queries and resumed
updates expand zero new residuals.

Separate `tracemalloc` reruns exclude native SQLite allocations and process RSS.
Compatible additions retain almost identical peak allocations (414,997 versus
415,069 bytes), as does the previous protected-matching control (2,682,446 versus
2,682,518 bytes). The new lazy recognizer adds only its empty dictionary on these
paths; the underlying affected-clause indexes remain eager. Matching failures
retain about 24.84 MB of traced allocations in either mode.

## Limits, losses and next target

- Matching and parity moves are still undiscovered. In the largest matching
  control, the new path scans for binary pairs on 32 bases without finding a
  useful proposal; this sample is slower. Small timing reversals in other failed
  controls are not evidence of an optimization when the same work remains.
- Equivalences acquired through deltas and nonpaired implication cycles are not
  recognized. Their controls still fall back. Old base relations remain sound
  under additions, but they are an incomplete proposal set.
- The default 4,096-visit discovery budget counts moved variables and postings
  after scalar attempts. A 1,024-variable block exceeds it. Cold certificate
  checking is independent of discovery budget. Failure supplies no UNSAT verdict.
- A genuine contradiction needs a new UNSAT base. Joint repair avoids only the
  preceding satisfiable acquisition in that control.
- Assignment entries and internal postings are still visited individually.
  Repeated block moves store repeated variable lists; group references and
  boundary-only checks require further representation and proof work.
- After fallback, complete sources and base state are still duplicated.
  **Next target:** retain/discover matching structure and propose alternating
  changes through the joint checker. The current 4-choice control retains 33
  bases and 2.27 MB, making it the largest remaining multi-update loss here.

The [initial run](../cnf-equivalence-history-initial/README.md) is preserved. Its
signed additions were accidentally already compatible; the corrected run checks
that each signed addition fails the current model before timing the operation.
Do not pool the runs' timings. The first 12 recipes come unchanged from the
earlier coordinated-change diagnostic.

## Verification and reproduction

The 23 cases retain 46 archives and 1,282 acquisition/query/resumption results.
Their 1,144 historical versions and 869 residuals replay independently with
unchanged database bytes. A further 82 earlier archives, containing 7,342 versions
and 1,782 residuals, replay unchanged through the new reader. The solver test suite
passes 255 tests, including random branching histories, exact count/posting
recomputation, signed/coupled changes, budget failures and forged records. The
Lean build and axiom audit pass (4,083 declarations, 1,943 theorem declarations).

```sh
python3 experiments/compare_cnf_equivalence_history.py --output /tmp/oracle-equivalence-new
python3 -m unittest solver.test_cnf_equivalence_history -v
```

Use a fresh output directory. Exact recipes, per-operation counters, failure
records, source fingerprints and allocation profiles are in `report.json`;
`summary.json` aggregates its acquisition times and archive sizes. The comparison
does not bound arbitrary CNF acquisition or establish a uniformly polynomial
expansion procedure.
