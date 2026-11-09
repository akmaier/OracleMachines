# Parent-scoped learned hints and original-source residual cores

9 November 2026. This experiment separates the CNF used for child recognition
from the redundant clauses used in a checked parent continuation. It closes the
previous representation-sensitive loss without losing the selected-policy gain.
The favorable pilot timing and memory results do **not** extend to the full run.
The policy remains an optional research inventory; the decision solver is unchanged.

## Rule and exactness

`CoreLearningInventory` uses the same original probes, bounded selected batch,
baseline continuation choices, priorities and caps as `FixedOrderLearningInventory`.
Every implication and continuation is independently checked first. A successful
forced/common reduction restricts the original parent CNF by its checked
assignment. A signed equivalence substitutes its checked mapping into the
original clauses. A checked terminal conflict remains false. Successful children
must strictly reduce source support. Failed learning retains its proof and the
existing planner; no inconclusive probe is treated as SAT or as an exclusion.

The parent retains all hints and proof dependencies. They support its local
propagation but are not inherited by its child. Descendants rediscover hints.
Thus the same normalized core at the same depth and policy can share a plan
without an unrecorded hint context. Full source/edge checks and model lifting
remain necessary; edits or changed assignments invalidate stale parent evidence.
All existing overlapping recognition outcomes and exact AND/OR decompositions
remain available. Unresolved leaves still require the complete checked fallback.

Entailed clauses do not change the source model relation under any fixed partial
assignment. The two new Lean lemmas state this restriction identity and equality
of two independently justified hint views. Existing assignment, substitution and
refutation arguments cover the reductions. These are semantic results, not a
refinement of Python, its keys, serialization or complexity. Neither arbitrary
semantic equivalence testing nor a compact complete SAT classification follows.

## Matched full comparison

The corpus preserves all 1,281 previous inputs and adds 24 fresh random 3-CNFs
(eight each at 20, 32 and 48 variables) plus twelve growing/signed/edited controls.
Seed: **20261109064122**. The controls rotate forced, common and equivalence
fixtures through 1/2/4/8 blocks. Discovery receives CNF input, never generator
labels. There are **1,317** inputs, including 512 exhaustive two-variable cases
and **805 non-tiny inputs**. Depth/probe/learn caps remain 2/4/4.

| Mode | Non-tiny closed / 805 | Total seconds | Discovery seconds | SQLite bytes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solver | -- | 23.36801 | -- | 88,039,424 | 5.13926 |
| First four clauses | 718 | 94.86962 | 70.87369 | 284,110,848 | 40.28060 |
| Selected clauses, old choices | 718 | 97.40244 | 72.76849 | 284,299,264 | 41.15963 |
| Parent-scoped hints, core child | 719 | 97.83486 | 73.16855 | 284,094,464 | 40.38357 |

Core gains **1024** over baseline and recovers **956** relative to fixed order,
with no lost source closures against either. Source **1189** remains unresolved.
On the original non-tiny inputs, closure is 692/769 for baseline/fixed and
693/769 for core. All policies close **14/24** fresh random cases and all twelve
new controls. Core leaves **86 sources** structurally unresolved. Every original
SAT/UNSAT decision agrees with the independent solver, which stores **15,069
residuals** per mode. Structural closure and SAT decisions are distinct metrics.

Core total time is **3.13% above baseline** and **0.44% above fixed order** in
these single sequential samples. No general speed or significance claim follows.
Physical SQLite bytes decrease slightly from fixed order, but policy-tag length,
keys and page allocation contribute; this is not a measured general compression
result. The six-case Python peak is **20,021,661 / 20,127,082 / 20,265,076 bytes**
for baseline/fixed/core. It excludes native SQLite memory, RSS and full-corpus peak.
The [three-source pilot](../cnf-learning-core-pilot/README.md) is preserved as a
selected-case result, not substituted for this full comparison.

| Retained/work measure | Baseline | Fixed order | Core |
| --- | ---: | ---: | ---: |
| Pattern nodes | 17,778 | 17,858 | 17,833 |
| Logical node bytes | 113,403,053 | 113,635,007 | 113,536,866 |
| Probe-node logical bytes | 71,872,797 | 72,446,169 | 72,386,084 |
| Original logical probe attempts | 100,000 | 101,038 | 101,469 |
| Successful learned parents | 380 | 425 | 449 |
| Selected unresolved literal occurrences | 21,927 | 21,536 | 21,686 |

The implementation still constructs and checks the augmented reduction first.
Core reconstruction adds expected O(L+q+v) time and O(L+v) temporary space for
source literals L, learned binary clauses q and variables v. All normalizations,
full keys, source proofs, discovery, failed alternatives and persistence remain
charged. Across acquisition/checking there are **1,347 core reconstructions**,
omitting **3,156 clause / 6,312 literal occurrences** from child representations.
These are repeated-operation counts, not unique clauses or memory saved.
Hints remain stored at their parent, and no lifetime core-count bound is proved.

