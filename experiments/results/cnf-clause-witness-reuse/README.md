# Checked SAT witness publication before fresh search

On twelve constructed clause deletions, witness publication plus the existing
UNSAT guard reduces fresh reference expansions 427 -> 59 relative to the guard
alone. Six published query certificates make 65 new stored rows. Complete time
falls 50.39%; all 388 tests and cold replay pass. See
[analysis](../../../research/clause-witness-reuse.md) for costs and limitations.

Reproduce into a fresh directory from the repository root:

```sh
python3 experiments/compare_cnf_clause_witness_reuse.py /tmp/cnf-clause-witness
python3 experiments/validate_cnf_clause_witness_reuse.py /tmp/cnf-clause-witness
python3 experiments/screen_cnf_witness_rotation.py /tmp/cnf-clause-witness
```

The frozen protocol binds the unchanged 613-node seed and previous acquisition
cost. Three balanced fresh-process triples compare ordinary, guarded and witness
modes, each with a repeated visit. Every arm archive and query sidecar survives.
Cold replay disables fresh search and checks all certificates and source bindings.
The ordinary and guarded database bytes match the preceding study.

`checkpoint.json` preserves the full structural authority and both coverage
catalogs. Its `reference_union` contains all 1,169 distinct keys from earlier
and new reference histories; `reference_decisions` binds twelve replayable
answers. The previous `reference_study` remains bound and `witness_reuse_study`
adds this experiment. Alternate valid certificates remain in trial archives;
the union preserves the earlier payload on an overlapping key.

`rotation-screen.json` preserves seven post-hoc one-variable rotation attempts,
their failures, and two checked SAT witness proposals for absent roots. They
are candidates for the next experiment, not newly published cache rows or a
measured rotation speedup. Structural coverage remains 17/24 originals, with
separate supplemental coverage 24/24; no arbitrary-SAT efficiency result follows.
