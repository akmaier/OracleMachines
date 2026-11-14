# Bounded projection acquisition: smaller input, higher expansion cost

2026-11-14. The candidate exposed by [automatic target lookup](projection-lookup.md)
is now acquired and structurally classified. Original **1298 / index 47** closes,
raising coverage **62/83 -> 63/83**. Ordinary continuation closes the same source
with less work. The negative comparison is retained alongside the new certificate;
projection acquisition remains an optional research path.

## Exact construction and admission

The source has **37 variables / 151 clauses / 455 literals**. Eliminating local
variable **13** enumerates ten opposing pairs. The normalized projection has
154 clauses; deleting one clause with a checked retained proper subclause gives
**36 / 153 / 470**. Final clause growth is two, while literal count grows by
fifteen. The target did not occur in the acquired current-policy catalog.

`cnf_projection_acquisition.propose` constructs that exact target and its existing
projection/subsumption certificate. `acquire_projection` checks source identity,
policy, depth, variable transport and all clause obligations before acquisition.
It uses the caller's shared admission allowance without resetting it. A budget
stop preserves the proposal and any completed descendants, but returns no bridge.
A completed target is independently reloaded and checked before the bridge is
returned. An acquired unresolved target supplies a dependency, not source closure:
the target still requires a completed structural proof.

The existing bridge contract permits one eliminated variable and order-preserving
renaming. It rejects further support lost during subsumption. Extending that
contract needs an explicit model transport; the acquisition helper does not
silently broaden it. Old recognizers, proof records and policies are unchanged.

## Matched comparison

Four serial workers run in order ordinary, projection, projection, ordinary.
Every worker starts from the same independently copied authority, seeks closure
of the same 37-variable source, and has **12 advances / 32 new states**. Projection
construction, checking and acquisition consume its first advance and the same
state allowance. Subsequent steps use the unchanged continuation engine, focused
on the acquired target; closure is always checked at the original source. The
ordinary worker follows the source directly. Both branches of a saved split
remain required for structural coverage.

This comparison is conditional on the candidate preserved by the preceding
study. Its global discovery and catalog construction are not rerun or included
in these worker means. Each worker charges preparation, selection, acquisition,
route refresh, closure checking, delta export and cold delta validation. Global
restoration, combined checking and reference work are reported separately. Trials
share process and OS caches; two repetitions give no confidence interval or
holdout claim. No tests or builds ran during the measurements.

| Quantity | Ordinary continuation | Acquire projection |
|---|---:|---:|
| Source structurally closed | yes | yes |
| Advances | 4 | 8 |
| New states, all completed | 8 | 9 |
| External continuation assumption attempts | 20 | 44 |
| Mean expansion, seconds | 4.45329 | 8.70178 |
| Mean acquisition and ranking, seconds | 0.39953 | 0.53929 |
| Mean full route refresh, seconds | 4.05191 | 8.15891 |
| Mean worker, seconds | 16.62221 | 21.45978 |
| Mean preparation within worker, seconds | 7.41115 | 7.68350 |
| Compressed pattern/probe delta, bytes | 8,985 | 11,134 |
| Uncompressed delta database, bytes | 192,512 | 245,760 |
| Complete history database, bytes | 773,095,424 | 773,148,672 |

Expansion is **95.40% slower** and complete worker time **29.10% slower** for
projection on this development case. The sign agrees in both repetitions.
Complete route refresh consumes **91.0% / 93.8%** of expansion. Formula size alone
misses the cost of acquiring a target with its own probe history: three further
clear continuation blocks precede the ordinary split, versus six after projection
acquisition. The eventual pair is already recorded in each focus's initial
pattern record. These measurements suggest testing earlier split selection;
they do not prove that all intervening probing is redundant on other inputs.

External assumption counts cover continuation calls; they exclude probing inside
initial target recognition and other recognition work. All of that work remains
in acquisition time and the stored detailed counters. The state counts exclude
previously acquired records, whose acquisition costs remain in the old reports.
The compressed deltas exclude split/bridge sidecars, reference proofs and logs.
Database bytes measure retained storage, not peak RAM.

## Structure of the completed case

Both paths ultimately choose the same surviving variable: source local **22**
maps to target local **21** after eliminating source variable 13. In the ordinary
path, its false cofactor has **34 / 134 / 383** and three failed-literal
reductions reach the retained empty-clause refutation. Its true cofactor has
**34 / 129 / 380**; two reductions reach a **5-variable / 2-clause / 5-literal**
conjunction of disjoint components. The projected cofactors start at
**33 / 135 / 392** and **33 / 130 / 390** and reach the same refutation and exact
five-variable component key. These are checked structural paths, with independent
reference answers UNSAT and SAT respectively; lifted SAT witnesses satisfy each
source. A closed branch flag alone supplies neither answer.

