# One-pass independent checking and the next coverage opportunity

`SinglePassCheckInventory` replaces repeated reconstruction scans with one direct
pass, allocating a buffer only when a false occurrence must be removed and sharing
untouched immutable clause tuples. It uses no discovery index and adds no retained
cache. All unit reasons, conflicts, fixed points and pure rounds remain checked.
The [correctness/resource account](../../../research/single-pass-checking.md)
states the prefix invariant, copying costs and limitations.

## Matched full result

Both modes use indexed restriction, ordered propagation and the same 1 MiB
probe-check cache. All **1,497 answers, profiles, roots and archive bytes agree**.
Coverage remains **869/985 non-tiny sources**, with **116 sources / 148 selected
leaves / 33,651 literals** unresolved in the integrated inventory.

| Measurement | Indexed baseline | One-pass checker |
| --- | ---: | ---: |
| Total operation seconds | 137.78680 | 130.04664 |
| Discovery seconds | 93.90373 | 87.70857 |
| Ordinary solver seconds | 43.80997 | 42.26890 |
| Cold replay seconds | 57.32273 | 57.93447 |
| Warm inventory seconds | 0.29315 | 0.31028 |
| Initialization seconds, separate | 0.00131 | 0.23600 |
| Six-case Python peak bytes | 24,072,934 | 24,073,162 |
| Six-case retained Python bytes | 23,447,297 | 23,447,589 |
| SQLite bytes | 437,620,736 | 437,620,736 |

Discovery improves **6.60%**, total **5.62%**. The ordinary solver uses the same
path; its timing variation is included in total. Cold replay **regresses 1.07%**,
and warm replay also increases. These are one sequential full sample per mode,
not significance or industrial-performance evidence. Six-case peak differs by
only **228 bytes** and retained traced memory by **292 bytes**; this does not
establish a whole-process memory saving. It excludes native SQLite and RSS.

Twelve-query **ABBA BAAB** fresh-database controls average **4.56834 -> 4.35803 s
total (4.60%)** and **4.26007 -> 4.03725 s discovery (5.23%)**, four trials per
mode. Solver means are 0.30687 -> 0.31931 s. Timings overlap: baseline totals range
4.38895--4.67657 s, candidate 4.27284--4.50458 s. Within-mode counters and database
hashes repeat exactly. This selected subset supports the saving without replacing
the full result or its replay regressions.

## Work, copying and limits

Full candidate operation has 179,919 reconstruction calls, 396,183 checked
assignment entries, 18,338,248 clause positions and 50,055,987 actual visited
literal occurrences. It shares **15,777,372 clauses / 44,643,882 literal
occurrences**, rebuilds 773,494 clauses, drops 1,786,944 clauses, and copies
1,609,390 logical pending-buffer/output entries. There are 840 reference-scan
literal charges from calls outside the scoped candidate; no unusual-input
fallback occurs in this corpus. The baseline charges 51,574,914 input literals,
but that counter does not separately count its generator passes. These are
different operation categories, not a claimed primitive-operation speed ratio.
Every non-reconstruction operation counter is unchanged.

Prefix slices, list construction and tuple conversion copy references in
addition to the logical buffer-entry counter. A partially built buffer may be
discarded when a later true literal satisfies its clause. All such work is timed.
The worst-case O(1+A+m+L) conditional word bound is unchanged, for A assignments,
m clauses and L literals. Shared immutable tuples reduce transient copying,
not the already retained source or persistent proof size.

Forty-eight helper controls vary 16/64/256 clauses, widths 3/32 and eight stream
families. Every 32-query trial starts fresh; two reversed-order samples per mode
compare the scan, selected method and rejected support cache. At 256 clauses:

| Width / stream | Scan ms | One pass ms | Support cache ms |
| --- | ---: | ---: | ---: |
| 3 / sparse reuse | 4.33898 | 2.40483 | 1.61625 |
| 3 / equal new objects | 4.38952 | 2.41142 | 9.85410 |
| 3 / all clauses affected | 4.71375 | 3.47677 | 7.53040 |
| 32 / sparse reuse | 17.40710 | 14.80994 | 2.36685 |
| 32 / equal new objects | 17.58915 | 14.88975 | 33.28913 |
| 32 / all clauses affected | 21.06652 | 22.12113 | 24.90298 |

