# A failed gate transfer reveals exact nonterminal joins

Case 10 raises structural coverage **16/24 -> 17/24**, but the progress gate
does not improve acquisition. It makes the same choices as always-pilot and
uses **12.26% more patterns and 19.14% more probes** than immediate commitment.
The stronger finding is structural: the different routes rejoin at **four
nonterminal formulas**, sharing **39 new proof nodes**, of which **37 are
nonterminal**. An independently checked subproof preserves these exact joins.

## Unchanged transfer and the gate's limit

The [protocol](../experiments/results/cnf-progress-transfer/protocol.json)
transfers byte-identical policies, worker and validator to another known
development input. Budgets remain 128 admissions and sixteen operations per
batch, at most four batches. Two reversed fresh-process triples share the same
full parent. No threshold, budget or candidate count is tuned on case 10.

The original has **48 variables / 181 clauses / 543 literals**. Its selected
residual has **45 variables / 180 clauses / 557 literals / width five**. The
leading saved routes are pivots **22 and 17**. Pivot 22 begins with two
obligations and **1042 literals**. Its first trial costs **seven admissions /
64 probes**, leaving **three obligations / 1468 literals**. The gate explores.
The trial below pivot 17 costs **ten admissions / 67 probes**, leaving **two
obligations / 1040 literals**. Both pilots select pivot 17; the committed control
stays on pivot 22.

That large apparent frontier improvement does not lead to cheaper continuation.
The pilots perform twelve acquisitions versus nine and reach conditional depth
six versus four. The gate only distinguishes whether the first step reduces
literal mass; it cannot predict the value of the second route or its downstream
interaction. This result and the earlier successes remain together. Retuning
a scalar threshold on these examples would need separate validation.

| Resource | Committed | Always-pilot | Gated |
| --- | ---: | ---: | ---: |
| Batches to coverage | 1 | 1 | 1 |
| New patterns / distinct admissions | 106 | 119 | 119 |
| Probes | 653 | 778 | 778 |
| Source assumptions | 18 | 24 | 24 |
| New split records | 9 | 12 | 12 |
| Restoration and setup, seconds | 0.15288 | 0.13919 | 0.14310 |
| Expansion, seconds | 0.48031 | 0.56931 | 0.56577 |
| Bookkeeping, seconds | 0.14961 | 0.15439 | 0.14747 |
| Query-proof check, seconds | 0.25434 | 0.25716 | 0.26146 |
| Complete cold audit, seconds | 7.33273 | 7.34074 | 7.36450 |
| Compression, seconds | 0.84589 | 0.83085 | 0.82945 |
| Whole stream, seconds | 9.31591 | 9.39216 | 9.41249 |
| Mean peak RSS, bytes | 412,966,912 | 415,514,624 | 415,670,272 |
| Final SQLite bytes | 43,630,592 | 43,864,064 | 43,864,064 |
| Compressed bytes | 2,212,437 | 2,224,979 | 2,224,979 |

Gated local expansion rises **17.79%**, mean RSS **0.65%**, SQLite **0.54%** and
gzip **0.57%** against committed. Mean whole time is **1.04% higher**. The gated
paired times are **9.29810/9.52689 seconds**, versus committed **9.29744/9.33437**;
one difference is less than a millisecond. Two triples do not establish a
reliable small total-time effect. Always-pilot comparisons have mixed signs.
The two pilots have identical operations, proofs and archive bytes in both
repetitions; their timing differences are not different expansion work.

Complete auditing remains **78--79%** of time. The clock includes restoration,
setup, selection, gate, acquisition, bookkeeping, compression and both checks;
imports and final summary writing are excluded, while RSS includes all phases.
Parent acquisition remains in earlier records. Acquisition-free preflight costs
**0.17075 seconds** separately; retrospective validation costs **111.93 seconds**
outside timing, partly concurrent with tests. Pilot stays in the middle position
of both orderings, so this is not a complete position counterbalance.

## Four exact joins, beyond sharing contradiction

