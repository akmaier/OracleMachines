# Share first-false partition preparation

The [cofactor handoff study](cofactor-handoff.md) found four constructions of the
same six-branch partition per query. They occurred in premise publication,
acquisition, sidecar creation and independent sidecar checking. This experiment
removes repeated producer work while retaining the independent checker.

## Exact construction and trust boundary

Given source `F` and ordered missing clauses `C1,...,Ck`, branch `i` restricts
`F ∧ C1 ∧ ... ∧ C(i-1)` by the assignment falsifying every literal of `Ci`.
The regions are disjoint: any source model that fails a missing clause has a
unique first failed clause. A checked refutation of the strengthened premise
`F ∧ C1 ∧ ... ∧ Ck` excludes the remaining region. UNSAT therefore requires all
branch refutations. A branch model must lift through its falsifying assignment
and satisfy the source. Changing clause order changes the branch identities.

The new preparation snapshots the raw source and ordered missing-clause input,
validates exact nonzero integer literals, and rejects tautologies, missing clauses
already in the source, duplicate or empty missing clauses and variables outside
the source. Canonical solver input reaches this interface after normalizing
arbitrary CNF syntax. The descriptor retains both raw missing clauses and their
normalized versions, preserving the sidecar's exact representation. It also
retains a frozenset of validated source clauses for premise binding.

Immutable prefix tuples share source clause objects and preceding missing clauses.
Residual formulas are computed once. Premise publication uses the validated clause
data without constructing branches that it never consumes. Acquisition uses the
prepared residuals; sidecar creation uses the same prefixes and assignments for
model lifting. This path has no guard chain, matching the existing probe/partition
wrapper. Guarded sidecars continue through the existing implementation.

The final sidecar enters the unchanged independent checker. That checker receives
no prepared object: it reconstructs the source partition, checks the strengthened
premise, binds every child to the exact residual, and checks answers and lifted
models using fresh native reads. A descriptor does not authenticate a negative
answer. Missing dependencies, altered sources or reordered missing clauses remain
invalid. Only the existing native nodes and checked sidecars are persisted.

Preparation is local to one query and is not indexed, retained by the solver or
reused across queries. Caller mutation cannot alter its frozen contents. The
public factory's ordinary clause sets are used for validation; there is no
content-indexed memo search. This avoids recognition misses at unrelated callers.

## Resource bounds

Let `M` be the source clause count, `L` its literal occurrences, `R` the total
missing-clause occurrences and `L_i` the literal occurrences in residual `i`.
A shared prefix representation retains the source/missing clause objects once,
with `k M + k(k-1)/2` prefix references and all residuals. Its payload scales as
`O(L + R + k M + k² + Σ L_i)` cells, including validated clause membership and
assignments. Integer widths and object overhead remain explicit. Residuals are
still materialized; this is not compression of arbitrary SAT solutions.

Validation, clause sorting, restriction, tuple construction and sizing are charged.
The wrapper admits at most six missing clauses, but the descriptor has no fixed
byte cap: its memory grows with the source and residual outputs. The conservative
retained charge deliberately overcounts shared references; separate object-graph
walks check it after timing. Construction transients, allocator overhead, control
objects and the rest of the solver/process are outside that charge.

One producer preparation plus one independent reconstruction replaces four branch
constructions for completed partitions. The native search, probe budget, branch
order and sidecar format remain unchanged. Cheap construction does not make all
resulting branches cheap or yield a uniform arbitrary-SAT expansion bound.

## Frozen comparison

Four policies form two paired ablations: binary-frequency routing with/without
shared partition preparation, and cofactor-handoff routing with/without the same
preparation. Six previous novel edits become controls; six new fixed-seed nearby
edits have roots absent from the preceding union. Each arm restores the same
appropriate cold prefix. Donors/maps and previous acquisition remain supplied.

Forty-eight separate serial workers run in two opposite orders, giving 96 attempts.
Timing precedes profiles, tests and cumulative audits. Query measurements include
snapshots, validation, construction, sizing and cleanup. Complete worker time also
includes restoration, proof checks, warm reuse, persistence and cold reconstruction;
it is not production query latency. Each prepared arm must reproduce its parent's
models, decisions, expansions, native payloads and partition sidecars exactly.

## Result

| Stream / parent policy | Expansions, before = after | Query seconds before | Query seconds prepared | Mean query change | Mean complete-worker change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Six controls / binary frequency | 53 | 0.175473 | 0.161276 | -8.09% | -0.79% |
| Six controls / cofactor handoff | 55 | 0.209510 | 0.195654 | -6.61% | -0.35% |
| Six new edits / binary frequency | 58 | 0.189879 | 0.178205 | -6.15% | +1.07% |
| Six new edits / cofactor handoff | 61 | 0.235401 | 0.225972 | -4.01% | +0.23% |

Values sum separate case streams and average two serial orders. All four query
comparisons improve in both orders. On new edits the binary-policy paired savings
are 9.66 and 13.68 ms; the handoff-policy savings are 6.07 and 12.79 ms. Complete
new-edit worker time is worse in both orders for binary frequency, and has mixed
signs for handoff. We preserve that regression; there is no overall fresh-workload
speedup. The control complete-time reduction has both orders improving for binary
frequency and mixed signs for handoff. These small local comparisons do not
establish general runtime superiority, and general solver defaults remain unchanged.

