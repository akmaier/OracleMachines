# Exact projection connects the two expansion paths

2026-11-14. The two unresolved leaves of case 1299 share more than similar sizes.
The **29-variable / 108-clause / 337-literal** formula projects to the retained
**28 / 110 / 351** formula after eliminating one variable and deleting one
subsumed clause. This checked connection lets a proof of the smaller leaf serve
both paths. In two matched repetitions, completing both leaves takes **13 new
states rather than 25**, with **6 rather than 7 advances**.

Mean expansion time falls from **7.57375 to 6.42390 seconds**. Complete worker
time falls from **20.12211 to 18.70835 seconds**. Unlike the previous comparison,
both modes complete the same two structural obligations. These are measurements
on one adaptively selected development pair, not a universal scheduling result.

## What the certificate establishes

Let B be the 29-variable source and A the 28-variable target. Eliminate local
variable **16** from B by checking all **ten opposing clause pairs**. The
normalized projection is exactly A plus the clause
`[-21, -19, -14, 4, 5]`. The retained clause `[-19, 5]` subsumes it. The
certificate names the eliminated variable, the exact renaming and the two clause
indices; the checker reconstructs every resolvent and checks the subset relation.
It does not trust a reference answer or a similarity score.

For each assignment to the surviving variables, the projection is true exactly
when some value of variable 16 extends it to a model of B. Deleting a clause
that has a retained subclause preserves the models over those variables. The
composition therefore proves **A is the exact existential projection of B**,
under the recorded renaming. A target SAT model lifts to B by satisfying the
eliminated variable's opposing clause tails; a refutation of A refutes B. The
implementation checks the lifted model against the entire source.

This composes established elimination and subsumption rules. The new empirical
finding is that the independently expanded paths reconverge at a retained exact
target. It is not a new elimination theorem or a proof of efficient arbitrary SAT.

The intermediate projection has **111 clauses / 356 literals**. Its three-clause
increase exceeds the current ordinary elimination budget of two, before the
redundant clause is removed. The final 110-clause target satisfies that budget.
This explains why the isolated local projection was missed. Literal occurrences
still increase from 337 to 351; decreasing support is not decreasing every cost.

## Recognition, trust and limits

`cnf_projection_bridge.py` is additive; historical recognizers and records remain
unchanged. It scans at most 64 source variables, with at most 64 opposing pairs
per candidate, seeking an explicitly supplied retained target. The target must
be a subset of the normalized projection. Every additional projected clause
needs a retained proper subclause. Target support must match the projection's
canonical variable map, and final clause count is at most source count plus two.
Only order-preserving canonical transport is searched; arbitrary renaming,
signed symmetry and arbitrary implied-clause deletion remain outside this rule.
A failed search does not prove non-equivalence or hardness.

The route binds both existing endpoint keys, equal recognizer policy and depth,
and the full checked certificate. It adds B -> A as a sufficient structural
dependency. Open A leaves B open; no closure bit is manufactured. The positive
proof checker requires A to have an earlier justified proof step before it can
use the route. Current and retained-policy historical check caches keep their
original contracts. Both old sidecars and the new bridge sidecar must survive
restart. No earlier pattern row is overwritten.

For a candidate with k opposing pairs and maximum source width w, at most k
resolvents of width at most 2w-2 are generated, plus retained clauses. Source
scanning, normalization, sorting, target comparison and subsumption checks are
charged. Discovery's simple search can compare every removed projected clause
with every target clause. The certificate checker only checks the selected
subsumers, but still reconstructs all pairs. Working space includes that explicit
projection and the endpoints; whole-history reconstruction and checked caches
are additional costs. The fixed caps bound this local search, not the number of
expansion steps needed for arbitrary CNFs or the size of the stored history.

## Matched completion and storage

Each mode starts from an independent copy of
`experiments/results/cnf-split-cost-1299/report.json`, with a fresh shared
32-admission allowance and a twelve-advance cap. The targets are the same two
leaves in both modes. Both use the unchanged early-closed continuation policy;
the bridge mode additionally installs the checked projection route. Orders are
independent then bridge, followed by bridge then independent. Tests and builds
do not compete with the timed producer. All repeated logical results are checked
on cold reconstruction. The union retained for future work is never supplied to
an individual arm.

| Quantity | Independent | With projection route |
|---|---:|---:|
| Completed target roots | 2 / 2 | 2 / 2 |
| Advances | 7 | 6 |
| New admitted and completed patterns | 25 | 13 |
| Expansion, mean seconds | 7.57375 | 6.42390 |
| Complete worker, mean seconds | 20.12211 | 18.70835 |
| Compressed pattern/probe delta, bytes | 18,956 | 11,702 |
| Separate bridge sidecar, compressed bytes | 0 | 1,468 |
| Full arm SQLite history, bytes | 772,972,544 | 772,804,608 |

The new bridge is **5,189 uncompressed bytes**, including both full endpoint keys,
or **1,468 compressed bytes**. Including it gives **13,170** compressed bytes for
the new route and pattern/probe delta, versus **18,956** without it. Other split
sidecars, positive certificates, traces, reference proofs and logs remain extra.
The full archived experiment preserves the independent arm's additional work,
so its authoritative union is larger than the bridge arm alone. Disk size is not
peak RAM.
The complete new result directory, including all four arms, proof archives,
validation records and its manifest, is **3,642,090 bytes**. Its 71 manifested
artifacts preserve the comparison; they are additional to earlier checkpoints.

