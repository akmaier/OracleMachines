# Expanded public and chronological study

The final run has 162 isolated workers, 1,260 correct completed answers
(1,062 SAT and 198 UNSAT), and no missing event, timeout, or failed query.
The query budget is three seconds. The host is an Apple M3 Pro with 12 CPUs
and 18 GiB of memory, running the macOS/Python versions in metadata.json. Each of six modes sees 70 queries in each
of three rotating-order repetitions. This is a local mechanism study, not a
SAT-competition claim. Machine scheduling and background host activity were
not controlled; the first few seconds also overlapped the integration tests.
Three repeats do not justify small timing differences or confidence intervals.

Public inputs are selected before timing from five SATLIB archives: six random
SAT, six random UNSAT, six graph-colouring, six AIM (three yes, three no), and
four circuit faults (two yes, two no). The fixed filename rules are in the runner.
Additional streams test signed-unit training/held-out transfer, a shift to graph
colouring and back, root extensions over shared planted structure, and repetition.
Labels come from SATLIB or the synthetic construction. The chronological stream
pays for all initial solving, checked labels, and model updates. The learner never
sees future labels. Held-out means a new query/witness after training in this
fixed mechanism study, not a broad statistical generalization guarantee.

| Stream | Direct ms | Checked ms | Portfolio ms | Incremental ms | Learned ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random SAT, 50 | 5.56 | 12.22 | 14.00 | 9.94 | 13.13 |
| Random UNSAT, 50 | 5.32 | 14.39 | 23.83 | 19.31 | 28.86 |
| Graph colouring | 5.36 | 12.94 | 10.33 | 9.09 | 7.26 |
| AIM | 5.33 | 12.32 | 17.43 | 13.10 | 18.08 |
| Circuit faults | 7.34 | 857.26 | 957.52 | 887.56 | 1045.45 |
| Unit transfer | 5.18 | 5.88 | 6.02 | 0.54 | 0.53 |
| Distribution shift | 5.25 | 12.48 | 7.43 | 8.82 | 6.81 |
| Shared definitions | 5.20 | 7.14 | 5.26 | 1.97 | 2.24 |
| Exact repetition | 5.22 | 6.93 | 0.34 | 0.33 | 0.35 |

These are median query latencies pooled over three runs. Raw events retain
per-query phase partitions and summary.json also reports p95 latency and complete
worker time. First-use startup is inside the stream. Worker time includes process
startup, input transfer, service initialization, conversion, all query execution,
measurement, shutdown, and output transfer. All checked variants keep durable
results. Compilation and benchmark archive download are excluded.

Modes:

- `direct`: original CNF, syntax-normalized DIMACS, CaDiCaL under the bounded
  external wrapper. No certificate check or result archive. This is a calibration
  baseline with a different front end, not a bare solver-CPU measurement.
- `checked`: same checked service and durable writes, exact reuse disabled.
- `exact`: checked service plus exact cache, stored proposals disabled.
- `portfolio`: exact cache and checked archived witnesses/proofs.
- `incremental`: exact cache and live CaDiCaL, archived proposals/model disabled.
- `learned`: combined portfolio, live CaDiCaL, and bounded online predictor.
  Its improvement over `checked` cannot be attributed to learning alone.

The shared-definition stream retains three learned clauses after its first call;
subsequent calls begin with them and add 13 clauses rather than the initial 784.
Whole-worker medians are 245.98 ms checked and 200.28 ms incremental. Clause
retention is observed; the study does not isolate it from other retained state.

The learner accepts all 24 held-out unit queries and 27/30 queries overall in
that stream. These are new witnesses, not only retrieved assignments. Incremental
alone is equally fast at the query scale: 0.54 versus 0.53 ms. Whole-worker times
are 184.02 versus 184.47 ms, respectively. None of the shifted graph queries gets
a learned hit; verified witness reuse handles four of six graph queries per run.
The first return to units falls back and retrains before learned hits resume.

On random UNSAT, redundant proposal/checking work increases median latency.
Circuit inputs expand to approximately 0.5--5.8 million ASCII bits in the unary
encoding, making conversion, native representation, checks and storage expensive.
The largest child-process RSS high-water mark is 349.86 MiB; the largest service
mark is 213.27 MiB. They are process-lifetime maxima, not a simultaneous sum.
The largest final database is 95,199,232 bytes, the largest saved proof aggregate
736,019 bytes, and learned states are at most 56 bytes in this study. A small model
does not make the archive or complete pipeline small. Live child CPU is excluded
from the reaped-child counter until shutdown.

Evidence:

- `manifest.json`: source URLs, archive and case hashes, order, labels, phase.
- `runs.jsonl`: all worker and query events, including failures if any.
- `summary.json`: completed/failed/missing counts, median/p95 latencies and totals.
- `metadata.json`: platform, versions, source/binary/raw fingerprints.
- `persistence.json`: independent replay/audit of the real local store; all
  1,420 prior result rows and 258 proofs remain byte-for-byte identical as rows.
  The current engine adds 355 results and 129 proofs (1,775 total result rows).

Raw SHA-256: `810efa544359bd4c4805d80257781ad7dcfc18ff0197817be0cbf0aac18abf51`.
The earlier pilot remains separately in `../expanded-pilot/`, including all 32
errors. Its measurements are not pooled here. No third-party CNF files are
redistributed or relicensed by this repository; retrieve archives from the
manifest and compare their hashes.

Reproduce after building the pinned native engine and incremental bridge:

```sh
python3 experiments/run_expanded.py --archives /path/to/satlib-archives \
  --output /path/to/new-empty-results --repeats 3 --query-timeout 3
```

Put the five `.tar.gz` archives named in the manifest in that directory. The
runner refuses a nonempty output directory. It reads archive members without
extracting paths and rejects malformed DIMACS. Balanced formula construction
avoids unnecessary AST depth. An outer worker budget retains partial JSON events
if a worker hangs; a service error cannot become an UNSAT answer.
