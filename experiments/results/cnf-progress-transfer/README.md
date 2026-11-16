# Progress-gate transfer and exact nonterminal joins

The unchanged gate and always-pilot policies both cover case 10, but need more
work than immediate commitment: 119 versus 106 new patterns and 778 versus 653
probes. Both switch to pivot 17 after the first route's unresolved literal mass
grows. Structural coverage rises from 16/24 to 17/24 in all three modes.

The more useful structural finding is four exact joins between the different
proofs: 39 new shared nodes, including 37 nonterminals. Their independently
checked 40-step subproof and full anchor keys are retained under `joins/`.
This is convergence within one original, not a measured cross-input saving.
See [analysis](../../../research/progress-transfer.md).

From the repository root, reproduce into fresh directories:

```sh
python3 experiments/compare_cnf_progress_transfer.py /tmp/cnf-progress-transfer-reproduction
python3 experiments/validate_cnf_progress_pilot.py /tmp/cnf-progress-transfer-reproduction
python3 experiments/analyze_cnf_route_joins.py /tmp/cnf-progress-transfer-reproduction /tmp/cnf-route-joins-reproduction
```

The worker, all three policies, budgets, orderings and validator are byte-identical
to the parent study. Only a transfer driver is added before measurement.
`protocol.json` binds the inherited policy, parent, original, sources and
acquisition-free preflight. `report.json` retains all six fresh-process streams.
`reconstruction.json` records independent full replay, original bindings,
query proofs, complete catalogs, immutable prefixes, shared budgets and cold
scheduling state. All old results and every exploratory result remain retained.

The post-hoc join analyzer is separately source-bound in `joins/report.json`
and `validation.json`; it is not part of the measured runtime source ledger.
It checks identical steps, boundary keys, disjoint new regions, no acquisition
and an independently verified positive subproof. It records raw row bytes,
not a claimed memory or runtime saving. A wrong SQL column name in its initial
byte-count query is preserved under `joins-initial/`; corrected analysis succeeds
without altering benchmark data or solver code.

The union has 2,443 patterns, 249 pairs, seventeen inherited missing children
and a 999-step structural coverage proof for seventeen originals. Seven remain
unknown. `next-discovery.json` binds case 7. The current research priority is to
test whether related, previously unseen inputs can reach the recorded joins
cheaply; direct whole-query reuse already handles this original.

`tests.txt` records 372 passing tests, with the exact command in
`test-command.txt`. `validation.json` also binds policy equality, repeated
identities, preservation and manuscript checks. `manifest.json` hashes every
artifact in this directory except itself. Preflight, tests, retrospective
validation and join analysis are outside operational timings.
