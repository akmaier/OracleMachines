# Reuse conditional unit certificates inside a local cofactor

24 November 2026. This experiment holds the guided probe policy fixed and tests
whether saved unit-conflict traces can replace fresh propagation over the whole
cofactor. It introduces no new proof rule or default solver change. The parent
comparison and its regressions remain in [guard-probe-selection.md](guard-probe-selection.md).

## Exact transport and its boundary

Let a checked template consist of source clauses H and a unit refutation under
guard G. At a current probe, rho records the source assignments already fixed
on the path and the proposed probe value. Transport requires rho to extend G.
The current canonical child has an injective coordinate map from the remaining
source variables. Every clause of H that survives rho must occur, after that
map, in the actual child. A guard for the full source does not establish this
condition for a selected component or subset.

The implementation reduces the template clauses under rho and records their
actual child clause indices. It then walks the saved trace. A forced literal
already fixed to the same value needs no step. If rho fixes it to the opposite
value, its reason is a conflict after the preceding retained steps, and the
trace can stop there. Otherwise its renamed literal and actual reason index
are retained. If no earlier conflict occurs, the original final conflict is
renamed in the same way. The native unit-proof checker validates every result.

The justification is induction along the original unit trace. Before the first
opposite fixed value, each previous forced literal is either supplied by rho
or derived by a retained step. All other literals in the next reason remain
false. Thus the next step is either redundant, unit, or an earlier conflict.
The same argument applies to the final conflict. Additional child clauses
cannot invalidate a refutation using a contained subset. This argument assumes
the checked source proof and exact local containment; it grants no authority
to an unchecked coordinate hint.

A missing residual clause, unavailable coordinate, incompatible guard or
exhausted transport allowance falls back to the existing lazy probe. Empty-clause
canonicalization can remove other support clauses, producing a conservative
miss even though ordinary propagation immediately refutes the child. Satisfied
support clauses need no child representative. Source support is checked before
admission, and all surviving local support is required, even if a smaller prefix
would suffice. There is no general source-rewrite or semantic-equivalence search.

The implementation lives in `experiments/cnf_guard_certificate_solver.py`.
It extends the frozen guided solver and places transport after its checked-cache
lookup and before fresh cofactor propagation. Preparation, selection, pending
handoffs, lazy binary fallback, opposite-branch acquisition and split/model
composition retain their previous roles. Compiled template references are
released when the query returns or stops. Existing proof payloads are never
replaced in the cumulative history; alternative valid traces remain in the raw
trial archives.

## Accounting and comparison protocol

Four alternating serial repetitions compare the guided parent with direct
certificate reuse on all eight exposed edits. Each restores the causal prefix
immediately after its origin. All 395 templates were acquired previously;
later repeats, the cumulative union and the separate census bank never seed
these comparisons. Setup includes bank loading/copying. Solve includes source
validation, coordinate maintenance, matching, support construction, transport,
native checking, publication and fallback.

Complete-worker measurements additionally include database restoration,
retained-graph accounting, warm replay of new native nodes, full native cold
replay, serialization and compression. Imports, source hashing and case loading
are outside that interval; original acquisition/extraction and the subsequent
preservation audit are additional. Warm replay is a proof-cache measurement,
not a second whole-query completion. Separate traced reruns record ordered
visits, expansions, probe inputs and selector choices without contaminating the
four timed repetitions.

For a cofactor with L literal occurrences and a support of S occurrences and t
trace steps, constructing the child clause-position table costs O(L) expected
hashing work. Support restriction and renaming cost O(S), plus per-clause sorting
O(sum |c| log |c|); trace transformation costs O(t). Map construction, guard
scans, native checking, canonical preparation and persistence are additional.
Hash-table bounds are expected implementation bounds, not worst-case machine
proofs. The method avoids discovering a unit trace over the full cofactor, but
still reads that cofactor to bind reasons and validate the native certificate.

Each query allows 100,000 candidate checks and 1,000,000 reserved support
literals. These limits exclude guard-pair inspections, child position tables,
trace work, source validation, active maps and native proof checking. They do
not bound total runtime or memory. Retained checked-cache bytes, the compiled
bank graph before release, database bytes and process peak RSS are distinct
measurements. Sums across separate workers are neither simultaneous memory use
nor the deduplicated cumulative archive size.

## Result: less repeated propagation, little total-cost change

All 64 timed trials exhaust 256 native dispatches. Direct reuse transports 148
unit refutations, skips 566 already fixed steps and stops at three earlier
conflicts. It retains 1,946 transported proof steps. Fresh probe propagation
charges 3,009,722 literal visits instead of 3,634,460, a 17.19% reduction.
Fresh probe trace entries fall from 15,039 to 10,453; those counters exclude the
1,946 transported steps and must not be presented as total proof length.

