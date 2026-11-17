# Bounded partition screening: successful controls and a fresh regression

Resume `expanded-checkpoint.json`, which extends the separately preserved fresh
`checkpoint.json` with seven historical control discoveries. All 21,225 previous
native payloads remain unchanged; the final union has **21,482 keys**, occupying
**67,891,200 SQLite / 4,970,840 gzip bytes**. Retain the original ordinary catalogs,
200 earlier chains, eight earlier partitions, 192 new mixed decisions and six
historical control records. Composed source lookup requires checked sidecars;
a native source root need not exist.

The optional screen uses prepared overlapping cores with two/three missing
clauses, at most eight checked core reads and four forward/reverse plans.
It runs frozen unit propagation without SAT search, then reuses selected
forced-prefix/conflict traces to publish native certificates. Every publication
is checked by the unchanged native verifier. No optimal-cost guarantee follows
from terminal count, residual size or the candidate budget.

Historical exact-prefix controls select core 240 reverse for case 6, core 258
reverse for 68 and core 209 reverse for 135. New rows fall **41 -> 23** and native
payload **54,884 -> 32,763 bytes**. Nine trace publications replace expansion calls;
these publications and their verification remain real work. Case 135 rejects
its nearest two-clause plans before selecting a three-clause alternative, which
keeps seven rows and reduces their payload. The first control harness incorrectly
assumed all selected keys already existed. Its five completed arms, source and
failure log are preserved under `historical-controls/` and `controls-incomplete.txt`.
The complete rerun under `historical-controls-complete/` checks all six arms and
retains the seven new keys. This harness failure is not a SAT correctness failure.

The fresh matched study excludes all prior sidecar roots and native roots. It
uses 192 neighbouring CNFs from three templates, a fixed acquired bank and two
reversed-order pairs in separate processes. Both arms agree on every answer,
including 94 SAT cases. No tests, builds or profiles overlap production. Full
cold replay, preparation, publication, serialization and compression are charged;
original bank acquisition remains an inherited cost. Peak process RSS is recorded
but does not isolate live solver memory.

Only fresh case 176 reaches partition screening. Its unsplit target already
has a unit conflict, yet the selector still examines four plans and accepts two
terminal branches. Expansions fall **27 -> 26**, but rows increase **247 -> 249**
and native payload **495,506 -> 499,414 bytes**. Combined child/screen propagation
literal visits rise **8,190 -> 12,369**, plus 68 trace-check visits. Mean query time
increases 1.243 -> 1.306 seconds. Complete means 14.225 / 14.178 seconds establish
no stable total-speed or live-memory gain. Keep the selector optional.

Next, reuse a terminal unsplit trace before partition discovery. Then inspect
fresh cases 43 and 172, accounting for 19/26 remaining expansions after an accepted
extra guard, a stage this policy never screens. Case 70 adds four expansions.
Restore exact pre-query prefixes; do not substitute the union, which already
contains these answers. `cost-attribution.json` retains all paired timings,
per-phase metrics, counterexamples and remaining expansion cases.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_partition_screen.py /tmp/new-partition-screen
python3 experiments/validate_cnf_partition_screen.py /tmp/new-partition-screen
python3 experiments/analyze_cnf_partition_screen.py /tmp/new-partition-screen
python3 experiments/check_cnf_partition_screen_controls_complete.py /tmp/new-partition-screen
python3 experiments/finalize_cnf_partition_screen.py /tmp/new-partition-screen
```

The earlier incomplete control producer is retained for failure reproduction;
it is not required for the complete workflow. The runtime protocol binds 439
sources. The final ledger includes four post-hoc files, for **443 sources**.
`previous-decisions.json` is a compact exclusion-root list; the original complete
catalogs remain bound by the parent checkpoint and are independently replayed.
Every fresh trial retains its full native archive, first-query records, warm
lookups and cold audit. Historical arms retain strict-prefix digests, all native
deltas, composed records, screening traces and costs. Full trial archives retain
any alternative proofs; the unions preserve earlier payloads by priority.

All **1,042 full-suite tests**, fourteen focused tests and all **512 two-variable
CNFs against independent truth tables** pass. The full suite retains 44 earlier
unclosed-SQLite ResourceWarnings; focused tests emit none. Independent validation
reconstructs guard and plan choices from each exact pre-query state, checks every
native proof, rebuilds partition branches without the producer and verifies
warm lookup without fresh solving. All 2,957 ordinary inherited decisions replay;
final cold replay checks 406 composed records. The complete controls are historical
evidence, not fresh-query generalization.

All four frontier lineages pass. Ready/pending counts are **131/39 original,
138/69 legacy, 81/95 causal and 81/122 expanded causal**. Origins and catalog
bindings stay unchanged; readiness increases through the preserved acquisitions.
Structural authority stays 2,614 patterns / 259 pairs / 17 missing children;
original 17/24 / 999 and supplemental 24/24 / 208 remain separate. The final
checkpoint changes only parent/union/source bindings from the previous authority
and adds four fields for fresh and control study records.

All **435 prior sources / 4,762 artifacts / 83 manifests** pass preservation.
The paper builds to **204 pages**, preserving all **64 prior proof blocks**, with
no overfull/undefined/LaTeX warnings. This milestone adds no Lean theorem,
unrestricted-SAT polynomial guarantee, new arbitrary-CNF class or stable
memory/runtime improvement claim. See [the analysis](../../../research/partition-screen.md).

New manifest: **81 artifacts**. Next preservation audit: **4843 artifacts / 84 manifests**.
