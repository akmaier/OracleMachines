# Exact separator messages for cyclic signed choices

The preceding conditioned-forest rule leaves five fully represented nonclique
external cases outside its structural class. Each retains many cycles after two
vertex removals. This experiment keeps cycles within elimination bags and checks
complete relations at their interfaces. It is an optional experimental route;
older witnesses, capacity proofs and production defaults remain intact.

## Exact source obligations and recomposition

The source grammar is unchanged: variable-disjoint nonempty signed demand clauses,
plus binary exclusions of their choices. Every normalized clause must be classified.
Tautology-only variables remain in raw-source model checking. A satisfying model
can be reduced to one representative per demand because the remaining constraints
are exclusions. This is an existence equivalence, not equality of Boolean model
sets. Arbitrary additional positive constraints cannot inherit that normalization.

Discovery proposes a deterministic minimum-fill elimination order (missing neighbor
pairs, degree, then demand index). The checker validates a complete permutation,
rebuilds bags from the original graph, fills later neighbors, and assigns each
message to its earliest remaining separator vertex. This construction gives edge
coverage and running intersection; child-scope containment is also checked directly.
The heuristic need not find a minimum-width order.

A message contains precisely those separator assignments with an extending value
for its eliminated demand that satisfies original exclusions to later demands
and every incoming message. Existential elimination preserves the active factor
conjunction. An empty checked message therefore proves UNSAT even before all
vertices are eliminated. Nonempty incomplete prefixes remain unknown. Complete
nonempty messages permit reverse reconstruction, followed by checking every raw
source clause and the full Boolean variable support. Tables are canonical and
must include every live tuple and omit every dead tuple. A reordered, missing,
duplicated, foreign or fabricated row cannot silently change the relation.

The checker uses the supplied order but does not call the order heuristic or the
table constructor. It rebuilds source obligations and enumerates separator tuples
again. In particular, **small stored relations do not imply cheap verification**:
omitted tuples must be checked too. For a bag eliminating v with separator S,
the candidate assignment bound is |D_v| times the product of |D_j| for j in S.
The bound is exponential in unrestricted separator size. Source parsing, graph
preparation, lookup work and raw-model checking remain additional obligations.

## Freeze, controls and resource limits

The four scientific files and protocol are frozen before generating sixteen
signed sparse controls: ladders, triangle strips, mixed-domain ladders and
ternary edits at 8/16/24/32 demands. All 78 previous inputs remain, explicitly
labelled as exposed, for 94 total. Neither route receives labels or metadata;
all inputs and outcomes are kept. These are designed tests, not a representative
SAT survey.

A graph-only pre-freeze pilot on the five exposed descriptions found separators
of size 6–9, largest bags of 2,187–59,049 assignments, and full plans of
15,042–141,654 assignments. We deliberately choose limits admitting those exposed
plans: 200,000 total reserved bag assignments, 65,536 per bag, and 1,000,000
ordering pair tests. This is disclosed calibration, not a fresh external holdout.
Only complete messages fit within the construction budget; partial messages are
never certified. Caps do not bound all preparation, verification, transient
memory, storage or cumulative work.

The preceding cutset route and the new separator route each run in two fresh
processes in opposite orders, with no fallback. Four further fresh processes
read, hash, decompress and check stored artifacts with constructors disabled.
OS caches are not flushed. Discovery includes the producer's internal check;
further checking, JSON/gzip/write costs, RSS and process startup are recorded
separately. Old acquisition, panel preparation and independent audits are extra.

| Stratum | Cutset ≤2 SAT / UNSAT / unknown | Separator SAT / UNSAT / unknown | Shared / separator-only / neither |
|---|---:|---:|---:|
| Old external panel (37) | 0 / 0 / 37 | 5 / 0 / 32 | 0 / 5 / 32 |
| Nonclique path (1) | 1 / 0 / 0 | 1 / 0 / 0 | 1 / 0 / 0 |
| Exposed controls (40) | 19 / 13 / 8 | 19 / 17 / 4 | 32 / 4 / 4 |
| Fresh controls (16) | 3 / 0 / 13 | 12 / 0 / 4 | 3 / 9 / 4 |

No case is cutset-only in this panel. This does not imply dominance under all
possible limits or descriptions. The five old external cases are e012–e015
(four original flat30 sources) and e031 (a signed permutation). The old panel
contains 25 originals plus 12 derived controls, not 37 independent originals.
Earlier models for these five remain preserved; the gain is an exact explanation
of their cyclic compatibility. The new route adds four K5 UNSAT results to the
exposed control panel. Fresh coverage is twelve SAT cases; the four ternary
edits stay unrecognized.