## Controlled mechanism and next gap

`mechanisms.json` preserves both previous parent controls, full selected paths
for 956/1024/1189, all actual gains/losses and every selected unresolved leaf.
On 956's saved parent, all three policies force only `14=false`. Baseline's
57-clause augmented child closes; fixed order's 58-clause augmented child stays
open; the identical **54-clause original restriction** closes under core policy.
The different batches are checked as entailed. A regression test acquires that
same core from both independently checked views and confirms an exact reuse hit.
At 1024, fixed/core both force `3=true` and close their children.

In the full core archive, **449** learned edges comprise 311 forced, 42 common
and 96 signed-equivalence reductions. **385** change normalized child syntax;
none changes the compact variable-name transport. There are 380 identical
parent-CNF/depth controls in the fixed archive, with identical parent probe
proofs. **No two learned parents in this run share a child core.** Therefore the
measured coverage gain is a descendant-discovery effect, not demonstrated large
within-run core merging. The controlled reuse test establishes the narrower
same-core opportunity.

A separate diagnostic transports each proved batch through its checked reduction,
removes tautologies and renames it into the actual child variable universe.
It finds 992 eligible hint occurrences: 85 already occur in the core and **907**
are absent. No hint in this sample mentions a variable absent from the core;
the diagnostic records that possibility explicitly. **319 absent occurrences
are learned again in the immediate child's selected batch, across 165 edges**
(127 learning-clear and 38 learned children). These are parent/child occurrences,
not unique implications or measured avoidable seconds.

The next discovery experiment should transport checked hint evidence separately
while retaining core-based recognition. Start with these 165 edges and the saved
956/1024/1189 controls. Reuse must bind the source proof, exact restriction or signed
substitution, variable transport and hint-dependent propagation context. A plan
computed under one hint set cannot be keyed solely by its core unless its behavior
is made context-independent. Test whether useful transported hints reduce fresh
probe work or expose new certified structure; charge transport/checking/storage
and retain losses. Do not assume that omitting syntax or inheriting every hint
improves bounded discovery.

The selected frontier has **124 distinct unresolved leaves**, 86 learning-clear
and 38 clear. Source **1297**, a fresh 48-variable CNF, has the largest unresolved
discovery time (**1.47150 s**, 456 selected unresolved literals). Its separate
profile takes 3.36725 s: restriction, simplification checking, propagation and
literal helpers dominate. It has only one successful learned parent, so hint
transport alone is unlikely to remove its main cost. Reusing checked propagation
state is the supporting cost target; all source/proof dependencies must remain
explicit. Probe records occupy **63.76%** of core logical node bytes. Uniform
efficient arbitrary-SAT discovery and compact total storage remain open.

## Validation, accounting and reproduction

All **366 Python tests** pass (32.601 s). New tests check all 512 two-variable
inputs and 3,304 three-variable subsets of at most three clauses at caps 0/1/4,
exact model fibers, independently expanded references, forced/common/equivalence
cores, signed mixtures, edits, disabled learning, corrupt dependencies and wrong
child bindings. A constructive opposite-output fixture checks that learned
terminal conflicts remain false. Cold coexistence preserves older policy rows.
The full Lean build/axiom audit passes at **4,125 declarations / 1,967 theorem
declarations**. This does not certify the Python implementation.

The forced/common/equivalence fixtures are samples 15/391/58 at the stated seed
(8 variables, 20 clauses, widths chosen from 2/3/3/3). A failed search for a
learned terminal-conflict fixture tested 25,000 sources at seed20261109064123
(8 variables, 30 clauses, widths 2/3/3/3/3) without finding one. The retained
constructive fixture instead joins two copies of `learning_source()` that force
opposite values of shared output 7, with other variables disjoint. Preserve this
negative search result; it is not evidence that such conflicts cannot occur.

Four full, four pilot and four preceding full archives replay byte-identically;
every pattern alternative, source binding and ordinary solver certificate is
checked. Warm reuse inserts nothing. Full warm lookup totals are
0.21444 / 0.21218 / 0.21418 s for baseline/fixed/core. Both reports record
47 matching code/test/Lean fingerprints. Reports save raw sources, failed
attempts, costs and compressed databases; the analyzer records its own hash.

Primary runs, separate Python-allocation diagnostics, cold audits and separate
profiling ran sequentially without overlapping tests, Lean builds or commits.
Operation time includes acquisition, recognition, checking, serialization,
persistence, exact solving and successful root lifts. Generation, truth tables,
summary walks, initialization, archive compression and post-run diagnostics are
excluded. Warm and cold replay are reported separately. These synthetic runs do
not establish an industrial speedup, statistical significance or polynomial
construction for arbitrary CNFs.

```sh
python3 experiments/compare_cnf_learning_core.py --output /tmp/new-core-study
python3 experiments/analyze_cnf_learning_core.py /tmp/new-core-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
```
