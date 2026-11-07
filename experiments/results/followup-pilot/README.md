> Retained pre-correction run. A later review moved chain witness construction
> behind the explicit request and removed repeated list concatenation.
> The final repeated study is in `../followup/`; these measurements are unchanged.

# Durable reuse, balanced chains, and checked fragments

This study measures commit `a0811b2fa2b28a9474fda8997922651fb208599a` on
7 November 2026. The source and binary hashes are in `metadata.json`.
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
| Local edits | 189.13 | 218.10 | 231.62 | 199.26 | 221.65 | 155.10 | 511.14 |
| Width shift | 167.85 | 152.29 | 156.03 | 153.74 | 167.18 | 138.93 | 391.56 |
| Proof reuse | 176.75 | 145.37 | 138.40 | 135.83 | 165.92 | 131.35 | 360.18 |
| Chain to 128 | 181.65 | 229.93 | 263.61 | 231.43 | 186.27 | 168.80 | 429.86 |
| Distant edits | 272.45 | 445.95 | 534.24 | 380.08 | 333.19 | 239.38 | 1141.95 |
| Public SATLIB | 257.82 | 291.55 | 393.89 | 384.80 | 280.77 | 570.58 | 1909.78 |
| Distribution shift | 234.25 | 234.49 | 277.77 | 278.16 | 228.21 | 346.26 | 1077.39 |
| TACAS towers prefix | 966.65 * | 1002.00 * | 917.37 | 914.67 | 1003.36 * | 1178.62 * | 1931.22 * |
| TACAS LIDRUP example | 135.77 | 131.47 | 132.65 | 129.70 | 135.33 | 129.53 | 208.37 |
| Held-out counter | 418.07 | 475.81 | 429.38 | 413.60 | 456.41 | 426.96 | 1971.63 |

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
| Local edits | 112.92 | 3.61 | 2.67 |
| Width shift | 111.06 | 0.96 | 0.65 |
| Proof reuse | 108.56 | 0.63 | 0.62 |
| Chain to 128 | 117.91 | 2.60 | 2.59 |
| Distant edits | 119.05 | 8.57 | 4.82 |
| Public SATLIB | 160.25 | 6.21 | 4.40 |
| Distribution shift | 143.70 | 3.47 | 2.29 |
| TACAS towers prefix | 329.08 | 10.64 | 5.55 |
| TACAS LIDRUP example | 108.36 | 0.52 | 0.40 |
| Held-out counter | 131.98 | 7.58 | 4.22 |

The largest observed interval is 46.15 ms. There are 83 missed process reads
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

The measured sources pass 114 service tests. The Lean build audits 1,827
transitive declarations, including 941 theorem declarations, without admitted
proofs or additional axioms. `validation.json` records commands and checked
fingerprints. The formal chain bound concerns tree operations. RUP soundness is
proved, but complete JSON/session/Python/SQLite refinement remains open.

`persistence-before.json` records a full local SQLite backup and historical file
hashes. Revalidation adds 355 current-engine results and 129 proofs. The semantic
audit passes on all 355 inputs (226 SAT, 129 UNSAT). The live archive now has
3,195 results and 903 proofs across engines. Every previous row, including all
2,840 results and 774 proofs, remains unchanged. All 53 earlier experiment files
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
