# Pilot: select learned clauses at the same retained budget

9 November 2026. Thirteen previous source misses were selected by the frozen
closure study's implication frontier. Both modes use depth two, four arbitrary
conditioning choices, four probe variables per pass and at most four retained
learned clauses. The new policy enumerates up to sixteen proved candidates,
then greedily ranks newly activated saved closures, a new origin assumption,
total activation, and original order. Selection and checking costs are charged.
Inputs carry no generator labels into recognition.

| Mode | Closed / 13 | Total seconds | SQLite bytes | Cold seconds | Nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving | -- | 0.49373 | 2,928,640 | 0.13192 | -- |
| First four clauses | 0 | 7.74651 | 22,786,048 | 3.51560 | 1,684 |
| Activation and diversity | 1 | 7.88838 | 22,851,584 | 3.58444 | 1,696 |

The gain is original source **1024**, a satisfiable `probe_invalidation` input
labelled `guard_32`. Its selected unresolved remainder previously had 272 literal
occurrences. All thirteen original decisions agree with the unchanged independent
solver. The new selected plan closes one source, but increases total time by
about 1.83% and SQLite by 0.29%. Do not generalize the selected pilot to coverage
or performance on arbitrary inputs.

Discovery is 7.29644 -> 7.45429 s. Logical node bytes are 12,113,212 -> 12,154,642;
source bytes 89,695 -> 89,617. The first-three-case Python peak is 10,213,449 ->
9,663,178 bytes, excluding native SQLite/RSS and full-corpus peak. Candidate
selection accounts for 12,454 assignment entries, 36,250 delta literal visits
and 8,492 greedy score evaluations across discovery and repeated checks.
All three archives cold-replay byte-identically; warm reuse adds no records.

All original proofs precede selection. Every candidate is a consequence of the
original source under a saved assumption; choosing a subset preserves model
sets independently of ranking. Active additions and fresh assumptions still
use full propagation. Support reduction remains required before acquiring a
child; an unsuccessful batch remains recorded and does not recurse by itself.
A score predicts local activation, not whole-source closure or optimal cost.

These are single sequential synthetic samples without concurrent tests/builds.
The full comparison and local fixed-choice controls are recorded separately in
[the complete study](../cnf-learning-selection/README.md). The pilot's positive
and negative outcomes remain preserved. To reproduce, use a new destination:

```sh
python3 experiments/compare_cnf_learning_selection.py --pilot --output /tmp/new-selection-pilot
```
