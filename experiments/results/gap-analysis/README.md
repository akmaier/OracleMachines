# Post-implementation diagnostics

Review target: `ee3ba62`. These diagnostics use fresh temporary databases and
leave the live archive and earlier datasets unchanged. They measure operation
counts and reanalyse existing timings; they are not a new performance benchmark.

- `semantic.json`: changing the first XOR to equality in a 16-edge chain leaves
  the first projected table `[true,true]` unchanged, yet all 17 buckets recompute.
- `replay.json`: at width four, 256 distinct edges produce 511 native nodes,
  exceeding the reset threshold of 187. Both a one-edge update and a subsequent
  unchanged query replay 511 definitions. Width three is a control: nine
  definitions for the edit and zero for the unchanged query.
- `routing.json`: injecting a storage-accounting failure after one solved query
  records both success and failure for the same route. This is a synthetic
  late-failure test, not a naturally occurring benchmark failure.
- `phases.json`: medians of per-run phase totals from the immutable structured
  study. Portfolio `native_prepare` is 10,806.82 ms versus 52.23 ms for checked.
  This phase combines proposal checking and other preparation; it does not
  isolate the cost of each individual candidate or certificate.
- `metadata.json`: source commit, seed and source/binary fingerprints. The
  routing diagnostic was added after the initial two reproductions; both script
  fingerprints are retained.

All solver answers in the semantic/replay diagnostics are SAT and correct.
The replay generator ensures this by allowing the zero-state path in every
relation. The semantic test reads both complete two-entry projected tables.
These results expose lost reuse and measurement flaws, not an incorrect SAT
verdict or a counterexample to the mathematical tree theorem.

Reproduce into a fresh directory:

```sh
python3 experiments/analyze_current_gaps.py --output /tmp/oracle-gap-reproduction
```

The detailed interpretation and completion criteria are in
`research/implementation-gaps.md`, under “Post-implementation gap analysis”.
No solver or manuscript changes are included in this analysis.
