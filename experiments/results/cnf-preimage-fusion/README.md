# Fused canonical preimages for causal support

See [the analysis and invariant](../../../research/preimage-fusion.md),
`protocol.json`, `analysis.json`, `repeat-report.json`, `next-target.json`, and
the sealed `checks.json`/`manifest.json`.

The optional serial method shares untouched checked clause tuples and uses
order-preserving variable compaction to map selected child positions directly
to their first parent representative. It retains the full child-key comparison
and unchanged native checking. No new inference, memo, proof format, default or
SAT coverage cell is added. Every paired native delta and partition is identical.

The initial two-order comparison saves 5.53% on controls and 5.65% on new-edit
query means. Six additional balanced repeat pairs, including mode setup, save
6.32% and 4.49%. One new-edit pair regresses; the zero-hit isolated branch has
noisy timing in both studies. Complete-worker means barely change (+0.27% /
-0.16%). Persistent storage and checked-object endpoints do not shrink. The
traced kernel-allocation probe is neither process RAM nor full-query memory.

Reproduce in a fresh directory:

```sh
mkdir experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/probe_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/compare_cnf_preimage_fusion.py prepare experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/compare_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/analyze_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/profile_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/repeat_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
python3 experiments/validate_cnf_preimage_fusion.py experiments/results/cnf-preimage-fusion-reproduction
```

Keep timings serial and finish them before running tests or cumulative audits.
The profile was used to assess the initial no-hit control before freezing the
supplemental repeat protocol; repeated timings are posthoc on exposed inputs.
The main comparison has 15 targets, 36 workers and 60 attempts. The repeats add
36 aggregate samples, 84 restored streams and 156 attempts. Earlier donor/map
selection and acquisition remain sunk. All failed/noisy observations are retained.

`validation-first-failure.log` preserves a reporting failure after replay: a local
extractor variable shadowed the new-record counter. The validator now uses
separate names and supports rerunning its unsealed union archive. The final
validation reruns the audits; frozen kernels, cases and timed samples were not
changed to repair this bookkeeping failure.

For the next experiment use `next-target.json`'s `novel` observation at query
position 0, acquisition index 2: 125 variables, 259 ternary and 56 binary clauses,
889 literal occurrences, remaining budget 247 and three earlier native IDs.
The target was absent. Restore only the bound prefix and those IDs from its
trial delta; replay the preceding probe and branch for warm pools. The final
union contains answers and must not seed comparisons. Census repeated conditioned
sources and proof reasons in `force_all`/`excluded_context` before trying a bounded
handoff. Preserve every native check and full-CNF recomposition obligation.

Validation: both readers replay 76,102 native records, all retained extension
records and 322 partition records. Earlier payloads are preserved. All 1,488
full and 196 focused tests pass; the full suite emits 43 unclosed-SQLite warnings
and the focused suite none. The 243-page manuscript builds without warnings and
retains all 64 prior proof environments byte-for-byte. The source ledger has 780
entries. No new Lean refinement theorem is claimed.
