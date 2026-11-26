# Sharing B8 preparation within checked B10 calls

Checkpoint: 26 November 2026. Reusing the common B8 preparation inside B10
discovery and, independently, inside cold checking reduces matched complete
runtime **39.30%**, from **1.06922 s to 0.64904 s**. All sixteen historical B10
results, clause banks, origins and search counters are unchanged. This is a
replay-cost improvement: coverage stays **232/246**, with **14 open**. The two
already certified roots remain in the sixteen-case matched workload.

## Why this sharing is exact

The previous implementation validates the B9 history and the newer B8 comparison
separately. Both reconstruct the same B8 prefix from the same eighteen original
inputs and closure. Profiling confirms 32 shared-joint preparations for sixteen
discovery calls. The new implementation performs sixteen.

The call first privately copies its inputs, all closures, and any supplied cursor
or result. It reconstructs the common B8 clauses and provenance once, then checks
the original B8 program and the B8 comparison independently on that bank. Each
keeps its original trace allowance and full binding. If their allowances differ,
the comparison receives a distinct binding: the bound changes the binding but
does not change the common clauses, provenance, residual order or source inputs.

Next, the original B8 failures construct B9 in the original insertion order.
The B9 closure, binding, deterministic schedule and original-bank proof reasons
are checked independently. Checked comparison B8 and B9 failures then construct
B10 in exactly the frozen order, including duplicate-clause origin selection.
Its complete supplied closure is checked, and the existing search engine runs
with the unchanged policy, bounds and serialized format.

Thus each distinct input history still has a proof check on its original bank.
The only omitted work is a second reconstruction/check of the identical shared
prefix. Three upper histories are checked per call, while the common lower
histories are checked once. Equality with the frozen implementation is verified
for every prepared bank and origin tuple, not merely the final verdict.

No caller-provided verified marker or prepared state is accepted. Each cold check
starts again from copied portable inputs; no authority passes between discovery
and checking. Changed sources, histories, closure traces, bounds, cursor bindings
or schedules are rechecked. Invalid proof reasons are rejected. Open completions
remain scheduling hints, never SAT certificates or proof of semantic exhaustion.

## Matched measurements

Two isolated repetitions run in opposite mode order. `separate` is the frozen
B10 implementation; `shared discovery` changes only discovery; `shared both`
uses a fresh shared preparation again in the independent cold check. Every result
also passes the frozen full validator during the final audit.

| Measurement | Separate | Shared discovery | Shared both |
| --- | ---: | ---: | ---: |
| Source reconstruction (s) | 0.21076 | 0.21109 | 0.20871 |
| Discovery, including preparation (s) | 0.42215 | 0.22290 | 0.21272 |
| Independent cold checking (s) | 0.41358 | 0.41542 | 0.20808 |
| Serialization/reload (s) | 0.00752 | 0.01100 | 0.00797 |
| Complete census (s) | 1.06922 | 0.88594 | 0.64904 |
| Serialized result bytes | 189,782 | 189,782 | 189,782 |
| Peak process RSS (bytes) | 99,287,040 | 99,500,032 | 99,467,264 |

Sharing both paths reduces discovery **49.61%** and checking **49.69%**; both
improve on all sixteen case-level means. Persistence is **5.90% slower** in the
shared-both arm and eleven unchanged-checker case means regress in the
shared-discovery arm. The reports preserve these variations. Process RSS is
slightly higher, so no peak-memory reduction is established. Startup/input
loading, historical acquisition, profiling, the pilot, native compilation and
final lineage auditing are additional to the census totals.

The exact search work remains **258 probe attempts**, **14,406 occurrence visits**
and **1,946 imported completions** in every mode. Common prefix preparations
fall from **32 to 16** per discovery census; shared cold checking makes the same
reduction. The new upper-history counter records **48 independent checks**.
The benchmark neither changes the bounded search frontier nor repeats a claim
that the previous two refutations were newly discovered here.

## Resource scope and next target

If the common B8 preparation costs `P`, and the three distinct upper history
checks plus B9/B10 construction cost `V + A`, the duplicated preparation portion
changes from `2P + V + A` to `P + V + A`, with fewer ownership copies too. This
is an exact local saving, not a polynomial bound on `P`, history size, native
context expansion or general SAT. The proof and result representations remain
unchanged. Lifetime storage still grows as experiment evidence accumulates.

After sharing, source reconstruction, discovery and cold checking account for
**32.16%, 32.78% and 32.06%** of total time respectively. The duplicated common
prefix is no longer the dominant avoidable cost. The remaining prefix/provenance
checking still costs work, and native reconstruction's earlier regression at
`(28,18)` is unchanged. This module does not replace the native feedback compiler
or the production solver's policy.

The next coverage targets remain `(37,39)` and `(67,63)`, whose closures gained
variables 112=true and 66=false in the preceding checkpoint. Use this checked
preparation when testing their next feedback layer. Preserve the unfinished
`(1,15)` order too. Eleven exhausted unchanged orders still require stronger
interactions or a different decomposition; exhaustion does not establish SAT.

## Preservation and validation

Resume `experiments/results/cnf-shared-b10-preparation/checkpoint.json`. Its
`shared_b10_preparation.remaining` binding points to the unchanged B10 overlay;
load it with `compare_cnf_b10_probe_cursor.load_frontier`. The overlay, all native
archives, reference/cumulative tables, **1,159 existing source fingerprints** and
**30,012 artifact entries in 207 manifests** are retained unchanged. The final
source ledger contains 1,163 entries. There are no new native records or archives.

Nine new tests cover exact historical replay, independent original-bank checking,
different trace bounds, alternate valid closure ordering, cold and interrupted
continuation, private ownership, malformed histories/results and generated inputs.
Exhaustive signed unit/binary formulas on two variables plus seventy generated
five-variable formulas are unit-simplified before applicable open histories are
constructed; returned failures/refutations agree with exhaustive model checking
and the frozen implementation. All **2,100 full tests** and **52 focused tests**
pass; existing SQLite ResourceWarnings remain in the full suite. All **64 original
manuscript proof blocks** are unchanged.

For fresh timing runs, first copy the frozen `pilot.json` and `pilot-source.py`
into a new output directory. Run `prepare` and `run_census` through
`experiments/compare_cnf_shared_b10_preparation.py`, then `validate` through
`experiments/validate_cnf_shared_b10_preparation.py`. Retain the output and run
the tests/build before `seal`; do not overwrite this checkpoint's frozen reports.
