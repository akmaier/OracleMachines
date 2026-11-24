# Retire consumed preparation and account for what remains live

The preceding handoff experiment held an offer until its whole child visit
returned. Even after canonicalization and propagation consumed it, that offer
continued to occupy the preparation allowance. This experiment clears the
consumed references and separates that cleanup from a change in admission policy.

## Ownership and correctness

`ProbeLifetimeSolver` uses a private mutable lease. The producer still performs
the same exact restriction, canonicalization and deterministic propagation.
The existing parent identity, assignment, counter identity and actual-child
bindings select its consumer. After canonicalization, the native visit owns
its canonical formula, name map and key; the lease drops its raw and canonical
references. After propagation copies its assignment and trace, the lease drops
the remaining propagation reference. It becomes an empty object carrying only
state and charge metadata. This also clears data reachable through the earlier
expansion frame's local reference to the lease.

If propagation is never consumed, its lease stays charged until the visit ends.
An unvisited branch stays charged until its continuation discards it. Cleanup
also runs on exceptions and budget stops. Verification suppresses both the new
propagation binding and the earlier hint dispatcher; native proof authority,
pool priority, recognition and branch order are unchanged. A retired lease
cannot supply another result. Positive results still require full-source
witness checks, and a nonconflicting probe still gives no verdict.

This releases preparation references, not necessarily the underlying formula.
The native visit still needs its canonical formula, map and key; its Python
frames can also retain raw inputs. Clearing a lease alone therefore does not
prove that its full charged payload has left process memory.

## Three accounting questions and a capacity control

Every policy uses the same native 256-dispatch cap. The four arms are:

- **Retain:** the preceding immutable handoff with a 2 MiB full-visit allowance.
- **Clear:** clear consumed lease fields but keep their charge until the visit
  returns. This includes the mutable carrier, dispatcher and accounting changes.
- **Transfer:** use the same cleanup, but release its preparation charge after
  consumption, allowing new pending offers within 2 MiB.
- **Room:** retain the original implementation and increase its allowance to
  4 MiB, testing the simpler explanation that more capacity buys the reuse.

The transfer and clear arms differ only in their release policy. The mutable
lease has one additional state slot; the same conservative estimator charges
its actual header size. It avoids the immutable producer's replacement object.
Thus clear versus retain measures the combined carrier/cleanup implementation,
not a perfectly isolated reference-clear instruction.

Early release changes the scope of the bound. Besides its pending charge, we
record each released charge until the associated native visit returns. Their
maximum concurrent sum is the **full-visit accounting envelope**, comparable to
the earlier conservative accounting. It is not the sum of separate peak values. It can exceed 2 MiB. It overcounts shared objects and
includes some already freed data; it is not a measured heap size. Reporting it
prevents a lower preparation counter from masquerading as lower total memory.
Control containers, frames, allocator overhead and construction transients remain
outside the selected-payload cap. Retained solver graphs and worker RSS are
separate measurements.

## Exposed mechanism check and prospective protocol

An empty-start chronological replay through the preceding largest unresolved
case 37 (construction size 138) preserves every earlier result and proof payload.
The old 2 MiB policy consumes 11 offers and rejects 90. Transfer consumes 92,
discards 14 and rejects one, with a pending peak of 2,084,962 bytes and a
full-visit envelope of 3,923,426 bytes. The original 4 MiB control consumes 93
and rejects none, peaking at 3,923,242 bytes. All still stop at 256 dispatches.
The larger control nearly reproduces the increased reuse, so reuse counts alone
cannot establish a benefit from cleanup.

The protocol freezes four alternating serial repetitions on the exposed 114/138
stream and a fresh 120/144 stream with seed 202611240203. Each has 72 queries,
48 distinct roots and six construction families, without outcome filtering.
Search receives only source CNFs and earlier results from its own empty-start
stream. Parent-archive novelty supplies no answers. All recognition, misses,
sizing, copies, checking, persistence, serialization, warm/cold replay,
reconstruction, compression and worker RSS are measured. Worker timers start
after imports, source checks and case loading, and stop before final report
bookkeeping. The two 38-query diagnostics, cumulative audit and posthoc profiles
are excluded from matched timing means.

