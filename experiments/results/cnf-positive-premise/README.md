# Positive-premise model recovery

Optional saved-screen recovery, following `cnf-binary-probe`. See
[`research/positive-premise.md`](../../../research/positive-premise.md) for the
argument, bounds, measurements and remaining gaps.

The selected saved case 50 replaces three acquired nodes / 2,503 native bytes
with one model node / 1,482 bytes. Thirteen older controls retain their exact
certificates. Thirty control arms include case 50 in both policy orders.
Sixty new excluded queries contain two further positive-premise successes,
cases 26 and 54. Fresh additions fall 410 -> 406 nodes and
472,534 -> 469,867 native bytes. All modes answer 44 SAT / 16 UNSAT.
Query time decreases in both matched comparisons; complete-worker differences
have opposite signs. Diagnostic sidecars grow slightly. This is neither an
arbitrary-SAT result nor a general end-to-end speedup.

## Reproduce

Run from the repository root, with a new output directory:

```sh
python3 experiments/compare_cnf_positive_premise.py /tmp/new-positive-premise
python3 experiments/validate_cnf_positive_premise_replay.py /tmp/new-positive-premise
python3 experiments/analyze_cnf_positive_premise.py /tmp/new-positive-premise
python3 -m unittest solver.test_cnf_positive_premise solver.test_cnf_binary_probe solver.test_cnf_positive_child solver.test_cnf_trace_fallback
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

The six production workers run serially in baseline/filtered/recovered order
and its reverse, with no overlapping tests, builds or analysis. The baseline
uses the same inherited preparation and native solver. Family labels are
metadata. Targets are excluded from inherited native and decision roots;
49 remain unfamiliar after preparation. Exhaustive small-family truth checking
runs after timing and is not an efficient solver feature.

`protocol.json` freezes 512 source fingerprints. The posthoc analyzer and
corrected replay validator are additionally fingerprinted by `validation.json`.
The first frozen validator stopped on a reused temporary directory in the
repeated case-50 control; `validator-initial-failure.txt` preserves that failure.
The replay revision changes only that temporary pathname and its explanatory
docstring. No timed implementation, protocol or measurement was changed.

`report.json` binds the control and fresh reports; `attribution.json` audits
135 recovery/filter counter records. `reconstruction.json` records independent
prefix, certificate, persistence, union and inherited-bank checks. The
checkpoint retains previous native payloads; alternate valid model payloads
remain in the measured deltas and archives. Old payloads are never overwritten
to create an apparent storage saving. All 1,120 tests and 31 focused tests pass.
The full suite retains 44 existing unclosed-SQLite warnings; the focused suite
has none. The manuscript builds at 212 pages with its 64 proof blocks unchanged.

Resume through `checkpoint.json`, and use the current priority record to work
on checked acquisition and transport of nonterminal conditioned families.

The validated union contains **23,987 keys**, preserving all 23,577 prior native
payloads, with 210 new composed records and 3,371 inherited composed records.
Ordinary decisions (2,957), projections (six), structural authorities and all
four support frontiers remain checked and unchanged. Three distinct alternate
model payloads occur six times in the measured evidence and remain preserved.
The union is 76,537,856 database bytes / 5,571,577 compressed bytes. Earlier
508 source fingerprints, 5,780 artifacts and 95 manifests pass preservation.
