# Checked signed equivalence from paired probe traces

9 November 2026. The optional policy closes seven additional old source cases,
but raises total acquisition and replay cost on the full comparison. It remains
an analysis layer; the independent decision solver is unchanged.

## Rule and exact composition

After the unchanged failed-literal and common-consequence phases are clear,
intersect each false-branch unit set with the negation of its true-branch set.
The first nonempty intersection defines a signed block around the probe
variable. A low consequence -y and high consequence y imply y=x; opposite
signs imply y=not x. Choose the smallest block member as representative and
record the sign of every member, including the representative's positive self
map. Substitute **every clause**, preserving all interactions and leftovers.
The normal child edge removes tautologies/duplicates and records compact names.
The arbitrary conditioning depth does not change.

The checker replays every assumption and unit reason against the exact source,
checks the earlier priorities, first pair, full map, strict support reduction
and exact child identity. Lifting composes the child renaming and signed map;
representatives that vanish during normalization can receive arbitrary values.
All lifted models must satisfy the full source. A source edit gets a new
identity; deleting a reason clause can invalidate the old implication. The
versioned policy can coexist with old records without overwriting them.

For retained variables Y, the child G satisfies `G(y) iff exists h, F(y,h)`.
Case splitting proves the block relations in every parent model. Under those
relations, literal substitution preserves evaluation in every clause. Conversely,
a child model extended by the recorded signs satisfies every parent clause.
Inconclusive probes alone do not prove equivalence or SAT. Recognition overlaps
remain in the profile; this is a checked reduction, not a new tractable class.

