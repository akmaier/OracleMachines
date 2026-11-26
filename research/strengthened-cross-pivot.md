# Repeated cross-pivot feedback completes the retained frontier

Date: 26 November 2026. Parent checkpoint: `94b0d459`.
Evidence: `experiments/results/cnf-strengthened-cross-pivot/`.

## Result and scope

The original `(61,50)` bank and its two-unit strengthening both remain flat
failed-literal fixed points. Conditioning the strengthened bank, however, yields
nine further failed sides. Their implied units jointly contradict that bank.
The generic compiler reconstructs this two-level dependency through the original
source, and both cold readers accept it. Structural coverage is now
**246/246 retained frontier snapshots**, with an empty remaining overlay.

This closes the finite recorded frontier, not arbitrary SAT or every generating
target formula. The new inference rule alone still stalls on the unsatisfiable
four-variable CNF containing all sixteen clauses that exclude its sixteen
assignments. The tests preserve that explicit counterexample. It does not show
failure of the entire solver portfolio or a complexity lower bound.

## Reusable rounds and exact dependencies

`cnf_iterated_cross_pivot.py` repeats one schema: condition at most sixteen unfixed
source-order pivots, apply existing saturation on both sides, collect checked
failed-side implications, and add their opposite units. Each level's seed is
exactly the preceding augmented bank. Discovery stops at a checked contradiction,
the round limit, or no new unit from its bounded search. The last outcome is not
SAT and is not a claim that all possible decompositions have been exhausted.

Resume validates the saved chain and continues from its last bank. A saved
refutation can be reused without fresh probes. A saved no-new-units outcome is
rechecked when resumed, replacing its unchanged final round: larger bounds might
find information that the earlier pass missed. In the discovery implementation,
each productive unresolved round fixes at least one previously unfixed pivot.
There can therefore be at most as many such productive rounds as seed variables.
That monotonicity bounds unit accumulation, not the number of unsolved cells or
the cost of reconstructing source-only certificates.

The old first level retains `60=false` and `73=false`. The new level finds nine
failed sides and a 52-step joint contradiction. Final-level compaction keeps
seven sides and 21 steps. Earlier levels are unchanged because later histories
bind their exact banks; pruning an earlier level would require transporting and
rechecking every dependent proof. The compact chain thus retains 2 + 7 branch
certificates, versus 2 + 9 in the full chain.

Native reconstruction uses a generic level-indexed environment map. A cross-pivot
reference from a branch must decrease the feedback level; local saturation
references decrease the bank stage. Exact branch assumptions remain in every
recursive context, and an assumption cannot justify its own excluded context.
Slice memo keys distinguish environment, stage, assumption and trace. All levels
share one direct-unit work allowance per compilation. Incoming provenance is
checked before warm cache hits. This removes the need for a new compiler per
feedback level, while preserving the earlier fixed B13 base and all its proofs.

## Matched discovery and reuse

Six fresh-process permutations compare one round, a two-round restart and a
one-round continuation of the saved first round. Every saturation call keeps its
existing limits: eight internal rounds, 512 probes, 2,097,152 work units and trace
length 256. Restart and resume produce identical chains and concatenated search
histories. The one-round control has less search and remains unresolved.

| Mode | Load (s) | Prepare (s) | Discover/resume (s) | Cold check (s) | Persist (s) | Complete (s) | New probes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| One round | 0.00072 | 0.01336 | 0.22822 | 0.02666 | 0.00701 | 0.27634 | 6,078 |
| Two-round restart | 0.00072 | 0.01329 | 0.56682 | 0.11809 | 0.02240 | 0.72224 | 14,799 |
| Saved first round + one new round | 0.00141 | 0.01355 | 0.36004 | 0.12052 | 0.01658 | 0.51269 | 8,721 |

With the first round already available, resume avoids **6,078 probes** and reduces
complete time **29.01%**. Discovery is about 79% of restart cost and 70% of resume;
independent verification remains about 24% of resume. Preparation, loading,
serialization and cold seed reconstruction are charged. Historical preprocessing
and acquisition remain additional. Creating the first round now and then resuming
costs **0.78903 s**, more than the **0.72224 s** uninterrupted restart. The prior
first-summary acquisition and new checked wrapper (0.02824 s) are separately
recorded; there is no free acquisition assumption.

| Mode | Chain bytes | Newly written search-history bytes | Peak RSS (bytes) |
| --- | ---: | ---: | ---: |
| One round | 86,885 | 816,360 | 57,933,824 |
| Two-round restart | 633,696 | 2,033,696 | 81,412,096 |
| Resume | 633,696 | 1,217,338 | 72,237,056 |

