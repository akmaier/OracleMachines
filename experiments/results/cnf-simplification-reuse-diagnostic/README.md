# Simplification-check reuse diagnostic

`report.json` observes the unchanged checker at commit `7eb2c56` on twelve fixed
sources. All roots, profiles and summaries match the previous full study. Input
report and observer hashes are recorded. The observer retains source/clause
objects and serializes exact keys, so it makes no timing or memory claim.

Across 12,209 checks, 2,649 exact source/certificate/policy combinations repeat.
There are 669,809 repeated clause-object positions out of 1,003,961 positions,
but only 594 repeated whole-source object calls. This motivates clause-level
sharing over a whole-source identity cache. Simulated LRU budgets are diagnostic;
they do not charge implementation guards, serialization or result decoding.

The [subsequent experiment](../../../research/single-pass-checking.md) preserves
the unsuccessful support-cache attempt and selects direct one-pass reconstruction
with lazy copies instead. No structural coverage change follows from this observer.

Reproduce against the recorded commit's checker (with this observer present):

```sh
python3 experiments/analyze_cnf_simplification_reuse.py /tmp/new-check-reuse-diagnostic
```
