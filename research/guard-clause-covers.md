# Wider source clauses covered by learned binary consequences

Updated 2026-11-24. This follows [shared local contexts](guard-context-reuse.md).
The experiment adds a bounded recognizer and a native proof compiler. The live
search policy is unchanged.

## What is certified

Let F be the actual local CNF. Each selected binary edge is either a clause of F
or a checked consequence whose unit-refutation support consists of actual clauses
of F. A path from literal l to its negation proves F implies not-l. If this holds
for every literal of an actual clause C in F, then F is unsatisfiable, even when
the binary consequence graph itself is satisfiable. This is an elementary
consequence argument; no novelty or unrestricted tractability claim is made.

The compiler checks the source clause, all selected edge transitions and all
selected guard supports before publishing a node. For each literal of C, it
refutes the true branch under the preceding false assignments. The last branch
falsifies C itself. Each implication path similarly splits on its next literal,
using the checked support to refute the excluded branch. Supports and paths may
share variables. Their independence is not assumed. Changed contexts are
restricted and canonicalized again; absent variables require identical child
keys. Synthetic graph indices never become native source-clause indices.

All published certificates use the existing empty, unit and split rules. The
new code is experimental Python, checked by the existing native readers, with
no new Lean refinement. The earlier 64 manuscript proof blocks remain unchanged.

## Discovery and accounting

The census observes satisfiable graphs already produced by the existing guard
gate. Its model screens out source clauses already satisfied by that model and
clauses with variables absent from the graph. A genuinely covered clause could
pass both filters, since every graph model must falsify each of its literals.
The remaining clauses are tested by breadth-first searches from each literal to
its negation. Completed searches share paths or established unreachability
within that graph call. Stopped searches never become cached negative results.

Bounds are width 8, eight distinct BFS roots, 4,096 visited edges and path length
256 per graph call. Graph construction, model validation, source scanning and
recording the diagnostic events are additional costs. In a word-operation model,
with S source literal occurrences and g graph clauses, the traversal work is
O(S + g + E), where E is the number of visited edges across the bounded searches;
root and path bookkeeping is also charged. Working structures include graph
adjacency, a BFS predecessor map and retained paths. Full diagnostic event
retention adds the local CNF, graph, model and coordinate binding for every call;
it is not part of a proposed low-memory live policy.

For a supplied valid cover of width w with path lengths p_i, the compiler creates
O(w + sum p_i) native nodes, before exact-key reuse. Each node may carry a full
conditioned source and full child keys. Small graph witnesses therefore need not
produce small proof archives. Source preparation, template checks, restriction,
canonicalization, native verification, database accounting and persistence remain
charged. Nothing here bounds acquisition of useful templates for arbitrary CNFs.

The read-only observer retains the existing native search and verifies exact
archive equality with the frozen context control. It uses a scoped function hook
inside the solver's existing exclusive synchronous session. The hook is restored
on normal return and exceptions. Every candidate is independently reconstructed
from its saved local coordinate binding before support checking and compilation.

The initial timing run overlapped the full test suite. Those results remain
preserved as diagnostic data. The reported timings come from a separate serial
run after the initial run and tests finished. No tests or other experiments run
concurrently with its timed workers. Controlled examples and local follow-up
comparisons run afterwards, separately.

## Measured coverage and costs

The eight exposed queries produce 615 satisfiable graph calls across the
existing gate's 669 sites. Bounded discovery proposes 15 covers; all 15 have
valid local supports. Four repeat an exact local root, leaving 11 distinct
refutations. Nine first occur at sites where the old gate was inconclusive;
two occur at sites the old gate subsequently closes. All 11 roots are already
available in the ordinary completed query archive. Thus this extends local
recognition, but adds no final result on this workload. All eight whole queries
still stop unresolved at 256 dispatches. No cover is used during live search.

Across the eight queries, the sum of per-case mean solve times rises from
8.42563 to 8.69481 seconds with observation; complete-worker means sum to
93.66518 and 93.83854 seconds. The observed graph/discovery/event-construction
work totals 0.18786 seconds. Saved diagnostic JSON totals 12,269,105 bytes.
Native archive bytes and all existing proof/search counters remain identical.
The sum of per-case mean peak RSS rises 2.16%; this includes diagnostic retention
and is not a simultaneous peak or a general memory bound.

