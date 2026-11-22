# Bounded binary target rankings

See [the research account](../../../research/ranked-binary-targets.md) for the
soundness argument, resource bounds, comparison and limitations.

`protocol.json` freezes the source hashes, three policies, two opposite orders,
historical prefixes and six novel edits before timed solving. `inspection.json`
records the read-only census motivating the policies. The isolated branch uses
`branch-prefix.json.gz`, containing only the saved prefix and five pre-branch
publications. Other trials reference the preceding immutable prefix archives.
No trial is seeded from the final cumulative union.

Each worker directory retains query traces, native proof deltas, partition
sidecars, warm results and restoration/replay measurements. `analysis.json`
keeps individual attempts and paired order changes, including regressions.
`validation.json` independently checks chronological proof availability and
replays cumulative authority with both readers. `checkpoint.json`, `checks.json`
and `manifest.json` bind the preserved results and source ledger.
`next-target.json` saves the replacement branch's exact pre-branch state and a
dependency census showing that its regression is not explained simply by losing
the original policy's one reused previous-query proof.

Reproduce from the repository root into a new directory:

```sh
python3 experiments/compare_cnf_ranked_binary_targets.py prepare /tmp/oracle-ranked-repeat
python3 experiments/compare_cnf_ranked_binary_targets.py /tmp/oracle-ranked-repeat
python3 experiments/analyze_cnf_ranked_binary_targets.py /tmp/oracle-ranked-repeat
python3 experiments/diagnose_cnf_ranked_binary_targets.py /tmp/oracle-ranked-repeat
python3 experiments/validate_cnf_ranked_binary_targets.py /tmp/oracle-ranked-repeat
```

Use the preserved protocol for exact input comparisons. The policies are
experimental process-local replacements of native discovery inside the existing
probe/partition wrapper. They do not change the general affine solver default,
automatically supply donors or maps, or prove efficient unrestricted SAT.
