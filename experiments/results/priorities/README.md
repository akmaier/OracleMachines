# Seven-priority implementation study

This study records commit `a62bf5c` and the source/binary fingerprints in
`metadata.json`. Eight modes, two streams and three sequential rotating repeats
give 48 runs and 1,152 planned queries. All were attempted: **1,047 correct answers,
141 of them UNSAT, and 105 explicit resource-limit failures**. There are no wrong
answers or missing queries. Of the correct answers, 903 (114 UNSAT) use the checked
service; 144 (27 UNSAT) use the direct, unverified CNF reference.

## Selection and comparison

The chronological stream contains 32 fresh signed-unit formulas (seed 1710) and
eight public random-3-SAT formulas at the workload shift. The public inputs are
lexicographic members 6:10 of each `uf50-218` and `uuf50-218` archive; previous
project studies used 0:6. The first eight unit formulas form the initial training
segment; online updates after every checked answer remain charged. Eight public
formulas follow unit 24, then the final eight units return to the earlier pattern.

The application stream uses previously unmeasured `ssa2670-141`, `ssa7552-159`,
`ssa7552-160`, `towers05` horizons 12, 13 and 38, and `unsat300cubes` horizons 0 and 1.
The circuit labels come from the [SATLIB circuit-fault table](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/BF/descr.html).
The incremental inputs and labels come from the [TACAS 2026 artifact](https://zenodo.org/records/18330441).
Selection and full inputs were frozen before timing. The three application SAT
cases include the final Towers horizon. Source hashes and all needed prior
increments are recorded. These members were unused in older project studies;
the final run repeats the preserved follow-up pilot after a harness correction,
so it is not a second blind development holdout.

All seven service modes use the same source formulas, checked acceptance boundary,
three-second query deadline, 64 MiB logical SQLite cap, 8 MiB encoded-input cap
and 16 MiB proof limit. Exact-input reuse is disabled in every mode. Setup,
conversion, verification, archive writes and training are charged. The polarity
baseline proposes each variable's more frequent syntactic sign, with no learned
weights; every proposal is checked. Live/restarted proof modes differ in whether
the worker survives the next query, while both preserve the database. Direct
uses normalized original CNF without the service's certification/archive costs.

| Mode | Chronological median ms | Completed | Application median ms | Completed |
| --- | ---: | ---: | ---: | ---: |
| Direct CNF reference | 163.24 | 120/120 | 3656.86 | 24/24 |
| Checked | 458.58 | 120/120 | 6034.49 | 9/24 |
| Portfolio | 2850.59 | 120/120 | 7737.82 | 9/24 |
| Learned | 649.47 | 120/120 | 7778.52 | 9/24 |
| Polarity heuristic | 263.01 | 120/120 | 7398.72 | 9/24 |
| Live proof | 762.92 | 120/120 | 12285.01 | 9/24 |
| Restarted proof | 4547.90 | 120/120 | 16058.84 | 9/24 |
| Adaptive | 446.86 | 120/120 | 6188.64 | 9/24 |

These are medians of three full-stream elapsed totals, including failed attempts.
Every chronological service query completes. Application methods complete different
subsets, so their charged times are **not rankings for equivalent completed work**.
The direct-reference column has a different acceptance boundary throughout.

## What changed and what did not

The polarity heuristic accepts all 32 novel signed-unit queries per repetition;
the learner accepts 30. Across three repetitions, their accepted counts are 96
and 90. Neither accepts a public-shift proposal or an application proposal.
The heuristic is faster than checked mode on this synthetic distribution, while
the learner is slower. The earlier unit-stream result therefore does not establish
a benefit specific to learning. Portfolio attempts remain costly even with the
new reserved budget: 24 chronological attempts end at that budget across the
three repeats. Budgeting bounds speculation; it does not make that policy optimal.

The application failures comprise 39 archive-cap failures, 21 encoded-input
rejections, 30 proof-size failures and 15 query deadlines. The final Towers SAT
horizon needs 181,707,058 bytes in the unary formula encoding, exceeding the
8 MiB input cap, and is retained as a failure in every service run. It is solved
by the direct CNF reference. This exposes a representation/service limit, not a
complexity lower bound or an UNSAT conclusion.

## Structural diagnostics

The separate `diagnostics.json.gz` contains 30 records and 69 correct answers,
including 36 UNSAT. It is not part of the full-formula timing comparison.

- Distinct width-four relations (seed 1711), lengths 256 and 1,024, three repeats:
  initial registration needs 511/2,047 native nodes; an adversarial replacement
  by the empty relation needs 9/11; an unchanged query needs zero. The native cell
  cap is exactly the live working-set size. Older entries are evicted without
  discarding the live closure. Restart replays the requested closure.
- XOR-to-equality edits at 16, 64 and 320 edges establish one semantic equality,
  acquire two combination rows and rebind 16/64/320 successor projections.
  Evidence still changes in 17/65/321 buckets. Contradictory endpoints and deletion
  of a necessary assumption are checked. Native row acquisition for the equal
  edit is five at each length; this excludes provenance and whole-context work.
- Checked source compilation at 16, 64 and 256 edges records two compilation
  passes and 64/256/1,024 relation cells per pass. These diagnostic sources are
  UNSAT; the regression suite additionally compares mixed-label random sources
  against exhaustive independent truth tables and rejects forged bindings.

Tests cover a 320-edge dependency stack without the old depth-256 fallback,
late routing failures, telemetry-write failure, proposal budget reservation,
working-set refusal, old branches, corrupted data and restart. **129 tests pass**.
Lean audits **2,090 declarations / 1,047 theorem declarations**, with no admits
or added axioms. This does not prove the complete service or compiled runtime.

## Resources, telemetry and preserved evidence

The scratch watchdog observed at most 84.26 MiB. **Process-tree RSS was unavailable**:
all 9,655 process reads failed, with zero valid RSS samples. Consequently the RSS
watchdog provides no usable evidence in this run. In derived records, missing
RSS is `null`, not zero. The maximum observer interval was 32.80 ms. The data
establish neither a hard total-memory bound nor a measured process-tree RSS peak.
The logical archive cap and native cell cap have their separately stated meanings.

The [pilot](../priorities-pilot/README.md) preserves 24 direct-reference parser
errors caused by passing raw SATLIB trailing delimiters to CaDiCaL. Normalization
was fixed, a regression was added, and every mode was rerun in a fresh database.
No solver parameters or instance selections were tuned in response.

A post-run logging correction clears `last_metrics` before input conversion in
future runs. In this recorded run, 18 preallocation rejections inherited a prior
query's ledger. `runs-original.jsonl.gz` retains the exact original records;
`runs.jsonl.gz` omits only those inapplicable ledgers and marks them, and represents
unavailable RSS as `null`. Outcomes and elapsed measurements are unchanged.
`summary-original.json` retains the original derived table. The validator checks
current runtime fingerprints and reconstructs the recorded harness/regression
versions from commit `a62bf5c`; the two later changes concern only logging and its
test. Run `python3 experiments/validate_priorities.py experiments/results/priorities`
to reproduce those checks and the record normalization.

All 3,905 prior results, 1,161 prior proofs and every other previous database row
are preserved, as are all 93 earlier experiment files. Revalidation adds 355
current-engine results and 129 proofs; all 355 current inputs pass the semantic
audit. The live store contains **4,260 results / 1,290 proofs**. Four expansion
versions and two CNF source bindings were also saved in the live solver and
checked after restart; their identities are in `durable-examples.json`.
The pre-run backup remains under the ignored local cache directory.

`inputs.json.gz`, source manifests, raw/derived logs, diagnostics, test/build logs,
validation, proof-block preservation and database-preservation reports provide
the audit trail. The manuscript retains all 30 prior proof blocks and adds one
restricted source-compilation proposition. Broader decomposition coverage,
whole-service refinement, cost-sensitive gating, proof-size guarantees and hard
total-resource bounds remain open.
