# Conditional unit supports: useful certificates, limited additional coverage

The 23 November checkpoint extracts six guarded unit refutations from the
remaining mixed binary/ternary donor. It also separates the small runtime
certificates from the larger extraction archive. These are optional experimental
paths. Default search, native proof formats and verification rules are unchanged.

## What the pattern means

A template stores source clauses S, a partial assignment a, and a checked unit
refutation of S restricted by a. If every clause of S occurs in a target G in the
same variable coordinates, the template proves that G restricted by a is UNSAT.
It does not assert that G is UNSAT. A stronger query assignment must extend a;
the materializer rechecks unit conflict on the restricted support before emitting
an ordinary proof for the entire target cofactor. SAT witnesses and missing
support use the existing bounded native solver.

Extraction follows a previously checked negative DAG through unit, split and
component steps. Each local reason is lifted to an original donor clause using
its exact restriction preimage and variable map. Unit traces from ancestors are
included. Backward slicing from the conflict removes irrelevant forced literals
and reasons; every remaining unexplained variable must belong to the split
assumptions. Other endpoint kinds remain explicit unresolved obligations. Node
occurrence and visited-CNF literal budgets bound traversal, but not total source
scanning or elapsed time. They do not establish a polynomial-size proof for every
CNF.

The correctness argument is direct. Under an assignment satisfying the recorded
assumptions, every retained trace step is forced by its reason clause. The final
clause is false, so no satisfying assignment extends those assumptions. Clause
containment transfers this contradiction to G. Injective signed variable maps
preserve literal truth under the corresponding assignment transport; both the
original and transported trace are checked. Automatic discovery of such maps is
not implemented here. A whole-formula decision would additionally require an
exhaustive checked cover of assignments and a proof for every branch. The active
cache intentionally contains no authority for that composition.

## Donor census and the stronger comparator

The supplied donor has 315 clauses, 125 variables and 889 literal occurrences.
Fresh acquisition costs nine expansions and yields fourteen native nodes: five
splits and nine unit nodes. Six end in conflicts and three require child proofs.
Lifting ancestor reasons gives six templates with the following sizes:

| Template | Clauses | Source literal occurrences | Needed assumptions | Original split path |
|---|---:|---:|---:|---:|
| 0 | 6 | 13 | 2 | 2 |
| 1 | 8 | 18 | 2 | 3 |
| 2 | 15 | 37 | 4 | 4 |
| 3 | 17 | 42 | 4 | 5 |
| 4 | 28 | 72 | 5 | 5 |
| 5 | 3 | 6 | 1 | 1 |

The earlier census counted 148 literal occurrences in local reasons across nine
unit nodes. The lifted templates contain **188 source literal occurrences**,
counted with repetition across templates. Neither is an unconditional core or a
compression ratio against all stored CNFs. Extraction records 22,191 restriction
literal visits and 110 backward trace steps. Flattening ancestor reasoning has a
real acquisition cost.

The existing whole causal core uses 48 clauses. It already matches the donor and
the nearby edit. Targeted deletions can break this whole core while preserving
three to five templates, but that is an incomplete comparison: conditioning the
existing causal core on each supplied guard and slicing again also recovers every
one of the 40 conditional reuse hits below. No incremental coverage against that
stronger comparator was found.

## Frozen matched workloads

The main protocol uses eleven distinct clause sets: donor/nearby and targeted
support edits, four fixed-seed three-clause deletions, and an empty positive
control. Each is queried under the same six exposed guards, giving 66 queries
per worker. Three policies run in two opposite serial process orders (396
attempts). All restore the same historical prefix, then acquire the donor; no
final cumulative union seeds a trial. Repeated/cached roots are retained.

| Main policy | Query expansions | Preparation expansions after donor | Reuse hits | New native rows | Preparation + query mean (ms) | Compressed proof delta + raw hints (bytes) |
|---|---:|---:|---:|---:|---:|---:|
| Native | 68 | 0 | 0 | 98 | 193.30 | 65,359 |
| Conditioned causal cores | 28 | 5 | 40 | 123 | 226.37 | 75,905 |
| Unit templates, full metadata | 28 | 0 | 40 | 91 | 212.57 | 115,438 |

Every arm also pays the common nine donor expansions. All produce 59 UNSAT and
seven SAT **cofactor** answers, including twelve cached queries. The remaining
fourteen queries use native fallback in both reuse arms. Acquisition reductions
do not imply lower total runtime: both reuse methods lose to native solving in
this main preparation-plus-query comparison. Complete-worker means are 2.116,
2.011 and 2.208 seconds, respectively; two orders and variable reconstruction
costs do not support a reliable end-to-end speedup claim.

