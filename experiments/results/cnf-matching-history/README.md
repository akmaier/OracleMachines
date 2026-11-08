# Retained matching state and checked alternating changes

`MatchingRepairHistory` removes all **80 matching fallbacks** in the previous
coordinated-change diagnostic. Across the expanded 37-case matrix it avoids 161
fallback acquisitions while preserving the earlier scalar/equivalence paths.
At 32 blocks of eight choices, acquisition/update time falls from **8.30345 to
0.25308 seconds**, and logical payload from **20,331,832 to 424,089 bytes**.
These are matched synthetic samples, not a competitive incremental-SAT benchmark.

## Structure, maintenance and checking

Recognition runs lazily after the scalar/equivalence proposals fail. It checks
the whole normalized base for disjoint positive choice clauses and complete,
disjoint negative exclusion cliques. This adapter requires every indicator to
belong to a choice and exactly one indicator for each represented choice/resource
pair; parallel indicators and unused negative-only variables are rejected. Exact
source records retain duplicates and tautologies even though discovery ignores
them. Variable names are preserved in the graph binding.

The retained view maps each choice to its selected indicator and each resource
to its owner. A third persistent trie tracks unit-constrained indicators.
Earlier additions are replayed when the view is first requested. Later versions
share unchanged paths and update only changed endpoints and added unit pins.
Choice/resource changes are applied together before validating the view. A valid
SAT model can have several true indicators in one choice when resources are
spare; such a model invalidates this optional matching view, not the SAT verdict.
A lazy reconstruction can recover a later exact matching model; cached invalid
views otherwise conservatively reject matching proposals.

For a positive request, search forces the requested edge and redirects its
displaced owner. For a negative request, it finds a replacement for the selected
edge. Breadth-first search follows alternating ownership until reaching a free
resource or the starting choice's released resource. Unit pins prevent both
removing forced edges and adding forbidden edges. Each path becomes an ordinary
`append-joint` variable list. The inherited checker independently verifies every
affected original or added clause and the new clause; graph claims are never
trusted. The prior `EquivalenceRepairHistory` reader can check the resulting
archives without knowing the matching adapter.

