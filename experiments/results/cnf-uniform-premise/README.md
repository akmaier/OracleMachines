# Uniform completion of conditioned residuals

Optional completion of saved nonterminal premise screens, following
`cnf-positive-premise`. See
[`research/uniform-premise.md`](../../../research/uniform-premise.md) for the
argument, resource bounds, measurements, failure cases and next targets.

Seventeen exact-prefix contexts compare previous recovery with uniform
completion; the new nonterminal control is repeated in reversed order, for 36
arms. Case 14 of the earlier binary-probe stream changes from three acquired
nodes / 2,439 native bytes to one checked model node / 1,363 bytes. The other
sixteen contexts preserve their previous certificates.

Sixty fresh excluded queries give nine additional completions. Together with
three previous positive recoveries, all twelve gated-Horn inputs publish one
model each. New additions fall 452 -> 434 nodes and 535,908 -> 521,248 native
bytes; all modes answer 43 SAT / 17 UNSAT. There are 96 failed uniform checks.
Query differences have opposite signs; complete workers are faster in both
pairs, without a general scaling claim. Diagnostic sidecars grow about 2.83%.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_uniform_premise.py /tmp/new-uniform-premise
python3 experiments/validate_cnf_uniform_premise.py /tmp/new-uniform-premise
python3 experiments/analyze_cnf_uniform_premise.py /tmp/new-uniform-premise
python3 -m unittest solver.test_cnf_uniform_premise solver.test_cnf_positive_premise solver.test_cnf_binary_probe
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

The six production workers run serially in baseline/recovered/uniform order and
its reverse, without concurrent tests, builds or analysis. The baseline shares
the same native preparation. Labels never enter recognition. All 48 family
targets remain unfamiliar after preparation; all twelve neighbour controls
become known. Independent exhaustive truth checks and posthoc diagnosis are
outside production timings.

`protocol.json` freezes 518 source fingerprints. The posthoc analyzer is
additionally fingerprinted in `validation.json`. `report.json` binds all matched
reports; `attribution.json` independently audits 138 counter records and the
256-formula construction showing why rejection of both uniform completions
does not solve the remaining class. It also retains twenty mixed two-CNF
conditions: four source-checked positive models for fresh graph case 39 and
sixteen checked negative implication certificates for cases 43/51/55/59.
These SCC routes remain posthoc and are not counted as timed solving.

All 1,129 tests and 23 focused tests pass. The full suite retains 44 existing
unclosed-SQLite warnings; the focused tests have none. Independent reconstruction
checks every chronological prefix, certificate, support bank and persisted
record. The manuscript builds at 212 pages with all 64 proof blocks unchanged.

Resume through `checkpoint.json`: 24,444 native keys preserve all 23,987 earlier
payloads, with 216 new composed records alongside 3,581 inherited records,
2,957 ordinary decisions and six projections. Five alternate model payloads
occur fourteen times in the retained evidence; earlier payloads are not
overwritten. The preservation union uses 77,484,032 database bytes / 5,677,574
compressed bytes, including comparator evidence. Earlier 514 sources, 5,918
artifacts and 96 manifests pass preservation. Original structural coverage
remains 17/24. The causal and incremental-causal banks each gain one ready core;
the attribution records whether these refer to the same native result.

The newly ready entries are causal core 46 and incremental-causal core 51,
both pointing to the same 568-byte certificate acquired during ordinary
preparation for neighbour case 1 in every mode. This common acquisition changes
ready/pending counts to 87/89 and 87/116, respectively; it is not a benefit
attributed to uniform completion. The other banks remain 132/38 and 141/66.
