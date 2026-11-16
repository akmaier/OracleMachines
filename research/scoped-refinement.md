# Check the reachable split graph, preserve the full history

An optional query view closes case 22 with the unchanged nested work policy and
reduces complete measured time **12.59685 -> 6.94722 seconds (44.85%)**. Both modes
store identical records and produce identical choices and proofs. Structural
coverage rises **7/24 -> 8/24**. The saving comes from avoiding an eager semantic
check of unrelated history before the query; full independent cold verification
still runs after every batch.

## Exact scope and its restrictions

[`ScopedSplitRegistry`](../experiments/cnf_scoped_refinement.py) scans all split
identities into a source index. Starting at the requested original root, it checks
every split for each reachable source with the existing checker, activates only
pairs whose two children are present, and follows every enabled internal or
external route. Unchosen alternatives remain included. Ordinary pattern lookups
consult the complete database, so a working-view miss never means global absence.
The scheduler, recognition, candidate ranking and acquisition methods are inherited
unchanged from `NestedRefinement`.

For a fixed valid snapshot, let R be the nodes reachable from the requested roots
through ordinary rules and active external splits. The source index contains
every persisted split. At each visited source, the scoped and full builders
therefore expose the same ordered rules and premises. Induction along reachability
gives the same R and rules on R. The finite positive-coverage fixed point, and thus
coverage of the requested roots, is unchanged. Sources outside R cannot supply
a missing premise without first being reached. This is an exact restriction of
an existing derivation graph, not a new tractable SAT class.

Refresh retains the existing append, policy, schema and external-writer guards.
It rescans reachability after an append, including newly reachable sources and
previously pending pairs whose children have arrived. A second guarded read
transaction protects exposure after suffix indexing. Insertion order and repeated
premises are retained. The live-cache contract requires immutable historical
objects and exclusive append-only ownership; raw file/pragmas or in-memory object
mutation are outside it, as in the existing registry.

The query view is **not a whole-archive validity certificate**. An unrelated
malformed semantic certificate may remain deferred. Tests confirm rejection when
it becomes the requested source and by the full cold checker. Identity mismatches,
missing reachable premises, changed policies and detected non-append writes fail
closed. Every archived result below passes a separate complete check, with fresh
acquisition disabled.

## Matched continuation of case 22

[The protocol](../experiments/results/cnf-scoped-refinement/protocol.json) fixes
the same 1,790-pattern / 171-pair parent and the same disjoint binary-mixture input.
The selected unresolved component has 48 variables, 204 clauses and 612 literals.
Its four saved pairs already have eight child records; one branch of pivot 18
is covered. Both modes start from this complete history. Each may use four batches
of 128 recognition admissions and sixteen pair attempts, with source assumptions
charged separately. Two repetitions reverse mode order and run in fresh processes.
This is a known development input, not a new holdout.
Acquiring the parent history was paid for in earlier preserved experiments and
is not repeated in these continuation means; restoring and accessing it is charged.

Both modes close in one batch with **9 new patterns / 2 new pairs / 4 source
assumptions / 29 probes**. No budget is reached. The independent validator compares
all acquisitions, selected operations, stored payload digests, complete reachable
catalogs and target proofs across all four streams. The archive bytes also match
between modes. No inference default is changed.

| Resource, mean unless count | Eager startup | Scoped startup |
| --- | ---: | ---: |
| Startup, seconds | 5.72447 | 0.16200 |
| Local expansion, seconds | 0.08052 | 0.07272 |
| Bookkeeping, seconds | 0.09733 | 0.08495 |
| Full cold check, seconds | 6.01717 | 5.96027 |
| Compression, seconds | 0.61285 | 0.60763 |
| Whole stream, seconds | 12.59685 | 6.94722 |
| Peak process RSS, bytes | 461,447,168 | 360,734,720 |
| Initial checked pattern nodes | 1,790 | 40 |
| Initial checked split certificates | 171 | 4 |
| Final checked pattern nodes in live inventory | 1,799 | 49 |
| Final checked split certificates in live registry | 173 | 6 |

Whole-stream timing includes restoration, identity indexing, guards, discovery,
bookkeeping, snapshots, compression and every cold check. It excludes interpreter
imports and the final summary write. Process RSS includes imports, both live and
cold verification, and all other phases. The observed mean RSS reduction is
**21.83%**, not an asymptotic space bound or isolated cache saving. Only two
repetitions were run; raw samples are preserved. The main inventory's checked-node
count is not total process memory.

Each final arm occupies **34,148,352 SQLite bytes / 1,651,015 gzip bytes**. The
preservation union has the same SQLite size but **1,652,138 gzip bytes** from its
own serialization. Persistent storage is unchanged between modes. The scoped view
still retains an index of all 173 split identities, including 167 deferred records.
Its final route metadata serializes to 155,123 bytes plus an 800,567-byte source
index, versus 4,520,121 bytes for the eager route metadata. These are diagnostic
serialization sizes, not peak RAM or persisted cache formats.

## What this discovery reuses

[The original-input proof](../experiments/results/cnf-scoped-refinement/explanation.json)
has **32 distinct steps**: one component decomposition, three conditional nodes,
26 unary reductions (twenty probe rewrites and six eliminations), and two family
leaves. Of its pattern steps, **23 were already retained and nine are new**.
The easy component is a nine-variable / eight-clause / sixteen-literal 2-CNF,
also recognized as Horn, dual-Horn, zero-valid and one-valid. The random core's
four conditional leaf occurrences share the contradiction terminal. Only that
terminal is shared: 35 unfolded occurrences become 32 nodes. This does not show
broad nonterminal sharing across arbitrary inputs or a new SAT/UNSAT output API.

Maximum conditional depth is three, with branch-local coordinates and reductions
between choices. It is not a fixed three-variable backdoor or a minimum-depth
result. The proof checks both branches and exact recomposition with the easy
component; the original's completion is not inferred from a single successful
cofactor.

## Remaining costs and continuation

The full union retains **1,799 patterns / 173 pairs / 17 inherited missing children**,
with a **477-step positive proof for eight originals**. Sixteen originals remain
structurally unknown. All **351 tests** pass, including pending activation,
interrupted cold resume, corruption and invalidation controls. Independent checks
cover the parent, four trial archives and the union. Previous results and all
64 existing manuscript proof blocks remain unchanged.

Startup still reads the full archive and pattern rows, scans all split identities,
and pays global table guards. Its cost is not bounded just by the reachable graph.
Each refresh revisits the reachable graph. Live semantic checking now depends on
the requested graph and its checker dependencies, but raw historical row maps and
the complete identity index still use history-dependent space. Recognition and
expansion worst cases are unchanged. Fully connected histories can eliminate the
benefit and add indexing/traversal overhead; no universal speedup follows.

The **5.96027-second full cold check is now about 86% of the scoped whole stream**;
compression adds about 0.61 seconds. The next cost opportunity is to share one
guarded session and one complete checkpoint audit across several queries, while
retaining each result and checking every positive proof. That changes audit
granularity and requires an explicit matched comparison; it is not implemented
by this result.

For broader structural coverage, [the bound successor](../experiments/results/cnf-scoped-refinement/next-discovery.json)
is case **23**, a **connected binary mixture** with a selected **59-variable /
255-clause / 767-literal / maximum-width-four** residual. All eight children of
its four saved pairs are present and uncovered. Transfer the same policy there
and examine the shared-variable interaction; the disjoint decomposition that
helped case 22 is not available in the same form. Historical query times select
the target, not a fresh timing against this expanded union.
