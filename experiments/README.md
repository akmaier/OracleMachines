# Executed reuse and persistence study

This is a deterministic mechanism study of the actual Lean engine and SQLite
service. It compares repeated exhaustive solving, witness reuse, exact caching,
and their combination. It is not a neural-learning or competitive SAT benchmark.

## Reproduce

Build the pinned engine as described in [the formal project](../formal/README.md).
Then run from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
python3 experiments/run_workloads.py --output /tmp/oracle-study-new-run
```

The default study uses widths 2, 4, 8, and 12; six ordered workloads; 32 queries
per stream; and three repetitions in rotating mode order. All variants start
with no answers or witness. Fresh temporary databases isolate the runs; they do
not overwrite the service's persistent database. The checked-in run contains
288 runs and 9,216 correct answers. Core counts agree across repeated runs.
The current environment and binary fingerprint are in
[metadata](results/with-parsing/metadata.json). Choose an unused output directory:
the runner refuses to overwrite saved inputs or results.

The exhaustive solver eagerly generates all assignments before looking for a
witness. Formula evaluation visits both conjunction operands. This intentionally
simple baseline makes core costs explicit; savings relative to it do not imply
savings relative to a modern SAT solver.

## Workloads

The first positive formula requires every variable to be true. A second requires
every variable to be false. Appending pairs of negations creates distinct inputs
without changing the required assignment. UNSAT inputs conjoin a contradictory
literal with the positive formula. The streams test repetitions, transfer,
one workload shift, alternating incompatible witnesses, all-negative queries,
and a mix of positive and negative queries. Their known answers are checked
against every returned result. These deliberately easy syntactic families are
controls, not representative held-out practical instances.

## Current results, including binary parsing

The updated native engine uses the Lean-verified counted parser. `parse_work`
records binary syntax parsing, `core_work` records solver/hybrid operations, and
`counted_work` is their sum. Every core count matches the earlier engine on the
same frozen inputs. All 288 new runs check 9,216 answers. Acquisition occurs
inside each stream; no initial witness or result is supplied for free.

Ratios below compare **parser plus core operations**. Wall times are medians of
three runs, including setup, complete query service, and shutdown.

| Workload (12 variables) | Baseline counted work | Witness / baseline | Cache / baseline | Hybrid / baseline | Baseline total ms | Hybrid total ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Repeated SAT | 14,832,768 | 0.032577 | 0.031252 | 0.031252 | 198.93 | 136.50 |
| Distinct, same witness | 18,907,904 | 0.026185 | 1.000046 | 0.026185 | 223.18 | 141.01 |
| One witness change | 8,951,360 | 0.059270 | 1.000097 | 0.059270 | 175.14 | 140.25 |
| Alternating witnesses | 9,934,160 | 1.000531 | 1.000087 | 1.000531 | 181.31 | 186.34 |
| Distinct UNSAT | 19,433,536 | 1.000003 | 1.000003 | 1.000003 | 227.37 | 229.87 |
| Mixed SAT/UNSAT | 19,170,720 | 0.535378 | 1.000024 | 0.535378 | 225.10 | 187.20 |

On distinct formulas sharing a witness, the hybrid transfers 31 times after one
fallback. Its combined work is 495,109 operations against 18,907,904 for repeated
solving, including 27,776 parser operations in each. Exact caching alone has no
hits. Repeated identical queries avoid 31 parses and solves through the exact
cache. One witness change needs two fallbacks. Alternating incompatible witnesses
and distinct UNSAT formulas incur overhead. The mixed stream preserves the active
witness through UNSAT answers and obtains 15 successful transfers.

The transfer stream's median total time is 141.01 ms against 223.18 ms with the
same front end. This local observation is not a proportional-time interpretation
of operation counts. Tiny instances can lose the benefit to setup and persistence.
Three timing repetitions do not establish a distribution-independent speedup.

The [original run](results/summary.json) and its inputs, raw records, and metadata
remain unchanged. It reported only solver-core counts (parsing still contributed
to elapsed time). The updated records are stored separately under `with-parsing/`.

## What is charged

- **Counted work:** operations in `Parsing.lean`, `CostedSAT.lean`, and
  `Hybrid.lean`; acquisition and witness updates occur inside the stream. Binary
  tokenization and formula assembly are counted. JSON and ASCII conversion are
  covered by elapsed time only.
- **Setup:** compiled-engine fingerprinting and database connection/schema setup.
  All modes pay the same front-end setup, including an empty database for the
  two modes that do not store results. This is a common-front-end comparison,
  not timing against a minimal standalone executable.
- **Service:** native process startup on first use, parsing, JSON communication,
  query execution, exact lookup, checksums, committed database writes, and active
  witness updates. Per-query latencies are retained in the raw records.
- **Shutdown:** native process exit and database close, including final SQLite
  checkpointing. Total time is setup + service + shutdown for each run; medians
  of the separate components need not sum to the median total.
- **Storage:** raw records include final database bytes and the combined input
  and witness payload size. At width 12, persistent databases occupy 20,480 to
  49,152 bytes after close, including SQLite overhead. Empty baseline databases
  occupy 20,480 bytes. These figures exclude transient WAL files and process heap;
  peak memory and energy are not measured. Payloads use ASCII bits, not bit packing.

A cache hit reports zero **parser and core** work because no Lean query runs. It is not a
zero-cost service operation. Instrumentation-counter arithmetic is excluded from
the abstract core but contributes to elapsed time. Engine compilation, Python
interpreter startup, observer statistics, and the experiment runner are excluded
from the elapsed totals. Hardware scheduling,
filesystem cache, and the small repetition count limit timing conclusions.

## Saved evidence and proof boundary

- [Inputs and known labels](results/with-parsing/inputs.json), with a hash per ordered stream.
- [Raw runs](results/with-parsing/workloads.jsonl), including timings, hit counts, storage,
  and engine fingerprints.
- [Summary](results/with-parsing/summary.json), with median timings and core ratios.
- [Metadata](results/with-parsing/metadata.json), including a hash of all raw records.

The binary parser, functional solver, candidate checker, adaptive core accounting,
and exact cache invariant are verified in Lean. SQLite, the Python adapter, JSON
and ASCII conversion, process communication, disk integrity, and compiler/runtime
behavior are outside
the kernel proof. Integration tests cover persistence and corruption behavior.
The uniform resource bound for SAT with no size restriction remains unresolved.
Proved polynomial bounds apply to a fixed variable cap or to a specified
logarithmic relation between variable width and input length. These conditions
do not apply to every SAT instance.
