# Persistent source updates: matched study

The adjacent-block source API preserves the source clauses at every version and
checks local replacements against their predecessor. This study compares local
edits with full source reconstruction using the same native checker, persistent
tree, input streams, and resident relation-cell cap. It is a synthetic mechanism
study, not a general SAT competition or evidence of a learning-specific gain.

## Reproduce and inspect

From the repository root at runtime commit `07354c8` (the harness is committed
with this report), build the pinned Lean engine and run:

```sh
python3 experiments/run_source_updates.py --output /tmp/oracle-source-new-run
python3 experiments/validate_source_updates.py experiments/results/source-updates
```

The runner requires a new output directory and access to `/bin/ps` for its own
worker and checker PIDs. The validator is read-only. It verifies all 74 captured
runtime fingerprints, labels, phase arithmetic, local update bounds, resource
samples, and summaries. If the runtime later changes, use the recorded revision
and original build for fingerprint verification; do not overwrite this evidence.

The Python worker starts fresh with a temporary database for each run. There are
48 runs: widths 1 and 4, lengths 16/64/256/1024, local/full modes, three repetitions
with alternating method order. The seed is `1830 + 10000*width + size`; complete
inputs are frozen in `inputs.json`. A 38-query stream includes initial construction,
32 genuine bucket replacements, unchanged replay, an empty-clause contradiction,
deletion, a branch from the initial version, and restart. Local relations are bit
permutations/flips, so independent enumeration establishes the positive labels.
The empty clause establishes each negative label. Endpoint states are unrestricted.

## Results

All **1,824 queries** return the expected answer, including **48 UNSAT answers**.
No errors or timeouts were dropped. The validator independently checks 2,976 local
bijections. The full regression suite passes **141 tests**; the Lean audit checks
**2,279 declarations / 1,106 theorem declarations**, with no admits or added axioms.

| Width | Edges | Local edit ms | Full edit ms | Local stream ms | Full stream ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 16 | 0.587 | 1.065 | 189.266 | 213.797 |
| 1 | 64 | 0.653 | 2.881 | 198.599 | 280.333 |
| 1 | 256 | 0.792 | 9.998 | 227.486 | 571.101 |
| 1 | 1024 | 0.972 | 39.850 | 325.481 | 1762.670 |
| 4 | 16 | 2.715 | 5.481 | 299.459 | 410.897 |
| 4 | 64 | 3.145 | 15.443 | 435.403 | 900.513 |
| 4 | 256 | 3.725 | 55.004 | 819.478 | 2705.678 |
| 4 | 1024 | 4.268 | 210.808 | 2348.178 | 9986.786 |

Edit medians pool 96 edits per configuration. Stream medians use three totals,
including service setup, all queries, timed restart, and final shutdown. Full
source reconstruction is inside the timer. Whole-worker elapsed time separately
includes Python startup, observer/control overhead, and log serialization.

At width 4, 1,024 edges, local/full medians respectively are:

- Source node reads: 64 / 2,079.
- Patch/source-binding visits: 21 / 2,047.
- Native request bytes: 6,068 / 293,786.
- Newly stored knowledge objects: 13 / 13.
- Newly stored packed payload bytes: 2,752.5 / 2,752.5.
- Complete worker elapsed: 2,415.00 / 10,058.21 ms.

Both modes benefit from content sharing. The latency advantage comes from avoiding
full source reconstruction, compilation, and binding. It is not a measured storage
advantage over this full-source baseline. Local initial construction is 1,096.90 ms,
old-branch replay 73.98 ms, restart 928.25 ms, and an unchanged decision 0.17 ms.
These costs prevent extrapolating warm edit latency to all requests.

## Retention and memory

The resident native relation-cell limit equals the live tree's working set. Each
single-edge transition retains its predecessor until verification succeeds, so
it can temporarily exceed the resident cap by at most `(height+1)*q^2` cells.
The validator checks at most `height+1` native definitions/evictions, `2*height+1`
patch visits, `4*height+2` live-reference updates, and `height+3` newly inserted
knowledge objects per warm single-edge decision edit. Final cells return to cap.

There are 1,548 valid RSS samples and zero missed reads. The largest observed
service-plus-checker total is 133.20 MiB; the checker alone peaks at 92.81 MiB.
The longest interval between sample starts is 61.99 ms. The observer samples only
its own Python worker and native checker, excluding the driver and short-lived
sampling subprocess. Peaks between samples can be missed. The cell cap excludes
source clauses, object headers, maps, serialization buffers, database memory,
and other native stores. This is not a hard RSS or total-resource guarantee.

## Preserved evidence and limitations

`runs.jsonl.gz` contains every raw run, phase ledger, operation counter, storage
report, setup/shutdown timing, and RSS summary. `metadata.json` pins inputs,
source commit and runtime hashes. `validation.json` records independent checks.
`tests.log` records the regression run. The pre-existing SQLite ResourceWarning
is retained in that log; the suite still passes.

The earlier run is preserved in `../source-updates-pilot/`, including its exact
harness. It omitted initial setup and final shutdown from its stream sum. This
final run repeats the same input hash and solver policy with corrected lifecycle
accounting. It is not a second blind holdout.

`durable-source.json` records a SQLite backup, preservation checks for every old
row in all 20 pre-existing tables, fresh verification of 355 older inputs, and
restart checks for five persistent source versions. The live ignored archive now
has 4,615 generic results and 1,419 refutations; prior records are never imported
as trusted answers for a new engine. All 119 previously tracked experiment files
remain unchanged. The backup and database remain local, outside git.

The local reference cost theorem and native source invariant do not establish a
complete refinement through global variable IDs, JSON, Python, SQL, or the native
reference-count store. The supplied partition and width limit remain premises.
The general factor-DAG solver still has global provenance costs. Decision-only
requests avoid full witness output; explicit witness requests pay that cost.
