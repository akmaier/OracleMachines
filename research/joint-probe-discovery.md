# Learn binary constraints from paired assumptions

Checkpoint: 27 November 2026. Source-checked pair probing raises structural
coverage **124/138 to 131/138**, while increasing bucket width from eight to nine
stays at **124/138**. It closes two of the four previously exposed unique roots,
one SAT and one UNSAT, plus the SAT repeat. New unique coverage rises **15/24 to
19/24**. No baseline verdict is lost. The common fallback already answers every
query. Production defaults remain unchanged.

Sharing propagation prefixes avoids substantial acquisition work and compresses
local evidence. Its small total-runtime difference from rebuilding prefixes has
mixed signs. Broader coverage is the established improvement; a reliable runtime
win against the baseline is not established.

## The pattern and its restrictions

The previous seven exposed leaves have no failed single assumption. A pair can
still conflict: for distinct variables, a contradiction under `a` and `b` proves
`not a or not b`. This supplies binary constraints that are absent syntactically
from the mixed-width input. It differs from the older
[joint forcing policy](joint-binary-consequences.md), which batches already found
forced values. Both reuse checked consequences; neither defines a new tractable
SAT family.

`cnf_pair_probe_learning.py` builds one occurrence index for an exact normalized
leaf. It ranks variables by descending occurrence frequency, breaking ties by
identifier, then enumerates signed pairs in a deterministic order. Already
present binary clauses are skipped. A pass attempts at most **256 pairs** and
retains at most **32 new clauses**. Every proof refers to the **same original
leaf**; learned clauses do not feed back into that acquisition pass.

A first-assumption prefix records justified unit steps and any conflict. A second
assumption either contradicts a forced value, triggers a checked propagation
suffix, or produces no learned clause. An already conflicting prefix also proves
the binary clause, though it admits a stronger unit consequence. All conflict
clause references and unit reasons are checked on the exact source. A successful
probe does not certify satisfiability or any stronger exhaustion claim.

Two acquisition modes isolate state reuse:

- **Restart** rebuilds the first-assumption propagation state for each pair.
- **Shared** retains that state for consecutive second assumptions with the same
  first assumption. It copies assignment, clause-counter and satisfaction state
  before each needed suffix. The saved prefix is never mutated or carried into
  a changed formula.

Both modes share the occurrence index and persist each used prefix trace once.
A clause record references its prefix and retains its own second assumption and
suffix. Cold replay checks each prefix once, copies the relevant assignment and
checks every suffix. Evidence is bound through the containing leaf certificate,
not through a variable identifier or a digest-only match. Restart/shared proofs
are identical modulo the outer mode field.

`cnf_joint_probe_buckets.py` refines unresolved depth-zero buckets. It adjoins a
nonempty checked clause batch and invokes the previous selective-restart engine
at depth zero, with no recursive pair refinement. This includes leaves under
already-SAT parents; that unsuccessful selection cost remains charged. Empty
batches retain the original unknown bucket.

Adjoining entailed clauses preserves the full model set. A terminal witness is
therefore a witness for the original leaf and lifts through its original incoming
unit/relation maps. A terminal refutation refutes that leaf. Existing conditioning
requires one SAT child or both UNSAT children. Every SAT edge and root witness is
checked, including branches not selected for the final model. Unknown terminals
remain unknown. Base and width-nine controls translate exactly to the preceding
engine with their corresponding bucket allowances.

At depth two there are at most four leaves: **1,024 pair attempts and 128 learned
clauses per root**. Nonempty batches add at most four depth-zero terminal
preparations to the at-most-seven original edges. Earlier single probing,
restriction, relation recognition, buckets and each new terminal retain their
separate quotas. Prefix building, suffix copying, candidate ranking, failed
attempts, proof construction and checking are charged. These bounds are not a
wall-time guarantee or an efficient unrestricted-SAT procedure.

## Frozen coverage and complete costs

The comparison preserves all 110 preceding queries and adds 24 frozen unlabelled
constructions plus four exact normalized repeats. New cases are random three-CNFs
at 32–48 variables, nonfolding hidden-binary motifs with deleted-conflict controls,
and parity prisms. The motifs need two simultaneous guard values to activate a
conflict. No new exact source duplicates the preceding panel, though families
recur. Labels never guide acquisition. There are 84 SAT and 54 UNSAT queries;
this synthetic sample is not representative external SAT evidence.

| Cohort | Base | Width nine | Pair learning |
| --- | ---: | ---: | ---: |
| Previous queries | 105/110 | 105/110 | 108/110 |
| New unique inputs | 15/24 | 15/24 | 19/24 |
| New repeats | 4/4 | 4/4 | 4/4 |
| Total | 124/138 | 124/138 | 131/138 |

Five cyclic process orders start empty with the same fallback. Complete time
charges input, discovery including internal checking, explicit checks, evidence
and database writes, warm/cold replay and compression. Startup, protocol
construction, oracle labels, historical acquisition, lineage audit and post-hoc
profiles are additional. Both native cold readers audit fallback archives; the
two JSON passes share one implementation.

| Policy | Complete seconds | Compressed SQLite + JSON bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| Fresh | 6.65687 | 1,595,454 | 221,233,152 |
| Base | 8.72905 | 755,262 | 136,986,624 |
| Width nine | 9.78001 | 761,157 | 140,656,640 |
| Pair restart | 8.70655 | 535,762 | 114,343,936 |
| Shared prefixes | 8.64378 | 536,114 | 115,474,432 |

