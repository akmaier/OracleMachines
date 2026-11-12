# Bounded elimination: opportunity, structure and validation

This record accompanies the [99-leaf comparison](../cnf-variable-elimination-frontier/README.md)
and [83-original-source comparison](../cnf-variable-elimination-originals/README.md).
All are saved prior unresolved inputs, not a new holdout or a full-corpus rerun.

`raw-opportunity.json` extracts 99 selected unresolved leaves and their 83 source
origins from the previous full prepared archive. The initial scan finds 81 leaves
with a non-growing candidate within the 64-pair cap, 71 with mixed candidates and
55 with pure candidates; the latter groups overlap. `initial-opportunity.py` is
the exact original observer, with script/report hashes in `initial-provenance.json`.
It has a fixed output destination: reproduce in an isolated checkout or change
that destination rather than overwriting retained evidence. The observer itself
did not repeat the entire historical archive audit. `initial-pilot.json` is an
early in-memory diagnostic with no captured exact runtime fingerprint, before a
model-validation tightening; it is not the final persistence or total-cost result.

`structure-reuse.json` comes from the read-only
[`analyze_cnf_variable_elimination.py`](../../analyze_cnf_variable_elimination.py).
It hashes all six completed archives, counts accepted elimination types and exact
target references, and examines every variable in the remaining selected frontier
under the pair cap. On original inputs, 1,123 accepted steps are pure, 1,588 have
one occurrence on one side and 111 have multiple occurrences on both sides.
The 2,822 elimination edges reach 2,821 distinct targets; this is little exact
target sharing, not evidence of large temporal cache savings. Of 59 open selected
leaves, 58 have pair-bounded candidates but none has a current non-growing step.
Ten would admit one after omitting resolvents implied by a retained source clause.
That is a candidate opportunity, not a new checked policy or closure.

```sh
python3 experiments/analyze_cnf_variable_elimination.py /tmp/bve-structure-new.json
```

`validation.json` records report/runtime fingerprints, archive hashes, SQLite
integrity, equal ordinary-solver residual tables, closure counts and containment,
the unchanged 63 manuscript proof blocks, 225 unique labels and final paper hashes.
The accompanying `tests-validation.txt`, `lean-validation.txt` and
`latex-validation.txt` preserve the actual check output. Python passes 501 tests;
Lean builds and audits 4,168 declarations / 2,004 theorem declarations. The new
Lean result is semantic projection, not a refinement of the Python implementation.
`visual-review.json` binds manual inspection of the rendered changed pages to the
final PDF. Complete cold audits and independent endpoint/model checks live in
the two comparison reports, separately charged from query acquisition. In
particular, the 2,822-edge original-input model diagnostic costs 688.09686 seconds.

The bounded policy closes 29 original misses, 18 beyond pure-only, while total
query time rises 64.76503 -> 80.09857 seconds. It remains optional. Next profile
failed candidate analysis, test cheaper sufficient admission, and certify
retained-clause subsumption. Preserve ordering regressions and measure fresh
transfer before promoting a policy. No general polynomial SAT bound follows.
