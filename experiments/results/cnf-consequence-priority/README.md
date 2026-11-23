# Checked cofactor priority before one late binary consequence

See [the interpretation](../../../research/consequence-priority.md),
`protocol.json`, `analysis.json`, `next-target.json` and the sealed
`checks.json`/`manifest.json`.

The optional policy reuses the earlier two-polarity cofactor probe only when
broader binary discovery selects a single later-ranked consequence, distinct
from the ordinary split candidate. A checked refutation selects the surviving
ordinary cofactor; misses retain the preceding policy. First-ranked singles and
two-consequence batches retain joint behavior. Existing proof formats/checkers
remain unchanged. The recognition rule is heuristic, not an optimum guarantee.

Six new edits take 71 / 63 / 57 expansions under one-target / joint / priority.
Priority saves 4.54% query time and 3.91% native payload versus joint, and 3.34%
query time versus one-target. Controls remain 0.80% slower than one-target.
The useful exposed branches retain identical joint proof bytes. Case61 recovers
baseline-identical native proof bytes, including evidence for the following query.
Compilation outside the ordinary expansion counter remains charged.

Reproduce in a separate directory:

```sh
mkdir experiments/results/cnf-consequence-priority-reproduction
python3 experiments/probe_cnf_consequence_priority.py experiments/results/cnf-consequence-priority-reproduction
python3 experiments/compare_cnf_consequence_priority.py prepare experiments/results/cnf-consequence-priority-reproduction
python3 experiments/compare_cnf_consequence_priority.py experiments/results/cnf-consequence-priority-reproduction
python3 experiments/analyze_cnf_consequence_priority.py experiments/results/cnf-consequence-priority-reproduction
python3 experiments/profile_cnf_consequence_priority.py experiments/results/cnf-consequence-priority-reproduction
python3 experiments/validate_cnf_consequence_priority.py experiments/results/cnf-consequence-priority-reproduction
```

Finish serial timing before profiles, tests and cumulative audits. The frozen
comparison has 15 targets, 54 workers and 90 attempts. Every target already
closes as UNSAT under the baseline, so there is no new decision coverage cell.
The case61 single-selected diagnostic is exposed; all its proofs are checked
and retained. Supplied donors/maps and prior acquisition remain sunk.

Both readers recheck the cumulative 76,003 native records, prior extensions and
306 partition records. All 1,478 full and 186 focused tests pass; the full suite
emits 43 unclosed-SQLite warnings and the focused suite none. All 64 proof blocks
remain unchanged; the 243-page manuscript builds without warnings. The source
ledger has 771 entries. There is no new Lean refinement theorem.

The next largest query still becomes slower than joint despite fewer expansions.
Investigate repeated conditioned structure and causal support in its remaining
six-expansion branch. In `next-target.json`, use the `novel` observation at query
position 1, acquisition index 4: 125 variables, 257 ternary clauses, 60 binary,
one unit, 892 literal occurrences, 242 remaining budget. Restore its bound prefix
plus only its 42 earlier native IDs from the bound trial delta. Replay the prior
stream for warm pools. The final union contains answers and must not seed
comparisons. Unfinished diagnostic frames are marked separately from rejected
candidates; reporting errors are retained without altering frozen timed samples.
