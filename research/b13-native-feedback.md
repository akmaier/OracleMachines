# Source-only certification of the strengthened B13 conflict

Checkpoint: 26 November 2026. The retained `(67,63)` candidate now has a native
refutation checked against its **original 419-clause, 1,215-literal snapshot** by
both independent cold readers. Certified structural coverage increases from
**232/246 to 233/246**; thirteen frontier cases remain. This certifies a snapshot
root, not the entire generating target formula or arbitrary SAT. Bounded fresh
solving also refutes this case and is cheaper than reconstruction.

## Exact reconstruction and reuse conditions

`experiments/cnf_b13_probe_feedback.py` extends the earlier B10 reconstruction
algorithm without changing any frozen source file or native proof format. It
first validates all input histories on their original banks, reconstructs B13
and appends each new failed assumption's negated unit to the feedback bank B14.
The retained final 34-step unit contradiction is checked on that exact bank.
This is a feedback bank for checking and compilation, not a new search layer.

Provenance maps B10 comparison to bank 10/input 23; B11 to bank 11/input 22;
B12 source/unseen to bank 12/inputs 24/25; B11 continuation to bank 11/input 26;
and B13 failures to bank 13/input 27. Earlier origins keep their existing maps.
Each derived-unit edge must descend to a strictly lower bank and the actual
failed assumption must be present in the current context. Source clauses and
guard templates are reconstructed from the original source support.

The correctness argument is by induction through those dependencies. A unit
step splits the restricted source on its forced literal. The excluded branch
is refuted by the clause's checked origin, and the live branch by the rest of
the trace. Source/guard leaves use checked source unit contradictions; optional
direct shortcuts also use only the restricted source. If a variable is absent,
the excluded branch must have the same canonical root before it can close the
parent. The stage decreases on origin expansion and the trace position advances
within a stage. Existing native empty/unit/split checks validate every published
node; both cold archive readers independently check the resulting source graph.

The ordinary prefix reconstruction remains available and is checked before
publication. **This measured case has an empty prefix**, so its timings do not
establish nonempty-prefix cost. A compiler call validates histories and the final
trace before a warm root hit; corrupted bindings, source, final proof or prefix
status are rejected before new records are written. Native archive consumers
need only the source and native records, not the B13 discovery histories.

This does not bound acquisition, future strengthening rounds or the size of an
unfolded native graph for unrestricted inputs. Deep chains can repeat work under
different conditioning contexts. Fixed bank/trace limits restrict the procedure
but do not supply complete arbitrary-CNF coverage.

## Matched costs, including the regression

Six mode permutations run in separate processes before heavy tests. All three
arms refute the same snapshot. Fresh solving uses the existing 256-node limit;
`disabled` compiles provenance without direct unit shortcuts; `direct` uses the
existing source-unit shortcut with work 262,144 and trace bound 256. Native
canonical-context reuse remains enabled in both compiler arms.

| Arm | Solve/compile (s) | Warm (s) | Both cold readers (s) | Persistence (s) | Complete (s) | Native records | Record bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0.25507 | 0.00192 | 0.25065 | 0.08280 | 0.59542 | 95 | 1,256,004 |
| disabled | 7.68111 | 0.02437 | 8.32237 | 2.35030 | 18.46791 | 2,507 | 31,081,306 |
| direct | 0.31226 | 0.02295 | 0.33677 | 0.11514 | 0.79089 | 117 | 1,664,028 |

Direct compilation is **22.42% slower to construct**, **34.36% slower to cold
check**, **32.83% slower end to end**, and uses **32.49% more record bytes** than
fresh solving. Compiler warm time includes revalidating the supplied histories;
fresh warm time invokes the solver again. These are distinct public workflows,
not an isolated comparison of the same native root lookup. Direct shortcuts
greatly reduce the disabled arm's proof expansion, but do not beat the fresh
baseline. There is no production-default change or measured speedup over fresh.

Peak RSS is **72,220,672 / 427,671,552 / 76,873,728 bytes**, and compressed archive
sizes are **126,513 / 3,217,692 / 164,024 bytes**, in table order. The complete
timing includes database creation, construction with original-bank validation,
warm reuse, cold readers and compressed persistence. Historical acquisition,
discovery, loading and the final lineage audit are additional. Six balanced
orders on one selected case do not establish performance across SAT categories.

Cold checking accounts for about 43% and construction about 39% of the direct
workflow. Native graph size is therefore a concrete remaining cost: reducing
unfolded source contexts could save both construction and cold checking. The
disabled arm's 2,507 records versus 117 with shortcuts preserves a useful
counterexample to assuming that following stored provenance is automatically
cheap. An effective cost gate must include these costs and a fresh-solve option.

## Preserved state and next priorities

Resume `experiments/results/cnf-b13-native-feedback/checkpoint.json`, key
`b13_native_feedback.remaining`, with the comparison module's `load_frontier`.
The **6,099-byte overlay** excludes only `(67,63)` and binds its source root and
selected archive. Every field of the other thirteen rows is unchanged, including
the new `(37,39)` closure from the preceding run. The **263,160-byte case record**
and all benchmark archives are additional to the retained parent histories.
All three distinct native archive variants pass both readers; they certify the
same root and are not counted as three coverage gains.

The audit preserves **1,190 old source fingerprints**, **32,649 artifact entries
in 215 manifests**, existing cumulative tables and earlier native archives.
Four new source files bring the source ledger to 1,194. The certificate lives in
supplemental archives; no earlier authority table is rewritten. Initial test
fixtures incorrectly treated a tuple as mutable and assumed a nonempty prefix.
Both failed runs and test sources are preserved. The corrected tests change only
those mutations, not the compiler, benchmark or timing results.

Validation includes **2,167 full tests**, **31 focused tests**, exhaustive
two-variable and seeded five-variable generated histories checked against truth
tables, malformed-proof rejection, warm invalidation, source-only cold readers,
and unchanged prior proof blocks. Only generated cases with valid interrupted
histories enter the new layer; this is not a claim of exhaustive five-variable
coverage. Earlier SQLite ResourceWarnings remain recorded in the full-suite log.

**Next coverage priority:** use `(37,39)`'s retained new closure and investigate
stronger interactions or another decomposition on the thirteen remaining cases;
do not repeat exhausted unchanged-bank searches. **Next cost priority:** compare
smaller native source supports or a cheaper representation of repeated conditioned
contexts against fresh solving, charging cold checking and storage. Profile that
conversion before choosing another optimization. Keep certificate availability
separate from whether reconstruction is the economical route to obtaining it.
