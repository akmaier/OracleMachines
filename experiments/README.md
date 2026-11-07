# Executed reuse and persistence study

This is a deterministic mechanism study of the actual Lean engine and SQLite
service. It compares lazy solving, the original exhaustive reference, single
witness reuse, exact caching, and persistent witness/refutation portfolios. It is not a neural-learning or competitive SAT benchmark.

## Reproduce

Build the pinned engine as described in [the formal project](../formal/README.md).
Then run from the repository root:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
python3 experiments/run_workloads.py --extended --output /tmp/oracle-study-new-run
```

The extended study uses widths 2, 4, 8, and 12; nine ordered workloads; 32 queries
per stream; and three repetitions in rotating mode order. All five variants
start without stored answers. Fresh temporary databases isolate runs from the
service's persistent database. The saved new run contains 540 runs and 17,280
correct answers; operation counts agree across repetitions. The default without
`--extended` uses the six original workloads. The runner refuses to overwrite
saved inputs or results; choose an unused output directory.

The new lazy solver branches on distinct occurring variables and closes branches
using partial evaluation. The retained `exhaustive` mode eagerly generates all
assignments. Both are small verified mechanisms, not competitive SAT baselines.

## Workloads

The first positive formula requires every variable to be true. A second requires
every variable to be false. Appending pairs of negations creates distinct inputs
without changing the required assignment. UNSAT inputs conjoin a contradictory
literal with the positive formula. The streams test repetitions, transfer,
one workload shift, alternating incompatible witnesses, all-negative queries,
and a mix of positive and negative queries. Their known answers are checked
against every returned result. These deliberately easy syntactic families are
controls, not representative held-out practical instances.

## Current results with lazy search and certificate portfolios

The new run retains the 24 original ordered streams byte for byte and adds
sparse highest-index variables, immediate false conjuncts, and conjunction
extensions of `x0 AND NOT x0`. The eager reference reproduces every historical
baseline operation count. Full inputs, raw records, and all three historical
raw-data hashes remain intact.

| Workload (maximum width 12) | Lazy counted work | Lazy / eager | Hybrid / lazy | Witness hits | Refutation hits | Lazy total ms | Hybrid total ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| repeated sat | 513,280 | 0.034604 | 0.031258 | 0 | 0 | 134.74 | 135.62 |
| distinct same witness | 550,976 | 0.029140 | 0.086452 | 31 | 0 | 136.49 | 141.83 |
| distribution shift | 475,472 | 0.053117 | 0.129650 | 30 | 0 | 139.67 | 145.41 |
| alternating witness | 478,352 | 0.048152 | 0.137023 | 30 | 0 | 140.62 | 146.72 |
| distinct unsat | 543,712 | 0.027978 | 0.425747 | 0 | 31 | 135.12 | 138.55 |
| mixed sat unsat | 547,328 | 0.028550 | 0.282432 | 15 | 15 | 137.13 | 143.59 |
| sparse index | 29,376 | 0.027543 | 0.494656 | 31 | 0 | 134.28 | 139.59 |
| root conflict | 64,224 | 0.003350 | 0.464764 | 0 | 31 | 134.68 | 140.52 |
| unsat extension | 69,760 | 0.003518 | 0.457024 | 0 | 31 | 140.20 | 141.34 |

All operation ratios include binary parsing. The new core ledger charges support
collection, deduplication, sparse reads, partial evaluation, search, witness
materialization, and candidate checks. The eager and lazy backends have distinct
explicit ledgers: their ratio is not a machine-instruction ratio. The earlier
fixed-width constants and single-witness overhead theorem remain attached to the
reference implementation.

The alternating workload now reuses both acquired witnesses. Negative streams
reuse checked refutation trees after the first acquisition. Yet persistent
reuse is slightly slower than lazy solving alone in every displayed timing row.
These tiny problems expose database, checksumming, and serialization overhead.
A stronger fallback substantially changes the baseline; reduced counted work
must not be presented as an elapsed-time improvement. Three repetitions on easy
synthetic streams do not establish general timing behavior.

Every negative certificate is stored, although only up to four distinct proofs
of at most 65,536 serialized bytes each are proposed on a new query. No archive
entries are evicted. The new databases occupy 32,768--90,112 bytes after close;
raw records separate input/witness payload from certificate payload. These are
ASCII/JSON payloads, not bit-packed representations or peak process memory.
The single-witness mode remains an ablation without negative or portfolio reuse.

- [Current metadata](results/lazy-search/metadata.json).
- [Current frozen inputs](results/lazy-search/inputs.json).
- [Current raw runs](results/lazy-search/workloads.jsonl).
- [Current summary](results/lazy-search/summary.json).
- [Persistent-store replay and audit](results/lazy-search/persistence.json): all
  710 prior rows unchanged; 355 revalidated inputs and 129 refutations added;
  all 355 current results and retained certificates audited.

## Historical results with the exhaustive fallback, including binary parsing

That historical native engine used the Lean-verified counted parser. `parse_work`
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
  `Hybrid.lean` for the historical run, plus `Search.lean` and `Knowledge.lean`
  for the current solver; acquisition and witness updates occur inside the stream. Binary
  tokenization and formula assembly are counted. JSON and ASCII conversion are
  covered by elapsed time only.
- **Setup:** compiled-engine fingerprinting and database connection/schema setup.
  All modes pay the same front-end setup, including an empty database for the
  modes that do not store results. This is a common-front-end comparison,
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
and exact cache invariant are verified in Lean. The lazy solver adds semantic
correctness, refutation soundness, and a search-node bound, without inheriting
the earlier numeric cost coefficients. SQLite, the Python adapter, JSON
and ASCII conversion, process communication, disk integrity, and compiler/runtime
behavior are outside
the kernel proof. Integration tests cover persistence and corruption behavior.
The uniform resource bound for SAT with no size restriction remains unresolved.
Proved polynomial bounds apply to a fixed variable cap or to a specified
logarithmic relation between variable width and input length. These conditions
do not apply to every SAT instance.
