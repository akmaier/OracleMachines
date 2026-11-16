# Bounded model rotation on unseen clause deletions

The fixed comparison expands from twelve edits to **257 previously uncached
single-clause deletions** of three retained UNSAT templates. Bounded model
rotation reduces fresh reference expansions **1,876 -> 1,509 (19.56%)** relative
to the guarded control. It publishes **57** independently checked SAT nodes,
so total new rows fall **1,876 -> 1,566 (16.52%)**. Mean complete runtime falls
**11.28948 -> 10.48075 seconds (7.16%)**, and peak RSS falls **3.86%**. This is a
measured decision improvement on constructed neighboring inputs, not broader
structural-family coverage or a polynomial bound for arbitrary SAT.

## Inputs and exact reuse condition

The frozen protocol selects all single-clause deletions of old templates 6, 8
and 12, in round-robin sorted-clause order. It deduplicates full canonical query
keys and excludes roots already in the current 1,169-node reference union.
There are 260 candidates, three cached exclusions and 257 unseen inputs.
Runtime matching uses CNF clause sets in common coordinates; reporting labels
do not choose the reuse route. The two positives from the prior rotation screen
are deliberately included. These are development inputs, not a blind holdout.

All three templates have checked UNSAT certificates. Their retained SAT deletion
models are the three initial seeds. If an assignment satisfies `F \ {C}` and
`F` is UNSAT, then its only falsified clause of `F` is `C`. Flip a variable in
`C` and scan `F`. If exactly one clause `D` is now false, the resulting complete
assignment is a witness for `F \ {D}`. Check that target and publish an ordinary,
self-contained SAT certificate. Zero or multiple false clauses supply no
negative conclusion. This is established model rotation, not a new SAT theorem;
see Belov and Marques-Silva, *Accelerating MUS Extraction with Recursive Model
Rotation*, FMCAD 2011, Proposition 1 (already cited in the manuscript).

The experiment keeps one witness per discovered deleted clause, explores these
witnesses FIFO and permits at most **64 flips per template over the whole
stream**. The budget never resets per query. Initial rotation runs before the
first query. Later checked SAT answers can seed additional rotations. Every
flip scans all template clauses; there is no occurrence-index optimization.

The control modes are ordinary residual solving and the existing witness/UNSAT
guard wrapper. Both bank modes first check the direct query cache. A guard
requires a checked UNSAT stronger formula; it forces the removed clause false
and solves the exact remaining cofactor. Rotation adds only the bounded witness
exploration and checked publications. All modes inherit the same full reference
union; earlier acquisition costs are retained in the historical records.

## Matched measurements

Three fresh-process triples rotate mode position. Each stream visits all 257
queries twice. All return **72 SAT / 185 UNSAT**, and every repeat adds zero
rows. Node counts, answers, witnesses and database bytes agree across repeats.

| Measurement | Ordinary | Guarded | Guarded + rotation |
|---|---:|---:|---:|
| Fresh expansions | 6,126 | 1,876 | 1,509 |
| New stored rows | 6,126 | 1,876 | 1,566 |
| Split nodes | 2,240 | 617 | 469 |
| Mean complete seconds | 27.82621 | 11.28948 | 10.48075 |
| Mean query-stream seconds | 18.91448 | 7.53591 | 6.96639 |
| Mean cold-check seconds | 7.44940 | 2.91281 | 2.72486 |
| Mean compression seconds | 1.38813 | 0.78315 | 0.70113 |
| Mean peak RSS bytes | 279,844,181 | 159,105,024 | 152,966,485 |
| SQLite bytes | 27,746,304 | 10,850,304 | 10,399,744 |
| Database gzip bytes | 1,986,351 | 990,965 | 907,510 |
| First-trial raw sidecar bytes | 6,555,319 | 9,428,777 | 9,014,252 |
| Gzip database + raw sidecars | 8,541,670 | 10,419,742 | 9,921,762 |

The complete clock includes restoration, bank preparation, matching, premise
checking, model rotation, publications, search, bookkeeping, cold replay,
sidecar serialization and database compression. Imports and final summary
writing are excluded. Selection and preflight cost **0.35307 s** separately;
retrospective validation is also outside the timed workers. No tests, build or
profiler run alongside the timed streams. Complete time improves in all three
paired comparisons. This small development experiment does not establish
population-level performance.

There are **189 flips**: 99 leave a single false clause and 90 fail. Of the
successful flips, 57 publish absent keys and 42 reach already stored keys.
Three publications happen before the stream. **37 first encounters** use a
published direct query answer; later publications can materialize an answer
whose guarded cofactor was already solved. Publication count is consequently
not the count of fresh solves avoided. Full flip scans charge 47,684 literal
positions as a conservative volume count; clause evaluation can short-circuit.
Observation and publication checks are counted separately. There
are no per-query fresh-expansion regressions relative to the guarded arm on
this fixed order. Failed flips and all alternative valid certificates survive.