Exact models, dispatches, chronological publications and all six authority-table
payloads must match across arms, including proofs retained after budget stops.
No new certificate format, persistent hint, production default or tractable SAT
category is introduced.

## Matched results

Four repetitions give the following mean seconds. Changes compare with retain
on the same stream; neither stream is compared with a different-size stream.

| Policy | Exposed solve | Fresh solve | Exposed complete worker | Fresh complete worker |
|---|---:|---:|---:|---:|
| Retain, 2 MiB | 14.3310 | 18.7398 | 28.0744 | 38.1723 |
| Clear, 2 MiB | 14.4375 (+0.74%) | 18.7623 (+0.12%) | 28.3516 (+0.99%) | 38.0417 (-0.34%) |
| Transfer, 2 MiB pending | 13.6760 (-4.57%) | 18.0773 (-3.54%) | 27.6054 (-1.67%) | 37.4411 (-1.92%) |
| Retain, 4 MiB | 13.6428 (-4.80%) | 18.1255 (-3.28%) | 27.4300 (-2.30%) | 37.5269 (-1.69%) |

Every transfer and 4 MiB pair improves solve time. Exposed complete-worker
time has one slower pair for each (0.28% and 0.17%); all fresh worker pairs
improve. Transfer versus 4 MiB is mixed: solve mean is 0.24% higher exposed
and 0.27% lower fresh. These small differences do not establish that the more
complex lifetime policy is better than increasing the original allowance.
Cleanup without early admission brings no solve-time improvement.

Fresh transfer consumes 1,505 offers, against 994 for retain, and rejects 231
instead of 838. It reuses 1,256 propagation results instead of 811. The original
4 MiB control consumes 1,527 and rejects 211. All policies still size offers
through 2,094,512 literal visits. Transfer also copies 7,504 trace/assignment
entries rather than 4,134. Saved repeated scans therefore do not equal total
time saved. The clear control consumes two fewer offers than retain because its
larger mutable header crosses the admission boundary on those occasions.

All arms have identical results, models, dispatches, six-table payloads and
coverage: **42/48 exposed and 40/48 fresh distinct roots**. The new fresh stream
is harder for the fixed budget; this is not a loss caused by the lifetime
policy. Its eight still-unresolved roots comprise six random-three roots and
one edited source in each of disjoint-mix and shared-mix. Random-three consumes
53.80% of fresh transfer solve time; the two mixture families consume another
43.56%. No input receives these diagnostic family labels during solving.

## Memory and persistence

The fresh pending peak is 2,094,861 bytes, but the full-visit envelope reaches
**4,607,922 bytes**, above the original 4 MiB control's peak of 4,193,790.
Exposed values are 2,087,302 pending and 4,316,943 full-visit bytes. This is a
change in the scope of the allowance, not a demonstrated halving of memory.
If there are `d` transferred charges on active visits and the pending allowance
is `B`, each charge is at most `B`, so the conservative envelope is at most
`(d + 1) B`. The pending bound alone is independent of depth; the envelope is
not. Neither expression bounds all solver memory or construction transients.

Selected retained Python state is identical across policies: 248,400,985 bytes
exposed and 315,074,010 fresh. The respective native key-plus-payload sizes are
58,546,391 and 76,527,327 bytes, with 5,599 and 6,974 records. SQLite sizes are
90,890,240 and 117,870,592 bytes; compressed sizes are 6,995,653 and 8,769,102.
These are unchanged across policies. Instrumentation grows the fresh sidecar
from about 28.21 to 28.28 MB, so identical proof storage does not mean identical
experiment-log size.

Mean worker RSS ranges from 824.8 to 833.4 MB exposed and 1,172.5 to 1,198.6 MB
fresh. The fresh transfer mean is 0.96% below retain, while clear is 1.25% above
it. RSS includes acquisition, replay, reconstruction and reporting; these
differences do not isolate the much smaller offer payload. Fresh transfer cold
reconstruction also rises from 2.4434 to 2.6012 seconds despite identical proof
bytes, while cold verification changes from 7.3844 to 7.3328. All are included
in the complete-worker comparison.

