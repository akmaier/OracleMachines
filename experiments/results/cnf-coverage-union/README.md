# Full historical corpus: source-bound policy union

The new positive certificate checks **1,497/1,497 historical inputs**, including
**985/985 non-tiny cases**, without new acquisition. It binds each source to either
the original retained policy or the expanded policy; their configurations remain
separate. Both fresh-process repetitions pass for full-history and standalone replay.
See the [research record](../../../research/full-corpus-coverage.md).

Mean process time is **46.48527 s** with historical restoration and **11.22907 s**
from the self-contained **11,271,594-byte compressed bundle**. This is prepared
proof replay, not unseen-input discovery or SAT-solving time. Historical acquisition
and old archives remain paid resources. The bundle adds storage and does not
replace the expansion checkpoint. Peak RAM is unmeasured.

After duplicate roots are collapsed, the earlier successful set shares **67
nonterminal steps**, reaching eighteen variables. The two policy proofs share only
**20 exact family steps**, each at most three variables. Larger components in edit
families are the next candidates for measured transfer to unseen inputs.

Reproduce into a fresh directory:

```sh
python3 experiments/compare_cnf_coverage_union.py /tmp/cnf-coverage-union-new
python3 experiments/analyze_cnf_coverage_union.py /tmp/cnf-coverage-union-new
python3 -m unittest solver.test_cnf_coverage_union
```

`claims.json` is the independent ordered claim; `coverage-union.json.gz` carries
only replay data. `proof-parts.json.gz` supplies the same positive proofs for the
full-history control. Four worker logs retain both repetitions. `report.json`
binds the producer sources and reports costs. `sharing-findings.json` records
independently cross-checked ownership after duplicate canonical roots are collapsed.
`validation.json` and `manifest.json` preserve source and artifact fingerprints,
checks and manuscript validation. The original cases are development data, not a
fresh holdout. All **306 tests** pass; no unrestricted-SAT efficiency claim follows.
