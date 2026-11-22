# Native probe before six-clause partitioning

See [the research account](../../../research/probed-support-partition.md) for
recognition, budgets, proof obligations, results, regressions and the next target.
This is an optional supplied-candidate residual pilot. All nine targets already
finish under the affine baseline; no general SAT coverage theorem is claimed.

- `protocol.json` freezes five arms, two opposite orders, the expansion budgets,
  source fingerprints, exact seeds, cases and limitations.
- `prefix-*.json.gz` includes the old historical prefix plus the preceding
  experiment's first addition proofs. Deletion results and later work are excluded.
- `cases.json` contains three exposed boundary targets and six new edits whose
  roots were absent from the cumulative union when the protocol was frozen.
- `boundary-*` / `fresh-*` retain worker measurements, chronological queries,
  proof deltas, checked partition sidecars and warm results.
- `analysis.json` includes paired costs, each branch's expansion count, probe
  retention and read-only proof dependency reachability. Reachability does not
  by itself attribute a runtime saving to reuse.
- `next-branch.json` binds the dominant 61-expansion branch and exact pre-branch
  state: its seed plus five rows selected from the bound trial delta. The target
  root is absent. The diagnostic performs no search or publication.
- `union/`, `union-partitions.json`, `checkpoint.json` preserve cumulative native
  authority and new checked compositions. Previous partition sidecars remain
  referenced through the inherited checkpoint fields.
- `validation.json`, `checks.json`, `manifest.json` record independent replay,
  source/artifact preservation, tests, manuscript build and hashes.

The combined policy improves aggregate query time, but a fresh deletion regresses
from 65 to 86 expansions. Complete-time differences are small, sidecar storage
grows, and warm setup plus lookup regresses. The general affine baseline stays
in place. Initial test fixture failures and their source are retained in
`initial-tests/` and `development-tests.log`; the kernel was unchanged by the fix.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_probed_partition.py prepare /tmp/oracle-probe-repeat
python3 experiments/compare_cnf_probed_partition.py /tmp/oracle-probe-repeat
python3 experiments/analyze_cnf_probed_partition.py /tmp/oracle-probe-repeat
python3 experiments/analyze_cnf_probed_partition.py /tmp/oracle-probe-repeat next
python3 experiments/validate_cnf_probed_partition.py /tmp/oracle-probe-repeat
```

Use the preserved `protocol.json` when comparing against these exact trials.
Do not seed a new experiment from the final union when measuring these targets:
their later answers are already present there.
