# A covered branch does not identify the cheapest continuation

Case 6 now has two independently checked structural proofs, raising original
coverage **12/24 -> 13/24**. The comparison exposes a limitation of the current
reuse heuristic: following its preferred saved split needs **74 new patterns /
547 probes**, while a control reconstructing the source splits needs **63 new
patterns / 345 probes**. Both finish in one batch. Preserve this counterexample;
having less visible work remaining does not guarantee cheaper expansion.

## What was compared

The parent contains 1,981 patterns and 199 split certificates. The selected
case-6 source is a 36-variable, 148-clause random 3-CNF. Four saved source splits
use local variables 11, 15, 8 and 13. All eight children already exist. Pivot 13
has one covered child and one uncovered child; the other six children are open.

The existing selector already skips the covered branch. Its remaining-literal
scores are **796, 820, 758 and 409**, respectively, so it selects pivot 13 and
works on a 34-variable, 135-clause, 409-literal residual. An acquisition-free
diagnostic on all twelve remaining original roots finds twelve reachable
unresolved sources with saved choices. Counting only distinct, currently
uncovered obligations selects the same candidate at every source. We do not
install that ineffective ranking change or claim a new saving from it.

The [frozen comparison](../experiments/results/cnf-saved-split-reuse/protocol.json)
keeps the existing scoped refinement and canonical full auditor in both arms.
The retained arm starts from the complete parent. An isolated control copy
omits only the four split certificates at the selected source, before any live
verifier or append-only session opens. It retains **every pattern row**, including
the child results, and all other splits. The authoritative parent is never
modified. Once a variant opens, its complete initial state must be an immutable
prefix of every subsequent snapshot.

Without those certificates, the unchanged proposal rule chooses pivot 11. It
reconstructs that certificate and reuses the already stored children. It does
not reconstruct all four omitted certificates. The intervention removes both
certificate availability and the selector's information about those choices;
it does not isolate the cost of the covered branch alone, and it is not an
empty-history solve. This is a known development case, with two reversed-order
paired fresh-process repetitions and the same limits of four batches, 128
admissions and sixteen pair attempts per batch.

## Expansion, runtime and memory

| Resource | Retain four source splits | Omit four source splits in control |
| --- | ---: | ---: |
| Batches to structural coverage | 1 | 1 |
| New pattern rows / distinct admissions | 74 | 63 |
| Probe attempts | 547 | 345 |
| Fresh source assumptions | 10 | 12 |
| Split rows acquired during continuation | 5 | 6 |
| Split identities new to the full parent | 5 | 5 |
| Restoration, control preparation and setup, seconds | 0.14979 | 0.06303 |
| Local expansion, seconds | 0.24952 | 0.25645 |
| Bookkeeping, seconds | 0.10629 | 0.10445 |
| Independent query-proof check, seconds | 0.13827 | 0.13380 |
| Complete cold audit, seconds | 6.61766 | 6.45945 |
| Compression, seconds | 0.72647 | 0.72109 |
| Whole stream, seconds | 8.07061 | 7.82088 |
| Mean peak process RSS, bytes | 410,058,752 | 384,090,112 |
| Final SQLite bytes | 38,567,936 | 38,408,192 |
| Compressed snapshot bytes | 1,927,364 | 1,928,639 |

The retained choice needs **17.46% more new patterns and 58.55% more probes**.
It saves two source assumptions, and its measured local expansion is slightly
faster despite the higher probe count. Its whole stream is **3.19% slower** and
mean peak RSS **6.76% higher** than the control. The compressed retained snapshot
is 1,275 bytes smaller despite more pattern rows. Thus these cost measures do not
induce one common ranking. Two timing repetitions do not establish a general
runtime or memory advantage for discarding history.

The wall clock charges restoration, preparation of the isolated control, setup,
selection, acquisition, bookkeeping, compression and both cold checks. It
excludes interpreter imports and final summary writing; RSS includes imports
and all phases. The earlier acquisition of saved results remains recorded in
parent experiments. Diagnostic and retrospective validation costs are separate.
No tests, profiler or validator run concurrently with the timed streams.

Each full audit checks all remaining pattern and split rows, all 24 original
bindings and the complete positive proof with acquisition forbidden. Each
query proof is independently checked against its exact snapshot. Control
omission is not a relaxed semantic check. Both variants retain the parent's
twelve covered originals before beginning the new continuation.