## Exact-prefix profile and next discovery target

The largest mean unresolved fresh transfer attempt is case 37: an edited
144-variable, 612-clause random-three source, at 1.2852 seconds before
instrumentation. All four profiles reconstruct its exact chronological prefix
from empty state and retain the matched worker's payloads. The separate
allocation pass reconstructs that prefix again and starts `tracemalloc` only
immediately before this attempt, after garbage collection.

| Policy | Consumed offers | Rejected offers | Normalizations | Restriction scans | Native UP calls | Peak new traced bytes |
|---|---:|---:|---:|---:|---:|---:|
| Retain, 2 MiB | 5 | 102 | 797 | 916 | 354 | 27,181,906 |
| Clear, 2 MiB | 5 | 102 | 797 | 916 | 354 | 27,181,146 |
| Transfer | 67 | 32 | 735 | 854 | 303 | 27,324,505 |
| Retain, 4 MiB | 70 | 28 | 732 | 851 | 300 | 27,327,641 |

The allocation pass shows no substantial reduction: transfer is 0.52% above
retain and nearly identical to the larger original control. Existing prefix
objects, native memory and the profiler are excluded from these byte counts;
the attempt's new checked proofs and bookkeeping are included. This is one
diagnostic attempt, not a process-memory bound. All four still stop at 256
dispatches. Profiling runs outside matched timing means, alongside validation.
Function cumulative times overlap and do not supply independent phase totals.

The same attempt performs 145 binary SCC checks, finds ten binary-subset
refutations and has 135 satisfiable-subset misses. It also has 49 whole-probe
misses. Existing whole probes use cached negative results and unit propagation;
an inconclusive probe need not have a satisfiable binary core after its forced
assignments. **The next discovery step is a census of these exact probe
residuals**, including case 37 and the two unresolved mixture edits 61 and 67.
Test whether existing source-bound binary implication paths can refute a probe
before ordinary child expansion, including any required post-UP restriction.
Record both polarities, source mappings, recognition work and checks. A
satisfiable subset remains inconclusive. No such additional refutation or
coverage improvement has yet been demonstrated by this run. Only implement a
new gate if the census identifies useful cases; charge its many possible misses.

Case 61 also retains 20 of 25 leaves from a previous whole proof but exhausts
the acquisition budget on the remaining leaves. This gives a concrete mixture
control for any new recognizer, rather than assuming that more cache capacity
will close an uncovered interaction. The fresh unresolved roots are explicit
in `next-target.json`; repeats remain unresolved until a checked result exists.

For supporting runtime work, 372 negative-child checks account for about half
of canonicalization time in the case-37 profile. Earlier bounded proof memo
and ordered-normalization studies already price this opportunity and retain
mixed results. Consult them before proposing another general cache. The
remaining selected-state growth and persistence costs also survive this change.
Keep all four lifetime policies experimental; there is no evidence here for
making the more complex policy the default or for an efficient partition of
arbitrary SAT.

## Validation and preserved history

All 1,677 tests pass, including 66 focused checks. Independent readers audit
2,304 benchmark queries and 76 diagnostic queries, including every retained
prefix node and all 342 previous partition records. The source ledger and
parent manifests bind the earlier history; the cumulative archive retains its
original payloads and raw trial archives retain alternative proofs. The
checkpoint uses `experiments.cnf_archive_parts.restore_archive` for multipart
transport. This transport preserves bytes and does not compress the logical
history into fewer authoritative records.
The complete audit takes 1,018.6 seconds outside matched worker means. It
preserves all 157 preceding manifests and their 14,120 artifacts, then adds
6,962 native records and eight affine-negative records to the cumulative
union. The resulting totals are 139,745 native and 131 affine-negative records;
the four binary tables remain at 42, 53, 22 and 34 records. Current-stream proof
storage is equal across policies, but this cumulative research history grows.
The full suite retains 44 pre-existing SQLite ResourceWarnings; the focused
suite has none. The manuscript builds to 253 pages without warnings, and all
64 previous proof environments remain unchanged. No Lean theorem is changed
by this ownership implementation or by the empirical discovery hypothesis.
