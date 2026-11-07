# Bounded layers and comparable full-input study

All 175 runs completed: 2,450 correct answers, including 350 UNSAT. This includes
2,100 checked-service answers (300 UNSAT) and 350 standalone, unverified CaDiCaL
reference answers. No query or watchdog failure occurred. The 2026 application
prefixes are small and all UNSAT; this is not a representative application suite.

Inputs were frozen before timing: first two increments of roverg10, transportg29
and entertainment08 from the [TACAS 2026 artifact](https://zenodo.org/records/18330441),
six SATLIB instances, and a chronological stream (16 signed-unit training
formulas, 32 distinct later formulas, six public shift queries, four repetitions).
Online learning sees an answer only after its query completes; subsequent model
updates are charged. The selected SATLIB examples were also used in older
studies, so “holdout” means unseen earlier in this fresh worker's stream, not
never used during project development.

There are five sequential repetitions per mode, with rotating order, fresh
workers and databases. Builds, tests and archive revalidation did not overlap
these timings. Each service mode receives complete formulas and pays input
conversion, setup, checking, storage and applicable training. The direct mode
uses original normalized CNF without independent certification or archival;
its different responsibility is explicit.

| Stream | Direct | Checked | Exact | Portfolio | Learned | Proof live | Adaptive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rover prefix | 12.95 | 441.33 | 448.19 | 458.16 | 461.60 | 563.57 | 456.78 |
| Transport prefix | 11.50 | 152.23 | 153.35 | 156.59 | 156.46 | 161.26 | 155.30 |
| Entertainment prefix | 12.04 | 173.96 | 174.45 | 177.18 | 179.80 | 195.12 | 178.84 |
| SATLIB selection | 33.80 | 207.70 | 205.80 | 224.35 | 230.97 | 325.95 | 216.18 |
| Chronological shift | 305.65 | 533.08 | 505.29 | 11327.88 | 317.00 | 769.08 | 470.36 |

Values are median complete-stream milliseconds, including service setup.
`summary.json` also retains ranges and all status counts. The learner accepts
47 novel predictions per repetition: 15 training and all 32 later signed-unit
formulas. It has no accepted prediction on the public shift. Its restricted
success does not establish general-SAT learning. Portfolio-only unsuccessful
proposal work is costly; it takes 11.33 seconds for the whole chronological
stream. No individual query reaches the five-second deadline.

Every service has a 64 MiB logical-page cap. A parent samples descendant RSS and
scratch files, requesting 20 ms intervals, and kills a worker over 512 MiB RSS or
256 MiB scratch. These are sampled watchdog thresholds, not hard memory limits.
Observed maxima: 250.45 MiB summed RSS, 20.98 MiB scratch, 10.96 MiB WAL/SHM;
maximum sampling interval 147.38 ms, 51 missed process reads. Shared pages can
be counted more than once; short-lived processes and between-sample peaks can
be missed. The monitor is excluded.

## Separate structural and cache evidence

`structure.json` has 72 correct supplied-layer answers: widths 2, 3 and 4,
lengths 16, 64, 256 and 1,024, two cache settings. The largest replacement uses
ten compositions and eleven node-write attempts. A positive full witness checks
all 1,024 edges. The full-scan composition budgets are 640, 5,120 and 40,960
middle-state tests. These timings receive precompiled relations and are not
mixed with the full-CNF table above. Repeated transition relations share many
nodes; the two cache settings do not exert pressure on this simple family.

The six delta answers are also correct. At lengths 16 and 64, changing an
endpoint reads two source references, copies zero metadata entries, compares
zero whole source sets, and affects one bucket. Length 256 hits the existing
lazy dependency-depth cap and uses checked fallback. Its 514 source-delta reads
come from rebuilding sources; it does not demonstrate a local update. Full
active-context checks and certificate/witness processing still cost global work.

`cache-pressure.json` separately uses distinct random eight-state relations with
a planted all-zero path, 256 edges and 20 edits, with three repetitions. Each run
returns 21 checked witnesses and replays three older roots after restart: all
144 answers are correct. A 4 KiB cache retains 3,833 serialized bytes with 12,741
evictions; a 2 MiB cache retains 143,990 bytes without eviction. Median sums of
query ledgers are 175.94 and 86.95 ms. All runs retain the same 713 objects,
109,997 raw / 79,530 stored payload bytes and 413,696-byte closed database.
Smaller active retention preserves historical evidence at a retrieval cost.
These payload measurements are not heap or RSS measurements.

## Proof, preservation and reproduction

119 integration tests pass. The Lean audit checks 1,957 declarations, including
991 theorem declarations, without admits or new axioms. The development test
log retains the initial layered timeout: arity expansion delayed construction
of function-valued summaries. Joins now eagerly materialize data, confirmed in
generated C. The same repair applies to the older Boolean-chain join; earlier
experimental data remain untouched.

`persistence.json` records independent revalidation and audit of 355 inputs.
All previous rows (including 3,550 results and 1,032 proofs) and 73 historical
experiment files are preserved. New totals: 3,905 results and 1,161 proofs.
`persistence-before.json` records the backup and old-file hashes.

Run from the repository root, supplying the original source archives:

```sh
python3 experiments/run_structured.py --artifact /tmp/oracle-tacas2026.zip --archives /tmp/oraclemachines-satlib --output /tmp/new-structured-study
python3 experiments/run_cache_pressure.py /tmp/new-structured-study/cache-pressure.json
```

The first script requires `psutil` and permission to enumerate worker descendants.
Source archives are not committed. `metadata.json` records source/binary hashes,
selection, limits and hardware. `runs.jsonl.gz` is lossless compression of the
original raw log; `log-integrity.json` records both hashes. Decompress it to read
individual events. Regenerating the runner produces uncompressed JSONL.
