# Stop premise discovery at a checked positive completion

The optional inline policy moves uniform completion into the bounded premise
probe loop. It reuses the canonical formula, propagation assignment and residual
that the current probe has just computed. Once a full source model passes
verification, it stops discovery and publishes the ordinary native model node.
The previous late-completion policy remains the matched comparator.

## Recognition, stopping and correctness

For each eligible assumption, propagate once. A conflict follows the existing
negative-guard path. Otherwise scan the residual for the two uniform witnesses:
all-false works exactly when every clause contains a negative literal; all-true
works exactly when every clause contains a positive literal. If either works,
combine that completion with the freshly forced values, transport through the
premise and target variable maps, and check every clause of the raw target plus
assumption. Native model publication independently checks the target again.
This full source check is the trust boundary; correctness does not depend on
trusting a propagation trace merely because it was produced in memory. Saved
traces are independently reconstructed after timing.

The ranking, candidate cap and residual binary-incidence filter remain the same.
Only the prefix through the first valid positive model or negative guard is
executed. Candidates beyond a positive stop remain unexamined: they are not
reported as failed probes or filter skips. A model may now preempt a later guard
or a different positive-terminal model. Both answers are sound, but selected
routes and native model payloads need not agree. Old persistent payloads remain
unchanged and alternate witnesses remain in the evidence.

A failed uniform check is inconclusive. On misses, it adds a residual scan;
there is no all-input runtime dominance. The negative binary filter can still
omit positive opportunities, and neither mixed two-CNF acquisition nor negative
parent recomposition is added by this change. The general-SAT embedding into
the uniform-miss cell from [the previous study](uniform-premise.md) still applies.

## Incremental cost

Let k be the eligible probes the old selector would execute, and j <= k the
prefix executed here, assuming the same input and retained state. Every
nonconflicting actual attempt adds O(R_i) sign recognition for residual literal
length R_i. The first accepted model adds O(n+L) variable transport and raw
source checking, for n active variables and L literal occurrences. Canonical
binding, restriction and unit propagation from that attempt are reused directly;
completion does not canonicalize or reconstruct the premise a second time.
Compared with late completion, early success avoids all discovery for the
remaining k-j attempts and the late trace-reconstruction pass. It can also
avoid a later guard's child lookup/probe. The added checks on unsuccessful
prefixes remain charged, including situations where a later guard would have
prevented the old late wrapper from attempting completion at all.

These are expected dictionary-operation counts with integer widths and full-key
construction charged separately. The extra live assignment/residual/model uses
O(n+L) words; each attempted completion adds one constant-size diagnostic
record. Earlier screens already retain their own keys and unit traces, which
can take O(j(L+n)) words overall. Early stopping can reduce that retained
prefix, but it does not bound total solver state, arbitrary-SAT acquisition,
archive census, serialization or inherited replay. No new polynomial bound for
arbitrary CNF, Lean theorem or native proof schema is claimed.

## Validation and measurements

The tests include first-model stopping, terminal and nonterminal residuals,
preemption of a later known-child guard, unchanged negative/positive-child
routes, candidate caps and filter omissions, mandatory raw-source verification,
forced-prefix transport and cold persisted reuse. An exhaustive finite check
covers 1,024 clause subsets in two coordinate systems (2,048 comparisons), with
independent truth enumeration. Seventeen saved-prefix contexts, sixty excluded
fresh selections and an eight-query worker with full inherited cold replay
pass preflight. Production workers run serially in baseline / late uniform /
inline order and its reverse. The baseline shares native preparation. Family
labels and generator parameters never enter recognition. The complete workers
charge setup, preparation, query work, warm checks, full inherited cold replay,
serialization and compression. Independent truth enumeration and attribution
run after production.

### Fresh matched stream

The new sixty-query stream excludes all inherited query roots. It contains
48 unfamiliar family targets and twelve neighbours already known after shared
preparation. Every mode returns 42 SAT and 18 UNSAT answers. The two policies
publish thirteen models: twelve gated-Horn targets and one graph-colouring
target. The policy changes discovery work, not this stream's solved coverage.

