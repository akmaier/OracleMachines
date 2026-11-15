# Mixed terminal classes after conditional reduction

The previous case-1120 checkpoint left both targets of a **25/96/309** split
pending. This continuation keeps the original **39/162/510** focus and resumes
the exact saved pair before choosing further work. Two independent histories
use the unchanged worker and two 32-entry allowances. The second repetition
runs under cProfile to locate costs; its timings are diagnostic and are never
averaged with the ordinary repetition.

## Structural progress

The ordinary run stores **16 patterns** in its first batch and **19** in its
second. The two new terminal formulas belong to different recognized classes:

| Terminal | Recognized classes | Excluded classes relevant here |
| --- | --- | --- |
| 7 variables, 7 clauses, 19 literals | Zero-valid | Horn, dual-Horn, 2-CNF, one-valid |
| 6 variables, 6 clauses, 12 literals | 2-CNF | Horn, dual-Horn, zero-valid, one-valid |

These are checked reductions of conditional inputs, not supplied family labels.
The two cofactors need not end in the same tractable class. Neither terminal
is Horn or dual-Horn; the second requires more than testing either uniform
assignment. The experiment extends the retained decomposition of this input,
not the list of recognition algorithms or a complexity guarantee for arbitrary
CNFs. The separate reference solver's SAT witnesses do not discharge missing
structural obligations.

The union adds **35 patterns**: eighteen elimination, eleven probe, four
binary-path and two family nodes. The first batch interrupts sixteen inputs;
they are reentered and charged in the second. There are **64 admissions across
the two budgets / 48 distinct entered inputs**, with **13 final inputs** still
lacking stored pattern certificates. A bounded retry cannot count an incomplete
recursive frame as a reusable result. Cold replay confirms that the second
batch reuses all sixteen certificates from the completed false cofactor while
acquiring nineteen for the true cofactor.
All nine inputs interrupted at the preceding checkpoint are now stored as well.

The 25-variable interaction closes, but the enclosing focus stays open and
original-input coverage remains **66/83**. Work proceeds to another interaction
with **34 variables / 120 clauses / 355 literals**. Both targets are pending:
**31/102/295** and **31/104/295**. Resume that saved pair rather than selecting a
replacement split. The remaining work is a structural decomposition obligation,
even though the reference solver can answer these specific inputs.

## Where the remaining time goes

The ordinary two-batch sequence costs **17.86459 s** in workers, or **18.12464 s**
including sequence bookkeeping. Its measured phases are:

| Phase, summed over two batches | Seconds |
| --- | ---: |
| Preparation | 17.31958 |
| Initial session construction and both boundary guards, within preparation | 7.54351 |
| Expansion | 0.34281 |
| Acquisition, within expansion | 0.12987 |
| Append export | 0.03214 |

The second repetition produces the same logical work under instrumentation.
In its first batch, initial checked session construction takes **22.17872 s**
of **27.75842 s** reported by cProfile. In its second batch, the checked session
already exists, but recomputing table digests takes **3.78143 s** of **4.78940 s**.
That call scans all eight exported tables in key order. The table-digest loop
has **3.54659 s** own time, while SHA update calls take **0.18191 s** across the
whole second worker. This points to the full ordered scan and digest construction,
not just the hashing primitive. Snapshot copying takes **0.13202 s**, the append
boundary **0.01045 s**, and the retained session guard **0.00393 s** in that
profile. Nested cumulative times are not additive. Profiling adds overhead;
these figures identify the call path and establish no runtime reduction.

The next concrete cost investigation should measure the individual tables and
compare guarded reuse of unchanged table digests against complete rescanning
on the same expansion. A cached digest is valid only for the same verified
snapshot with no unaccounted writes, schema changes or external modification.
Changed tables need recomputation or a separately checked incremental structure.
The current digest hashes rows in key order: hashing a new suffix does not in
general update it, because new keys may sort between historical keys. Charge
recognition of unchanged tables, guards, maintenance, export and cold replay.
Initial authority checking remains a separate cost.

The complete producer costs **254.45498 s**, including **109.96162 s** historical
restoration and **68.75357 s** final route preparation/global coverage. This
includes both the ordinary and instrumented sequences and profile output; it is
not an ordinary end-to-end runtime benchmark. No comparative speedup or
holdout estimate is claimed.

## Persistence and resumption

History grows **430,080 bytes** to **778,416,128 bytes / 42,303 patterns**. The
union delta uses **487,424 SQLite bytes / 18,876 compressed bytes**. One new split
sidecar is retained; there are no new external probe rows. Reference evidence
grows **4,114 -> 4,153 nodes**, preserving every old payload. The global positive
certificate is byte-identical and remains at **3,360 steps**. The live index
has **708 routes / two missing-target links**. Persistent sizes are not peak RAM;
there is no established bound on total retained state or required batch count.

Resume `experiments/results/cnf-reduction-reuse/report.json` through
`continue_cnf_reduction_reuse.restore_checkpoint`, report SHA-256
`e6610fbbbbd52dcc6986ca8881f4e8aea1a3ba16ef33fb9beee5b42ec978337e`.
Preserve evidence **(1, 42, 156, 55, 1)** and **two bridges**. The bound
`next_selection` archive identifies the pending source with key hash
`1aa4a355993275a5aed0d3f263d5e5d2078b4fd6330ce9f8eb3d864fec88db6a`.
The original binding remains case **1120**, retained index **22**. The focus's
39-variable source and the pending 34-variable interaction are different keys.

The raw cProfile files, machine-readable call entries, readable listings and
`profile-summary.json` are retained alongside all operation records and deltas.
Run from the repository root into a fresh directory:

```sh
python3 experiments/continue_cnf_reduction_reuse.py /tmp/cnf-reduction-reuse
python3 experiments/validate_cnf_reduction_reuse.py /tmp/cnf-reduction-reuse
```

## Validation

Independent cold replay passes in **417.85190 s**, reproducing every intermediate
catalog, operation and logical result without fresh discovery or reference
search. All **4,153 reference nodes** verify and all **4,114 previous reference
payloads** remain unchanged. All **1,428 artifacts across 28 prior manifests**
are preserved. All **238 regression tests** pass. The manuscript builds to
**163 pages**, with no overfull boxes or undefined references and all **64
previous proof blocks** unchanged. The new manifest binds **65 artifacts**;
`validation.json` records commands, source fingerprints and timing scope.

The machine-readable profile entries match the raw pstats files, and the summary
matches those entries. Native pstats text listings retain their original blank
lines at the end; their bound bytes are preserved. Regression tests and the first
manuscript build ran after the producer, overlapping cold validation; a final
manuscript-only rebuild followed the replay findings. No new comparative
speedup, recognition algorithm or Lean refinement theorem is claimed.
