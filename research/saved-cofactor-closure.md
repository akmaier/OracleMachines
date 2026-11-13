# A saved split closes the 19-variable residual

2026-11-13. After the two checked augmentations failed to reduce the remaining
19-variable / 84-clause leaf, conditioning a retained variable pair completes its
structural decomposition. Coverage rises from **55/83 to 56/83**, including the
growth-exception ablation. This is one additional reused development original,
not a new unrestricted SAT guarantee.

## What changed

The new runner `experiments/continue_cnf_saved_splits.py` ranks up to 64 saved
pairs; all **fourteen** available pairs are ranked in this run. No fresh source
assumption trace is needed for selection. The score first minimizes uncovered
and missing children, then maximum child support, total child literals and the
variable ID. It selects **variable 15**. This is a heuristic over retained pairs,
not a proof of the globally cheapest split; the source has nineteen variables.

The two checked cofactors are:

| Assignment in the 19-variable leaf | Variables | Clauses | Outcome |
|---|---:|---:|---|
| 15 = false, after saved unit closure | 11 | 36 | structurally closed |
| 15 = true, after saved unit closure | 17 | 71 | structurally closed |

Both branches share a **32-state** recognition allowance and use **18** new
states. These comprise four probe reductions, seven eliminations, two binary-path
reductions, one component conjunction, one polarity transformation, one retained
plan and two recognized-family nodes. The false branch passes through further
probe reductions to a constant-valid leaf. The true branch exposes an elimination
chain and components. The new family nodes include Horn/zero-valid and one-valid
formulas. All eighteen new states are structurally closed.

The gain is development case **71**, originally case **1441**, labelled `n48` in
the historical `subsumption_holdout3` group: **48 variables / 204 clauses**. That
group name is historical; repeated adaptive use means this is not a held-out
result. The additional route completes the retained decomposition of the original
formula. It does not show that all formulas of that size admit such a route.

Independent reference solving finds the source, both cofactors and the gained
original SAT and verifies lifted models. SAT of one branch alone would suffice
for a SAT verdict, but the structural-coverage claim here checks **both** branch
plans. All seven retained split sources are now closed, with no pending child or
open saved-split leaf. All eleven acquired learned targets are also closed.

## Costs and retained storage

| Work | Seconds |
|---|---:|
| Restore the parent history | 14.47566 |
| Prepare checked routes and original roots | 67.69189 |
| Navigate and rank fourteen saved pairs | 0.04395 |
| Acquire both cofactors and their reductions | 0.05914 |
| Compose coverage and diagnostics | 0.13114 |
| Export the immutable delta | 5.51052 |
| Full cold inventory audit | 110.35857 |
| Cold route reconstruction and coverage | 64.20861 |
| Reference acquisition / cold reference check | 0.12232 / 0.72437 |
| Complete pipeline, including remaining I/O | **271.74133** |

These are one-run wall times. Local acquisition uses the resident checked source
and earlier traces; preparation and past acquisition remain charged. The earlier
augmentation comparison has different validation obligations, so its total time
is not a matched whole-solver baseline. No general speedup or peak-RAM result is
claimed.

The working SQLite file grows **200,704 bytes**, from 769,646,592 to
**769,847,296 bytes**, and contains **41,728 pattern nodes**. Its 1,548 source rows,
21,838 residual rows, 563 pivot trials, 25 coupled trials, one growth trial,
87 windows and 128 ordinary continuation rows are preserved unchanged. The delta
is 270,336 bytes before compression and **9,471 bytes** afterward; its schema and
page overhead differ from the working-database increment. The new split record,
rankings, coverage proof and diagnostics are additional artifacts.

All **1,775** previous reference nodes are preserved byte for byte within **1,869**
reference nodes. The reference database is 14,241,792 bytes and its complete
compressed archive is 931,396 bytes. This archive includes the old reference
content; it is not a 931,396-byte delta. The earlier parent-lemma sidecars are
untouched. No old solver or proof records are replaced.

## Resume and validation