| Case | Maximum separator size | Largest bag assignments | Full reserved assignments | Retained relation rows |
|---|---:|---:|---:|---:|
| e012 | 8 | 19,683 | 70,140 | 5,794 |
| e013 | 7 | 6,561 | 38,640 | 3,211 |
| e014 | 9 | 59,049 | 141,654 | 10,255 |
| e015 | 6 | 2,187 | 15,042 | 2,704 |
| e031 | 8 | 19,683 | 85,206 | 5,845 |

All five complete 30 messages. Their full plans satisfy the frozen limits.
Of the 32 unresolved external cases, 26 fail source classification and six reach
the per-bag limit. Their prior portfolio certificates are not revoked. The eight
unrecognized constructed inputs are the four old and four fresh ternary edits.
These are failures of the proposed source descriptions, not exhausted separator
searches or a proof excluding every alternative description.

Mean cost over the complete 94-input panel, with two opposite-order samples:

| Route | Discovery (s) | Extra checking (s) | Encoding + gzip + write (s) | Process wall (s) | Cold worker / process (s) | JSON / gzip bytes | Construction / replay peak RSS (bytes) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Cutset ≤2 | 0.12029 | 0.01264 | 0.00922 | 0.23418 | 0.02011 / 0.09876 | 45,520 / 13,179 | 41,402,368 / 40,878,080 |
| Separator | 1.56959 | 0.76843 | 0.07359 | 2.50316 | 0.79480 / 0.87459 | 753,180 / 111,578 | 46,612,480 / 44,859,392 |

The new route solves 54/94 versus 36/94, including eighteen additional checked
answers, and costs more. This is a coverage/cost comparison, not a speedup claim.
Storage includes unknown markers and incomplete exact prefixes, which supply no
SAT answer. Complete structural replay is different from checking only the final
SAT model. Timings include source classification and checking; they exclude old
portfolio acquisition and independent audits.


## Remaining gaps and next step

This result does not replace the old portfolio or improve its historical union:
the five external SAT models were already known through other routes. It explains
their global compatibility with an exact structural decomposition. Checking that
complete structure costs more than checking an already available SAT witness.
The old matching proposal can still supply a model outside this exact grammar.

Unclassified source clauses and excessive table width are separate failure modes.
Clique-capacity inputs should retain their specialized proofs rather than be
forced through enormous explicit tables. Next: test source-bound separator tables
for clauses outside the signed-choice grammar, preserving full Boolean semantics
and recording the resulting width. Higher-arity exclusions preserve the present
representative normalization; arbitrary positive interactions require a separate
proof or full Boolean domains. Alternate descriptions and orderings, useful
cross-edit message reuse, preprocessing and efficient unrestricted SAT remain open.
No bound on arbitrary-CNF treewidth or a uniform polynomial SAT algorithm follows.

## Validation and reproduction

Sixteen focused tests cover cyclic cliques beyond two-cut forests, SAT cycles,
disconnected inputs, early empty-message refutations, incomplete positive prefixes,
changed clauses, signed sparse inputs, malformed orders/tables, all caps and
constructor-disabled replay. Independent semantic audits reproduce 3,880 small
CNFs, 24,576 exact message projections and 32,768 prefix verdicts across all
4,096 cross-conflict subsets of three binary demands, with internal exclusions
and two reversed orders. Every message is compared with brute-force existential
projection of its raw constraints, not merely with the constructor's output.

All **2,739 full and 16 focused tests pass** (full suite: 281.514 seconds).
Existing unclosed-SQLite ResourceWarnings remain in the saved log. All paired
proofs, outcomes and counters reproduce, and the preceding route exactly repeats
its earlier counters and outcomes on the original 78 cases. Four cold replays
have constructors disabled. Validation checks **257 prior manifests and
85,720 artifact entries**, preserving all **1,392 previous scientific sources**.
Four frozen scientific files bring the ledger to 1,396. All **94 earlier proof
blocks** and **3 publication snapshots** remain unchanged; the manuscript adds one
elimination-message proposition/proof (95 total).


Resume `experiments/results/cnf-choice-separator/checkpoint.json`, key
`choice_separator`. From the repository root:

```sh
python3 -m unittest solver.test_cnf_choice_separator
python3 -m unittest discover -s solver
python3 experiments/validate_cnf_choice_separator.py semantic experiments/results/cnf-choice-separator semantic-audit-reproduced.json
python3 experiments/validate_cnf_choice_separator.py validate experiments/results/cnf-choice-separator
```

Use a new output directory for a new freeze/panel/measurement run. Existing
certificates, counterexamples and publication snapshots remain preserved.
