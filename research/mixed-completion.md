# Mixed two-CNF models from live conditioned residuals

The optional mixed-completion policy extends
[inline completion](inline-completion.md). After unit propagation, uniform
completion keeps priority. During the same residual sign scan, the selector
also records whether every clause has width at most two. Only a failed uniform
completion with a binary residual invokes the existing SCC solver. No family
labels, extra assumptions, changed ranking or expanded candidate cap enter
selection.

## Correctness and reuse

The SCC solver operates on the live residual with its existing variable IDs.
For a positive result, the selector verifies that the assignment contains
exactly the residual variables with Boolean values and does not overlap the
forced prefix. It combines the assignments, transports through the premise
and target name maps, and verifies every clause of the raw target plus the
assumption. Ordinary native model publication independently checks the target.
A checked model of F together with an assumption is a sufficient witness for F.
This route requires neither further branching nor another propagation pass.

The baseline assignment, canonical binding, residual and completed candidate
prefix are reused directly. The first checked positive witness stops discovery.
No binding, restriction or unit trace is reconstructed for completion. SCC
results are produced from that residual, not fetched from an unverified family
label. The source model check is the correctness boundary. Independent
posthoc validation decides each retained binary condition by graph reachability
without invoking the SCC implementation, then checks the supplied model or
both contradictory implication paths.

A negative result is evidence only about that condition. Its implication paths
and source-bound propagation screen remain in the diagnostic record, and
probing continues. The selector neither publishes a parent refutation nor
marks a negative condition as a discovered unit conflict. Recomposition with
other conditions or an existing parent certificate is still required. Tests
include a satisfiable parent whose first condition is unsatisfiable, malformed
models and paths, noncontiguous variables, forced prefixes, coordinate changes,
zero native search budget and cold persisted reuse.

The remaining residual cell still contains general SAT. After unit closure,
let G be a fixed unit-free unsatisfiable formula if a conflict was detected,
or the consistent unit-closed residual otherwise. In either case conjoin fresh clauses (a OR b), (NOT a OR NOT b), and
(c OR d OR e). The fresh constraints are satisfiable, so the conjunction is
satisfiable exactly when G is. It rejects both uniform assignments and contains
a ternary clause. The construction is polynomial and unit-free. Thus failure
of the uniform and binary recognizers is still an unresolved general-SAT cell;
it is not a new tractable class. This argument concerns residual classification,
not guaranteed access to a particular residual under the bounded probe policy.

## Incremental resource bound

For each visited nonconflicting residual, width recognition adds one clause
length comparison to the existing sign scan. For a selected binary residual
with n_i variables and L_i literal occurrences, graph construction, the two
SCC traversals and optional extraction of two contradiction paths take
O(n_i+L_i) operations after variable ordering. The existing implementation sorts
its distinct variable IDs, adding O(n_i log n_i) comparison work. Temporary
graph and assignment storage is O(n_i+L_i) words. Integer widths and dictionary
costs remain explicit assumptions; the bound is not simply a linear bit-time
claim for this Python implementation.

Across k binary attempts, sum those costs. A first accepted mixed model adds
O(n+L) transport and full source verification; native publication, original
propagation and canonicalization, serialization, retained state and cold replay
remain separately charged. Negative attempts may repeat SCC work and retain
up to O(n_i+L_i) proof data each. These costs can outweigh saved acquisition.
Direct model publication also omits intermediate native subproblem nodes that
a search route would have stored, so later reuse cannot be inferred solely
from the current-query saving. The preservation union retains earlier and
comparator payloads; it is not a minimal live-policy archive.

## Evaluation design

Twenty-five exact-prefix contexts include the seventeen previous controls,
four mixed-model opportunities and four negative SCC controls from the prior
inline stream. Positive case 51 repeats in reverse policy order (52 arms).
The four positive controls formerly acquired 14 native nodes / 6,163 bytes.
The four negative controls formerly acquired 54 parent nodes / 75,511 bytes;
one negative condition cannot replace those parent certificates.

An eight-query preflight worker checks warm and full inherited cold replay.
A separate sixty-query stream excludes all inherited query roots and compares
native baseline, inline uniform completion and mixed completion in two opposite
serial orders. Family labels are never selector inputs. Preparation,
recognition, graph solving, source/native checks, persistence and full cold
replay remain in the measured workers. Tests, truth enumeration, builds and
attribution run outside production timing. Eight new tests include 512 small
gated-source/coordinate comparisons with independent truth enumeration.


## Measured acquisition and complete cost

All four motivating positive controls publish one model each: **14 -> 4 native
nodes**, **6,163 -> 2,357 bytes**. Positive case 51 retains the saving in both
orders. The other 21 saved contexts keep their native certificates, including
the four negative-condition contexts. Diagnostic evidence can grow even when
native certificates stay unchanged.

