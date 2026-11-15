# Retain coverage and reuse it during original selection

The latest global query reopened the inventory and spent about 69.65 seconds on
route preparation and coverage. Earlier measurements already showed that much
of this cost comes from cold semantic checking. This investigation separates
three methods: reopen and fully recompose; retain checked inventory objects and
fully recompose; retain both inventory objects and the coverage indexes, then
use the full index for the original selector's closure queries.

The comparison replays the exact six-pattern append from the preceding
case-1061 experiment. It adds no new discovery or original coverage. The
authoritative discovery checkpoint remains
`experiments/results/cnf-original-handoff/report.json`, with **68/83** originals
covered. Its next focus remains **40/158/467**, original **case 1443**, index
**72**, with no pending split. Preserve evidence **(1, 42, 156, 56, 1)** and two
bridges when resuming through `compare_cnf_original_handoff.restore_checkpoint`.

## The reused object and its authority

The existing `CoverageIndex` stores every rule reachable from the original roots
and computes their least fixed point. Its closure means that a complete finite
recognition plan is available, not that a formula is SAT. Conditioning requires
coverage of both children. An unsupported cycle contributes no justification.
This experiment uses the same index implementation and full plan checker as the
earlier [incremental coverage study](incremental-coverage.md).

The new `cnf_indexed_navigation.select` replaces the selector's repeated
composition queries with membership in this checked closure. The selected paths,
probe ranking, retained-split preference and original bindings are unchanged.
For an indexed source, the graph already contains all of its reachable rules,
so its closure agrees with full composition rooted at that source. A retained
split can be outside the original graph; such a query explicitly falls back to
full composition. Absence from the index is never interpreted as noncoverage.

For an indexed source, every premise of every available rule is in the retained
graph. Any finite derivation rooted there therefore uses only its reachable
dependency subgraph. Conversely, a derivation found by composing that subgraph
is also a derivation in the complete index. This gives equality of the two
closure answers, including negative answers for the fixed finite catalog.
It does not turn noncoverage into UNSAT or exclude future discoveries.

Before navigation, root order and closure flags must match the index, and its
external catalog must equal the supplied complete checked catalog. After a
checked append, the index compares the full external catalog, checks changed
reachable sources and newly reachable descendants, and propagates newly
justified premises. Historical internal nodes and their implicit rules remain
immutable. Newly admitted targets can activate old external records, so the
complete route builder must run before refreshing the index. Comparing only
newly inserted route records would be insufficient.

These are in-process authority conditions. The caller owns the checked caches,
uses the same immutable pattern history and recognition policy, and permits no
concurrent mutation during navigation. Root and catalog comparison do not prove
those conditions independently. Here each transition is the hash-bound,
conflict-checked archived append and a complete route rebuild. Deletion,
rebinding, policy changes or arbitrary external writes require reconstruction.

## Comparison boundary

Every arm starts from an independent copy of the same restored checkpoint. It
constructs and checks the initial coverage, selects the initial focus, applies
and verifies the saved append, then queries final coverage and selects the next
focus. Both initial and final selections must exactly equal the original
selector's archived results. The order of the three methods is reversed in the
second repetition. No fresh structural recognition is permitted.

All query timings include complete route preparation, composition or index
maintenance, certificate construction, the original plan checker and original
selection. Complete sequence timings additionally charge copying, delta
verification, digest checking and serialization of result certificates and
selections. Parent reconstruction is shared and reported separately. Complete
post-update index audits and independent cold validation are diagnostics outside
the timed sequences.

The coverage indexes remain ephemeral. A restart reconstructs them from checked
authority; this experiment does not write a new large index snapshot or trust
saved negative flags. The earlier full-snapshot persistence regression remains
valid and is not replaced by a claim of cheap cold loading. Output artifacts
are additional experiment storage; the SAT history and reference nodes are
unchanged from the discovery checkpoint.

## Resource boundary

Retention avoids repeating semantic checks on unchanged objects. Once a complete
index exists, a covered-source query uses its interned identity and justification
membership; string hashing and comparison still process key representations.
Queries outside the graph pay full composition. The selector still traverses
selected internal paths, verifies retained split records and ranks available
probe variables. Catalog binding still compares the complete external catalog.

Updates pay for catalog comparison, changed reachable rules, new descendants,
and propagation through affected premise occurrences. Each source becomes
justified at most once in an append-only session. This bounds repeated graph
propagation, not graph discovery or graph size. The implementation retains both
the full and without-growth control graphs, in addition to historical verifier
caches. Graph counts and encoded-key bytes do not measure peak RAM or establish
compression relative to retaining only an inventory. No polynomial arbitrary-SAT
or globally minimum-expansion bound follows.

## Reproduction

Run `python3 -u experiments/compare_cnf_global_navigation.py OUTPUT`, then
`python3 -u experiments/validate_cnf_global_navigation.py OUTPUT`. The latter
uses the original full composer and selector on fresh inventories for both
versions, checks every archived selection and positive coverage certificate,
audits rebuilt graph sizes and verifies the preserved reference database.
Fresh recognition and reference search are disabled. The scheduler-body audit
checks that the only changes to the three copied scheduling functions are the
closure calls and the argument carrying those calls.

