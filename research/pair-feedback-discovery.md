# Bounded feedback of checked pair consequences

Checkpoint: 27 November 2026. Two checked pair-learning rounds raise structural
coverage **151/160 to 155/160**. A single batch with the same maximum total pair
allowance reaches **152/160**. Feedback closes three exposed SAT roots and one
new UNSAT root, with no baseline verdict lost. The common fallback already
answers every query.

This is a coverage improvement with a measured cost regression: feedback costs
**3.38% more than the current implementation**, **2.70% more than the larger
one-shot batch**, and **34.72% more than fresh solving**. Every paired timing
comparison has the same unfavorable sign. Production defaults stay unchanged.

## What the new certificate establishes

The current implementation derives binary consequences from two assumptions on
one unchanged source, then prepares and checks an augmented depth-zero terminal.
The new policy can use that terminal's **final normalized residual** as the source
for one more pair batch, only if the terminal remains unresolved. It rebuilds the
occurrence index and reranks variables on the changed source. This tests the
whole feedback policy, including restriction, substitution and changed ranking;
it does not isolate the effect of clause propagation alone.

Each batch contains consequences independently checked against its current CNF.
Adjoining them preserves that CNF's complete model set. Checked terminal
preparation preserves satisfiability and supplies inverse model maps. The checker
reconstructs each next source from the preceding terminal; it does not trust a
stored intermediate CNF or carry a stale index across sources. A final model
lifts through the maps in reverse order and is checked on the original leaf.
A terminal refutation propagates through the same satisfiability equivalences.
The outer conditioning graph still needs one SAT child or two UNSAT children.
An unresolved terminal supplies no verdict.

Rounds are an ordered list of length at most two. Empty retained batches,
continuation after a verdict, changed policies and malformed evidence are rejected.
Cold replay runs no acquisition. Reconstructing the transport after checking an
unknown terminal repeats some work; this is charged, not silently cached away.
No later clause can justify an earlier round. Finite round bounds are neither
exhaustion certificates nor unrestricted efficiency guarantees.

The controls execute the unchanged parent module directly:

- **Base:** one batch of 256 candidate pairs and at most 32 retained clauses.
- **Larger:** one batch of 512 pairs and at most 64 clauses on the original leaf.
- **Feedback:** up to two 256/32 batches, using the checked residual between them.

At depth two there are at most four original leaves. Larger and feedback share
maxima of **2,048 pair attempts and 256 retained clauses per root**, but actual work
differs. Feedback can add eight terminal preparations versus four for larger.
All single-probe, relation, bucket, unsuccessful acquisition and checking costs
remain charged. Evidence establishes valid retained consequences, not the number
of unsuccessful attempts or completeness of the acquisition schedule.

## Frozen comparison

All 138 preceding queries are retained. The new panel was frozen before evaluation:
18 unique constructions and four exact normalized repeats, comprising random
three-CNFs at 32–48 variables, hidden-pair/deleted-conflict controls and parity
prisms. No new normalized source duplicates the preceding panel; families recur.
Labels are audit-only. There are **99 SAT and 61 UNSAT queries**. This is synthetic
coverage evidence, not an external benchmark or general SAT distribution.

| Cohort | Base | Larger | Feedback |
| --- | ---: | ---: | ---: |
| Previous queries | 131/138 | 131/138 | 134/138 |
| New unique inputs | 16/18 | 17/18 | 17/18 |
| New repeats | 4/4 | 4/4 | 4/4 |
| Total | 151/160 | 152/160 | 155/160 |

Feedback gains are `d-d-j07`, `d-k16`, `d-k17` (SAT) and `f05` (UNSAT).
Larger gains only `f05`. No baseline verdict is lost. The three exposed SAT cases
now have full original-source certificates, extending the earlier diagnostic
leaf results. Every preceding base certificate matches its saved parent exactly.

Four cyclic process orders start empty with the same fallback. Complete time
charges input, discovery and internal verification, explicit checking, writes,
warm/cold replay and compression. Startup, labels, historical acquisition, lineage
audit and post-hoc diagnostics are additional. Native fallback archives have two
independent readers; the JSON cold passes use the same checker twice.

| Policy | Complete seconds | Compressed SQLite + JSON bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| Fresh | 8.17343 | 1,944,229 | 250,740,736 |
| Base | 10.65167 | 684,328 | 128,745,472 |
| Larger | 10.72171 | 669,474 | 127,107,072 |
| Feedback | 11.01131 | 600,427 | 120,225,792 |

Feedback versus base has paired regressions **3.20%, 2.59%, 4.93%, 2.79%**;
versus larger, **2.13%, 3.35%, 2.28%, 3.05%**. RSS values are observed process
peaks, not worst-case bounds. The package reduction comes with **larger JSON**:
431,825 base to 460,656 feedback bytes. Fallback records fall **491 to 300**.
Diagnostics add 882,348 bytes and are reported separately.

