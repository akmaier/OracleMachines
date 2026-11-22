# Probe cheap native queries before support partitioning

The preceding pilot found a useful first-false decomposition which its branch-count
screen rejected. It also spent too much on two queries already cheap under native
reuse. This experiment tests a different admission step: spend at most eight native
expansions before preparing the supplied support. A completed probe returns its
checked answer. A stopped probe preserves every completed checked proof in its
pending publication batch, then tries the six-clause partition or native fallback.

The solver remains experimental and optional. The candidate origin and variable
map are supplied. This is an acquisition probe, not automatic structural discovery
or an oracle for the eventual search cost.

## Correctness and persistence

Native publication already checks a node before inserting it and requires its
proof dependencies to exist. At an ordinary expansion-budget stop, all pending
nodes therefore describe completed subproblems, even though the queried root may
be absent. Committing this dependency-closed prefix preserves valid knowledge.
It does not turn the stopped query into UNSAT. Tests use a satisfiable source
whose early branch is refuted to enforce this distinction, then reopen the saved
archive under the independent native checker.

Unexpected exceptions, failed commits and uncertain transactions keep the existing
rollback and checked-cache invalidation behavior. The probe's commit path applies
only to the recognized native expansion-budget stop. Its result is explicitly
unresolved until a complete checked root or partition conclusion exists. A stopped
probe does not enter the negative-root pool as though it had a verdict.

The optional partition increases the previous maximum from five to six missing
clauses. It otherwise uses the same support preparation limits (32 nodes, 8,192
source literals and 128 KiB retained plan charge), injective transport check,
strengthened-premise check and first-false recomposition. Every negative branch
must complete. A positive branch supplies a native witness that lifts to the exact
target residual. An encountered residual's answer is not an answer to its original
source query without the missing composition evidence.

Probe and later acquisition share one total of 256 native expansions per query.
The remaining allowance is reduced by the probe's actual count. Later branches
and native fallback retain the original budget-stop publication behavior. Search
restarts from the target using saved proofs; no live continuation stack is retained.
Some incomplete work can therefore be repeated. Retained witness and negative
hints can also affect the subsequent search. Neither eight expansions nor the
256 total bounds normalization, full proof checking, SQLite work, time or RAM.

## Frozen comparison

Each cold seed contains exactly the preceding historical prefix plus the first
addition's committed proof rows from the previous reverse-policy worker. Deletion
answers and all later work are excluded. Every current target root is absent from
its seed. This is a matched cold-start comparison; counts need not equal the
previous experiment's warm addition/deletion stream.

The three exposed targets are the prior deletions for cases 25, 31 and 61. Six
fresh targets remove different clauses shared with their supplied core, optionally
adding one fixed signed ternary clause. They are generated before timing, with no
outcome selection, and their roots are absent from the preceding cumulative
union. They remain local edits of selected residuals, not representative external
SAT benchmarks or an independent broad family-discovery sample.

Five arms run in separate serial processes in two opposite orders: the full
input-safe affine baseline; the native-only baseline; probe followed by native
fallback; unconditional reverse six-clause partitioning; and probe followed by
that partition. The native ablations expose dispatch and restart overhead. The
probe does not replace the affine fast path in the general solver. Broader
integration must preserve that path and measure its interactions.

The unchanged measurement harness charges support preparation, proof checking,
publication, branch work, composition, warm-bank setup and lookup, full cold
replay, reconstruction, diagnostic measurements, serialization and persistence.
Complete measured worker time includes full-prefix restoration and replay, which
can dominate these short queries. RSS includes loaded archives and measurement
allocations. Endpoint object/SQLite totals sum three separate worker states; they
are not a single combined live-state or peak bound. Prior acquisition and supplied
candidate selection are separately preserved sunk work.

Proof deltas and raw partition sidecars retain each trial's exact evidence.
The cumulative union preserves earlier authoritative payloads; alternative valid
trial proofs stay in the deltas. Partition sidecars remain necessary even if the
native archive lacks a whole-target record. Their duplicated source descriptions
are charged, and compression/interning is still a separate opportunity.

## Results: a useful probe, with remaining routing regressions

All nine targets finish as UNSAT in every arm: 90 attempts across 60 workers.
The benefit concerns measured acquisition cost, not increased decision coverage.
Totals below sum three independent case streams and average the two arm orders.

| Measurement | Boundary affine | Boundary probe + partition | Fresh affine | Fresh probe + partition |
| --- | ---: | ---: | ---: | ---: |
| Query seconds | 0.16900 | 0.09087 | 0.36859 | 0.32256 |
| Complete measured worker seconds | 23.81367 | 23.70347 | 24.50441 | 24.37343 |
| Native expansions | 81 | 32 | 138 | 122 |
| New native records | 89 | 33 | 172 | 148 |
| New native key/payload bytes | 825,948 | 289,557 | 1,548,770 | 1,241,463 |
| Endpoint checked-object bytes | 3,519,190 | 1,862,548 | 6,570,208 | 6,238,693 |
| Endpoint SQLite bytes | 188,932,096 | 188,092,416 | 190,066,688 | 189,603,840 |
| Compressed delta + raw partition sidecars | 64,399 | 81,616 | 118,075 | 209,095 |
| Warm setup + lookup seconds | 0.00378 | 0.01000 | 0.00682 | 0.01995 |