Five of 48 one-pass controls regress, including all three sizes of wide affected
clauses and two small early-satisfaction cases. At width 3, sparse-control Python
peak falls 42,392 -> 7,032 bytes, but fully affected clauses grow 38,384 -> 43,496.
At width 32, sparse peak falls 160,936 -> 7,296, while affected peak grows
157,160 -> 162,504. Mutable clauses require copies. Control allocation excludes
preconstructed inputs and retains the last output; these helper results are not
full-workload memory measurements. The cache wins some warm controls, but loses
on novel equal objects and in both full-acquisition pilots; all failed evidence
is retained in the linked preceding studies.

The new full run selects source **1446** as its slowest unresolved baseline case.
Separate instrumented discovery is 2.16326 -> 2.14334 s. Reconstruction cumulative
time falls **0.37732 -> 0.29957 s** for 1,063 calls, and complete simplification
checking 0.38577 -> 0.30865 s for 1,195 calls. The candidate helper still has the
largest named own time (0.20778 s). Normalization has 678 calls / 0.15782 s own /
0.40226 s cumulative; propagation 1,125 / 0.13218 / 0.20934; indexed subset
certificates 110 / 0.12360 / 0.16593. These are diagnostic profiles, not primary
timings, and nested cumulative costs must not be added. Further scalar cache
tuning should not displace new structural discovery.

## Concrete next coverage target

`polarity-frontier.json` is a separate read-only probe of the 148 selected
unresolved leaves. **35 leaves (369 clauses / 852 literals)** admit consistent
variable flips making every clause Horn. The probe constructs 32,018 pair
constraints across all leaves and takes 0.02850 seconds for construction, SCC
solving and certificate replay, excluding loading, serialization and self-tests.
This is an established recognition reduction; see
[Mannila and Mehlhorn (1985)](https://people.mpi-inf.mpg.de/~mehlhorn/ftp/RenamingHorn.pdf),
which presents Lewis's pair-constraint characterization. We do not claim its
novelty or implement that paper's faster graph representation.

Every positive flip list is checked directly on all source clauses. Every negative
result replays two implication paths refuting the **auxiliary pair formula**;
it excludes this renaming class, **not satisfiability of the original CNF**.
The script also enumerates all flips for all 512 normalized two-variable formulas.
Pair generation costs the sum of binomial clause widths, and leaves most remaining
literals unresolved. The 35 positives are opportunities, not 35 new root closures:
policy integration, exact model transport, persistence/cold checks and root
recomposition have not yet been performed. This is the next ranked discovery gap.

## Validation, provenance and reproduction

All **433 Python tests** pass. The new eight tests include 175,032 exhaustive
reconstruction/assignment/fixed-point combinations per candidate, all compatible
complete truth assignments, 2,048 complete-checker policy cases and 8,000 seeded
random/edited reconstruction-policy comparisons. They check forged reasons,
conflicts and omitted fixed points, mutable edits, type aliases, shared outputs,
scope restoration, independence from discovery, all 148 saved frontier proofs,
byte-identical archive construction and cold corruption rejection.

Both full modes cold-audit 25,047 pattern nodes, 1,465 source bindings and 21,838
ordinary solver residuals. They preserve the earlier archive hash
`1a431206ef825d2a8f7d5697cf1342119fe68d97950ca6ca8f180d18b6bdccf3`
and reference that archive rather than duplicate it. Warm replay inserts nothing.
The implementation checkpoint is `d0b8917`; the full report has **75 source
fingerprints**, and timing/profile/controls/frontier diagnostics have their own
script and input hashes. All earlier experiments and unsuccessful prototypes
remain; the latter have explicit source snapshots and invocation records.

The manuscript preserves all 58 preceding proof blocks and adds the reconstruction
invariant. Lean sources are unchanged and were not rebuilt. This is not a formal
Python refinement or an unrestricted-SAT construction. Benchmarks, profiling,
allocation and the next-gap probe run sequentially.

```sh
python3 experiments/compare_cnf_single_pass_check.py --output /tmp/new-single-pass-check
python3 experiments/recheck_cnf_single_pass_check_timing.py /tmp/new-single-pass-check
python3 experiments/analyze_cnf_single_pass_check.py /tmp/new-single-pass-check
python3 experiments/measure_cnf_single_pass_check_controls.py /tmp/new-single-pass-check
python3 experiments/probe_cnf_polarity_frontier.py /tmp/new-single-pass-check/polarity-frontier.json
```