The committed proof has **116 distinct steps**, including 106 new nodes; the
pilot proof has **122 steps**, including 113 new nodes and six additional unused
trial patterns. Their acquisitions share 45 new rows and five splits, while
their final proofs share **39 new nodes** with identical rules and children:
33 unary reductions, four conditional nodes and two 2-CNF terminals.

These shared new nodes form four disjoint descendant regions. Each region has
the same entry key in both proofs, reached from different parent keys:

| Join formula | Entry transformations in both routes | New nodes below join | Inherited nodes |
| --- | --- | ---: | ---: |
| 27 variables / 81 clauses / 239 literals / width five | Elimination from distinct 28-variable parents | 12 | 1 |
| 32 variables / 95 clauses / 274 literals / width four | Probing from distinct 33-variable parents | 12 | 1 |
| 39 variables / 153 clauses / 475 literals / width five | Elimination from distinct 40-variable parents | 13 | 1 |
| 4 variables / 5 clauses / 11 literals / width three | Probing from distinct 11-variable parents | 2 | 0 |

The inherited node in the first three regions is the same contradiction
terminal. Their union therefore has **40 unique steps**, all verified by the
unchanged positive checker without acquisition. Full keys, boundary-parent
hashes, shapes, proof and verification counters are saved in
[`joins/`](../experiments/results/cnf-progress-transfer/joins/report.json).
The analysis takes **0.18489 seconds**, including archive restoration and
checking; this single diagnostic time is not a comparative benchmark.

The 39 shared rows occupy **283,851 raw key/payload bytes**, plus **39,431 raw
split-identity/payload bytes** for four split certificates. These exclude database
pages, indexes, Python objects and snapshots; they are not measured memory
savings. The union already stores each exact row once.

The 39-variable join is particularly informative. Its two parents each have
40 variables and 151 clauses, but 460 and 457 literals. Checked elimination
maps both to the same 153-clause, 475-literal formula. Literal count increases
while variable elimination reaches a reusable boundary. Likewise, two different
33-variable parents converge after probing to the same 32-variable formula.
This is evidence for investigating equivalent elimination or propagation
results, rather than using only raw frontier size to predict useful reuse.

Recognition here is exact equality of the complete policy/depth/canonical-CNF
key, with checked transformations into that key and checked proof dependencies.
An approximate match, equal formula shape, or an unchecked projection is
insufficient. The joining subproofs use changing local variable coordinates;
no fixed backdoor-size or general cheap-canonicalization bound follows.

These are two routes through **the same original**, not different queries.
Since that original is now covered, direct root reuse already avoids solving it
again. The analysis establishes reusable evidence at intermediate formulas,
not an additional speedup on this query or demonstrated cross-input reuse.

## Preserved checkpoint and next experiment

The union retains **180 distinct new patterns and sixteen splits**: **2,443
patterns / 249 pairs / seventeen inherited missing children**, with a
**999-step positive proof for seventeen originals**. Seven remain unknown.
Storage is **44,810,240 SQLite / 2,271,560 gzip bytes**. Independent full replay
checks all six trial archives and the union, including original bindings,
complete catalogs, query proofs, immutable prefixes and cold scheduling state.
All **372 tests** pass. All 307 prior sources, 3,500 artifacts and 64 manuscript
proof blocks remain unchanged. A post-hoc analyzer is separately bound; its
initial SQL column-name failure and source are retained. Solver policies stay
optional and unchanged.

**Highest next reuse target:** test the four checked joins on related inputs
whose complete root is not already stored. Start with distinct parents that
have the same checked elimination image, include edits that break that image,
and charge discovery, boundary verification, lookup, replay and persistence.
The existing exact lookup already handles a recognized key; the gap is reaching
that key cheaply from a new input and recognizing when reuse is invalid.
Compare against the current solver from matched histories before claiming
avoided work. Prefer that evidence over another threshold fitted to these cases.

The independent discovery pointer remains **case 7**, random 3-CNF with selected
**33 variables / 152 clauses / 470 literals / width four**. All eight saved
children exist; pivot 14's true child is already covered and seven are open.
Only the depth-zero original root exists. This offers a separate coverage
control while investigating whether nonterminal joins transfer beyond one input.