## Removing unnecessary active metadata

The full template bundle carries donor clauses, entire native keys, provenance
indices and a traversal tree. None is needed to validate an individual unit
refutation once its clauses, assumptions, trace and conflict index are retained.
The compact cache deep-copies and rechecks those fields. The full bundle and all
donor proofs remain in the immutable research archive. In particular, compaction
does not delete the persistent solver's earlier answers.

A separately frozen comparison runs full and compact hints in two opposite
serial orders (264 further attempts). Every native proof byte, answer, route and
expansion count agrees. Active hint JSON falls **51,929 to 11,505 bytes (77.84%)**.
Compressed proof deltas remain 63,509 bytes, so proof delta plus hints falls
115,438 to **75,014 bytes**. This is only 891 bytes below the conditioned causal
arm from the main run, and remains larger than native-only storage.

Preparation-plus-query means are 213.03 ms with full hints and 216.34 ms with
compact hints; complete-worker means are 1.898 and 1.874 seconds. Copying and
rechecking are charged. These mixed timings justify the smaller representation,
not a runtime speedup claim. The selected-container Python endpoint drops
4,006,028 to 3,943,718 bytes. That measure omits set contents, bank-instance
internals, SQLite/native allocations and other live state; whole-process RSS is
roughly unchanged. Neither figure proves a general memory bound.

Workers charge donor acquisition, preparation, normalization, containment,
checking, ordinary native publication, hint/proof serialization, warm answer
reads, reconstruction and cold answer replay. They do not reload persisted hints
in their complete-worker timer. `hint-reload.json` separately records reading
and validating those hints, including native proof reads for causal cores.
Those diagnostic measurements are additional costs, not a paired runtime result.
The initial probe's reporting exception and first report are also preserved.

## Bounds and next target

For q visited path occurrences and L donor literal occurrences, this extractor
may rescan the full donor for each occurrence: source scanning has an O(qL)
literal-work upper bound, in addition to child normalization, proof checking and
slicing. This counts dictionary operations at unit cost; bit costs are additional.
Shared DAG paths can be revisited. Let H be retained template size. Template
validation and cache copying scale with H (plus clause sorting/checking and
integer encoding costs). Exact target containment scans G. Native materialization
still normalizes and stores the full conditioned target; it does not retain only
a small learned clause. Repeated distinct target cofactors therefore continue to
grow the proof database. There is no bound on H or q that makes arbitrary SAT
uniformly easy.

The most informative remaining misses are support deletions, not another
metadata micro-optimization. Case 4, `delete-reason-2`, template 4 needs five fresh
expansions (13.94 ms in the first template order); its template-3 query needs four.
Case 7, `random-three-deletions-1`, template 4 needs six and is SAT. The last case
is an important counterexample to treating surviving donor structure as a
negative answer. Investigate inexpensive recovery of alternative reasons and
SAT witness reuse together, with a bounded attempt before native fallback.
`analysis.json` preserves the full source, assumptions, counters and new IDs for
all fourteen misses. Restore the bound historical prefix, preparation delta and
only preceding query additions when reproducing them.

Automatic useful-guard selection, donor/map discovery, exact whole-input
composition and full proof-space growth remain open. The experiments provide no
new efficient class covering arbitrary CNF, and no P-versus-NP result or new Lean
refinement theorem.

## Reproduction and persistent record

Runtime modules: `experiments/cnf_conditional_unit_support.py` and
`experiments/cnf_conditional_unit_cache.py`. The two comparison scripts retain
frozen source fingerprints before timing. `validate_cnf_conditional_unit_support.py`
checks conditional source bindings, replay, chronological prerequisites, cache
roundtrips, prior partition records and the cumulative native/extension union.
Resume from `experiments/results/cnf-conditional-unit-support/checkpoint.json`.
Full and focused test logs, raw samples, the failed first probe, hint reload
costs and a sealed artifact manifest are stored beside it.

Validation passed 1,510 full tests and 218 focused tests. The full suite retains
44 unclosed-SQLite resource warnings; the focused suite has none. Both readers
replay all 76,272 cumulative native records, the unchanged extension tables and
342 prior partition records. Ninety native identities are new in the union;
previous payloads remain byte-identical. All 12,442 preceding artifacts across
140 manifests are unchanged. The new seal binds 797 runtime/test/audit source
files. The manuscript builds to 245 pages without layout or LaTeX warnings, and
all 64 earlier proof environments remain unchanged.
