# Frozen external transfer and exported root exclusions

The constructed-panel gain does **not** yield more answers on the new external
sample: both frozen repair policies certify **8/24 originals and 4/12 derived
controls**, with identical answered sets. Mean complete cost changes **−0.92%**
with mixed paired signs, so no reliable transfer speedup is claimed. Conditional
proof storage and replay grow substantially. The new evidence exposes fourteen
inputs unresolved by both kernels and the independently checked full portfolio.

A separate concrete improvement exports six completed root refutations that the
repair wrapper had discarded. It gives the repair kernel **six additional checked
UNSAT answers**: four originals and two controls. These overlap the older
portfolio's negative coverage; they do not increase the combined portfolio union.
The post-transfer follow-up keeps the 20,000 total-state cap by charging fresh
acquisition and a bounded proof-recording replay. Earlier results and the frozen
comparison are unchanged.

## Selection, controls and unchanged policies

The source is the public [SATLIB benchmark collection](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html).
Before downloading new contents or evaluating them, freeze zero-based
lexicographic member indices 10, 30, 60 and 90 from each of `uf50-218`,
`uuf50-218`, `uf75-325`, `uuf75-325`, `uf100-430` and `uuf100-430`. This gives
24 originals. Add one sparse signed permutation and one deletion/literal-flip
edit of the first selected source per group, yielding twelve related controls.
Signed substitutions preserve satisfiability; edited truth is not inherited.

Selection is size-limited and nonrepresentative. Exact canonical comparison finds
no overlap with the previous 37 external, 32 constructed or 182 synthetic inputs,
and no exact duplicate in the new panel. This is not an all-history novelty or
semantic-isomorphism claim. Raw selected bytes, archive hashes, member names,
indices and deterministic transformations are retained. Only parsed clauses
reach discovery; labels, file names, truth results and IDs do not choose search.

Baseline is the unchanged 20,000-state disjoint search. Boundary repair keeps its
10,000-state prefix, remaining shared budget and eight-round maximum. Every
proposal and index is acquired afresh. No parameter, ranking or solving rule is
retuned on the new sources. The paired trial preserves conditional evidence and
rechecks every model against its original raw source. Both kernels still return
SAT or unknown; a publisher label or completed but unrecorded search does not
supply an independently checkable UNSAT certificate.

## Transfer measurements

Four fresh-process pairs alternate mode order. Timing charges raw DIMACS reads
and hashes, preparation, search, internal and explicit checks, proof/sidecar
writes, three compressions, warm and two cold reload/checks. Cold passes have no
surviving search state; OS caches are not flushed. Download, imports/startup,
reporting metadata and independent reference runs are additional.

| Measurement | Disjoint baseline | Boundary repair |
|---|---:|---:|
| Original SAT / unresolved | 8 / 16 | 8 / 16 |
| Signed-control SAT / unresolved | 2 / 4 | 2 / 4 |
| Edited-control SAT / unresolved | 2 / 4 | 2 / 4 |
| Explored states | 430,480 | 422,860 |
| Mean complete seconds | 11.06400 | 10.96200 |
| Acquisition/internal checks | 10.86008 | 9.55053 |
| Explicit checking | 0.02620 | 0.26806 |
| Warm replay | 0.05027 | 0.31467 |
| Two cold replays | 0.09521 | 0.61522 |
| Model JSON bytes | 20,171 | 20,164 |
| Discovery JSON bytes | 78,339 | 5,510,680 |
| Combined gzip bytes | 2,027 | 478,862 |
| Maximum observed RSS bytes | 33,325,056 | 78,151,680 |

Paired complete-cost changes are **−2.01%, −0.76%, +0.87%, −1.79%**. Acquisition
improves, but checking, replay and persistence consume most of the savings.
Identical answered sets need not have identical model assignments or compressed
bytes. Four original SAT cases at 50 variables and four at 75 variables are
solved; all four 100-variable SAT originals remain unresolved in both kernels.
There are no newly gained or lost SAT answers. Equal state caps remain unequal
units of computational work. No fresh-CDCL speedup or complete-solving ratio is
inferred from these incomplete-policy timings.

## Separate reference checks and the remaining interactions

One fresh process per input runs the unchanged full portfolio, and another runs
Z3 5.4.1 with fixed random seed zero and a 10-second solver timeout. Each process
has a 30-second outer timeout; none fires. Portfolio outputs receive independent
project certificate checks. All Z3 SAT models are checked against raw clauses;
its UNSAT outputs are **trusted reference results, not project-checkable
refutations**. Publisher labels agree where available. Edited inputs are checked
separately, and signed SAT models transport back to their originals.

