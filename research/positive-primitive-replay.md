# Check the selected derivation without replaying its search history

The hybrid positive checker verifies the existing 2,748-step graph for the same
58 covered roots among 83 reused development inputs. Mean cold replay falls
from **30.15238 to 2.71821 seconds (90.99%)** in two matched repetitions with
reversed order. This is a reduction in positive proof replay, not a new SAT
decision, broader structural coverage or a complete expansion benchmark.

## What is sufficient for the positive claim

`experiments/cnf_positive_primitives.py` reads a row without admitting it to the
historical validator's cache. It first verifies the exact normalized CNF,
configuration and depth. It then checks the selected rule's semantic premises.
The ordered proof must establish every child before its parent. The selected
rule need not be the cheapest rule or the one preferred by the old search policy.

| Rule | Required positive evidence |
|---|---|
| Family | Recheck a recognized syntactic family, or validate the explicit affine certificate and its pure-system/conflict conclusion |
| Components | Exact complete variable-disjoint components and every child, including repeated occurrences of a shared canonical child |
| Conditioning | Both exact restrictions of a source variable; independently replay any fused simplification and its variable transport |
| Retained plan | The identical source and depth under the designated retained configuration, with its own earlier proof |
| Elimination | Recompute all opposing resolvents with the original bounded-elimination checker and bind the entire result to the child |
| Binary paths | Source-bound implication paths using retained binary reasons for every deleted wide clause |
| Polarity | Validate the signed renaming and its Horn result |
| Simplification | Replay unit/conflict reasons and any permitted pure rounds against the complete source |
| Probe | Use the original policy-specific probe checker, retaining its original/learned antecedents, source reconstruction and selected reduction |
| Affine projection | Check extraction, every row operation, the exact coupling variables and complete boundary encoding |
| Subsumption and external routes | Keep their full original validators and historical dependencies |

The sufficiency argument is induction over the ordered graph. A terminal has a
checked decision procedure. Each selected transformation gives a checked
decision-preserving reduction to an earlier node. Conditioning covers both
values, and component conjunction covers every component with disjoint support.
An exact retained reference transfers the earlier proof of the same formula.
The external-rule validators preserve their existing contracts. Thus every
claimed root has a finite derivation into recognized leaves. A false closure bit,
an unverified failed recognizer or a ranking score is never an induction premise.
This argument does not bound the size or construction cost of such a graph for
arbitrary inputs. Python implementation refinement into Lean remains open.

The new checker directly handles **2,687 internal steps**. The five subsumption
steps and 56 external steps still use the existing validators. The implementation
does not alter those validators or put weaker positive results into either of
their `checked` maps. Discovery, archive auditing, exclusion and exhaustion
continue to require their stronger historical contracts. A deliberately malformed
losing alternative can be irrelevant to a valid selected proof while remaining
an archive-validation error; the tests demonstrate this distinction.

## Matched replay and accounting

Both modes read the same serialized graph, original sources, configuration and
all five sidecar lists. Each cold arm creates fresh verifier objects and empty
in-memory checking caches. The execution order is historical/primitive, then
primitive/historical. Operating-system caches are shared; these two repetitions
are not a confidence interval. No tests or builds ran during these measurements.

| Measure | Historical expanded checker | Hybrid primitive checker |
|---|---:|---:|
| Cold samples, seconds | 29.89761, 30.40714 | 2.71504, 2.72138 |
| Mean cold seconds | **30.15238** | **2.71821** |
| Mean warm seconds | **0.25349** | **1.88878** |
| Nodes receiving full historical validation | 11,955 | 471 |
| Their retained node JSON payload, bytes | 97,225,536 | 3,096,763 |
| Distinct inventory rows read overall | 11,955 | 2,797 |
| Historical nodes outside the explicit graph | 9,207 | 49 |

The hybrid reads all 2,748 graph rows directly, totaling **18,568,514 bytes**.
Its original validators additionally read 471 rows, including 422 graph rows and
49 other dependencies. Adding those reads gives **21,665,277 node-payload bytes**,
including duplicate reads. Both verifier policies are counted: the hybrid's
historical caches contain 463 current-policy nodes and eight retained-policy
nodes. It avoids full historical validation of 11,484 nodes; many still receive
direct semantic checks. The distinct row-read reduction is 9,158, not 11,484.

The 56 selected external routes, 25 ordinary prefixes, 26 learned prefixes and
ten learned contexts remain checked in both modes. Direct probe checking also
retains its own source-bound antecedent traces. This does not establish that all
9,207 formerly external-to-graph nodes were unnecessary under every contract.

These are logical JSON payloads and access counts, not measured peak RAM. The
expanded graph, its keys, sidecar indexes, other caches and transient decoding
still consume memory. SQLite remains byte-identical at **770,338,816 bytes /
41,758 pattern nodes**; none of the archived losing alternatives or old results
is deleted. The graph is still **777,176 compressed bytes** and still refers to
the historical inventory and external sidecars. No standalone portable proof has
yet been exported.

## The warm regression and remaining bottleneck

Warm replay is about **7.45 times slower** for the hybrid in this experiment.
Each call checks the direct transformations again and reads their rows again.
The old checker instead reuses its much larger fully validated node cache. Both
warm arms create fresh route objects, while retaining their inventory and probe
caches. The cold saving therefore does not justify replacing every warm path.
Any future positive-validation cache must be distinct from the historical cache
and bound to the exact proof, source, configuration and relevant immutable data;
a saved closure Boolean or hash alone is insufficient.

Restoring the preserved history and sidecars costs **20.91624 seconds**, now much
more than the hybrid's cold replay. The complete comparison costs **98.10909
seconds**, including restoration, four cold arms, four warm arms, accounting and
integrity checks. It is not the time for one expansion. Older discovery runners
still prepare and audit the full history; integrating the new checker has not
yet changed their costs.

The next useful integration is a sufficient selected-proof bundle plus the
actual open-frontier dependencies, so preparation need not reconstruct unrelated
history. Its missing records must never be treated as an exhausted search or a
complete discovery catalog. Preserve the existing warm path until the separate
positive-cache tradeoff is measured. The unchanged 23-variable / 93-clause leaf
remains the next coverage target, with saved pairs **5, 6, 11, 13** and ordinary
candidates **7, 9, 16, 17** under a shared admission allowance.

## Reproduction and validation

Run `python3 experiments/compare_cnf_positive_primitives.py OUTPUT_DIRECTORY`.
Results and dependency hashes are in `experiments/results/cnf-positive-primitives/`.
The run disables new recognition and external discovery, sets SQLite read-only
for every replay and verifies unchanged history bytes and logical table digests.

The new tests cover separate checking contracts, retained references, shared
component multiplicity, omitted/reordered branches, missing resolvents, false
family claims, altered bindings and source clauses, probe reasons, projection
interfaces, fused closure transport and missing external evidence. They also
enumerate all 512 two-variable clause subsets and check all 504 applicable
eliminations after normalization against exhaustive assignment semantics.
All **132 relevant tests** pass. The manuscript builds to 150 pages with no
overfull boxes or undefined references; all 64 earlier proof blocks are
byte-identical. The three preceding result manifests and the new measured
source fingerprints also pass their integrity checks.

This report is a verification study, not a discovery checkpoint. Resume discovery
from `experiments/results/cnf-reused-branch/report.json` through
`continue_cnf_reused_branch.restore_checkpoint`, preserving all five lists
**(1 rewrite, 42 learned bases, 156 augmented blocks, 11 splits, 1 affine family)**
and earlier sidecars. Coverage and the unresolved frontier remain unchanged.
