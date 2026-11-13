# Later lookahead on retained learned formulas

This study starts from the two exhausted selected leaves in `cnf-target-probe`.
It checks saved pairs, complete binary reachability and single-assumption
exhaustion, then derives at most 16 source-justified clauses. A clear initial
four-variable augmented pass can continue through at most eight later blocks.
Controls probe the original source using exactly the same variable order.
Target recognition has one 32-state budget per source.

- `report.json`: parent hash, implementation fingerprints, counters, timings,
  coverage, admission outcomes and reference bindings.
- `learning-bases.json.gz`: the two complete source-bound learning records.
- `continuations.json.gz`: every later block, including inconclusive prefixes.
  Each block references its full base by a digest; base evidence is stored once.
- `diagnostics.json.gz`: pair/graph misses, source exhaustion certificates,
  same-order controls, augmented exhaustion where reached, and remaining leaves.
- `proof-delta.sqlite3.gz`: additive eight-table history changes.
- `coverage.json.gz`: finite original-level structural coverage witness.
- `reference.sqlite3.gz`: independent successful source/target and gained-original
  proofs; SAT model transport is checked against each complete source.
- `validation.json`, `full-validation.txt`: standalone cold replay and full tests.
- `pilot/`: preliminary scans and later-block controls. The initial test-fixture
  failure is retained: canonical names are tuples before JSON serialization and
  lists after it. Tests now compare canonical encoding and mutate a copied list.

Run tests and timing sequentially from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' > /tmp/frontier-learning-tests.log 2>&1
python3 experiments/compare_cnf_frontier_learning.py experiments/results/NEW
python3 experiments/validate_cnf_frontier_learning.py experiments/results/NEW --test-log /tmp/frontier-learning-tests.log
```

Restore with `compare_cnf_frontier_learning.restore_checkpoint`. It returns the
report, paired rewrites, all learning bases, and learned continuation blocks.
Pass all three evidence lists to `ContinuedLearningRoutes`. Older loaders omit
these additional alternatives. For later probing, `LearningBlocks.advance`
reuses checked prefixes, resumes successful targets without rediscovery, and
returns no new block when the augmented ranking is exhausted. The experiment
runner itself fixes its input to the parent study; use the restoration API to
start a subsequent study rather than rerunning the same input.

These are reused development residuals, including a pilot, not independent
holdouts. Same-variable controls test propagation strength, not competitive
end-to-end performance. State caps do not bound state bytes or peak RAM. Clear
probes and absence of graph consequences decide neither SAT nor UNSAT.

Coverage increases **46/83 -> 47/83**, with case 32 independently proved SAT and
all 47 still covered without growth-exception routes. The 23-variable source
closes after a later forced block and 17 target states. The 39-variable source
remains open and has an exact single-assumption exhaustion certificate even
with its six added clauses. All same-variable original-source controls remain
clear. Nine later blocks, including eight inconclusive ones, are retained.

Full accounting and the next target:
[frontier-learning-continuation.md](../../../research/frontier-learning-continuation.md).

All **573 tests and independent cold replay pass**. The acquisition/validation
pipeline takes 256.47 seconds; standalone validation adds 71.67 seconds. Cold
checking dominates. SQLite grows 212,992 bytes; the node delta compresses to
11,813 bytes. `acquisition.log` retains the run's console output. No peak-RAM or
whole-solver speedup claim is made.
