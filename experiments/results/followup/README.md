# Durable reuse, balanced chains, and checked fragments

This study measures commit `f19c4b2` on
7 November 2026. The source and binary hashes are in `metadata.json`.
The pre-correction run is retained in `../followup-pilot/`; the chain query now
constructs a witness only on request and uses linear list construction.
It contains **210 worker runs, 2,289 query attempts, 2,259 correct answers
(1,188 UNSAT), and 30 archive-cap errors**. There are no wrong answers,
missing query records, worker crashes, or timeouts. Failed queries remain in
`runs.jsonl`; they do not count as completed decisions.

## Inputs and protocol

The seven earlier streams are copied exactly from `../scaling/inputs.json`.
Three new streams were defined before timing:

- The first twelve `towers05` increments in the
  [TACAS 2026 artifact](https://zenodo.org/records/18330441), with expected UNSAT
  labels from its manifest. Permanent clauses accumulate; each new `a` line
  replaces the previous query assumptions.
- The complete three-query LIDRUP example from the same archive (UNSAT, SAT,
  UNSAT). This is a protocol example, not a difficult industrial benchmark.
- A four-bit synchronous counter unrolled to depth twelve. At each depth we
  request its arithmetic state (SAT) and a state with one incorrect bit (UNSAT).
  This adds 24 new queries with independently specified arithmetic labels.

`inputs.json` freezes the converted formulas and deltas. `metadata.json` records
archive/member hashes and the source DOI. The artifact is by Dominik Schreiber
and accompanies Schreiber, Fleury, Fazekas and Biere's
[2026 paper](https://doi.org/10.1007/978-3-032-22752-2_18).
We use selected example inputs, not their distributed implementation, full
experimental suite, or reported speedup. The original public SATLIB provenance
remains in the earlier scaling and expanded studies.

All workers run sequentially, with three repetitions and rotated mode order.
Each query receives five seconds; SQLite's logical page cap is 8 MiB in every
mode. Exact-result lookup and learned prediction are disabled. Delta modes
receive explicit add/replace/remove requests; other modes receive the full
formula. This API difference is part of the comparison. Acquisition, checking,
result persistence and service setup are charged. Stream totals sum the query
records, including initial setup and per-query close in restart mode. Interpreter
startup, monitoring and live-mode final close are excluded from these totals;
complete worker elapsed times are also retained. Builds and test suites did not
run concurrently with the timed workers. Host load remains uncontrolled.

## Median stream time in milliseconds

| Stream | Checked | Full interface | Delta | Symbolic delta | Adaptive | Live proof | Restart proof |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Local edits | 185.81 | 213.03 | 229.32 | 197.45 | 219.97 | 153.90 | 512.21 |
| Width shift | 168.38 | 152.15 | 157.63 | 153.62 | 166.38 | 136.71 | 390.31 |
| Proof reuse | 168.60 | 139.31 | 141.01 | 136.35 | 168.36 | 132.36 | 362.35 |
| Chain to 128 | 183.87 | 236.58 | 267.97 | 231.58 | 189.49 | 172.91 | 431.84 |
| Distant edits | 273.05 | 446.81 | 533.06 | 382.47 | 332.93 | 241.25 | 1140.70 |
| Public SATLIB | 263.07 | 298.84 | 383.80 | 386.42 | 284.28 | 566.52 | 1894.08 |
| Distribution shift | 235.82 | 221.25 | 278.02 | 279.81 | 230.63 | 346.69 | 1032.51 |
| TACAS towers prefix | 956.18 * | 997.54 * | 905.66 | 912.11 | 1020.46 * | 1173.81 * | 1917.87 * |
| TACAS LIDRUP example | 137.07 | 132.66 | 132.14 | 130.24 | 136.66 | 130.81 | 211.40 |
| Held-out counter | 425.09 | 490.01 | 422.67 | 424.68 | 465.38 | 427.06 | 1964.10 |

An asterisk marks an incomplete stream: the final two towers queries hit the
archive page cap on every repetition in that mode. Those totals include the
failed attempts and must not be interpreted as time to solve all twelve queries.
The two delta modes complete all twelve. On repetition zero, their closed
archives use 1,007,616 and 970,752 bytes. They share compressed constraints and
expansion evidence, whereas full-input routes retain repeated complete inputs
and certificates. A failed transaction can roll back below the configured cap;
the final database size therefore need not equal 8 MiB after exhaustion.

Live proof reuse improves several structural streams, but loses to checked
solving on public SATLIB and the distribution shift. Restart is consistently
costly. Symbolic delta is close to checked solving on the held-out counter;
three repetitions do not establish a meaningful advantage from that small
difference. The earlier scaling study is retained; cross-study differences
combine several code changes and host variation and are not isolated ablations.

## Resource observations

The parent samples each worker and its descendants with psutil, requesting a
20 ms interval. Scratch includes SQLite/WAL/SHM and external temporary files;
input staging and monitor output are outside scratch. Reported RSS sums process
RSS, so shared pages may be counted more than once. It excludes the monitor.

| Stream | Max sampled process-tree RSS (MiB) | Max sampled scratch (MiB) | Max sampled WAL + SHM (MiB) |
| --- | ---: | ---: | ---: |
| Local edits | 112.95 | 2.32 | 2.31 |
| Width shift | 108.78 | 0.57 | 0.56 |
| Proof reuse | 108.52 | 0.45 | 0.44 |
| Chain to 128 | 117.88 | 2.74 | 2.73 |
| Distant edits | 118.94 | 8.27 | 4.82 |
| Public SATLIB | 160.30 | 6.18 | 4.40 |
| Distribution shift | 145.38 | 2.29 | 2.29 |
| TACAS towers prefix | 329.14 | 10.64 | 5.55 |
| TACAS LIDRUP example | 108.08 | 0.30 | 0.30 |
| Held-out counter | 131.64 | 9.50 | 4.22 |

The largest observed interval is 43.07 ms. There are 143 missed process reads
across the 210 runs, for example when a child exits between enumeration and
sampling. Transient peaks and short-lived children may be missed. These are
sampled observations, not hard memory or disk bounds, and the shared logical
page cap is not an equal-total-memory experiment.

## Restricted chain experiment

`chain.json` records 72 paired negative/positive replacements: lengths 16, 64,
256 and 1,024; three positions; three repetitions; and witness output on/off.
Each pair starts from the same immutable all-inequality chain. Replacing one
edge by equality changes the endpoint parity. All 144 answers are correct.

| Edges | Relation compositions per replacement | Node-write attempts per replacement | Positive witness edge checks |
| ---: | ---: | ---: | ---: |
| 16 | 4 | 5 | 16 |
| 64 | 6 | 7 | 64 |
| 256 | 8 | 9 | 256 |
| 1,024 | 10 | 11 | 1,024 |

These counters match the Lean tree ledger. They are not whole-service instruction
counts. Identical content shares objects, so node writes need not allocate new
physical nodes. Cold native registration, database work and complete witness
output remain separately charged. Positive requests follow their negative pair
and can reuse registration; their timings are not cold-update measurements.
The explicit chain API assumes the factorization is supplied. It does not
recognize arbitrary SAT formulas or generalize through a distant new edge.

## Symbolic and proof checks

At size 64, the projection microstudy allocates 8,499 total manager nodes with
separate conjunction/elimination and 8,034 with fused abstraction; both retain
32 after collection. The common construction already allocates 8,003 nodes.
Hence the projection adds 496 versus 31. For equality on two eight-bit words,
grouped order retains 765 nodes and interleaved order retains 24. These controlled
examples illustrate known representation/order effects. They do not bound
arbitrary diagrams or establish a general ordering heuristic.

Live and restarted proof modes each certify 141 completed negatives using
checked RUP fragments and 27 by checked conjunct-core transfer. Across completed
queries, live mode checks/accepts 2,367 fragments; restart mode checks/accepts
18,687, including replay. These are derivation checks, not distinct mathematical
clauses; counts exclude work in the failed queries. Root assumptions are never
permanent premises. Complete standalone certificates remain archived, so proof
construction/serialization and restart are still costs.

## Validation and persistence

The measured sources pass 114 service tests. The Lean build audits 1,828
transitive declarations, including 941 theorem declarations, without admitted
proofs or additional axioms. `validation.json` records commands and checked
fingerprints. The formal chain bound concerns tree operations. RUP soundness is
proved, but complete JSON/session/Python/SQLite refinement remains open.

`persistence-before.json` records a full local SQLite backup and historical file
hashes. Revalidation adds 355 current-engine results and 129 proofs. The semantic
audit passes on all 355 inputs (226 SAT, 129 UNSAT). The live archive now has
3,550 results and 1,032 proofs across engines. Every previous row, including all
3,195 results and 903 proofs, remains unchanged. All 63 earlier experiment files
match their recorded hashes. The local database/backup stay ignored by Git;
these reports and reproducible experimental evidence are committed.

## Reproduce

Build the pinned Lean and incremental bridge executables first (see the solver
README). Download `Archive.zip` from the source record above; expected MD5 is
`7b9a50e86396117e577f40c8dbacc94f`. Install psutil in the benchmark Python
environment. Run from the repository root with a fresh output path:

```sh
python3 experiments/run_followup.py --artifact /path/to/Archive.zip \
  --output /tmp/oracle-followup-new --repeats 3
```

The runner never overwrites an existing study. OS permission to inspect its own
worker descendants is needed for resource telemetry. Source hashes, every query,
all errors, and per-run sample intervals/misses must accompany any comparison.
