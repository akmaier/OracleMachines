# Residual binary-incidence filtering

See [the measured analysis](../../../research/binary-probe.md) for the proof
scope, matched costs and next reuse targets. This optional selector omits a
single-assumption unit-refutation probe only when its unassigned variable has no
binary incidence after consistent baseline unit propagation. Original ranking
and candidate budget are retained without replacement. Publication and native
SAT/UNSAT checking remain unchanged.

Twenty-six exact-prefix arms preserve all thirteen earlier controls. All native
payloads, composed records and selected results remain identical; no historical
probe can be skipped, so scan/report overhead remains visible. Six fresh workers
run baseline/previous/filtered and reverse order on 60 additional excluded roots:
48 new-family inputs and twelve old-template neighbours. Forty-nine targets are
unfamiliar after preparation. All modes answer 43 SAT / 17 UNSAT and add identical
450 native rows / 521,286 native bytes; warm replay adds no rows.

Filtering skips 192/386 probes, reduces discovery/acquisition propagation
252,999 -> 179,463 (29.07%), and query/warm sidecars 2.346 -> 1.991 MB (15.13%).
It scans 3,020 clauses and 1,252 binary literals and transports 287 names.
Native proof storage is unchanged. Timing pairs establish no stable query or
end-to-end gain; mean complete time regresses 21.947 -> 22.234 seconds. Cold
replay remains the largest component, and native baseline does less work.

Posthoc inspection finds a valid complete target model in case 50's discarded
positive premise screen. Direct publication is the next unimplemented/unpriced
reuse target. Eighty-nine conditioned residuals across twenty queries belong
to syntactically recognized families; these are not 89 solved queries. Signed
binary incidence could also omit 83 remaining probes / 28,774 visits. That
refinement is not enabled in this comparison and must remain scoped to negative
unit probing rather than rejecting useful positive witnesses.

All **1,113 tests**, 24 focused tests and independent reconstruction pass.
Resume `experiments/results/cnf-binary-probe/checkpoint.json`: **23,577 native
keys**, all 23,127 earlier payloads, **206 new composed records**, 3,165 earlier
composed records, 2,957 ordinary decisions and six projections. No alternate
payloads are needed. The union occupies 75,649,024 database bytes / 5,474,412
compressed bytes. Ready/pending banks remain 132/38, 141/66, 86/90 and 86/117.
Prior 503 sources / 5,655 artifacts / 94 manifests, structural authorities and
all 64 manuscript proof blocks remain unchanged. The 211-page paper builds
without overfull or undefined warnings. No new Lean theorem or unrestricted-SAT
resource bound is claimed.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_binary_probe.py /tmp/cnf-binary-probe-reproduction
python3 experiments/validate_cnf_binary_probe.py /tmp/cnf-binary-probe-reproduction
python3 experiments/analyze_cnf_binary_probe.py /tmp/cnf-binary-probe-reproduction
python3 -m unittest solver.test_cnf_binary_probe solver.test_cnf_positive_child solver.test_cnf_propagated_reuse
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

The runtime protocol freezes 507 sources; final validation adds one posthoc
analyzer for 508. The independent checker reconstructs historical prefixes and
fresh availability, regenerates the excluded catalogue, checks every skipped
screen and selected proposal, and replays native/composed certificates, all
support lineages and structural authorities without acquisition. Independent
exhaustive bitset truth tables check the 48 small new-family formulas after
timing; this exponential oracle is not part of the solver. The full suite emits
44 existing SQLite ResourceWarnings; focused tests emit none. All old results,
unsuccessful screens, alternative candidates and counterexamples remain saved.

New manifest: **125 artifacts**. Next preservation audit: **5780 artifacts / 95 manifests**. Final source ledger: **508**.