`solver.test_cnf_indexed_navigation` covers shared originals, independent navigation rows,
pending forced-target activation, both conditional obligations, closed
transitions, stale bindings, forged split evidence and a retained source outside
the indexed original graph. The existing exhaustive coverage-graph tests remain
part of the full validation suite.

## Measured costs and next target

| Mean measured cost | Reopen and compose | Retain inventory | Retain inventory and indexes |
| --- | ---: | ---: | ---: |
| Complete two-query sequence | 138.45321 s | 75.96089 s | 74.82933 s |
| Final complete query | 65.45308 s | 1.40345 s | 1.28188 s |
| Final route construction | 7.98904 s | 1.12777 s | 1.14222 s |
| Final composition and plan checking | 57.38432 s | 0.19835 s | 0.06835 s |
| Final original selection | 0.07972 s | 0.07732 s | 0.07131 s |

Retaining the inventory reduces the complete measured sequence **45.14%**.
This includes its first global query and subsequent update; it does not subtract
initial checking from the denominator. The final query alone falls from
**65.45308 to 1.40345 seconds**.
Thus most of the previously identified cold global cost is repeated semantic
checking. It must not be attributed to incremental graph propagation.

Indexed final queries average **1.28188 seconds**, but the
complete-sequence comparison against retained full composition is mixed. In the
first repetition it takes **74.19371 versus 73.95375 seconds**; in the second,
**75.46496 versus 77.96803 seconds**. The mean difference is smaller than the
observed sequence variation. Keep the new selector optional; these two runs do
not establish a stable total-cost benefit from retaining another graph. Full
snapshot serialization and peak RAM were not measured again.

Both indexed updates check **6 option sources** across the two graphs.
The full index contains **13,055 nodes / 13,175 rules /
13,647 premise occurrences**, with **38,977,588 encoded
node-key bytes**. The without-growth control retains a second graph of
**13,054 nodes**. These are logical representation sizes, additional
to the retained inventory caches, not peak resident memory. The first indexed
final selection uses **89 indexed closure queries** and
**0 full fallbacks**. Remaining selector work and complete
route preparation are still charged.

Shared parent reconstruction takes **119.41436 seconds**. The
producer, including all six sequences and diagnostic audits, takes
**704.28241 seconds**. These are not single-query latencies.
The authoritative history remains **778,899,456 bytes / 42,341 patterns** and
its reference graph **4,413 nodes**. This run preserves the prior transition
67/83 to 68/83; it earns no additional original coverage. Original case 1061 is
SAT with a checked model, despite the selected conditional residual being UNSAT.

The next useful step is fresh bounded discovery on **case 1443** within one
retained inventory, keeping global queries and the existing route-maintenance
state alive across expansions. The initial checked global graph is still costly,
and a process restart pays reconstruction again. Measure a longer sequence
before deciding whether the optional graph index pays for its retained state.
Avoid replacing the existing complete maintained routes with a partial catalog.
The still-open fifteen originals, cold replay and retained-state growth remain
separate obligations.

Within the warm final query, complete route reconstruction costs **1.12777 of
1.40345 seconds (80.36%)** with full composition, and **1.14222 of 1.28188 seconds
(89.11%)** with indexes. Composition and plan checking fall **0.19835 -> 0.06835
seconds**; original selection changes only **0.07732 -> 0.07131 seconds**. Thus
the graph index reduces repeated graph work, while further selector tuning has
little measured headroom here. Connect the existing complete route-maintenance
state to global queries before optimizing these closure lookups further.

Full recomposition visits **26,109 sources** across its two graphs. The index
checks six sources because the new targets' closed summaries supply base rules;
their underlying six probe certificates remain subject to semantic verification.
Graph-operation counts must not be confused with all certificate-checking work.
All three methods end with **20,270 checked pattern objects / 2,916 prepared
checked objects**. The indexed method additionally retains its two graphs.

The comparison report is `experiments/results/cnf-global-navigation/report.json`,
SHA-256 `cff5db1418f36f3a9fa1b81edadfa64859ef2e58312f1735154db1d44a1d57c5`. Resume discovery from the unchanged original-handoff
checkpoint described above, not from this comparison report.

## Validation result

Independent cold validation passes in **259.30996 seconds**, checking all
**twelve selections and coverage certificates** with the original algorithms on
fresh inventories and verifying all **4,413 reference nodes**. The copied
scheduler bodies match their frozen baseline after reversing only the closure
calls and extra argument. All **254 tests** pass; the manuscript builds to
**165 pages** with all **64 previous proof blocks** unchanged. All **1,634 prior
artifacts / 31 manifests** and **95 historical source files** are preserved.
The new manifest binds **32 artifacts**. Validation tasks overlapped, so cold
elapsed time is not a performance comparison.