Thus the projection preserves the useful split but adds intermediate clauses
and separate recognition records. This is a concrete candidate for transferring
split structure across transformations, while sharing the eventual component
proof. It does not justify treating the different cofactor roots as identical.

## Preserved result and cost account

The combined authority retains **14 distinct new patterns**, with three exact
new keys shared between the arms. It also adds eight continuation blocks, one
probe window, two split records and one new bridge. No prior row is replaced.
The union is not a single nine-state run. It preserves every alternative and
contains **41,926 patterns / 773,255,168 SQLite bytes**, an increase of 282,624
bytes. The union pattern/probe delta is **16,475 compressed bytes**. Both bridge
targets and all 26 retained split sources close. The positive proof has **3,145
steps**, and twenty originals remain structurally uncovered.

The complete producer takes **221.64457 seconds**. Restoration consumes
**53.81904 seconds**; preparing routes and checking final corpus coverage consume
**66.84462 seconds**. Union delta export costs **5.31714 seconds**. These costs
are additional to the local worker comparison. Reference solving and lifted SAT
witness checks are stored separately and never decide structural coverage.

## Validation and durable artifacts

Independent cold reconstruction takes **221.51064 seconds**, with fresh pattern
recognition and fresh reference expansion forbidden. It checks all four arms,
their identical repeated logical results, admission bounds, exact proposals,
both split branches, bridge proofs, lifted SAT witnesses, all **3,022 reference
nodes**, full corpus coverage, next selection and idempotent delta application.
Previous seed rows remain unchanged. Cold reconstruction includes two independent
parent restores and redundant checks; it is an audit cost, not a normal worker
latency estimate.

All **199 relevant tests pass**, including five new tests for acquisition,
resumption, budget exhaustion, tampered proposals and unsupported support loss.
The manuscript builds at **156 pages**, without overfull boxes or undefined
references; all **64 existing proof blocks** remain byte-identical. Hash checks
preserve **460 earlier artifacts across 16 manifests**. The new result directory
contains **73 manifested artifacts plus the manifest / 3,647,780 bytes**, including
all four arm records, deltas, reference archive, reconstruction, findings and logs.
This is additional experimental retention, separate from the reconstructed
SQLite history and the optional previous lookup index.

## Continuation and remaining gaps

Resume `experiments/results/cnf-projection-acquisition/report.json` using
`compare_cnf_projection_acquisition.restore_checkpoint`. Its SHA-256 is
`d865c287709cccdd0af56c1a23a564618e369be41fd4e971c21c0834b3510b2a`.
Keep the five evidence lists **(1, 42, 156, 26, 1)** and the separate `bridges`
archive containing both bridges. Construct routes with
`compare_cnf_projection_acquisition.routes_for(h, evidence, bridges)` and replay
extended positive proofs with `cnf_projection_bridge.verify_positive`.
The `projection_frontier` sidecar retains each acquired bridge target's status;
both currently close, with no leaves. Ordinary scheduling alone does not follow
an open projection bridge, so a future pending target must remain an explicit
scheduling obligation.

The next selected original is **1160 / index 29**, with a **37 / 151 / 456** leaf,
SHA-256 `614772f5cb0f59835870e117b1653b225e008eb44416371335350a725cac6149`.
Almost equal dimensions do not establish reuse: its normalized clause set has
zero exact clauses in common with the completed 37-variable leaf. More general
variable maps or shared abstractions require discovery and checking.

The immediate opportunities are to rank already saved split pairs before paying
for every clear probe, preserve useful evidence across exact transformations,
and avoid complete semantic route refresh when only probe availability changes.
For projection by x and conditioning on a distinct y, semantic commutation alone
does not certify transport of a particular unit-propagation trace. Both source
bindings, the surviving variable map, cofactor reduction and proof dependencies
must be checked. Prior unsuccessful recognition cannot be treated as semantic
exclusion. Keep forcing controls and cases that become easier only after more
probing in the next matched comparison.

No optimum expansion policy, general memory saving or uniformly efficient
classification of arbitrary CNF follows. The previous bridge saved work because
it reused an acquired target. Here a new target costs more than completing the
source directly. Both results belong in the accounting model.
