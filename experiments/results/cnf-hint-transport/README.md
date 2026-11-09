# Portable core hints: successful proof transport, unfavorable extra-pass costs

9 November 2026. The implementation translates checked parent implication traces
into proofs that replay directly against the exact child core. All **1,005 eligible
hint occurrences** in the study translate without fresh proof search. The explicit
hint-assisted plan gains one local child closure, but its runtime and storage
increase. The gain is explained by variable ranking, not stronger inherited hints.
Keep this control optional; no whole-source coverage improvement is established.

## Method and trust boundary

`transport_hints` first fully checks the parent's learned reduction. It maps
original unit-reason prefixes through that assignment or signed substitution and
the child's normalization. Parent certificates index clauses after their probe
assumption, so the original clause index is reconstructed before the child index.
Satisfied/tautological clauses disappear. Hint literals outside the child universe
are rejected explicitly. A missing translated refutation is retained as a miss;
there is no hidden fresh-search fallback.

`check_rup` independently checks a unit refutation after negating the candidate
clause, using only the normalized child core. This accepted proof can replay
without the parent graph. Full core/clause keys and matching payloads bind every
lookup. Parent evidence and previous archives remain preserved; provenance does
not substitute for proof. The method uses established hinted clausal checking,
as described by [Cruz-Filipe et al. (2017)](https://www.cs.cmu.edu/~mheule/publications/lrat.pdf),
not a new proof principle. The new Lean `core_fragment_sound` corollary specializes
the existing fragment checker to premises in the exact core. Python's integer
encoding, index conversion, storage and runtime are not formally refined.

`HintAssistedInventory.inspect_hints` accepts an explicit, ordered hint context.
Its persistent plan key includes the core, hint set, depth and policy. It first
recognizes the core and preserves earlier family, component and reduction priorities.
When eligible, it adds a bounded hint-assisted pass using the core's four ranked
variables. Successful assignment/equivalence reductions produce another original-
clause core, with exact model lifting; a checked terminal conflict remains false.
An inconclusive pass returns to the existing core planner. Descendants do not
automatically receive hints, and ordinary core-plan identity remains unchanged.
This control adds a pass and its costs; it is not a matched total-probe budget.

## Inputs and accounting

The study retains all **449 learned parents** from the previous core archive,
then adds **45 distinct parents** discovered from 36 fresh inputs at seed
**20261109064108**: 24 random 3-CNFs (eight each at 20/32/48 variables) and twelve
growing/signed/edited controls. The ordinary planner closes 30/36 fresh original
inputs. Their full source archive and solver decisions are retained. The 494
local cases include all learned-parent alternatives, including unselected paths;
they are not representative arbitrary CNFs or 494 distinct original source queries.
Discovery receives unlabelled CNFs. Parents, proofs, candidate clauses, local plans,
failures and measurements are saved in `report.json`.

All **907** prior eligible hint occurrences and **98** new ones transport. There
are **984 distinct core-clause records**, shared independently of discovery depth.
Omissions comprise 448 satisfied, 64 tautological, 99 already explicit and four
duplicate batch occurrences. There are no outside-core or failed-trace misses in
this sample; this is not a universal transport completeness theorem.

The translated-prefix walk examines **11,510 reason-literal occurrences** versus
**287,160** for fresh scan-based proof search given the same candidate clauses.
Transport preparation costs **0.95129 s**, including parent proof replay, core
projection, normalization, index reconstruction and independent child proof checks.
The conditional fresh-proof control costs **0.93100 s**, including proof search,
checking and persistence. These timing scopes differ; the literal-visit ratio
is not an end-to-end speedup. Generating/solving the 36 fresh input plans costs
**8.87824 s**, separately recorded before the local comparison.

| Local child mode | Closed / 494 | Operation seconds | Discovery seconds | SQLite bytes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing core planner | 223 | 14.41354 | 6.06309 | 55,119,872 | 4.70738 |
| Portable hints, extra pass | 224 | 16.82765 | 7.87721 | 63,885,312 | 7.72522 |

There are no lost local closures. Prior-edge closure is 198/449 -> 199/449;
fresh-edge closure is unchanged at 25/45. Both modes independently solve every
child core and retain **6,051 solver residuals**, with matching answers. Discovery
closure is distinct from SAT/UNSAT decisions. Transport preparation adds **0.95129 s**
to the hint pipeline beyond the operation column. That column includes local
recognition, discovery, checking, persistence, exact solving and successful lifts.
The hint mode costs **16.75%** more operation time, or **23.35%** more with preparation.

| Retained/work measure | Baseline | Extra hint pass |
| --- | ---: | ---: |
| Ordinary pattern nodes | 2,167 | 1,999 |
| Ordinary node logical bytes | 11,157,841 | 9,943,442 |
| Hint proof logical bytes | 0 | 2,181,006 |
| Context-plan logical bytes | 0 | 3,096,507 |
| Logical probe attempts | 14,468 | 16,136 |
| Selected unresolved literal occurrences | 57,827 | 57,595 |
| Warm seconds | 0.06691 | 1.31088 |
| Six-core Python peak bytes | 7,372,293 | 7,430,827 |

The smaller ordinary graph does not repay hint/context storage. The hint path
checks proof/context records on warm lookup; neither mode inserts new rows.
The allocation diagnostic uses the same six largest selected cores and excludes
preparation, native SQLite, RSS and full-corpus peak. Cold hint time includes both
the ordinary pattern/solver audit (**4.34585 s**) and a fresh hint/plan reader
(**3.37937 s**); overlap in replay work remains charged.

## The one local gain and the next experiment

`mechanisms.json` retains a controlled two-by-two test on local case **97**:
a 25-variable, 81-clause core at depth zero, derived by a checked common reduction.
It appears only in an **unselected alternative of original source 977**. No saved
selected whole-source path includes it; source 977's saved plan remains unresolved
with two selected leaves and 138 literal occurrences. The local baseline itself
has one unresolved leaf with 223 literals. Do not add this local gain to the
previous 719/805 original-source coverage count.

| Learned batch | Probe choices | Checked reduction | Local closure |
| --- | --- | --- | --- |
| Transported | core: 4, 5, 7, 19 | force 19=false, 13=false | yes |
| Rediscovered by child | core: 4, 5, 7, 19 | force 19=false, 13=false | yes |
| Transported | baseline continuation: 4, 5, 7, 11 | inconclusive | no |
| Rediscovered by child | baseline continuation: 4, 5, 7, 11 | inconclusive | no |

Thus the gain is explained by which variable is probed with the batch. A stronger
inherited batch is unnecessary in this control. The new hint pass is clear on
180 local cases, skipped by eligibility/priority on 83, forced on 169, common on
27 and equivalence-reducing on 35. A reduction is not itself a new source closure.

**Next priority:** rank continuation variables on the original core while using
the existing learned batch and existing number of passes. Test case97 and source
977, prior 956/1024/1189 controls, then complete prior/fresh source workloads.
Reconstruct choices from checked original traces or the exact core, never a
persisted unchecked list. Charge ranking and subsequent graph changes, preserve
any losses, and retain the present policies. This isolates the discovered cause
and may avoid rebuilding an augmented old batch solely for ranking.

Portable evidence can subsequently enter a separately checked continuation policy.
The diagnostic finds **1,456 inactive / 102 active deltas** across original probe
closures at **196** eligible cores. The original closure must first be validated;
only an inactive delta licenses direct reuse. These are unexecuted opportunities,
not saved probes. Integrating into an existing pass is preferable to assuming
that adding another fresh pass will save work. Global discovery coverage and
compact arbitrary-SAT closure remain open.

## Bounds and validation

For parent literal volume L, at most q hints and examined reason-literal volume R,
the translation adds expected O(qL+R) map/prefix work beyond full parent validation,
plus core normalization and repeated independent proof checks. Core normalization
is currently repeated per hint. Full-core keys/records require O(qL+R) payload
before context plans and ordinary descendants. Label bit lengths, checking cost,
number of cores and persistence must remain separate; no unrestricted polynomial
acquisition or lifetime-storage bound follows.

All **374 Python tests** pass (32.796 s). Eight new tests include exhaustive
512 two-variable formulas and 3,304 three-variable subsets of at most three
clauses, candidate RUP soundness, forced/common/equivalence translations, signed
renamings, edits, wrong parent dependencies, corrupted reasons, exact-core bindings,
empty/nonentailed clauses, context-specific model fibers, wrong child edges and
byte-identical cold replay without the parent graph. A first test incorrectly
expected a valid proof to fail after an unused clause was removed; the corrected
test distinguishes proof validity from the store's exact-source binding.

The full Lean build/axiom audit passes at **4,126 declarations / 1,968 theorem
declarations**. Four new archives replay byte-identically; all 51 measured code,
test and Lean fingerprints match. Older archives are untouched. Primary runs,
allocation diagnostics, Lean builds, tests and post-run controls were sequential,
without overlaps affecting primary timings. Generation, decoding/compression,
truth tables and post-run diagnostics are excluded from operation timings.
Object/database initialization is also excluded and was not separately timed.
Preparation, fresh-source generation and cold/warm replay are separately reported.
These are single synthetic samples, with no significance or industrial-speed claim.

```sh
python3 experiments/compare_cnf_hint_transport.py --output /tmp/new-hint-study
python3 experiments/analyze_cnf_hint_transport.py /tmp/new-hint-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
```