The new sixty-query stream returns 44 SAT / 16 UNSAT in every mode. All 48
family targets are unfamiliar after preparation; twelve neighbours become
known. Two fresh graph cases, 27 and 51, add checked mixed completions. Together
with thirteen uniform completions, the mixed policy publishes fifteen models.

| Cost across sixty queries | Native baseline | Inline uniform | Mixed completion |
| --- | ---: | ---: | ---: |
| New native nodes | 412 | 385 | 381 |
| New native payload bytes | 457,467 | 437,869 | 436,179 |
| Expanded nodes | 401 | 361 | 355 |
| Premise probes | 0 | 102 | 89 |
| Discovery/acquisition propagation visits | 62,149 | 96,413 | 94,004 |
| Mean query seconds | 0.35474 | 0.37242 | 0.35566 |
| Mean complete worker seconds | 24.11848 | 24.06008 | 23.88454 |
| Mean full cold replay seconds | 11.86784 | 11.78719 | 11.66327 |

The extension checks width across 3,101 residual clauses, makes fourteen SCC
calls, constructs 784 implication edges and retains twelve negative conditions.
Its two accepted mixed models contain 24 variables and are checked against
122 raw premise literals. Graph discovery falls 25,401 -> 23,449 propagation
visits, and graph acquisition 11,186 -> 10,729. Random three-CNF and coupled
parity stay at **272 acquisition nodes / 43,685 propagation visits** and receive
no assumption probes through the binary filter. Their broader coverage remains
unresolved.

Query differences are -0.03097/-0.00254 seconds, and complete-worker differences
-0.12069/-0.23039 seconds. The mean query reduction is about 4.50%. Cold replay
also drops about 0.124 seconds on average, accounting for much of the complete
worker difference; the two runs do not isolate that variation as an SCC benefit
or establish general scaling. Native baseline has almost the same query time
as mixed completion and substantially fewer propagation visits.

Diagnostic sidecars increase **1.18%**, from 1,780,852/1,780,821 to
1,801,856/1,801,866 bytes. Trial database size stays 79,302,656 bytes, compressed
size changes 5,884,124 -> 5,884,044 bytes, and mean process RSS rises about
1.91 MB (759.431 -> 761.340 MB). Thus a 1,690-byte native acquisition saving
coexists with larger diagnostics and process memory. Preserve this tradeoff
and the failed SCC attempts; neither native nor total memory improves uniformly.

## Next target: compose retained negative conditions

Fresh case 59 retains refutations under literals -141, 47 and 72, which cover
an existing source clause [-141, 47, 72]. This gives a sound parent-level
argument: every model of F must satisfy one literal of the clause, while each
corresponding F-and-literal condition is unsatisfiable. Unlike a single negative
condition, the full clause cover is exhaustive. Current acquisition still uses
twelve nodes for this parent. The posthoc record preserves the clause and
references to all source-bound refutations. Native publication, an independent
parent checker, persistence and timed resource accounting for that composition
remain to be implemented. The same posthoc audit finds covers in saved mixed-controls 43 and 47.
Across these two controls and fresh case 59, current parent acquisition totals
36 nodes / 50,554 bytes. These are costs to compare against a fully charged
combined certificate, not an already achieved saving. Other negative cases
without such a cover remain explicit misses. This is a concrete next candidate, not a measured acquisition
saving in the present policy.

The fourteen fresh SCC attempts contain no repeated exact ordered residuals
within a query. Simple exact memoization therefore offers no measured saving
on this sample; this does not exclude symmetry or cross-query reuse.

Also investigate positive discovery outside the binary filter and future reuse
of intermediate components omitted by direct model publication. General SAT
remains in the unresolved residual cell. The 257-formula finite embedding audit
supports the explicit reduction above, with no arbitrary-CNF tractability claim.

Evidence and reproduction:
[`experiments/results/cnf-mixed-completion/`](../experiments/results/cnf-mixed-completion/).

## Preserved checkpoint

All **1,145 tests**, 25 focused tests, 292 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-mixed-completion/checkpoint.json`:
**25,334 native keys**, preserving all 24,922 earlier payloads, with 232 new
composed records alongside 4,013 inherited records, 2,957 ordinary decisions
and six projections. The union uses 79,339,520 database bytes / 5,889,616
compressed bytes. Four roots have alternate certificates in eight retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no new activation is attributed to this policy. Original structural
coverage remains 17/24, supplemental positive coverage 24/24. All 524 prior
sources, 6,228 artifacts and 98 manifests remain unchanged. The manuscript
builds at 214 pages with all 64 existing proof blocks unchanged. The finite
embedding audit checks 257 formulas (255 SAT / two UNSAT).