The checkpoint is `experiments/results/cnf-saved-splits/report.json`. Restore it
with `continue_cnf_saved_splits.restore_checkpoint` and `routes_for`; keep all
**seven splits, 42 learned bases and 155 augmented blocks**. The new restorer can
append further checkpoints of its own format and namespaces inherited temporary
files so prior delta exports cannot collide.

```sh
python3 experiments/continue_cnf_saved_splits.py /tmp/cnf-saved-splits-new
python3 -m unittest solver.test_cnf_trace_split solver.test_cnf_split_batch \
  solver.test_cnf_split_frontier solver.test_cnf_route_composition \
  > /tmp/cnf-saved-splits-tests.txt 2>&1
python3 experiments/validate_cnf_saved_splits.py \
  experiments/results/cnf-saved-splits --test-log /tmp/cnf-saved-splits-tests.txt
```

The run audits all pattern and residual nodes, proves immutable delta preservation
and idempotent application, and recomposes coverage with and without growth
exceptions. The independent validator reconstructs the parent to reproduce the
ranking, then the child to check both branch obligations, complete coverage,
reference answers, model lifting and preservation with new discovery disabled.
All fourteen relevant core tests pass and cover forged bindings, missing children,
globally shared budgets, nested frontiers and cold reuse. Lean sources and the
older full-suite result remain unchanged; no new full-suite run is claimed.
Independent cold selection/coverage/reference replay passes in **163.73950 s**
with discovery disabled and both reconstructed databases byte-for-byte unchanged.

The saved split frontier is empty, so blindly continuing that scheduler would
produce no work. **18 learned bases / 92 ranked variables** remain ready. The
smallest has 29 variables, 362 literal occurrences and four untried candidates
after offset 24. Use `open-originals.json.gz`, produced by independent validation,
to relate that queue to the 27 still-open originals before choosing the next
expansion. It follows selected internal and ordinary routes, not every alternative
decomposition. Dependency-local checking of a full positive coverage plan remains
the principal cost gap; the earlier portable fact checker does not discharge it.

The validated snapshot contains **29 distinct leaves**, each appearing in only
one of the 27 open originals. All eighteen ready bases occur on these selected
paths, each in one original; case 14 contains two ready bases. Thus exact leaf
identity offers no measured cross-original sharing in this snapshot, although
internal components and alternative decompositions may still share work.

The next smaller structural candidate is the **20-variable / 80-clause** leaf of
case **73** (original 1444), whose ordinary and current augmented streams are
exhausted. Its source hash is
`f21d37de267399fe2d8df6700867334959f83ae2659d34e9450cb0ebec049770`.
The 29-variable ready base belongs to case **30** (original 1189), has 120 clauses,
and can be continued for four remaining augmented candidates as a bounded
alternative. The still smaller **11-variable / 49-clause** encoding-cap example
(case 0, original 742) has no binary clauses or saved probe pairs. Earlier work
already certified its minimum-width-five obstruction to unit triggering under
at most three assigned variables. Its two parity blocks plus a wide coupling
clause call for a structural representation or explicitly deeper conditioning;
do not repeat the exhausted shallow-probing approach.

The existing affine extractor was replayed on this exact source and saved as
`encoding-cap-affine.json`: two independent equations (supports 1--5 and 6--11,
right sides 0 and 1) and exactly one eleven-literal leftover clause. This exposes
a more general implementation opportunity than raising its projection-encoding
cap. For a consistent affine system with particular solution a and nullspace
basis N, a literal on variable i is compatible if a already gives its requested
value or some vector of N has coordinate i = 1. A single clause is satisfiable
with the system exactly when one literal is compatible. A suitable basis-vector
flip constructs a model; otherwise every literal is forced false. An inconsistent
system is already UNSAT. This uses ordinary linear algebra and avoids explicit
enumeration of the affine relation. A general CNF may have many interacting
leftover clauses, so this argument does not solve arbitrary mixtures.

**Implementing and independently checking this affine-plus-one-clause family is
the next structural opportunity.** The diagnostic only checks the extraction;
no new route, coverage gain, performance claim or Lean theorem for this family
is claimed in the present checkpoint. Preserve the 20-variable cofactor and the
29-variable learned continuation as general-workload alternatives.