## Where work is saved and added

| Work across unique programs | Base | Larger | Feedback |
| --- | ---: | ---: | ---: |
| Candidate pairs attempted | 8,591 | 17,289 | 12,130 |
| Binary clauses retained | 1,005 | 1,937 | 1,351 |
| Terminal preparations | 39 | 39 | 55 |
| Terminal bucket steps | 172 | 195 | 296 |

Feedback uses fewer pairs than larger while certifying three additional roots,
but its extra preparation and replay make total time worse. Sixteen refinements
receive a second batch, adding **346 clauses** and five leaf verdicts (four SAT,
one UNSAT). The additional SAT leaf `d-d-j08` is below a root already certified
SAT by base; its cost does not buy another root verdict. Eleven refined leaves
remain unresolved, including five below SAT roots.

The outer graph stays at **434 nodes, 172 splits and 1,626 bucket steps**. It has
43 shared targets and 38 distinct-raw merges, all constant. There is **no new
nonconstant sharing across leaves**. Local prefix reuse and exact-query reuse
continue, but feedback itself expands checked knowledge through source-bound
consequences rather than demonstrating cross-instance structural transfer.

Feedback discovery including internal checking costs **3.81341 s**, cold replay
**3.31908 s**, warm replay **1.54581 s**, and solve/explicit checking **1.69918 s**.
Base discovery/cold replay are **3.44547/3.28679 s**. Reduced solving does not cover
the extra discovery/replay cost. Acquisition and explicit checking reconstruct
49 intermediate transports. Returning a validated intermediate context from a
checker could avoid reconstruction, but its total saving has not been measured.
The dominant measured phases remain discovery and cold replay.

## Remaining gaps, ranked by current evidence

1. **Targeted elimination after checked closure.** Five unique SAT roots remain:
   `d-d-j06`, `d-k14`, `d-k15`, `d-k09`, `f03`. Their six final leaves all stop at
   width nine after positive elimination work. Post-hoc width-nine buckets certify
   three leaves (`d-k14`, `d-k15`, `f03`), while the other three stop at width ten.
   The same three opportunities already exist after **one** pair batch. Next
   compare selective width-nine elimination after one-round closure with a
   two-round control, including full root transport and complete costs. Do not
   credit these opportunities to feedback or count them as achieved root coverage.
2. **Avoid repeated verification work within exact source lifetimes.** Discovery
   and cold replay dominate. Reuse checked terminal/intermediate maps within one
   call, with exact source bindings and every incoming model transport retained.
   Measure the saving rather than extrapolating from fewer pair attempts.
3. **The remaining coupled interaction and broader transfer.** A third 256/32 pair
   batch on each final leaf adds **81 clauses but no terminal verdict**; simply
   repeating width-eight preparation also leaves all six unknown. Among **356**
   complete single-assumption probes, one failure remains, on `d-k09` node zero.
   Three third batches derive no new clause; two hit the clause cap, four the pair
   cap. Next investigate ordering, conditioning or a reusable description of the
   unresolved interaction, rather than assuming more identical feedback suffices.
   External workload coverage, nonconstant cross-instance reuse, efficient
   recognition and unrestricted recomposition bounds remain open.

All frontier screens are separately charged, source-bound leaf diagnostics.
Their results are excluded from matched acquisition, coverage and cost. The
failed-single diagnostic no longer supports the previous frontier's zero-failure
claim because the sources have changed.

## Verification and continuation

All **2,368 full tests and 30 focused tests pass**; existing SQLite ResourceWarnings
are retained. The focused suite includes thirteen new tests for exhaustive
two-variable formulas, small random feedback, exact one-round translation,
original-source model lifting, sparse signed IDs, changed/reordered dependencies,
policy limits, empty batches and cold replay with discovery disabled. An independent
semantic audit enumerates **12,456 assignments over 240 small CNFs**, checking
**563 entailed clauses, 295 rounds and 671 residual-model lifts**. It includes
thirteen two-round SAT outcomes and retains unresolved cases. The main audit
regenerates every certificate, diagnostic and counter across all sixteen reports,
checks independent oracle answers and witnesses, decodes JSON evidence and audits
the compressed fallback databases with both readers.

All **235 previous manifests, 57,145 artifact entries and 1,289 scientific sources**
are preserved; five new scientific sources are added. The manuscript appends the
feedback composition proposition while preserving all 77 earlier proof blocks.
Prior and failed preflight logs remain available; the initial invalid-policy test
mistakenly expected rejection of a valid inherited option and was corrected before measurement.

Resume `experiments/results/cnf-pair-feedback-buckets/checkpoint.json`, key
`pair_feedback_buckets`. `analysis.json` records costs and losses;
`remaining-profile.json`, `next-width-profile.json` and
`leaf-width-comparison.json` retain the next-step evidence. The complete test and
manuscript checks are recorded in `checks.json`. No production default changes.