The portfolio certifies **9 SAT and 10 UNSAT**, leaving 17 unresolved. Z3 returns
**18 SAT and 18 UNSAT**. Process totals are 55.67782 seconds for the portfolio and
3.07527 seconds for Z3, including process startup. These one-shot reference runs
do not perform the paired persistence/replay workload and do not support a
speedup ratio. Z3 models are not counted as structural transfer coverage.

Combining the independently checked portfolio with either repair kernel gives
**12 SAT + 10 UNSAT**, leaving **14 unresolved**: nine originals and five controls.
The original union is **15/24**; controls contribute **7/12**. The unresolved set
contains six reference-SAT and eight reference-UNSAT inputs:

| Group | Remaining IDs | Observed final free-set sizes |
|---|---|---|
| 75-variable UNSAT original/control | t013, t030 | 69, 72 of 75 |
| 100-variable SAT originals | t016–t019 | 88, 100, 95, 94 |
| 100-variable UNSAT originals | t020–t023 | 88, 99, 95, 94 |
| 100-variable SAT controls | t032, t033 | 85, 100 |
| 100-variable UNSAT controls | t034, t035 | 83, 88 |

Every unresolved source has one primal connected component. These are observed
policy widths, not minimum separators or irreducibility proofs. Retained complete
near-models and their false-clause indices carry no SAT authority. Width and
connectedness describe the remaining coupling; they do not by themselves provide
a tractability classification or a lower bound for arbitrary algorithms.

## Completed root refutations: a separately charged improvement

The frozen prefix exhausts its entire full-support root search on six inputs,
but `record=False` discards the proof nodes. This is a certificate-export gap,
separate from cases that exhaust their state allowance. The additive exporter
runs the unchanged boundary policy afresh. Only when its **root prefix** returns
`radius-exhausted`, it reconstructs the same seed and repeats that closed
traversal with recording enabled and a cap equal to the observed state count.
The independent old exclusion checker must accept the original source and a
radius covering every source variable. Local exclusions, partial-radius balls
and budget exhaustion are never promoted to global UNSAT.

If the first closed traversal takes `k ≤ 10,000` states, the replay takes the same
`k`, so both together use `2k ≤ 20,000`. All source scans, preparation, checks,
proof writes and replay costs are additional to state accounting and are timed.
This is a post-transfer follow-up chosen after observing discarded refutations,
not a result of the untouched frozen-policy comparison. It changes no production
default, search ordering or source selection.

The exported negatives are **t004–t007, t026 and t027**, with combined state
counts **6,272, 7,344, 9,058, 8,174, 9,220 and 6,594**. Recording replays add 23,331
states across the panel, bringing the follow-up total to 446,191. All twelve SAT
answers remain; the exporter returns **12 SAT, 6 UNSAT, 18 unknown**. The six new
kernel negatives were already certified by the older portfolio, so the combined
22/36 union remains unchanged. Their complete refutations are reusable evidence
subject to fresh checking against the current source.

The single complete follow-up costs **11.87175 seconds**: acquisition/internal
checks 10.11165, explicit checks 0.35007, warm replay 0.39526 and two cold replays
0.79990 seconds. Model/refutation JSON occupies 2,448,128 bytes, discovery JSON
5,510,680 bytes, and combined gzip 739,493 bytes. Peak RSS is 86,212,608 bytes.
This is one separately measured workflow, not a matched speedup claim. Persisted
historical evidence remains additional.

## Validation and next priorities

All **2,552 full and six focused tests pass**. The export audit checks all 512
canonical two-variable CNFs against truth tables: **95 SAT and 417 UNSAT**, and
rejects partial-ball promotion. Validation reproduces all eight frozen transfer
runs, their counters and cold replays, and all 36 export runs. Input tests verify
bijective signed transport, raw/parsed consistency, hash invalidation, empty and
sparse inputs, and unknown-versus-UNSAT separation. Source edits require fresh
validation through the existing independent source checker.

The checkpoint preserves **246 prior manifests, 82,741 artifact entries, 1,341
scientific sources and all 86 manuscript proof blocks**. The old external 37/37,
constructed 32/32 and synthetic 182/182 unions remain separate and unchanged.
An initial supplementary validator path comparison confused absolute and relative
paths; its failed log is retained and the comparison now checks equal digests
and resolved paths. No timed solving source or recorded outcome was changed.
Existing unclosed-SQLite warnings remain in the full-test log.

**Largest next gaps:** explain the six known-SAT misses and eight reference-UNSAT
misses without hiding extra acquisition; reduce nearly full-width interactions;
compress or reuse conditional negative proofs, whose storage/replay costs grew
sharply; and integrate economical global negative evidence without repeating
completed work. Further transfer needs newly frozen inputs after any policy
change. Efficient recognition, preprocessing, compact certificates and unrestricted
SAT expansion remain open; finite coverage is not an efficient general solution.

Resume `experiments/results/cnf-boundary-transfer/checkpoint.json`, key
`boundary_transfer`.