Two serial repetitions share process and OS caches and provide no confidence
interval. Global parent restoration, shared bridge discovery and final complete
corpus checking are separate from the worker totals. No end-to-end production
solver speedup is inferred from this local completion comparison.

Discovery and its checks cost **0.00691 s** with the endpoint rows already
loaded. Sixteen variables are tried: two exceed the pair limit, thirteen miss
the exact target, and variable 16 succeeds. Charging this shared discovery once
to each bridge completion gives **15.09%** lower expansion time and **6.99%**
lower complete worker time on the two-repetition means. Route refresh still
dominates: **7.04477 s** independently versus **6.02061 s** with the bridge.
Acquisition and candidate checking take **0.51750 vs 0.39478 s**. Both modes make
28 fresh external assumption attempts. The gain avoids an additional split and
its acquisition/maintenance; it does not save those earlier ordinary probes.

The complete four-arm producer takes **219.34858 s**, including **49.62108 s**
restoring the authority and **67.16398 s** for final global route preparation
and closure checking. These dominate the shared study cost. Bridge construction
does not make the accumulated historical preparation free.

## Checkpoint and next gap

The smaller leaf closes through two new splits and their probe/refutation chains.
The independent mode then acquires another twelve states to close the larger
leaf. The bridge mode instead checks the retained projection and reuses the
smaller leaf's completed proof. The original development input **1299 / index 48**
now closes, raising structural coverage **61/83 -> 62/83**, also without the old
growth-exception routes. Those views still include ordinary bounded additive
elimination and the new projection bridge; they are not non-growing-CNF claims.
Every source of the 24 retained split records closes, while 21 original inputs remain uncovered.

The union retains **25 new patterns** (sixteen probes, six eliminations, two
binary-path reductions and one unresolved intermediate), **four probe blocks**,
**three split records** and **one bridge**. Every entered state completes. Full
SQLite grows **372,736 bytes** to **772,972,544 bytes / 41,912 patterns**. The
combined delta is **18,956 compressed bytes**; the separate bridge adds 1,468.
The positive proof has **3,104 steps**. All **2,605** earlier reference nodes
remain among **2,921**. Earlier alternative results and their proof archives are
preserved rather than replaced with the cheaper arm's subset.

Resume **`experiments/results/cnf-projection-bridge/report.json`**, SHA-256
`aa68aa76ffac56fd767b0540b3ab9b683650a97ea3c4822dedb1bdd4cf4df809`, with
**`experiments.compare_cnf_projection_bridge.restore_checkpoint`**. It returns
the original five evidence lists, now **(1, 42, 156, 24, 1)**. Also load the
report's **`bridges`** archive and pass it to this module's
**`routes_for(h, evidence, bridges)`**; the legacy five-list catalog alone omits
this new rule. Use `cnf_projection_bridge.verify_positive` for positive proofs
that may select the bridge. Do not rerun the comparison to resume.

The next selected original is **1298 / index 47**, with leaf **37 / 151 / 455**,
SHA-256 `dd822fabc78af1efd220882ae9ead41593645ea916f4753c13b000b080a162b7`.
Its next ordinary probe variables are **15, 18, 19, 20**. Sixteen retained clear
pairs supply split candidates; the best current rank is **[2, 2, 34, 763, 22]**,
with neither child acquired. These are a starting profile, not a reason to skip
the remaining probes or assume that a useful projection exists.
The strongest discovery opportunity is to find these converging projections
without first being handed two selected targets: filter retained candidates,
check final subsumption before rejecting clause growth, and charge indexing,
normalization and failed proposals. Test novel originals and non-matching edits
as well as repeated paths. Complete route refresh remains the largest measured
warm cost and should be reduced without losing candidate or closure invalidation.

## Validation

All **187 regression tests pass**, including six new bridge tests. The semantic
test exhausts formulas with at most three distinct clauses over three variables,
checks every surviving assignment for each accepted bridge, and lifts every
satisfying target model. Additional tests reject changed endpoint clauses,
variable maps, subsumption witnesses, Boolean indices, missing bridge records
and positive proofs whose target has not been justified. This is bounded
exhaustive testing, not a Lean formalization of the new checker.

Independent reconstruction takes **212.53063 s**, with fresh recognition and
reference expansion forbidden. It checks all four arms, both split branches,
idempotent merges, repeated logical results, the bridge and positive proofs,
all **2,921** reference nodes, complete original coverage and the exact next
selection. Full cold coverage alone takes **69.22764 s**; restoration takes
**53.98568 s**. All **368 artifacts in fourteen earlier manifests** retain their
recorded hashes. These cold costs remain part of the persistent system's resource
accounting.

The manuscript builds to **155 pages**, with no overfull boxes or undefined
references. All **64 existing proof blocks** are unchanged; the new text states
the projection argument, empirical savings and limits. Source fingerprints,
checks and artifact hashes are in `validation.json`, `paper-check.json` and
`manifest.json` in the result directory.
