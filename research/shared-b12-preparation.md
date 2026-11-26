# Sharing common B10 preparation inside B12 calls

Checkpoint: 26 November 2026. Sharing the common B10 prefix within B12 discovery
and, independently, within cold checking reduces complete measured census time
**39.24% for source order** and **39.65% for untested-first**. Both orderings
reproduce all fourteen saved results exactly, including clause provenance and
search counters. Coverage remains **232/246**, with **14 open**. This improves
replay cost without adding a new native certificate or changing either order.

## Exactness and ownership

The frozen B12 route validates the B11 history and the continued B10 history
separately. Both paths reconstruct the same B10 bank from the same 21 inputs
and three closures. The candidate privately copies all 24 inputs, five closures,
and supplied cursor or result, then prepares the common B10 prefix once.

It independently checks the original B10 and comparison B10 programs, cursor
bindings, schedules and failed-probe proofs on their original bank. Different
trace allowances receive different bindings. The common clauses, provenance,
residual and source order do not depend on this allowance; only the B10 binding
and its unused no-change comparison do. Original B10 failures then construct
B11 in the frozen insertion order. B11's closure and history are independently
checked. Comparison B10 and B11 failures construct B12 in the same order as
before, preserving duplicate-clause origin selection. B12's complete closure,
source/untested-first order, policy binding and search engine remain unchanged.

Thus the two duplicated preparations become one, while all three distinct upper
histories retain independent checks. Lower histories are checked once through
the common preparation. No caller-provided verified marker is accepted. Cold
checking starts again from portable owned inputs; discovery confers no authority
on the checker. Source, proof, closure-trace, bound, schedule and binding edits
are rejected or trigger reconstruction as appropriate. Alternate valid closure
orders remain distinct. Old open completions are scheduling hints, never SAT
certificates or evidence of semantic exhaustion.

The final audit compares every prepared bank and origin tuple with frozen B12
validation and the prior independent reconstruction from lower-bank routines.
It also compares every result to the preserved result from the parent checkpoint.

## Matched measurements

Two isolated repetitions run all six modes in opposite order. The fourteen
inputs are already exposed research cases. `Shared discovery` changes discovery
only; `shared both` independently prepares again during cold checking. These
are matched replay results, not held-out performance or a production default.

| Order / preparation | Reconstruction (s) | Discovery (s) | Cold checking (s) | Persistence (s) | Complete census (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| source separate | 0.16299 | 0.36323 | 0.35923 | 0.00541 | 0.90794 |
| source shared discovery | 0.16564 | 0.18739 | 0.36588 | 0.00492 | 0.73612 |
| source shared both | 0.16557 | 0.18832 | 0.18233 | 0.00501 | 0.55167 |
| unseen separate | 0.16347 | 0.36726 | 0.36065 | 0.00646 | 0.91505 |
| unseen shared discovery | 0.17009 | 0.19088 | 0.37058 | 0.00636 | 0.74884 |
| unseen shared both | 0.16660 | 0.18777 | 0.18062 | 0.00638 | 0.55221 |

Shared-both discovery improves **48.15% / 48.87%**, and checking improves
**49.25% / 49.92%**, for source / untested-first respectively. Each improves on
all fourteen case-level means. Unchanged reconstruction is **1.58% / 1.91%
slower**; persistence has eight / six individual regressions despite lower
aggregate times. Shared-discovery leaves the checker unchanged, with ten / nine
checking case regressions. All case-level data and regressions are retained.

Common context preparations fall **28 → 14** per ordering's discovery census,
and likewise for shared cold checking. There are **42 distinct upper-history
checks** per census. Search remains **192 probe attempts**, **1,946 imported
completions**, and **5,650 / 6,686 occurrence visits**. Both complementary B12
proof histories and the later joint closure remain in the unchanged frontier.

Source-order results remain **154,254 bytes**, untested-first **154,210 bytes**.
Peak process RSS is **98,467,840 → 98,451,456 bytes** for source order and
**98,369,536 → 98,467,840 bytes** for untested-first. There is no material
peak-memory improvement. This is reduced repeated work, not proof compression.

The timed census charges source reconstruction, owned preparation, recognition,
search, serialization/reload and a cold proof check. Startup/input loading,
historical acquisition, pilots, native compilation and final lineage auditing
are additional. Timed censuses ran before the regression suite; final validation
ran alongside tests, so its elapsed time is an audit diagnostic, not a benchmark.

## Resource scope and next target

If common B10 preparation costs `P`, and distinct upper-history checks and bank
construction cost `V + A`, the duplicated portion changes from `2P + V + A` to
`P + V + A`, with fewer ownership copies too. It does not bound `P`, historical
proof growth, native compilation or arbitrary SAT by a uniform polynomial.
Every separate call still checks its inputs. No persistent trusted cache is added.

After sharing, reconstruction accounts for roughly **30%**, discovery **34%**,
and cold checking **33%** of measured total time. The duplicated prefix no longer
dominates this call. Repeated graph prefixes across future layers remain a design
risk: they should be shared only where identical source-derived dependencies are
explicit, preserving each distinct program's binding and original-bank check.

The next coverage target is the stronger `(67,63)` closure from both B12 orders,
which forces local variables 68=true and 83=false. Compare expansion from this
joint closure with continuing both saved B12 schedules, using this cheaper
preparation. Preserve unfinished `(1,15)` and `(37,39)` histories. Eleven exhausted
unchanged orders require stronger interactions or a different decomposition;
more repetition of an unchanged exhausted order cannot provide new coverage.
The earlier native-compilation regression at `(28,18)` remains open.

## Preservation and validation

Resume `experiments/results/cnf-shared-b12-preparation/checkpoint.json`, field
`shared_b12_preparation.remaining`, using
`compare_cnf_b12_progress_order.load_frontier`. It references the unchanged
**13,386-byte** B12 overlay and its **3,560,471-byte** transitive frontier data;
no duplicate resume export is created. Native archives and other retained files
are additional. New experiment diagnostics increase lifetime storage.

The audit preserves **1,171 earlier source fingerprints** and **30,651 artifact
entries in 210 manifests**. Four new source files bring the ledger to 1,175.
Reference/cumulative tables, all native archive bindings and both prior proof
sets remain unchanged. No new cumulative native records or archives are claimed.

Nine new tests cover both historical orders, every original history and closure,
different trace allowances, cold/interrupted continuations, policy isolation,
caller mutation after ownership transfer, proof corruption, alternate valid
closure traces and small-model checks. The latter enumerates all 256 subsets of
eight signed unit/binary clauses on two variables plus seventy generated
five-variable formulas, simplifies units, and compares both routes on applicable
unresolved histories with exhaustive models. This is not exhaustive general SAT.

All **2,127 tests** and **36 focused tests** pass. The full suite reports 44
SQLite resource warnings (43 in the parent run); the focused suite has none.
No SQLite implementation changed. The manuscript builds without
LaTeX warnings; all 64 existing proof blocks remain byte-identical. Machine-readable
protocol, pilot, paired census, audit, decision and checks are in
`experiments/results/cnf-shared-b12-preparation/`.