## Family transitions and reuse actually observed

The retained proof has **86 distinct steps**: six conditional nodes, one component
decomposition, 73 unary reductions and six family terminals. Its maximum
conditional depth is five. Twelve pattern steps predate the run, and 74 are new.
Unary steps comprise 35 probes, 15 binary-path reductions, 21 eliminations, one
polarity transformation and one subsumption. Terminals include contradiction,
2-CNF and Horn/zero-valid residuals; the Horn residual has six variables and
five clauses. The only node shared within this proof is contradiction, with
three occurrences; 88 unfolded occurrences become 86 distinct steps.

The control proof has **76 distinct steps**: six conditional nodes, one component
decomposition, 63 unary reductions and six family terminals. Its maximum depth
is four. Thirteen pattern steps predate the run, and 63 are new. Unary steps
comprise 37 probes, seven binary-path reductions, eighteen eliminations and one
polarity transformation. Its Horn/zero-valid residual has eight variables and
nine clauses. Contradiction and the empty formula each occur twice; 78 unfolded
occurrences become 76 distinct steps. Family overlaps remain explicit. These
depths use changing local coordinates, not fixed backdoor sizes or minimality
certificates. Structural coverage is not a new SAT/UNSAT output API.

One split in each proof has an identity already present in the full parent.
The retained arm actually reuses its pivot-13 record. The control reconstructs
its omitted pivot-11 record; matching a historical identity is not certificate
reuse in that arm. The explanations distinguish available initial split steps
from reconstructed omitted steps.

The two continuations share **zero newly acquired pattern rows and zero new
split identities**. Only three parent proof steps are common. All 137 new
patterns and ten new split identities are therefore retained in the merged
checkpoint. There is no observed cross-route sharing of new nonterminal states
here, even though both proofs reduce the same original to familiar families.
This also does not test equivalence under arbitrary variable renaming.

## What this changes in the gap analysis

Current remaining-literal counts omit the future cost of exposing tractable
structure. A branch already covered is useful evidence, but the hard sibling
can dominate subsequent work. The counterexample defeats a minimum-cost claim
for this selector; it does not establish that pivot 11 is globally optimal.
Blindly discarding saved choices would also discard their useful information.

The next selection experiment should retain all alternatives and charge a
bounded comparison of their downstream simplification progress, reusing every
admitted state. Compare it with the unchanged committed-choice policy. Consult
earlier lookahead experiments before repeating acquisition; count exploratory
work and failed candidates. A smaller frontier or one covered side alone is
not an adequate cost forecast. The unchanged twelve-source ranking diagnostic
rules out that particular simple fix on this parent.

Complete auditing still consumes about **82%** of either stream, while local
expansion is only about **3%**. Thus a better selector may reduce retained state
without producing a proportional end-to-end speedup. Both selection quality
and audit cost remain gaps; neither yields a uniform arbitrary-SAT bound.

## Verified checkpoint and next target

The union retains **2,118 patterns / 209 split records / 17 inherited missing
children**, with a **779-step positive proof for thirteen originals**. Eleven
originals remain structurally unknown. Its own serialization occupies
**39,448,576 SQLite bytes / 1,970,166 gzip bytes**, growing by 1,867,776 and 86,694
bytes from the parent. Both exploratory continuations are preserved; this union
is deliberately larger than either individual result.

All **363 tests** pass. Independent replay uses the frozen full auditor on all
four trial snapshots and both initial variants, checks each query proof and
reachable catalog, verifies byte-identical initial pattern rows and unchanged
other splits, and checks the complete union. The successful validation run takes
**88.50 seconds**, outside operational timings and partly concurrent with tests.
An earlier validation attempt reached union replay, then failed when generating
the next pointer because it tried to compose a missing optional root. Its code
and failure log are retained. The new pointer checks presence first; a missing
root remains unknown and triggers no acquisition or negative SAT claim. The
88.50 seconds exclude that failed attempt and are not total research effort.

The next target is **case 11**, random 3-CNF. Its selected residual has
**45 variables / 196 clauses / 608 literals / maximum width five**. All eight
children of saved pivots 2, 32, 7 and 6 are present and uncovered. The original
root at recognition depth zero is present; the optional depth-one root is not.
Resume from the verified depth-zero root and retained children, accounting for
any additional root acquisition explicitly. The pointer binds the full union;
historical enumeration timings only rank priority, not current expansion cost.
