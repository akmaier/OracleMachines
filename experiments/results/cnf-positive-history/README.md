# Checked source deltas avoid full-prefix copies

8 November 2026. The separate research candidate now supports an append-only
history interface for positive clauses witnessed by subsets in a fixed solved
base. This comparison retains **24 histories, 4,848 decisions and 48 compressed
archives**. All answers agree with the expected labels, every final reconstructed
source equals the input recipe, and all warm/cold replays add no solver nodes.
All **265 previous candidate archives** replay with unchanged residual-row digests.
The production solver and result archive are not changed by this experiment.

## Prepared-state invariant

`PositiveHistory.prepare(F)` uses ordinary checked residual solving, stores F
once and builds a positive-clause index. `append(parent, D)` finds a positive
base clause C with C subset D, checks that containment, and stores D, the witness
clause index, and integer parent/base references. It returns a version handle
and SAT verdict. Every version denotes its base followed by its exact addition
sequence, preserving literal order and duplicates. Every addition follows from
the base, so every version has the same models and answer as that base.

Warm append reads the delta and indexed candidate/witness clauses. It does not
rebuild the index, normalize the whole source, copy the full core key, or invoke
residual search. A parent must be checked in this archive; a handle alone does
not certify an unrelated full CNF supplied by a caller. IDs are archive-local,
not portable hashes or authenticated external identities. Records are immutable
through this single-writer API. Cold checks reject malformed witnesses, cycles,
cross-base parents and mismatched source/certificate bindings.

An uncovered positive addition raises `UnsupportedExpansion`, with no verdict
for that edit. In this driver, it explicitly triggers parent materialization
and ordinary solving of a fresh base; those costs are timed. Deletions, negative
additions or changed constraints likewise require a new base and cannot be
expressed by this append operation. Old versions and certificates remain intact.

## Matched histories and retained bytes

`full_source` is the preceding positive-core candidate, unchanged from `085b415`.
It receives each full formula. `delta_history` receives the initial base and
subsequent clauses through the prepared version interface. Recipes store the
base and additions once in `report.json`, instead of repeating every input prefix.
There are SAT and UNSAT matching bases of sizes 4, 8 and 16, with 8/32/128
additions, and 512-addition runs at size 4. Each fresh redundant clause contains
one positive base choice and a fresh variable. Four additional histories test
repetition, uncovered constraints and mixed updates.

| History | Additions | Full-source logical bytes | Delta logical bytes | Full SQLite bytes | Delta SQLite bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNSAT, 4 holes | 8 | 13,699 | 2,582 | 36,864 | 28,672 |
| UNSAT, 4 holes | 32 | 66,283 | 4,543 | 151,552 | 28,672 |
| UNSAT, 4 holes | 128 | 499,430 | 12,499 | 1,110,016 | 53,248 |
| UNSAT, 4 holes | 512 | 6,034,220 | 45,043 | 9,744,384 | 114,688 |
| UNSAT, 8 holes | 128 | 1,742,366 | 24,684 | 2,723,840 | 73,728 |
| UNSAT, 16 holes | 128 | 10,957,771 | 118,668 | 15,130,624 | 237,568 |
| SAT, size 4 | 512 | 5,198,151 | 44,427 | 8,826,880 | 114,688 |
| SAT, size 16 | 128 | 7,062,045 | 107,954 | 10,838,016 | 217,088 |

At 16 holes / 128 additions, summed acquisition/append time is 2.550 seconds for
the full-source interface and 0.04876 seconds for delta history, including base
acquisition. At four holes / 512 additions, it is 2.014 versus 0.1597 seconds.
These are single samples for this synthetic ablation, not competitive CDCL
claims. All 48 snapshots occupy 63,107,072 raw SQLite bytes and 2,094,008 gzip
bytes. Offline gzip compression is not used during online operations.

The 512th four-hole append performs one posting lookup, one candidate test,
four containment probes, ten delta-literal visits (discovery plus checking),
and four witness-literal visits. It serializes 65 bytes of JSON delta payload,
in addition to integer SQL bindings and database/index overhead, and inserts one
version. It performs no solver work or base-index reconstruction. The 128th
16-hole append similarly performs 16 containment probes and serializes 118
payload bytes. Pointer bit lengths and SQL index costs still grow with the archive.

