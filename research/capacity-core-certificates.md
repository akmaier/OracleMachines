# Clause-derived capacity cores

Checkpoint: 27 November 2026. An optional whole-source UNSAT gate recognizes
disjoint demands and shared capacity directly from CNF clauses. On the already
exposed external panel, it closes all five pigeonhole originals and their signed
renaming: original coverage rises **19/25 → 24/25**, and derived controls
**10/12 → 11/12**. The aggregate is 35/37, with no lost verdict. This is an
exploratory follow-up to the [external audit](external-cutset-audit.md), not a new
holdout or representative coverage estimate. The prior synthetic 182/182 union,
old source files, evidence and production defaults are unchanged.

Mean measured complete cost falls **35.06016 → 25.69409 seconds (26.71%)** in a
new matched comparison against the unchanged expanded external pipeline. All four
paired signs favor the gate. Unknown inputs remain unanswered; this is neither
total time to solve every input nor a comparison against fresh CDCL solving.

## Recognition and proof authority

Let selected source clauses be demands D₁,…,D_d with pairwise disjoint **literal**
sets. Variable sets need not be disjoint: x and ¬x are different literals.
Partition their union into nonempty groups G₁,…,G_g. For every pair a,b in a
group, require either a=¬b or the exact source clause (¬a ∨ ¬b). Each demand
requires at least one true literal, and disjointness makes these d distinct true
literals. Each group permits at most one. Thus **d > g proves UNSAT**.

The certificate stores demands and groups. The checker reconstructs the current
source clause set, checks every demand's containment, literal disjointness, the
exact group partition, every exclusion pair, and strict deficiency. It does not
invoke matching or discovery. Hashes, filenames, publisher labels and proposed
group names supply no logical authority. Duplicate clauses/literals and
tautologies are normalized; invalid literals are rejected. An explicit empty
clause has one empty demand and zero groups.

This is a refuting subset, not an exact factorization of the whole source. Adding
unrelated or interacting constraints preserves the core. Reusing it after an edit
requires fresh support checks against the current source; a deleted required
clause invalidates the proof. No source-equality shortcut or trusted persisted
index is introduced. Signed renamings are rediscovered from their clauses; the
prototype does not discover general isomorphisms between stored cores.

Discovery tries two fixed selections: greedily choose literal-disjoint clauses
of width at least three, then greedily choose from all nonempty clauses. Each
selection orders clauses by decreasing width and then literal tuple. Binary
exclusions and complementary literals define the conflict graph. A deterministic
degree-ordered greedy clique partition supplies candidate capacity groups.
Augmenting paths match demands to incident groups; a failed augmentation exposes
an alternating reachable subset with too few neighboring groups. Only that
subset and its intersected groups enter the independently checked certificate.
It can find local deficiency even if unrelated groups provide spare global
capacity. A matching itself supplies no SAT verdict: other clauses and conflicts
across groups may still prevent a model.

The shared 300,000-probe search allowance applies across both selections.
Exhaustion is unresolved, not an obstruction theorem. Input scans, sorting,
adjacency construction, certificate validation and storage are additional work,
all charged by the benchmark. Checking requires all source support and a pair
test for each pair within a group; compact output does not eliminate that work.
The selection and clique partition are incomplete heuristics, not efficient
recognition of every possible capacity core or a general SAT classification.

## Coverage, overlaps and remaining interaction

The gate sees only CNF clauses and runs before the old expanded pipeline. A
checked core proves the original formula UNSAT without visiting its old frontier;
otherwise the unchanged pipeline runs. All 31 non-hit proof payloads are exactly
equal to the matching baseline payloads. All baseline payloads also equal the
prior external checkpoint's certificates. The six gate hits previously had no
verdict, so there is no certified-result overlap on this panel. Logical overlap
with other recognizers is possible; gate-first dispatch is merely an operational
partition into certified capacity cores and an unrestricted remainder.

The five new original certificates have demand/capacity counts 7/6, 8/7, 9/8,
10/9 and 11/10. The signed `hole10` control has 11/10. Their six serialized
wrapper proofs total **14,120 bytes** and require **2,115 exclusion pair checks**
per complete verification pass. Source scanning and parser costs are additional.
All six are independently checked after JSON reload.

Only `uf50-01000.cnf` remains unresolved among the 25 originals. The edited
`hole10` control also remains unresolved; it must not inherit the original's
UNSAT certificate or truth label. The full source, old incomplete certificates,
gate diagnostics and remaining interactions are retained in `remaining.json`.
The measured panel performs 360,694 gate search probes in total; this is a sum
across 37 inputs, not a per-input limit or count of all primitive operations.

## Matched full-workflow costs