Discovery visits 47,629 edges from 4,714 roots and reuses 1,376 completed root
searches. The eight-root limit stops 520 calls. An adaptive offline pass relaxes
root/edge limits on the 600 bounded misses while retaining width 8 and path
length 256. It finds seven additional proposals in 0.19358 seconds, with 100,936
edge visits. Those extra proposals are neither support-checked nor compiled in
this checkpoint; they are explicit next-run candidates, not certified coverage.

The follow-up compares each of the 11 distinct supported local CNFs from empty
stores, alternating order. Ordinary search resolves all of them within its
256-dispatch cap. Cover compilation has no fresh SAT-search phase, but produces
more proof work and state:

| Total across 11 local contexts | Ordinary search | Cover compilation |
| --- | ---: | ---: |
| Solve/compile seconds | 0.17208 | 0.52823 |
| Stored authority records | 77 | 185 |
| Record bytes, keys and payloads | 745,772 | 2,098,251 |

Independent source binding and hint transport add 0.08092 seconds to the cover
side, before earlier origin acquisition and census costs. Only edit 28/event 23
has a lower compilation-only time, and adding its support checks reverses that
small saving. Full-context compilation is about 3.07 times slower in aggregate
before support checking and retains 2.81 times the record bytes. These are short
local diagnostics, not statistically established production ratios.

The controlled gadget family covers widths 3, 4, 6 and 8, with identity and
signed-permuted names and two alternating repetitions. Summed fresh solving
costs 0.03238 seconds versus 0.10670 for cover discovery/compilation; separate
family/template/model preparation adds 0.01571 seconds. Records total 168 versus
300, with 100,144 versus 164,386 bytes. Warm calls reuse exact roots without
publishing nodes. Satisfiable edits deleting a support clause, deleting the wide
clause, or flipping one wide-clause literal remain misses and have independently
checked satisfying assignments. These supplied-template examples establish
correctness and preserve the cost regression; they are not evidence of faster
acquisition or fresh real-world performance.

## Audit correction and preservation

The first local follow-up incorrectly assumed that every ordinary result had a
native root. Edit 28/event 3 instead returns a valid binary-equivalence-v3
certificate. The failed source, protocol, log, result reproduction and completed
archives are preserved. The corrected follow-up uses the existing full
six-table audit with both snapshot readers, checks the declared result
authority, and counts extension records as well as native records. No solver
rule or proof checker was weakened. The failed attempt is additional work
outside the final local comparison.

All 1,807 solver tests and 37 focused tests pass. The full suite retains the 43
existing SQLite ResourceWarnings; the focused run has none. Tests include
signed renamings, overlapping learned paths under stronger prefixes, all subsets
of a six-edge three-variable graph with signed wide clauses, malformed evidence,
missing supports, bounds, scoped-hook cleanup, truth tables and cold replay.

The preservation audit retains 171 prior manifests and 16,500 artifact entries.
The new checkpoint references 38 distinct, independently audited supplemental
archives. These preserve all new controlled and local proof results, including
ordinary alternative authorities. They are not automatically loaded into live
search or used as a causal prefix. The cumulative 160,338-record native bank,
its five other authority tables, layered reader and full-snapshot control are
unchanged. Resume `experiments/results/cnf-guard-covers/checkpoint.json`.

## Next gap

Keep this recognizer offline until its total cost improves. The immediate
composition target is the union of the selected path supports and the actual
wide clause, followed by a native negative-subset lift. Reuse that checked
support across contexts instead of storing full enclosing CNFs at every split.
The measured 2.10 MB versus 0.75 MB and 0.528 versus 0.172 seconds justify this
specific cost target; a smaller support is not itself proof of a speedup.

For broader discovery, first check the seven additional proposals against their
actual local sources and whether ordinary search already retains their roots.
Then inspect partial exclusions: a checked forced literal can shorten a wider
source clause without covering it completely, potentially exposing new binary
interactions. Recognize and compose that process exactly, reuse shared supports,
and charge reaching a fixed point. Use unresolved cases and fresh mixtures, not
only the 11 local roots already found by ordinary search. Useful automatic
origins, efficient complete SAT coverage and uniform expansion bounds remain
open.
