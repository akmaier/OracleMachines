# Clause overlap, mask pilot and preserved negative controls

This follow-up measures reusable immutable clauses across different residuals,
after whole-source identity indexing failed. Runtime checkpoint: `c7914b5`.
The original pilot predates that checkpoint and binds its exact runtime files by
hash. The two later matched controls bind the checkpoint and runtime fingerprints.

- `overlap.json`: sources 1194 and 1441, starting separately from the old prepared
  archive. FIFO clause identity hits are 228,432/324,855 and 172,963/245,241
  positions (70.32% and 70.53%). The observer also records exact clause values and
  fixed-position blocks of 4, 8 and 16 clauses. Its retained identity/value/block
  sets are unbounded analysis state; no time or memory saving follows from them.
- `pilot.json`: scan then mask on sources 1194, 1441 and 1471. Roots, profiles and
  summaries agree. Discovery times are 1.13617/1.12317, 0.90508/0.90426 and
  0.14570/0.14739 seconds. These fixed-order single samples establish no speedup.
- `analysis.json`: derived forward/reverse control totals and explicit limits.
  Both orders reduce reconstruction literal work 55.10% but increase query time
  2.58% and 3.58%. Four-case peak Python memory increases about 41%.
- `validation.json`: binds both reports, all four complete compressed archives,
  diagnostic scripts, runtime fingerprints, manuscript and PDF. Non-reconstruction
  counters and stored evidence match exactly, not just SAT answers. Observer
  FIFO hits, admissions, preparation and evictions match the actual pilot cache.
- Validation logs: all 496 Python tests and the unchanged Lean audit pass (4,148
  declarations / 1,988 theorems). All 63 old manuscript proof blocks are unchanged,
  and all 224 labels are unique. The PDF builds without layout warnings.
- `visual-review.json`: changed pages 127--129 rendered and inspected, with no
  clipping, overlap or malformed notation.

Complete matched control archives are preserved in
[forward](../cnf-clause-mask-empty/README.md) and
[reverse](../cnf-clause-mask-empty-reverse/README.md). They are byte-identical
after decompression, and every cold replay leaves its database unchanged.
The default implementation is unchanged. The mask candidate stays optional and
disabled. No full prepared-corpus rerun was justified; the historical 902/985
result is not a new measurement for this candidate.

Reproduce diagnostics into new files:

```sh
python3 experiments/measure_cnf_clause_overlap.py /tmp/clause-overlap.json
python3 experiments/probe_cnf_clause_mask.py /tmp/clause-mask-pilot.json
```

The [mechanism record](../../../research/clause-mask-reuse.md) gives exact cache
bindings, mask-collision handling, resource bounds and next priorities. Broader
checked variable elimination and equivalent-core discovery now take precedence
over another scalar clause cache. No new structural coverage, unrestricted SAT
bound or Lean refinement is claimed.
