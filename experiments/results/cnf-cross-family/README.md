# Unfamiliar family transfer

See [the measured analysis](../../../research/cross-family.md) for family costs,
limitations and the next candidate filter. Four matched workers compare native
baseline after shared preparation with the existing optional discovery policy.
There is no new solver policy in this study.

All 48 new-family CNFs remain unfamiliar after preparation. Twelve new neighbour
roots become known. Each query's familiarity is independently checked against
its chronological prefix. The solver receives only CNFs; construction labels
are analysis metadata. Independent exhaustive bitset truth tables check the 48
small formulas after timing; the twelve larger controls use retained native and
composed proof checks. The four finite generators are not a SAT taxonomy.

Both modes answer 44 SAT / 16 UNSAT, add identical 398 native rows / 483,695
native bytes, and reuse them warmly without publication. Optional discovery
adds 384 unsuccessful probes: propagation grows 65,842 -> 246,726 and mean query
time 0.354 -> 0.482 seconds. Both paired differences are positive. Cold replay
still dominates complete time. All traces and counterexamples remain saved.
The posthoc audit identifies 192 probes / 73,488 propagation visits that a
residual binary-incidence condition could exclude. That filter is not enabled
or timed here. It excludes only impossible single-assumption unit refutations.

All **1,106 tests**, 12 focused tests and independent reconstruction pass. The
new checkpoint is `experiments/results/cnf-cross-family/checkpoint.json`:
**23,127 native keys**, all 22,729 old payloads, **120 new composed records**,
3,045 previous composed records, 2,957 ordinary decisions and six projections.
There are no alternate native payloads. The union occupies 74,706,944 database
bytes / 5,364,377 compressed bytes. Ready/pending banks remain 132/38, 141/66,
86/90 and 86/117. All earlier 498 sources, 5,617 artifacts and 93 manifests
are unchanged. Structural authorities and all 64 manuscript proof blocks remain
unchanged. The 209-page manuscript builds without overfull or undefined warnings.

Reproduce into a new directory from the repository root:

```sh
python3 experiments/compare_cnf_cross_family.py /tmp/cnf-cross-family-reproduction
python3 experiments/validate_cnf_cross_family.py /tmp/cnf-cross-family-reproduction
python3 experiments/analyze_cnf_cross_family.py /tmp/cnf-cross-family-reproduction
python3 -m unittest solver.test_cnf_cross_family solver.test_cnf_positive_child
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

The 502 runtime source fingerprints freeze preparation, generation, acquisition
and validation. Final validation adds the posthoc analyzer for 503 total sources.
Prior native payloads, ordinary/composed decisions, six projections, all support
lineages and original/supplemental structural authorities are replayed without
acquisition. The 120 new composed records cover both modes' first repeats; all
four native archives are retained, and the checkpoint keeps the prior decisions.
The full test suite emits 44 existing SQLite ResourceWarnings; focused tests
emit none. No new Lean theorem or unrestricted-SAT resource bound is asserted.

New manifest: **38 artifacts**. Next preservation audit: **5655 artifacts / 94 manifests**. Final source ledger: **503**.