Only case 31 reaches partitioning in these streams. The other targets finish in
the existing probe without paying descriptor construction. On the six new edits,
explicit producer construction builds 12 rather than 24 branches and scans
11,232 rather than 22,464 restriction literals. Its clause-validation input count
falls from 7,776 to 3,980. These route counters exclude the independent checker's
local counters and must not be presented as all solver work. The separate audit
confirms the full construction change: four identical six-branch structures become
one prepared structure plus one independent reconstruction per partitioned query.

The descriptor shares immutable prefixes. For the selected deletion, its returned
object graph is **259,532 bytes**, versus **403,780 bytes** for one old returned
source/missing/branch bundle: **35.72% smaller**. The replacement has the same
relative reduction, 404,964 -> 260,308 bytes. The checker's reconstructed bundle
still occupies 402,964 / 404,164 bytes.
These are single returned graphs, not simultaneous live-memory or RSS peaks.
The descriptor remains live during independent checking. Maximum conservative
preparation charge is 741,716 bytes across the trials; the selected new descriptors
have charges 737,140 and 739,804 bytes. There is no fixed descriptor byte cap.

Native payloads and persisted sidecars match each parent exactly. On new edits,
binary-frequency native key/payload space remains **522,190 bytes**, and compressed
deltas plus raw sidecars remain **152,812 bytes**. The handoff figures remain
727,736 and 171,816 bytes. Summed endpoint checked-object graphs decrease slightly
(1,840 bytes in either new-edit arm), reflecting object sharing; this is not a
peak-memory bound. The new descriptor itself is not persisted.

The largest new query is the case-31 deletion. Its binary-frequency time falls
88.39 -> 82.51 ms; handoff falls 111.03 -> 104.77 ms. All four profiles retain
their respective native expansions and publications. Binary frequency still uses
29 publications and 24 propagations; handoff uses 39 and 31. Preparation removes
one normalization in either policy and repeated branch construction, without
changing their search trees. Profile durations include instrumentation and overlap;
use the paired uninstrumented trials for performance claims.

## Next structural target

The prepared binary-frequency policy remains cheaper than the prepared handoff
policy on these new edits. Its largest query has branch expansion counts
`[1,9,1,6,1,3]`, after eight initial probe expansions. The second branch takes
22.51 ms in the first trial and is the dominant remaining acquisition branch.
The corresponding handoff policy still takes nine expansions there; it also adds
one expansion in each of the fourth and sixth branches. Pure preparation sharing
cannot repair that continuation difference.

`next-target.json` now contains a `branch_candidate` captured **before** the
second branch is acquired. It has **125 variables, 57 binary clauses and 263
ternary clauses** (903 literals), with 247 ordinary expansions left in the shared
budget. The target root is absent. Its exact persistent seed consists of the
bound historical prefix plus **three** earlier checked native rows identified in
the frozen trial delta. A fresh reader checks those rows and their prerequisites
and confirms the target is absent. Warm transient pools are not serialized.

**Next primary investigation:** inspect the binary/ternary interaction in this
saved branch for a compact checked consequence set, useful decomposition or shared
subproof that the bounded recognizers miss. Compare existing recognition policies
before adding another mechanism; charge recognition and the surviving search.
A completed cofactor proof can be retained, but an inconclusive probe cannot
stand in for a verdict. The branch proof must still compose into the exact source
partition. No new decision coverage is claimed from the current acquisition gain.

The independent checker remains a necessary reconstruction boundary. Further
producer micro-optimizations should compete with this branch cost, probe admission,
source-level donor/map discovery and sidecar/cold-replay costs. The complete worker
includes repeated full audits, so its dominant replay costs must not be confused
with production per-query latency.

## Verification and preservation

All **1,438 tests** and **146 focused tests** pass. Ten new tests cover immutable
snapshots and prefix sharing, invalid syntax and missing clauses, disjoint
first-false regions, SAT/UNSAT recomposition, altered sidecars, stale prerequisites,
conservative graph accounting including large variable labels, identical policy
payloads, budget/failure recovery, cold readers and 254 small three-variable inputs.
The full suite retains 44 previously observed unclosed-SQLite warnings; focused
tests emit none.

Independent validation checks **96 attempts from 48 workers**, chronological
native dependencies, exact seeds, repeat-order agreement and previous controls.
All **48 prepared/parent query pairs** have identical decisions, models, native
payloads, partitions and expansions. Both readers replay the cumulative authority,
32 current partition records and 194 preceding records. The union adds **92 unique
native nodes**, reaching **75,508**. The 32 alternative-payload observations stay
in trial deltas; previous authoritative payloads and all extension tables remain
unchanged.

All 733 previous source fingerprints and 10,783 artifacts in 133 manifests are
verified unchanged. The final source ledger contains 740 files. Older unrelated
composed/inventory audits remain manifest-bound. The manuscript builds to 240 pages
without warnings and retains all 64 earlier proof blocks. Resume
`experiments/results/cnf-partition-preparation/checkpoint.json`. No external SAT
benchmark or Lean refinement theorem is added.