This is established matching machinery. In particular, [Régin (1994), pp.
364–366](https://cdn.aaai.org/AAAI/1994/AAAI94-055.pdf) uses alternating paths and
cycles and retains a known matching when propagating edge deletions. Our experiment
adds persistent source-bound proposals and full affected-clause checking; it
does not claim a new matching algorithm or implement Régin's complete filtering.
The existing Lean joint-preservation/extension lemmas support the final semantic
check. No new proof of the Python graph, matching-state or SQLite code is asserted.

## Matched costs

The comparator is the preceding equivalence-repair implementation. Each timed
acquisition/update includes recognition, state construction/maintenance, failed
proposals, checking, serialization, persistence and any materialized fallback.
DB initialization, warm/cold queries and cold resumed updates are separate.
Input assembly, inter-operation validation, offline compression and archive audits
are outside acquisition timing. Exact recipes and source fingerprints are retained.

| Case | Fallbacks before / after | Seconds before / after | Logical bytes before / after |
| --- | ---: | ---: | ---: |
| 32 blocks, 2 choices | 32 / 0 | 0.14695 / 0.01411 | 245,911 / 8,335 |
| 32 blocks, 4 choices | 32 / 0 | 0.92416 / 0.04882 | 2,267,324 / 50,257 |
| 8 blocks, 8 choices | 8 / 0 | 0.47466 / 0.05235 | 1,210,730 / 95,146 |
| 32 blocks, 8 choices | 32 / 0 | 8.30345 / 0.25308 | 20,331,832 / 424,089 |
| 4 blocks, 16 choices | 4 / 0 | 1.06571 / 0.19466 | 2,682,814 / 386,840 |
| 32 forbidden edges, 4 choices/block | 32 / 0 | 0.95851 / 0.03804 | 2,343,474 / 50,289 |
| One 64-choice alternating cycle | 1 / 0 | 0.00969 / 0.00566 | 11,440 / 6,144 |

For 32 four-choice blocks, bases fall from 33 to one and SQLite from 3,973,120 to
110,592 bytes. A separate allocation run measures peak traced Python memory of
24,840,875 versus 1,192,534 bytes. Tracing excludes native SQLite allocations and
process RSS. Compatible matching updates retain almost identical peaks, 876,369
versus 876,513 bytes, because no matching view is built. The previous protected
scalar workload likewise builds no matching graph and retains its earlier gains.

The last four-choice update scans two graph edges and changes two choices / four
indicators. Discovery and independent checking each visit 16 postings; eight old
counts change. Including matching-state maintenance, it allocates 182 trie nodes.
It scans no base, reconstructs no history or matching, and invokes no solver.
At eight choices the corresponding four-variable move visits 32 postings in each
pass and allocates 439 nodes. A 64-choice cycle changes 128 indicators and visits
256 postings per pass: the affected structure can be global even for one unit.

Cold final query for 32 four-choice blocks increases from 17.93 to 20.25 ms; the
first repeated last update after restart drops from 40.03 to 23.46 ms, including
fresh graph/state reconstruction. Both archives already contain this update's
result. At eight choices, final replay is 157.19 versus 168.12 ms, and resumed
update 355.27 versus 187.86 ms. Cold final checking does not need the graph view.
Preparation now dominates the successful growing case: 206.58 of 253.08 ms at
32 eight-choice blocks is initial acquisition, before any matching discovery.

## Retained misses and limitations

- Search tests only the first path found for each literal. A three-choice control
  with an earlier `(-2 OR -4)` rejects its chosen swap although a longer cycle
  satisfies the full source. Replacing that coupling with the unit `(-4)` guides
  search to the longer path successfully. Failure is not an UNSAT proof.
- A disjoint equivalence component added to the base makes whole-base matching
  recognition fail. Component-local extraction is still missing.
- Extra true indicators can invalidate the exact matching view. The control
  with choices `(1 OR 2)`, `(3 OR 4)` and exclusion `(-2 OR -3)`, followed by
  `(1)` and `(3)`, remains SAT but requires fallback. Valid model reuse is broader
  than reuse within a one-edge-per-choice representation.
- A small proposal budget rejects safely; a genuine resource conflict needs a
  newly checked UNSAT base. New graph structure introduced by additions is not
  recognized. Base additions cannot invalidate old constraints, but they can
  prevent every available path or move the formula outside the matching class.
- Parity histories still reacquire 33 bases. A 1,024-variable equivalence block
  still exceeds the default joint budget and takes roughly 0.8 s with fallback.
  Those losses remain alongside duplicated state on genuine fallback.
- Graph state is only an optional proposal accelerator. Recognition, matching
  reconstruction, sorting, integer and trie operations, all earlier candidate
  work, full affected-clause checking and durable move lists remain charged.

## Verification and reproduction

All 261 solver tests pass. The new tests cover 400 branching unit histories
against every permutation model of the three-choice square instance, exact
clause-count and matching-index reconstruction, long cycles, free resources,
pins, non-unit couplings, invalid views, duplicates, budgets, old versions and
legacy-reader/cold-resume compatibility. The earlier joint-record forgery tests
remain in the full suite.

The 37 cases retain 74 archives and 1,636 acquisition/query/resumption results.
All 1,414 historical versions and 608 residuals cold-check with unchanged bytes.
Another 58 prior archives (1,396 versions / 1,367 residuals) replay unchanged.
No cold audit expands new residuals. `report.json` retains failures and detailed
counters; `summary.json` aggregates its acquisition totals and storage figures.

```sh
python3 experiments/compare_cnf_matching_history.py --output /tmp/oracle-matching-new
python3 -m unittest solver.test_cnf_matching_history -v
```

Use a fresh output directory. This Python prototype is separate from the native
restricted engines. The results supply no uniform polynomial expansion or
acquisition bound for arbitrary CNF.