The final chain is identical under resume. Its new search file is smaller because
the earlier search history already exists; total lifetime history is not reduced.
Checked final-level compaction costs another **0.35524 s** and yields **513,811
bytes**, retaining every earlier bank binding. These costs are separate from the
native conversion measurements below.

## Native conversion and the shortcut-budget regression

Four cyclic mode orders put each mode in every order position. Full and compact
use the same global direct-unit allowance 262,144; `compact_large` raises only
that ceiling to 2,097,152. Fresh solving uses the existing 256-node bound and also
refutes the snapshot. The budgets are not equivalent across algorithms.

| Mode | Construct (s) | Warm (s) | Cold readers (s) | Persist (s) | Complete (s) | Records | Raw record bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh | 0.40304 | 0.00149 | 0.39587 | 0.13322 | 0.94034 | 236 | 1,776,473 |
| Full | 1.47282 | 0.12065 | 1.16627 | 0.33167 | 3.11340 | 626 | 4,301,898 |
| Compact | 1.41805 | 0.09971 | 1.15190 | 0.33231 | 3.01690 | 626 | 4,301,898 |
| Compact, larger allowance | 0.49760 | 0.10902 | 0.33100 | 0.09691 | 1.04320 | 170 | 1,520,105 |

Complete time includes input loading, database handling, a warm call, both cold
readers and compressed persistence. Discovery, summary acquisition and compaction
are additional. Full and compact generate identical native graphs. Their original
shortcut allowance is exhausted, causing 699 skipped direct-closure candidates
and 26 cross-pivot branch expansions. The larger-allowance control spends only
277,866 actual shortcut work units, versus 262,144, but avoids all budget skips
and uses fifteen branch expansions. A small change in actual shortcut work can
thus have a large effect on subsequent recursive expansion.

The larger ceiling cuts native complete time **65.42%** relative to compact at
the original ceiling. It is still **10.94% slower than fresh**, though it stores
**14.43% fewer raw bytes**. Fresh is the selected measured native workflow; all
three compiled certificates and the pilot archive remain. Do not present the
budget-control gain as a general speedup over fresh solving. Warm compiler calls
still check substantial provenance, unlike the inexpensive fresh warm lookup.

| Mode | Peak RSS (bytes) | Compressed native archive (bytes) |
| --- | ---: | ---: |
| Fresh | 82,919,424 | 193,713 |
| Full | 124,141,568 | 456,188 |
| Compact | 124,305,408 | 456,188 |
| Compact, larger allowance | 84,639,744 | 134,291 |

The fixed-budget regression, flat fixed points, all mode samples and all old
proofs are preserved. No production default changes. The larger budget neither
bounds worst-case native graph size nor establishes a universally good allowance.

## Validation and next investigation

Validation includes 2,210 full tests and 27 focused tests. New checks cover all 256
subsets of the eight two-variable unit/binary clauses, 60 seeded five-variable
formulas, empty and contradictory seeds, the explicit four-variable unresolved
counterexample, larger-budget rechecking, exact resumed histories, terminal reuse,
stale/reordered dependencies, warm invalidation, both cold readers, and equality
with the old compiler on a one-level certificate. All 1,213 old source fingerprints
and 33,491 artifact entries in 220 manifests remain unchanged, as do earlier
native results and all 64 manuscript proof blocks. Five new science/test files
bring the source ledger to 1,218.

Resume `experiments/results/cnf-strengthened-cross-pivot/checkpoint.json`, key
`strengthened_cross_pivot.remaining`. Its loader returns an empty frontier, while
the parent overlays preserve every earlier snapshot. Do not continue mining this
exhausted frontier as evidence of generalization. The next investigation should:

1. Freeze a fresh, unlabelled held-out panel with both SAT and UNSAT cases,
   structural mixtures and edits, and growing sizes. Measure discovery coverage,
   unresolved cases and total acquisition cost without using the old histories.
   Include the four-variable counterexample to distinguish a limitation of the
   new unit-feedback rule from the capabilities of other portfolio routes.
2. Separate reusable inference from the historical B13 constructor. The round
   kernel accepts arbitrary seed CNFs, but the native adapter still expects that
   acquired proof stack. A generic checked source/lemma dependency interface is
   needed to carry these patterns to new categories without replaying this lineage.
3. Compare non-unit boundary consequences or deeper conditioning against fresh
   solving when no new units are found. Charge recognition and native expansion;
   budget exhaustion and repeated whole-residual payloads remain concrete costs.

This completed finite validation establishes exact recomposition and useful reuse
on its recorded cases. Efficient discovery, compact summaries and bounded
recomposition for every CNF remain open requirements.