| Edit | Guided solve, seconds | Certificate reuse, seconds | Change |
|---:|---:|---:|---:|
| 1 | 1.31720 | 1.32044 | +0.25% |
| 4 | 1.08959 | 1.11248 | +2.10% |
| 28 | 0.62161 | 0.62076 | -0.14% |
| 37 | 1.37764 | 1.35586 | -1.58% |
| 40 | 1.22349 | 1.18917 | -2.80% |
| 61 | 0.71159 | 0.70749 | -0.58% |
| 64 | 0.67237 | 0.66689 | -0.82% |
| 67 | 1.08873 | 1.08486 | -0.35% |

These are four-repetition means. Their sum falls from 8.10222 to 8.05796 seconds
(0.55%), while complete-worker mean totals rise from 91.92411 to 92.11039 seconds
(0.20%). Full native cold replay mean totals are 43.02102 versus 42.95018 seconds;
new-node warm replay totals are 0.002573 versus 0.002553 seconds. These small
differences do not establish a reliable end-to-end speedup. The comparison
controls for the existing guided policy; it does not remeasure the ordinary
default solver or establish a gain over it. No additional whole input finishes.

Transport scans 50,796 candidates and 89,649 candidate guard pairs. It constructs
52,837 clause-position entries charging 144,497 child literal occurrences, and
visits 7,147 support literals. Binding checks and repeated guard validation in
the transport helper add work beyond these diagnostic counters. No transport
budget or local-support miss occurs in these trials; adversarial tests retain
the required fallback cases. All 2,930 insertion attempts remain, with attempted
key-plus-payload bytes falling 0.0695%, from 35,384,318 to 35,359,725.
Both arms retain the same 2,875 new rows summed across separate workers; the
remaining attempted writes are rolled back at the budget stop. Their retained
key sets agree, so shorter local certificates do not add residual coverage.

Native checked-cache endpoint totals fall from 157,044,382 to 156,832,198 bytes
(0.135%). The bank graph including compiled template references charges
252,495--406,059 bytes per worker before those references are released. Summed
SQLite sizes fall by only 8,192 bytes, from 721,055,744 to 721,047,552; page
allocation masks most small proof reductions. Persisted payload totals fall
24,593 bytes, and compressed worker archives fall 10,331 bytes. Mean process
peak-RSS totals instead increase 1.67%; this experiment establishes no peak
memory reduction. The process measurement includes setup and cold replay and
is noisy; sums describe separate workers, not one resident working set.

The saved trace removes repeated discovery of a local unit conflict, but the
whole cofactor still needs preparation, exact reason binding and native checking.
Those costs, matching and the unresolved opposite branch limit the total saving.
Keep this mechanism experimental. The stronger next target is the interaction
structure of conditional regions with several unfixed assumptions, not another
unmeasured reduction in one local counter. The existing guard-frontier tree and
its unsuccessful comparisons must remain controls rather than be rediscovered.

## Validation and remaining coverage obligations

Tests enumerate all 512 subsets of the nine non-tautological clauses on two
variables, including the empty clause, then check conditional templates under
further assignments. Canonicalization collapses some inputs to the same formula;
this is exhaustive small-formula testing, not 512 distinct hard instances.
Additional tests cover skipped steps, early conflicts, missing component
support, invalid bindings/evidence, sparse source names, resource fallback,
unchanged empty-bank behavior and 40 seeded small formulas against truth tables.
The existing native checker remains the publication authority. This experiment
adds no Lean refinement proof.

All 1,740 repository tests and 96 focused tests pass. The full suite retains 44
existing unclosed-SQLite warnings; the focused suite has none. The manuscript
builds to 259 pages without warnings, with all 64 previous proof blocks unchanged.
Sixteen separate traced reruns reproduce their untraced arm's counters and
archive bytes. For every edit, both arms have identical ordered search-path
digests and retained key sets. Both existing proof readers check one complete
database per target and arm; the other repetitions are bound by identical hashes.

The preservation audit verifies 164 earlier manifests and 15,303 artifact
entries. All six cumulative tables remain byte-for-byte intact, including
158,942 native records. No new key is needed in the cumulative database, so the
existing multipart archive is reused rather than copied into another snapshot.
Alternative payloads remain in the raw worker archives; their presence is not
additional solved coverage. Earlier full-history and 342-partition audits remain
hash-bound rather than repeated. The current audit takes 269.54 seconds; it is
preservation work, separate from the matched timings.

Resume `experiments/results/cnf-guard-certificate-reuse/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`. The protocol, all 64 timed
workers, 16 traced workers, analysis, logs and validation are retained there.
The new source files are frozen at this checkpoint, together with all prior
sources. For reproduction in a new output directory, run
`experiments/compare_cnf_guard_certificates.py` with `prepare`, `run`, and `trace`,
then `experiments/validate_cnf_guard_certificates.py`. Existing output directories
must not be reused or overwritten.

Local reuse does not discharge the opposite branch. Broader coverage requires
useful composition of guarded regions, including templates with more than one
unfixed assumption. The next investigation should group such guards by exact
current support and component, identify overlapping or complementary regions,
and distinguish compact reusable closure from regions needing acquisition.
Automatic origin discovery, general coordinate transport and fresh unlabelled
evaluation remain open. No uniformly efficient partition of arbitrary SAT or
unrestricted polynomial expansion bound follows.
