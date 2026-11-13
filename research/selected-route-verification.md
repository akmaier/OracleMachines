# Replay the selected positive coverage proof

The current checkpoint contains 593 explicit proof steps for 58 covered roots
among 83 reused development inputs. Previously, replay first reconstructed every
external route, including unsuccessful alternatives and unused probe prefixes.
The new `cnf_selected_routes.verify_selected_plan` loads only external records
named by this proof and their required dependencies. It uses the existing route
validators and the unchanged recursive inventory checker. No coverage, SAT
answer or stored solver result changes.

## Required evidence and scope

Selected coupled eliminations still require their checked first pivot. Ordinary
continuations still require every complete clear predecessor, and learned
continuations require their exact learning base and clear prefix. Saved splits
still verify both polarities, referenced unit reasons and exact child transports.
Affine routes retain their source-bound certificate. The finite proof checker
still rejects missing premises, cycles, duplicate steps and foreign roots.

A source/configuration-bound key is an index, not a substitute for checking its
payload. Every fresh replay starts with empty verifier caches. The experiment
binds the claimed roots to the actual original CNFs and configuration, disables
new recognition/probing/learning/affine discovery, and makes SQLite read-only
through `PRAGMA query_only=ON`. Reuse within one verifier assumes the same
immutable snapshot; changed evidence needs fresh checking. All five sidecar lists
are indexed, and that preparation is included in the selected arm.

This interface returns a **positive-only subset**, not a complete discovery
catalog. Missing routes say nothing about their validity or availability. In
particular, do not use absence from this subset to declare an original uncovered,
an expansion impossible, or a formula UNSAT. An unrelated malformed route can
be ignored by positive replay while a full catalog check rejects it; the tests
exercise that distinction. Archive preservation and complete-history audits
remain separate obligations.

## Matched cold comparison

Both arms replay the same certificate and the same 58 roots from the same
reconstructed database. Each starts with fresh Python verifier caches. The full
arm reconstructs all external routes; it does not audit every inventory node.
The execution orders are selected/full and then full/selected. Operating-system
caches are not flushed, and two repetitions do not provide a confidence interval.

| Work or retained payload | All external routes | Selected external routes |
|---|---:|---:|
| First cold replay, seconds | 36.01545 | 29.68143 |
| Second cold replay, seconds | 35.43063 | 31.02749 |
| Mean, seconds | 35.72304 | 30.35446 |
| Recursively checked pattern nodes | 11,514 | 10,258 |
| Node JSON payload, bytes | 100,554,675 | 88,614,890 |
| Pattern key payload, bytes | 30,735,716 | 27,263,272 |
| Exposed external routes | 657 | 56 |
| Checked ordinary continuation blocks | 133 | 25 |
| Checked learned continuation blocks | 156 | 26 |
| Checked learning contexts | 39 | 10 |

Mean cold replay falls **15.03%** in these measurements. The selected path avoids
1,256 checked pattern nodes and 11,939,785 bytes of node JSON payload. These are
logical retained payload counts, not Python heap, RSS or peak RAM. The 593-step
proof actually requires **10,258 nodes**, including **9,665** beyond its explicit
steps. It still checks 76,208 saved probe attempts and performs 86,328
simplification checks. These counters describe different operations and must
not be added as disjoint costs.

Selected route lookup reads 64 indexed SQL records totaling 333,267 payload bytes;
referenced trace reads and recursively checked inventory data are additional.
Warm replay of the already checked proof takes 0.00455--0.00491 seconds with the
selected catalog, versus 0.00703--0.00739 seconds with the complete catalog. Those
warm figures exclude cold verification and sidecar preparation.

The complete experiment takes **157.46531 seconds**, including four cold arms,
**20.91352 seconds** of checkpoint restoration, root binding, dependency
accounting, warm controls and persistence. This is not directly comparable with
the prior 271-second expansion pipeline, which also checks open originals,
audits the full archive, acquires new structure and replays reference proofs.
The new helper is available for positive replay; the older expansion runners
remain unchanged. No full-pipeline speedup has yet been measured.

SQLite remains byte-identical at **770,338,816 bytes / 41,758 pattern nodes**.
All previous deltas, sidecars and reference results remain intact. New diagnostic
files record the checked-key sets and measured counters; there is no new solver
state or smaller disk archive. The selected dependency set is a strict subset
of the full comparator's set and is identical across repetitions.

## Remaining cost and next experiment

The main remaining cost is inherited internal checking. Loading one inventory
node verifies its profile, stored alternatives, summaries and recursive children;
a `base` step can hide a whole checked plan. The additional 9,665 nodes therefore
cannot simply be discarded or labelled redundant. Measure which are required by
an expanded successful semantic proof and which support only historical policy
or losing alternatives. A standalone positive checker would need exact source
and configuration bindings, checked primitive transformations, both conditioning
children, valid component recomposition and every retained-plan premise. Its
certificate size and checking cost must be measured before claiming a bound.

In general, the cost depends on sidecar indexing, the selected external prefix
closure, the recursively checked inventory dependency set, each node's checking
work, and the finite proof scan. The explicit step count alone bounds none of
these inherited costs. This improvement establishes neither a compact closure
for all CNFs nor a polynomial unrestricted-SAT algorithm.

The discovery frontier is unchanged. Resume
`experiments/results/cnf-reused-branch/report.json` with
`continue_cnf_reused_branch.restore_checkpoint` and retain all five evidence
lists **(1, 42, 156, 11, 1)**. Case 30 still has the **23-variable / 93-clause**
leaf, with saved pairs **5, 6, 11, 13** and next ordinary block **7, 9, 16, 17**.
Compare a bounded block with those saved splits while sharing one admission
allowance. This verification study is not a new discovery checkpoint.

## Reproduction

Run `python3 experiments/compare_cnf_selected_routes.py OUTPUT_DIRECTORY`.
The matched cold arms use the independently established full-route validators
and reject any new discovery. The new tests cover selected and omitted records,
both branch obligations, missing children, configuration changes, corrupt and
missing ordinary/learned prefixes, foreign sources and malformed proofs. The
47-test suite passes, and the manuscript builds with all 64 existing proof blocks
unchanged. The report, dependency sets, test results, manuscript check and hashes are retained
under `experiments/results/cnf-selected-routes/`.
