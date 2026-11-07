# Executed reuse and persistence study

This is a deterministic mechanism study of the actual Lean engine and SQLite
service. It compares repeated exhaustive solving, witness reuse, exact caching,
and their combination. It is not a neural-learning or competitive SAT benchmark.

## Reproduce

Build the pinned engine as described in [the formal project](../formal/README.md).
Then run from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
python3 experiments/run_workloads.py
```

The default study uses widths 2, 4, 8, and 12; six ordered workloads; 32 queries
per stream; and three repetitions in rotating mode order. All variants start
with no answers or witness. Fresh temporary databases isolate the runs; they do
not overwrite the service's persistent database. The checked-in run contains
288 runs and 9,216 correct answers. Core counts agree across repeated runs.
The environment and exact binary fingerprint are in [metadata](results/metadata.json).

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

## Results

Ratios below compare total **core operations**, including first-solve acquisition,
verification, fallback, witness copying, and query control. Wall times are medians
of three runs and include setup, the complete query stream, and shutdown.

| Workload (12 variables) | Baseline core work | Witness / baseline | Cache / baseline | Hybrid / baseline | Baseline total ms | Hybrid total ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Repeated SAT | 14,815,904 | 0.031476 | 0.031252 | 0.031252 | 203.40 | 141.52 |
| Distinct, same witness | 18,880,128 | 0.024753 | 1.000046 | 0.024753 | 229.40 | 146.58 |
| One witness change | 8,921,472 | 0.056118 | 1.000097 | 0.056118 | 181.37 | 143.70 |
| Alternating witnesses | 9,904,272 | 1.000532 | 1.000087 | 1.000532 | 185.69 | 189.06 |
| Distinct UNSAT | 19,404,608 | 1.000003 | 1.000003 | 1.000003 | 228.61 | 234.41 |
| Mixed SAT/UNSAT | 19,142,368 | 0.534690 | 1.000024 | 0.534690 | 230.92 | 193.68 |

On distinct formulas sharing a witness, the hybrid transfers 31 times after one
fallback. It needs 467,333 core operations against 18,880,128 for repeated solving.
An exact cache alone has no hits on that stream. On identical queries, the cache
avoids 31 solver calls. One witness change requires two fallbacks. Alternating
witnesses transfer zero times and incur overhead. Distinct UNSAT formulas also
have no reusable positive certificate and show overhead. The mixed stream retains
the previous witness through UNSAT answers and transfers on 15 later SAT queries.

The 12-variable transfer case also saves elapsed time in these runs. Tiny
instances do not necessarily benefit after persistence and setup costs. Thus,
reduced core work and reduced service time are separate measured claims.
No arbitrary-workload or statistical-generalization claim follows from three
local timing repetitions.

## What is charged

- **Core:** the operations defined in `CostedSAT.lean` and `Hybrid.lean`;
  acquisition is inside the stream, not supplied for free.
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

A cache hit reports zero **core** work because no Lean query runs. It is not a
zero-cost service operation. Instrumentation-counter arithmetic is excluded from
the abstract core but contributes to elapsed time. Engine compilation, Python
interpreter startup, observer statistics, and the experiment runner are excluded
from the elapsed totals. Hardware scheduling,
filesystem cache, and the small repetition count limit timing conclusions.

## Saved evidence and proof boundary

- [Inputs and known labels](results/inputs.json), with a hash per ordered stream.
- [Raw runs](results/workloads.jsonl), including timings, hit counts, storage,
  and engine fingerprints.
- [Summary](results/summary.json), with median timings and core ratios.
- [Metadata](results/metadata.json), including a hash of all raw records.

The functional solver, candidate checker, adaptive core accounting, and exact
cache invariant are verified in Lean. SQLite, the Python adapter, parsing cost,
process communication, disk integrity, and compiler/runtime behavior are outside
the kernel proof. Integration tests cover persistence and corruption behavior.
The uniform unrestricted SAT resource bound remains unresolved; the proved
polynomial core bound fixes the variable cap and has an exponential coefficient.