Four paired process orders alternate gate/baseline ordering. Each run includes
initial raw-input parsing, discovery and internal checking, explicit verification,
proof writes, compression, warm reload and two cold verification passes. Every
replay reparses the source and loads its JSON. Verified-operator banks start empty
per phase; operating-system caches are not flushed. Startup, final metadata and
independent audits remain extra. There is no fallback solver.

| Metric | Expanded baseline | Capacity gate |
| --- | ---: | ---: |
| Complete seconds | 35.06016 | 25.69409 |
| Acquisition/internal checks | 15.76543 | 12.11574 |
| Explicit checks | 3.97096 | 2.57986 |
| Warm replay | 4.96090 | 3.53669 |
| Two cold passes | 9.90301 | 7.10375 |
| JSON proof bytes | 33,896,356 | 26,263,102 |
| Compressed proof bytes | 562,876 | 445,179 |
| Maximum process RSS bytes | 143,294,464 | 121,421,824 |

Paired complete-cost reductions are **26.08%, 27.16%, 26.64% and 26.96%**.
Both arms use the same wrapper serialization; its indentation changes absolute
JSON byte counts from the earlier adapter-only experiment. These are observed
process costs, not unrestricted runtime or memory bounds. The improvement comes
from replacing expensive unsuccessful expansion on six inputs with short checked
cores, while charging recognition on every input. No default changes follow from
this exposed convenience sample alone.

## Validation and retained counterexamples

The independent explicit truth-table audit covers **5,462 inputs**: all 512
two-variable CNFs, all 3,304 three-variable CNFs with at most three distinct
normalized clauses, all 64 and 512 domain restrictions for three demands with
two and three resources, 1,000 random small CNFs, 22 deletions and 48 signed,
edited or mixed controls. All **1,260 emitted refutations** are correct. Cold
checks disable discovery; a second run exactly reproduces the semantic records.

Each single-clause deletion from the 4-demand/3-resource core is SAT by direct
truth table and invalidates the old certificate. Added constraints permit four
checked core reuses. The mixed cases include shared variables, disconnected
components, sign changes, deleted demands and sparse signed renamings.

The audit also preserves failure: discovery misses **30 UNSAT domain-restriction
inputs** (six of 64 in the two-resource set and 24 UNSAT inputs in the
three-resource set), and **two of sixteen UNSAT mixtures**. All exact missed
sources are saved in `gap-diagnostics.json`. These are misses of the capacity gate alone;
the existing pipeline may still decide them. Certified soundness does not imply
complete discovery, even within these small encodings. Greedy demand selection
can be disrupted by overlapping clauses or edits; renaming invariance is not
proved in general.

All **2,467 full and 20 focused tests pass**. The focused checks include malformed
proofs, missing support, duplicate/overlapping demands, broken partitions,
non-strict deficiency, complementary literals, local deficiency with spare
global capacity, budget stops, cold replay and unchanged fallback. Existing
unclosed-SQLite warnings remain recorded. The validator rechecks all eight saved
runs, regenerates proofs/counters, replays warm/cold schedules and preserves all
241 preceding manifests, 80,996 artifact entries and 1,316 scientific sources.
The manuscript adds one elementary counting proof while preserving its earlier
82 proof blocks.
A metadata finalizer initially exceeded Python's import-recursion limit through
the long historical comparison chain. Its failed source and reproduced traceback
are retained; the finalizer now uses direct standard-library JSON/hash helpers.
The dependent seal first stopped on the missing decision file. Timed algorithms,
certificates, tests and measured results were unchanged by this metadata fix.

## Next priorities

1. Inspect the remaining random 3-CNF's coupled interaction and the edited
   capacity instance. The latter is outside this certified refuting core; no
   claim about its truth follows from failure to recognize it. Test whether a
   checked assignment can be reconstructed from useful choice structure, with
   every original clause verified before granting SAT authority.
2. Improve bounded demand selection or reuse a known core through edits, using
   the thirty domain and two mixed counterexamples. Selecting smaller or better
   overlapping demand sets must preserve literal disjointness, or introduce a
   separately proved weighted argument. Exact rechecking remains mandatory.
3. Freeze new unseen encodings before evaluating broader transfer. Auxiliary
   encodings, non-clique exclusions, heterogeneous constraints and arbitrary
   compact core discovery remain open. Validated source/context reuse and direct
   single-clause width reasoning remain supporting cost targets.

Resume `experiments/results/cnf-capacity-core/checkpoint.json`, key
`capacity_core`. This result establishes a restricted certified pattern and its
measured benefit, not a polynomial algorithm for arbitrary SAT or a disjoint
tractable partition covering all CNFs.
