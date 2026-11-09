# A checked obstruction is not enough to choose the best split

Implementation/evidence checkpoint **d25a2e5**.

**Decision: retain this optional heuristic, do not promote it.** The 106 saved
unresolved leaves each receive one additional conditioning level in both modes,
with four conditioning candidates, four probe candidates and four learned-clause
slots. No generator label chooses a route. This is a diagnostic on old frontier
residuals, not a held-out corpus or new closure count for the original 985 sources.

| Measure | Existing ranking | Obstruction ranking |
| --- | ---: | ---: |
| Structurally closed inputs | 60/106 | 57/106 |
| Discovery/checking/persistence (s) | 4.96403 | 5.21714 |
| Total including ordinary solver/lifts (s) | 8.01565 | 8.01856 |
| Ordinary solver (s) | 3.03052 | 2.78776 |
| Cold complete replay (s) | 3.49873 | 3.53507 |
| Warm inventory replay (s) | 0.02674 | 0.02743 |
| SQLite bytes | 35,840,000 | 37,498,880 |
| Pattern nodes | 1,540 | 1,609 |
| Selected distinct unresolved leaves | 54 | 60 |
| Their literal occurrences | 13,755 | 15,948 |
| Four-case Python peak bytes | 2,902,681 | 2,823,818 |

The candidate gains cases **12, 22, 72**, but loses **4, 17, 26, 50, 75, 100**.
Discovery regresses **5.10%**; lower ordinary-solver time masks that regression in
total time. These are single sequential samples, not significance estimates.
Allocation covers cases 0--3 only and excludes native SQLite, RSS and full-corpus
peak. Both complete archives are retained; historical storage is not freed.

## Implementation and mechanism

The [algorithm/proof account](../../../research/obstruction-conditioning.md)
explains the source-linked auxiliary paths, whole-clause supports, fixed ranking,
source/policy identity, exact recomposition and conditional resource bounds.
Every OR node carries its independent certificate; checking never repeats SCC
search. The old four-candidate cap is unchanged. All 106 new ranking certificates
are exclusions, totaling 15,629 serialized JSON bytes. The full auxiliary pair
formulas are not stored. All 212 discovery/check ranking passes change the old
choice list; counters include both phases and must not be treated as distinct
source counts. All original SAT answers agree. No auxiliary exclusion is an
original UNSAT certificate.

The saved `mechanisms.json` compares the exact shared normalized source at each
changed first split. In every loss the previous winning variable is absent from
the new candidate set; in **five of six**, it lies outside the saved obstruction's
source-clause support. These are counterexamples to using that support as a
universal gate for useful conditioning, even though it supplies a valid invariant
for raw restriction into the single renaming class.

`influence.json` independently checks existing original-pass probe traces without
new propagation. In case 4, variable 6 occurs outside obstruction support
{1,4,5,9,10,11,13}. Its false probe forces 10=false and 5=true; its true probe
forces 7=false, then 1=true and 8=true. These closures damage three/four of the
four saved auxiliary edges, while direct restriction damages none. This is a
concrete reusable computation missed by direct-overlap ranking. Cases 17 and 50
have original traces that damage no saved edge; later discovery still closes
their branches. Missing traces for other changed candidates remain explicit.
Breaking one saved obstruction never proves that every obstruction is gone.

The existing production/research baseline stays at **898/985 non-tiny structural
coverage**, with 87 source misses. This experiment does not replace that policy or
claim additional original-source closures. The union of both frontier results is
63/106, but an efficient combined acquisition/replay policy is not implemented.
Next test already-proved propagation influence while retaining baseline diversity
and explanations across families, rather than repeating static overlap tuning.

## Validation and provenance

All **448 Python tests** pass. The seven new tests cover all saved frontier
certificates, the endpoint-only guard counterexample, raw-restriction preservation,
512 tiny trees, 90 random/edited models, capped fallback, old rows, cold replay,
forged evidence and restored source contexts. Cold checks verify all branches,
106 source bindings and 2,534 ordinary solver certificates per archive, leaving
both databases byte-identical. Warm replay inserts no rows. Lean sources are
unchanged: existing exact conditioning semantics apply, without a new refinement
or complexity claim.

The report retains cases, per-query records, selected frontiers, both archives,
allocation measurements and **81 code fingerprints**. Summaries retain regressions.
Mechanism and influence diagnostics bind the exact report and their own scripts
by SHA-256. Influence timing excludes loading/decompression/indexing and output
serialization; it is not an acquisition-performance claim. All measured discovery
costs include new recognition, checks, ranking, normalization and persistence.
Loading, summary walks, compression/hashing and initialization are excluded or
separately reported; cold/warm replay is separate.

```sh
python3 experiments/compare_cnf_obstruction_choices.py --frontier --output /tmp/obstruction-frontier
python3 experiments/analyze_cnf_obstruction_choices.py /tmp/obstruction-frontier
python3 experiments/diagnose_cnf_obstruction_influence.py /tmp/obstruction-frontier
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