Database size falls 4.15% against the guarded arm. Combined gzip database and
raw sidecars fall 4.78%, but remain **16.16% larger than ordinary solving**:
repeated guards duplicate entire stronger CNFs. A smaller solver snapshot does
not imply smaller total research storage. The durable union retains all old
payloads and all distinct new keys from all arms: **9,104 keys / 32,595,968 SQLite
bytes / 2,524,507 gzip bytes**, up from 1,169 keys. Trial archives retain 81
occurrences of alternative valid certificates on overlapping keys.

## Costs and limits

For one template with `n` variables, `m` clauses and `L` literal occurrences, a
flip copies `n` model entries and scans `L` occurrences: `O(n + L)` before
recognition, canonicalization, certificate verification and persistence. A
budget `B` limits these scans to `O(B(n + L))`. Every observed SAT query still
requires exact matching and model checks; that stream-dependent cost is not
bounded by `B`. A successful publication also stores and checks a complete
query certificate, so it is not a constant-cost operation.

The engine retains at most one `n`-entry model per clause, at most `B` attempt
records with up to `m` failed-clause indices, and the template: a conservative
`O(nm + Bm + L)` word-space bound, excluding published certificates, solver
history and experiment sidecars. The representation is not compact in the
number of arbitrary SAT answers. Python object and serialized byte costs are
reported separately rather than inferred from this bound.

All 72 new SAT queries eventually contribute witnesses, partly through fresh
solving. Together with the seeds, the engine holds 26, 26 and 23 clause witnesses
for templates 6, 8 and 12. The first two hit their 64-flip caps, leaving six
queued flips each. The third makes 61 flips and exhausts its current queue.
One chosen witness per clause can miss routes available from another witness;
queue exhaustion is not complete exploration of the model graph. Saved state
includes models, origins, failed-clause lists, cursors and consumed budgets.
There is no engine-state import/resume API yet; cold certificate replay is
implemented and checked.

The partition here is only of **single-clause deletions of these three known
UNSAT formulas**. The 185 negative neighbors cannot be identified from failed
rotations. Nor does separate UNSAT for two single deletions justify deleting
both clauses together. No efficient recognition or compact closure argument
for arbitrary CNF follows.

## Highest next gap

**UNSAT inputs consume 1,216 of 1,509 remaining expansions (80.58%)**, unchanged
by rotation. SAT-query work falls 660 -> 293. By original template, the remaining
negative costs are 330, 274 and 612 expansions. Template 12 is the largest
negative target; new catalog case 11 alone requires 47 expansions and remains
UNSAT. The exact input, removed clause and target key hash are saved in
`cost-attribution.json`; this case number belongs to the new 257-input catalog.

The strongest next investigation is extracting and checking reusable **UNSAT
proof supports or common negative cofactors**. A checked unsatisfiable subset
would transfer to any query containing that subset, with exact containment and
certificate checks charged. First determine whether the retained proofs supply
small supports across these deletions, rather than assuming they do. Alternative
witnesses and larger rotation budgets target only the remaining positive work.
An occurrence index might reduce flip scans, but these small scans are not the
dominant remaining source of expansions. Raw sidecar deduplication is a separate
storage opportunity; it cannot replace a checked negative proof.

## Preservation and reproduction

All **394 tests** pass, including valid publications checked across all 255 nonempty subsets of the
eight nonempty two-variable clauses, budget non-reset, malformed premises and invalid models. Independent cold
validation checks all nine archives and **4,626 query replays**, all rotation
origins and flips, every union node, and the twelve inherited query answers with
fresh expansion disabled. Structural authority remains **2,614 patterns / 259
pairs / seventeen missing children**, original **17/24 / 999 proof steps**, and
separate supplemental **24/24 / 208 proof steps**.

Resume `experiments/results/cnf-model-rotation/checkpoint.json`. Preserve its
inherited `reference_study`, `witness_reuse_study` and `reference_decisions`, and
new `model_rotation_study`, `model_rotation_decisions` and `reference_union`.
The post-hoc analyzer is bound in the final ledger in addition to 329 runtime
sources. Earlier artifacts and manuscript proof blocks remain unchanged.

```sh
python3 experiments/compare_cnf_model_rotation.py /tmp/cnf-model-rotation
python3 experiments/validate_cnf_model_rotation.py /tmp/cnf-model-rotation
python3 experiments/analyze_cnf_model_rotation.py /tmp/cnf-model-rotation
```