| Cost across sixty queries | Native baseline | Late uniform | Inline completion |
| --- | ---: | ---: | ---: |
| Actual premise probes | 0 | 190 | 106 |
| Discovery/acquisition propagation visits | 75,216 | 171,670 | 109,554 |
| New native nodes | 478 | 446 | 446 |
| New native payload bytes | 578,201 | 556,237 | 556,240 |
| Expanded nodes | 466 | 421 | 421 |
| Mean query seconds | 0.41409 | 0.45709 | 0.42358 |
| Mean complete worker seconds | 23.24643 | 23.24245 | 23.40440 |
| Mean full cold replay seconds | 11.34532 | 11.31054 | 11.46130 |

Early stopping removes 84 probes (44.21%) and 62,116 propagation visits
(36.18%). Gated-Horn discovery falls from 94 to twelve probes and from 72,205
to 10,484 propagation visits, an 85.48% reduction. The graph family avoids two
more probes and 395 propagation visits. Its acquisition still costs 11,452
propagation visits. Random three-CNF and coupled parity perform no premise
probes under the binary filter and still pay 56,622 acquisition propagation
visits combined. Those unresolved costs are unaffected.

Selection normalization falls from 80,200 to 31,510 literal occurrences and
serialized full keys from 300,907 to 119,042 bytes. The new policy performs
106 sign checks: thirteen successes and 93 misses. It scans 3,469 residual
clauses / 7,423 literal occurrences, transports 210 accepted model variables
and checks raw target/assumption payloads containing 3,259 literals. These
charges replace the late completion's rebuilding work; the original discovery
and native model verifier remain accounted separately.

Query time falls 7.33%, with paired differences -0.02810/-0.03894 seconds.
Complete workers instead rise +0.16477/+0.15913 seconds. Cold replay rises
+0.11334/+0.18817 seconds and dominates the much smaller query difference.
This establishes less discovery work and a query gain on the measured stream,
not an end-to-end improvement or a general scaling result. Native baseline is
still slightly faster on queries than either discovery policy.

Diagnostic query/warm sidecars fall about 11.16%, from 1,973,313/1,973,314 to
1,753,113/1,753,155 bytes. Trial SQLite size stays 78,442,496 bytes; compressed
size changes only 5,783,144 -> 5,783,142 bytes. Native payload grows three bytes
across four alternative valid models with different Boolean serializations.
Mean process RSS is 749.920 -> 749.781 MB, a negligible two-run difference.
Thus the memory saving is in retained discovery diagnostics, with no meaningful
native-state or process-memory reduction. The preservation union additionally
retains comparator results and all historical payloads.

### Remaining targets

Posthoc analysis checks thirteen mixed two-CNF model conditions on this run's
fresh graph cases 15/27/39/51. Each model is transported and checked against its
raw target plus assumption. Current parent acquisition totals fourteen nodes /
6,163 bytes. Integrate these models using the live residual, then charge SCC
solving, transport and verification in a matched comparison. The same audit
checks fifteen contradictory implication paths on cases 43/47/55/59; parent
acquisition there totals 54 nodes / 75,511 bytes. These negative conditions
still require parent recomposition. All SCC work is posthoc, outside timed
acquisition. Keep the previous uniform study's case 39 and cases 43/51/55/59
as additional historical controls; those IDs refer to a different corpus.
Positive opportunities outside the negative binary filter
and the larger arbitrary-CNF interaction problem remain open. On the current
stream, random three-CNF plus coupled parity now dominate acquisition work
with 329 new native nodes.
Full inherited replay dominates complete worker time; any incremental replay
proposal must preserve the existing independent full audit as its comparator.

Evidence and reproduction:
[`experiments/results/cnf-inline-completion/`](../experiments/results/cnf-inline-completion/).

## Preserved checkpoint

All **1,137 tests**, 24 focused tests, 276 independent counter audits and
full reconstruction pass. Resume `experiments/results/cnf-inline-completion/checkpoint.json`:
**24,922 native keys**, preserving all 24,444 prior payloads, with 216 new
composed records alongside 3,797 inherited records, 2,957 ordinary decisions
and six projections. The union uses 78,471,168 database bytes / 5,788,630
compressed bytes. Alternate certificates for eight roots remain in fifteen
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116; no frontier activation is attributed to this change. Original structural
coverage stays 17/24 and supplemental positive coverage 24/24. All 519 prior
sources, 6,073 artifacts and 97 manifests remain unchanged. The manuscript
builds at 213 pages with all 64 existing proof blocks unchanged.