On that same 512th four-hole addition, the full-source path scans 2,660 discovery
literal occurrences, makes 2,048 containment probes, and checks 4,608 containment
witness literal occurrences. It serializes 17,738 key bytes and 13,902 certificate
bytes. The reduction in this structural work is independent of the full-source
API's additional archive-size telemetry scan.

## Cold replay, exports and accounting

Cold delta query checks the base proof and every required ancestor delta. At
four holes / 512 additions it checks 513 history records and one base, while the
preceding UNSAT representation checks two larger residual records. The observed
cold times are 0.00396 and 0.00732 seconds respectively. Small SAT cold queries
can favor the full-source representation: at size 4 / 32 additions it takes
0.00028 seconds versus 0.00052 seconds. A warm delta verdict uses checked version
metadata; no constant-cost restart is claimed.

The new interface answers SAT decisions and can export a sparse base assignment,
with all omitted variables false. The old `solve` API constructs its model on
each SAT call; the new interface times witness export separately. Final exports
are verified against full sources and recorded under `final_witness` and
`final_materialization`. Thus SAT timings compare the current interfaces, not
identical witness-output contracts. The UNSAT comparisons have the same verdict
output. Materializing and serializing a full source still costs its path and
output size; avoiding that output is a precondition of the delta-only bound.

Logical storage includes all residual keys/records, plus JSON encodings of
history rows including integer references and payload framing. SQLite page and
index overhead is reported separately; neither is a peak-RSS measurement. The
old full-source solve retains its per-query SQL size scan. The delta operation
does not scan the archive: its optional final `storage()` scan is separately
timed and recorded, along with final export/validation costs. Base initialization
is separate in both modes. `operation_seconds` includes rejected fast attempts,
materialization and new-base solving on unsupported additions. Common workload
assembly, offline digests, snapshots and compatibility auditing are not included
in online operation timings. The run began after the Python and Lean checks.

## Preserved losses and next patterns

| History | Additions | Full logical bytes | Delta logical bytes | Full operation seconds | Delta operation seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same clause appended to successive versions | 128 | 1,410 | 11,742 | 0.01535 | 0.03306 |
| Same parent and clause operation repeated | 128 | 1,410 | 1,411 | 0.00769 | 0.00353 |
| New positive unit each step | 32 | 30,657 | 57,756 | 0.01651 | 0.03814 |
| Alternating redundant and new units | 32 | 51,088 | 52,078 | 0.02532 | 0.03034 |

Canonical CNF deduplication makes repeated identical clauses cheap for the old
cache. Our exact event history retains each successive occurrence. Repeating the
same parent and payload instead reuses its existing version, but fixed table
overhead remains: its SQLite file is 28,672 bytes versus 12,288 bytes. Even on
the small SAT redundant stream, eight additions use fewer logical bytes but a
larger SQLite file (28,672 versus 20,480 bytes).

Novel units trigger 32 new bases; the mixed history triggers 16. This is a
measured failure of the fixed-base shortcut, not a hidden unsupported workload.
Potential next compression patterns are run-length representations of repeated
events, semantic no-op versions with explicit provenance, and sharing source
structure across fresh bases. Such representations must preserve the promised
source identity and handle witness invalidation. Cold validation and the earlier
subsumption policy regressions are still separate gaps. No universal minimal
expansion or polynomial arbitrary-SAT bound is established.

## Proofs, tests and reproduction

All **230 Python tests pass**. Six new tests cover exact SAT/UNSAT histories,
sparse original variable names, all assignments of small covered extensions,
forks, repeated operations, unchanged old rows, unsupported/deleted constraints,
malformed cold certificates and 1,200-step iterative cold replay. The Lean lemma
`positive_history_models` proves the covered positive conjunction invariant for
an entire addition list. The audit passes **4,067 declarations / 1,929 theorem
declarations**. It does not verify Python, SQL or machine costs.

```sh
python3 -m unittest discover -s solver -v
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
python3 experiments/compare_cnf_positive_history.py --output /tmp/oracle-positive-history-new-run
```

Use a new output directory. The report records the preceding commit and exact
candidate/driver fingerprints. All earlier experiment files are left unchanged.

`history-replay.json` records the final archive-local version handle and exact
source hash for each of the 24 history snapshots. These were independently
reloaded from gzip, matched against their full input recipes, checked against
their source witnesses where SAT, and verified to retain identical row digests.