Shared is **11.62% cheaper than width nine**, with all five paired signs favorable.
Its **0.98% lower mean than base** has one unfavorable and four favorable pairs;
its **0.72% lower mean than pair restart** has two unfavorable and three favorable
pairs. These small mixed differences do not establish reliable total-runtime
wins. Shared remains **29.85% more costly than fresh**. All regressions are kept.
RSS values are process observations, not worst-case memory bounds.

## What was actually reused

Across unique prepared programs, 7,062 pair attempts retain **846 binary clauses**
in **33 refinements**. There are 691 suffix conflicts, 123 contradictions of a
prefix-forced value, and 32 already conflicting prefixes. The latter 32 encode
consequences also implied by a unit; not every gain is attributable solely to a
conflict that requires both assumptions. Counts and exact proof bindings are in
`evidence-kinds.json`.

Sharing reduces first-assumption state builds **7,062 to 127**, avoiding **6,935**
rebuilds. Occurrence visits fall **467,895 to 272,842** (about 42%). Both modes copy
181,592 suffix-state entries. The pooled evidence contains 115 prefixes and 244
prefix unit steps. Inlining the prefix into each clause record would repeat 2,847
steps and use 183,171 compact bytes, versus **132,005 pooled bytes (27.93% less)**.
This is an explicit representation comparison, not a measured speedup against an
unpooled cold checker.

Nineteen refined leaves receive verdicts: seven SAT and twelve UNSAT. Fourteen
remain unknown, six below already-SAT parents. The outer graph remains at 374
nodes and 147 splits. Thirty-three separate terminal nodes and 152 terminal
bucket steps are added to 1,303 outer steps. Shared targets remain 37, with 32
distinct-raw merges, all constant. There is **no new nonconstant residual sharing
across leaves**. The prefix sharing is local to one exact source.

Shared compressed JSON **grows 291,751 to 356,193 bytes** versus base. Combined
package savings come from fallback records falling **856 to 355**. The small
restart/shared compression difference comes from their mode strings, not changed
proof structure. Diagnostics add 698,253 bytes.

The largest shared-policy costs are **discovery 2.86258 s**, including its internal
checks, and **cold replay 2.62962 s**. Solve/explicit checking costs 1.42324 s,
warm replay 1.19003 s, archive persistence 0.43102 s and evidence writes 0.09254 s.
Prefix reuse affects only part of acquisition. Repeated terminal/source checking
and validated normalization/intermediate reuse remain the larger cost questions.

## Remaining frontier and next target

Seven unique roots remain: `d-j07`, `d-j06`, `k14`, `k15`, `k16`, `k17`, `k09`.
All have SAT oracle labels; the structural engine does not yet certify them.
Their eight final residual leaves have widths 9–11; two stop before elimination.
They have no units, disconnected split, binary conflict, forcing or equivalence
block, and are neither Horn nor dual-Horn. All **606** single-assumption probes
finish without a conflict, with no truncation.

A separately charged diagnostic performs another bounded pair batch on each
**final** residual. It obtains **177 new clauses in all eight leaves**: five
batches hit the pair cap and three the learned-clause cap. Subsequent checked
depth-zero terminals certify three leaves SAT, belonging to `d-j07`, `k16` and
`k17`. This is **leaf evidence only**, excluded from measured root coverage and
timing. The other five leaves remain unresolved. Profiles target
`node.refinement.terminal.nodes[-1]` where a refinement exists, rather than the
outer node's earlier CNF; exact source and containing-proof bindings are retained.

**Next coverage investigation:** bounded checked feedback of learned clauses,
compared with a larger one-shot pair allowance. Rebuild or rebind indexes when
the source changes, prevent circular proof dependencies, charge repeated terminal
preparation, and compose any improved leaf through the whole root. Merely doing
more single-literal probing on these unchanged leaves has no remaining failure.
For cost, prioritize validated intermediate/source reuse within checking and
avoid assuming another reduction in prefix builds will move total time much.
General coverage, efficient recognition of all categories, compact recomposition
and unrestricted expansion bounds remain open.

## Verification and continuation

All **2,355 full tests and 55 focused tests pass**. Seventeen new tests cover every
two-variable CNF, small random inputs with tiny limits, a hidden binary constraint
with no single failure, deletion controls, prefix immutability, assumption clashes,
malformed evidence, exact baseline/width translation, signed model lifting and
cold checking with discovery disabled. The full suite retains existing SQLite
ResourceWarnings.

An additional independent semantic audit enumerates **10,160 assignments over
200 small CNFs** (197 satisfiable), verifying that all 1,455 learned clauses
preserve the complete model set and both acquisition modes emit identical evidence.
This audit is outside timed comparison. The main audit regenerates certificates
and diagnostics for all 25 measured reports, checks independent oracle answers and
models, decodes JSON evidence, and reopens fallback archives with both readers.

All **234 prior manifests, 51,826 artifact entries, 1,283 scientific sources and
76 proof blocks** are preserved. Six new scientific sources and one proof are
added. The manuscript is compiled and the new pages rendered for inspection.
Resume `experiments/results/cnf-joint-probe-buckets/checkpoint.json`, key
`joint_probe_buckets`. `analysis.json` retains costs and regressions;
`remaining.json` and the source-bound structural, single-probe and next-pair
profiles retain the frontier. No production default or unrestricted claim changes.