Query time falls **46.23% on the exposed boundary / 12.49% on fresh edits**, in
both orders. Complete measured time changes by only **0.46% / 0.53%** on the mean;
boundary paired signs are mixed. Full-prefix replay dominates those totals. The
small complete-time changes do not establish robust end-to-end improvement.
Endpoint checked-object totals fall **47.07% / 5.05%**, but these are not peak
memory bounds. Raw partition sidecars still dominate the incremental saved
package: it grows **26.73% / 77.09%**. Warm setup plus lookup also regresses.

The original six-clause boundary in case 31 takes 75 native expansions under the
matched cold affine baseline. Unconditional partitioning takes 18; the combined
policy takes 26, including its eight-expansion probe, and reduces query time from
**0.15347 to 0.07738 seconds**. The probe retains three checked pending records.
They do not reduce this partition's expansion count. Probe-then-native takes 80
expansions: five more than ordinary native solving because incomplete search
frames must be reconstructed. Retaining completed proofs is not the same as
retaining a live continuation.

The probe prevents the two known preparation regressions. Cases 25 and 61 finish
within two and four native expansions, without inspecting the supplied candidate.
Unconditional six-clause partitioning instead takes eight and nine. Across the
fresh edits, four cheap queries finish within the probe. Two probes stop and
retain six pending checked records in total. Those records survive restart and
are independently checked; incomplete source roots remain unresolved at the stop.

The fresh case-31 stream remains a counterexample to uniformly cheap expansion.
Its first deletion takes **86 rather than 65 expansions** under the combined
policy; its replacement takes **28 rather than 65**. The first partition's six
branch counts are **1, 61, 1, 10, 1, 4**, before adding eight probe expansions.
The second query's proof graph uses one native record published by the first,
which was absent from the common seed. This is exact result reuse, but it does
not establish how much of the timing difference comes from reuse: the formula
also changes. An independent cold ablation would be needed for that attribution.

Unconditional six-clause partitioning raises aggregate fresh query time from
0.36859 to 0.38211 seconds despite fewer expansions. Probe-then-native is also
slower (0.38244 seconds). The useful combination depends on avoiding preparation
for cheap queries and on a favourable partition for the expensive query. It does
not justify replacing the general affine baseline or assuming every near-core
edit is easy.

## Next gap and resume point

The dominant remaining acquisition is the second first-false branch of fresh
case 31's deletion: **61 of the combined policy's 122 fresh-stream expansions**.
`next-branch.json` saves its exact source and the state immediately before it:
the common prefix plus five newly committed native records from the probe,
premise and first completed branch. Its root is absent in that state, and its
unit screen remains nonterminal with 920 residual literals. Reconstructing the
state uses the bound trial delta; it never imports this branch's later answer.
No extra solving was done in the diagnostic.

Next, inspect the shared-variable interaction and binary structure in this branch
and compare a concrete recognition or decomposition change with ordinary solving.
A candidate must explain this regression and transfer to fresh inputs, rather than
being selected only after timing. Automatic donor/map retrieval and integration
back into original source queries remain larger coverage gaps. Retaining native
continuations and compressing sidecars are supporting opportunities; neither
should be credited before its full cost and invalidation rules are measured.

Resume `experiments/results/cnf-probed-partition/checkpoint.json`. The immutable
protocol and per-worker deltas preserve all outcomes and paired regressions.
`analysis.json` includes probe retention, branch counts and read-only dependency
reachability; the latter is not a counterfactual speedup experiment.

Validation passes: **1,388 full / 70 focused tests**, 90 chronological attempt
audits, 24 new and 36 previous partition records, and 5,650 earlier composed
records. Both native readers check the cumulative proof union: **74,517 native**,
71 affine-negative, 42/53/22 equivalence, and 34 binary-discovery records. All
690 prior sources and 8,866 prior artifacts are unchanged. Four alternative
payload observations remain in trial deltas. The full suite reports 44 existing
unclosed-SQLite warnings; focused tests report none. Warning collection sites are
not necessarily allocation sites. The final source ledger has 696 files. The
manuscript builds to 237 pages without warnings; all 64 existing proof blocks
remain unchanged.

The first test fixtures closed sooner than expected because symmetric residuals
shared canonical proofs. Their failure log and source are retained in
`initial-tests/`; corrected fixtures exercise budget stops before timing. No kernel
change was needed. This is tested Python with independent proof replay, not a
Lean refinement proof or a polynomial unrestricted-SAT result.