This is established equivalent-literal reasoning. Li (2003), *Equivalent literal
propagation in the DLL procedure*, Discrete Applied Mathematics 130(2), 251--276,
studies propagating equivalents to simplify CNF. [Publisher](https://doi.org/10.1016/S0166-218X(02)00407-9).
Heule et al. (2005), *March_eq*, pp. 345--359, describe integrated equivalence
reasoning and both positive and negative cost effects. [Author PDF](https://www.cs.cmu.edu/~mheule/publications/35420345.pdf).
Our implementation and resource experiment do not make the underlying rule new.

## Matched results

All 1,101 old inputs remain. The 36 additions are 24 fresh seeded random 3-CNFs
(eight each at 20, 32 and 48 variables) and twelve growing-component, signed and
edited controls. All modes use the same source order; generator labels never
select routes. Both inventories use depth two, four conditioning candidates and
four probe candidates. Ordinary solving still runs on every original source.
The 512 exhaustive two-variable sources are separated from non-tiny counts.

| Mode | Closed / 625 non-tiny | Fresh / 24 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Solving alone | -- | -- | 10.65714 | 40,939,520 | 2.28096 | -- |
| Common-consequence baseline | 567 | 18 | 38.29300 | 130,596,864 | 15.20846 | 9,584 |
| Signed equivalence | 574 | 18 | 39.73059 | 135,569,408 | 15.85644 | 9,952 |

Gains: old cases **799, 879, 931, 933, 962, 1021, 1048**. All seven are SAT;
799/931/933 are an original and two variants, not independent random gains.
No baseline closure is lost on this corpus. Old non-tiny coverage is 537/589 ->
544/589. All twelve new controls close under both depth-two policies; the small
fixture separately changes from unresolved to recognized at depth zero. Fifty-one
non-tiny inputs remain unresolved, including six new random cases.

The smallest indirect fixture is `(-4,-2,-1), (-3,1), (-2,4), (2,3)`.
It entails 2=not 1 and 3=1, reducing four clauses/nine occurrences to `(1,4)`.
Among all 624 acquired equivalence nodes, immediate children include 93 recognized
families, two component splits, one projection, 144 further probe rewrites,
123 OR nodes and 261 unresolved nodes. These include unselected alternatives;
they must not be reported as 93 new source closures.

The [16-source pilot](../cnf-probe-equivalence-pilot/README.md) selected the old
sources whose chosen unresolved path had an indirect equivalence opportunity.
It closes seven and slightly reduces time/storage. The larger full study
preserves that coverage gain but reverses the cost conclusion. Do not use the
post-selected pilot to claim general runtime improvement.

## Runtime, storage and memory

Discovery rises 27.77853 -> 29.08758 s; total time rises about 3.75% and database
bytes about 3.81%. Warm inventory replay rises 0.14485 -> 0.29462 s. These are
single sequential samples, without a significance estimate or industrial
comparison. Times include recognition, discovery, checking, serialization,
persistence, original-source solving and successful root lifts. Generation,
truth tables, summary walks, initialization, compression and later profiling
are excluded. Cold audit checks every alternative and source binding plus all
ordinary solver certificates. Both modes retain exactly 8,430 solver residuals.

There are 624 equivalence rewrites and 1,145 merged variables across nodes.
All **431** equivalent-parent CNF/depth pairs shared with the baseline retain
identical attempt lists. No new probe is requested at those parents. Nevertheless,
total attempts rise 37,049 -> 41,039 and checked attempts 74,647 -> 87,573 because
the reduced states lead to further acquisition. Conditioning candidates fall
2,232 -> 2,063. Selected unresolved literals fall 10,300 -> 9,674.

Logical node bytes rise 50,062,370 -> 52,575,330. Probe nodes alone occupy
32,136,270 bytes; signed witness JSON is only 25,670 bytes. Changed descendant
collections, full keys/profiles and the additional version identity all count.
Exact-source bytes rise 3,469,302 -> 3,681,921. All attempts, including unsuccessful
ones, remain in the archives. Smaller rewritten CNFs do not imply smaller total
persistent state.

A separate six-case allocation diagnostic (799, 875, 879, 931, 933, 1061) gives
Python peaks 14,564,269 -> 11,586,228 bytes, a 20.45% reduction. This targets
selected old cases and excludes native SQLite, RSS and full-corpus peak. It does
not contradict the larger full-corpus database. It is also a different diagnostic
subset from the preceding common-consequence study.

Let k be the probe cap, v occurring variables and L literal occurrences.
Opposite intersections take expected O(kv) set work plus O(v log v) sorting.
Full substitution visits all L occurrences; raw output has at most L occurrences.
The signed witness uses O(v log(v+k+2)) bits. These are additions to probe
acquisition/checking (scan-based O(k(v+1)L + v log v)), normalization, recognition,
serialization and archive work. One merge chain has at most v-1 steps, but the
number of distinct acquired alternatives remains unbounded by a polynomial.
Signed renaming can change heuristic ordering, so universal bounded-policy
coverage monotonicity is not asserted.

## Remaining interaction and next experiment

There are 77 selected distinct unresolved nodes with 9,674 literal occurrences.
The largest remaining discovery case is still 1061, a 48-variable old source:
0.96542 s main discovery versus 2.96676 s under a separate profiler. Restriction,
unit checking/propagation, normalization and literal helpers dominate own time.
Occurrence-driven scans and shared checked rewrite chains are supporting work.

Saved traces at 70 selected leaves already imply **552 node/binary-clause pairs**
absent explicitly in their parent. Of these, 176 have at least one reason of
width three or more in that parent. The separate binary-graph diagnostic removes
333 as already reachable implications; **219 lack a binary implication path**,
on **47 selected nodes affecting 37 of the 51 missed source paths**. This is
not a claim of semantic nonredundancy: other reasoning, including an inconsistent
binary subformula, may entail them. No extra clause is inserted in this run.

Next test bounded local learning from these checked reasons. Begin with the
remaining source cases listed in `implication-boundaries.json`, especially 1061.
Retain exact assumption/reason dependencies, remove duplicates and charge binary
redundancy tests, extra propagation, growth in clauses, checking, persistence and
cold replay. A proof-preserving clause addition can still increase runtime and
storage. Measure selected-path closure and total cost before enabling it globally.
The opportunity counts neither solve these sources nor establish small exact
classifications for arbitrary SAT.

## Checks and reproduction

All **333 Python tests** pass (27.90 s), including exhaustive two-variable fibers,
negative/transitive blocks, disappearing representatives, mixtures, signed
renaming, deleted reasons, invalid lifts, omitted/forged maps, cold corruption
and policy coexistence. Three new full archives, three pilot archives and three
preceding full archives replay byte-identically. The previous results remain
unchanged. Three named Lean lemmas prove signed-substitution evaluation, the
opposite-assumption implication and SAT preservation under explicit hypotheses.
The full build/audit passes at **4,101 declarations / 1,957 theorem declarations**,
including generated declarations. These do not refine Python, SQLite or costs.

`report.json` retains sources, fingerprints, counters and timings; `summary.json`
aggregates them. `mechanisms.json` retains gains, losses, remaining nodes and a
separate profile. `implication-boundaries.json` distinguishes explicit absence
from binary-path redundancy. Gzipped SQLite snapshots retain full witnesses and
all attempted alternatives. Reproduce using a new destination:

```sh
python3 experiments/compare_cnf_probe_equivalence.py --pilot --output /tmp/new-equivalence-pilot
python3 experiments/compare_cnf_probe_equivalence.py --output /tmp/new-equivalence-study
python3 experiments/analyze_cnf_probe_equivalence.py /tmp/new-equivalence-study
python3 experiments/analyze_cnf_implication_opportunities.py /tmp/new-equivalence-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
