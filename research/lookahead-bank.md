# Checked lookahead reuse and the missing-candidate gap

A new optional probe bank preserves source-bound lookahead evidence and lets
later acquisition replay it without probing again. On the frozen new-input
comparison it avoids **36 repeated probes**, with identical selected splits and
pattern payloads. The tested lookahead score nevertheless adds **34 probes over
size-based selection** and no coverage. It remains experimental; no default
planner or historical inference source is changed.

The larger discovery limitation appears before ranking: **22/24 inputs have no
saved assumption pair on the selected unresolved component under depth-zero
preparation**. This restricts the score comparison to two inputs. It is not a
failure of ordinary conditioning, which the existing planner can use at positive
depth, nor an argument that these SAT instances are unsatisfiable or hard for
every method.

## Frozen design

The seed is 20261115214950. Before any new acquisition, the protocol fixes twenty
random 3-CNFs: five densities (3.8, 4.1, 4.25, 4.4, 4.6) at each of 24, 36, 48
and 60 variables. Four additional random-core/binary-chain mixtures include two
connected and two disjoint cases. The 24 normalized sources are distinct and
absent from the 1,497 historical original cases and previous 42-input stream.
This novelty check does not search every historical intermediate residual.
Generator labels do not enter selection.

Shared preparation uses the existing planner at conditioning depth zero, with
at most 256 complete admissions per original. It stores 85 patterns, charges
85 admissions and 168 probes, and takes **0.77105 s** including ranking and archive
creation. No original has complete structural coverage at this stage. This is
preprocessing cost, not free knowledge. All later arms start from the identical
prepared history and use one selected unresolved component per original.

The four arms are size-based selection; one-profile lookahead followed by
recomputation; the same lookahead with checked evidence reuse; and enumeration
of existing saved pairs. Lookahead scores both cofactors by unresolved component
count, maximum unresolved support and literal count after one profile, breaking
ties by the old rank. It does not claim these features estimate optimum cost.
Each query shares **40 distinct acquisition-state admissions** between scouting
and expansion. Returning to an admitted source, checking, normalization and I/O
remain additional work. Two repetitions reverse arm order.

## Matched result and negative control

| Arm | Fresh probes | Admissions | New patterns | Bank rows | Query seconds | Covered originals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Size | 72 | 8 | 8 | 0 | 0.12251 | 0/24 |
| Lookahead, recompute | 142 | 12 | 8 | 8 | 0.15432 | 0/24 |
| Lookahead, reuse | 106 | 12 | 8 | 8 | 0.15344 | 0/24 |
| Enumerate saved pairs | 164 | 19 | 19 | 0 | 0.24883 | 0/24 |

Times are means; setup adds approximately **0.258--0.264 s** per arm. Query times
include ranking, scouting, repeated route checking, recognition, immutable-row
audits and proof persistence. Report serialization, compression and full cold
replay are separately recorded. All arms use the same optional inventory wrapper;
the size and enumeration arms have an empty bank and incur its lookup overhead.
This is not a direct production-solver runtime comparison. Peak RAM is unmeasured.

Only cases **21 and 23**, the connected mixtures, offer saved pairs: two each.
Lookahead evaluates all four candidate pairs across those inputs, acquiring 70
probe attempts. The chosen pair matches size-based selection on both inputs.
Reusing its four cofactor probe certificates saves 36 attempts compared with
recomputing them. The unused lookahead candidates still cost 34 probes, so total
work exceeds the size arm's 72. All three single-choice arms produce the same
stored pattern graph. No query reaches its admission cap. The two timing samples
show no reliable speedup from the bank; lower repeated acquisition is not the
same as lower total cost.

The bank has **8 entries / 36,684 logical key-plus-proof bytes**. Its SQLite
history is **1,814,528 bytes**, versus **1,740,800** for size ranking, and compressed
archives are **91,213 versus 85,124 bytes**. Enumeration occupies 1,949,696 SQLite
bytes. Thus this experiment retains more state without expanding coverage.
The cost and the failed ranking idea are preserved, rather than promoted as a
successful discovery policy.

## What is missing before lookahead can help

For all twenty random originals and the hard components of the two disjoint
mixtures, the selected unresolved residual has **zero binary clauses and zero
saved top-level probe attempts**. The existing probe selector ranks variables
appearing in binary clauses. At depth zero there is no ordinary conditioning
step to create shorter cofactors first. Increasing the width of that same
binary-only probe window would still produce no candidates.

This identifies a concrete entry condition for saved-pair expansion, not a
complete taxonomy of SAT. Next compare charged ordinary conditioning, using the
existing balanced shortest-clause ranking, with explicit broader source-pair
acquisition. Retain both assumption certificates and their variable maps. Then
test the same selection score and bank on the resulting common candidate pool,
charging this preparation rather than treating the pairs as already available.
Positive-depth preparation is a different experiment and must keep its own
budget and results. The previous depth-two 42-input stream remains complete.

A candidate-availability partition is easy to recognize: the selected residual
either has saved source pairs or it does not. That partition alone supplies no
tractability result. Further conditioning can expose binary interactions, but
repeated branching can remain exponential and may fail to produce reusable
components. The cost of finding useful pairs remains an unrestricted obligation.

## Exact persistence contract and validation

`LookaheadInventory` is optional. Only an explicit scouting call writes the new
`cnf_lookahead_probes_v1` table. An exact key binds the full recognition policy and
canonical CNF; probe evidence does not depend on remaining conditioning depth.
Every load passes through the original probe checker, including its bounded,
source/proof/policy-bound checked cache. A cold process independently reconstructs
the reasons. Foreign policies, altered source bindings and malformed traces
cannot be used as a hit. Already checked pattern profiles can be consulted without
fresh probe acquisition; ordinary acquisition does not populate the new table.

Scouting charges a missing pattern state before computing its profile. Partial
or transient lookahead evidence survives even when no recursive pattern is
completed. A score is never a closure certificate. The existing pattern checker
and external split verifier still establish every reduction and both branch
obligations. The old persisted proof format is unchanged. Bank growth is governed
by the number and size of distinct scouted CNFs and their certificates; no bounded
closure or general compression guarantee is claimed.

All **331 relevant tests** pass. Tests cover cold reuse with byte-identical pattern
rows, the zero-state gate, tampered evidence/policies and absence of ordinary
bank writes. Independent validation checks the seed and eight result archives,
all 192 source-bound query records, and every stored bank proof with acquisition
disabled. All 2,996 inherited artifacts, 48 manifests and 171 earlier source files
remain unchanged; the 64 manuscript proof blocks are preserved. No new Lean
refinement theorem or SAT/UNSAT verdict is asserted.

The frozen protocol, seed history, all eight banks/histories and all unknown cases
remain in `experiments/results/cnf-lookahead-bank`. The older completed 42-input
checkpoint is still `cnf-transfer-split/checkpoint.json`, with null selection.
Use the new depth-zero seed to study the missing candidate pool; do not confuse
these 24 unknown coverage cases with the completed old stream. Copy result files
before rerunning validation, which regenerates its report.
