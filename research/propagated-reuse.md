# Check the propagated residual before trying new premises

The optional selector now reuses a checked answer exposed by unit propagation
before it ranks new premises. At the exact saved prefix of case 85, propagation
visits fall from 5,750 to 955. A further 192-query comparison finds no successful
new residual reuse. It preserves that negative result and the lookup overhead;
the change is not a general runtime improvement.

## Recognition and publication

The existing known-target, syntactic-family and tautological-source priorities
remain unchanged. Otherwise, propagate once. After a nonempty forced prefix,
normalize the residual and check its native root. An existing checked answer is
accepted; a missing constant, two-CNF, Horn or dual-Horn residual is also accepted
when the required native leaf solver is enabled. The retained unit trace binds
the residual to its source. Existing checked publication reconstructs a SAT model
or links a negative child certificate. There is no new proof format.

A known residual adds at most one target row and performs no child expansion.
A missing recognized residual adds at most a leaf and target row and performs
at most one native leaf expansion. These bounds concern this path after earlier
preparation. They do not bound trace size, dependency checking, canonicalization,
serialization or cold reconstruction. Requiring a nonempty forced prefix ensures
strict progress before this additional lookup. Unknown nonfamily residuals keep
the old ranking, premise probes and admission/fallback behavior.

## Equal-state controls

Twenty-one arms compare native baseline, previous admission and propagated
reuse at seven exact prefixes: historical 43/70/172, older fresh-baseline
144/167/190, and preceding fresh-stream 85. Prefix restoration is shared outside
the timed arm; all arm deltas, records and cold checks are retained.

| Case 85 measure | Baseline | Admission | Propagated reuse |
| --- | ---: | ---: | ---: |
| New native rows | 1 | 1 | 1 |
| Added native bytes | 1,672 | 1,672 | 1,672 |
| Propagation literal visits | 955 | 5,750 | 955 |
| Premise probes | 0 | 4 | 0 |
| Expansion calls | 1 | 1 | 0 |
| Explicit trace publications | 0 | 0 | 1 |

The 23 forced variables expose the already checked positive binary root
`cnf-residual-v1:[[-2,-1]]`. The new route avoids 4,795 visits (83.39% against the
previous gate). Zero expansion calls still include trace publication and the
same retained result. The other six controls preserve the previous gate's
native payloads and propagation counts, including its rejection of useful
historical 43/172 guards. Across all seven controls, visits are
10,277 / 19,701 / 14,906: eliminating this regression does not eliminate all
discovery overhead. Single arm times establish no stable runtime bound.

## Another excluded stream

The frozen generator selects 64 double-deletion neighbours of each of three
existing templates, excluding 1,152 earlier query roots per template and every
native root. Catalogue selection costs 1.663 seconds separately. Six fresh
workers run baseline/admission/propagated, then the reverse order. Tests,
profiles and builds do not overlap production. Warm replay acquires no rows.
All policies answer 99 SAT and 93 UNSAT queries.

| Measure | Baseline | Admission | Propagated reuse |
| --- | ---: | ---: | ---: |
| New native rows | 215 | 199 | 199 |
| Added native bytes | 469,640 | 445,570 | 445,570 |
| Expansion calls | 37 | 11 | 11 |
| Explicit trace publications | 0 | 10 | 10 |
| Propagation literal visits | 9,528 | 14,907 | 14,907 |
| Mean query/warm sidecar bytes | 5,499,953.5 | 5,667,500 | 5,674,299 |
| Mean query seconds | 2.432 | 1.959 | 1.842 |
| Mean full cold replay seconds | 13.001 | 13.639 | 12.760 |
| Mean complete worker seconds | 27.071 | 28.277 | 28.119 |

The new path never activates on this set. Both admission policies produce
identical native payloads and propagation counts. The sixteen-row reduction
against baseline belongs to the existing gate. Additional residual lookup and
family scans remain charged, and sidecars grow another 6,799 bytes (0.12%).
Complete-time differences against admission are -2.304 and +1.987 seconds;
their opposite signs and substantial setup/cold variation support no stable
speedup. Process peak RSS averages 502/564/564 MB, not a live-state bound.
SQLite bytes are 71,483,392 / 71,434,240 / 71,434,240; compressed bytes are
5,159,931 / 5,155,317 / 5,155,317. The inputs remain neighbours of old templates,
not new general structural authority or arbitrary-SAT coverage.

## Next gaps: retained traces and small conditioning sets

Two rejected proposals account for all eleven remaining child expansion calls:

| Fresh case | Saved forced variables | Exposed variables / clauses / literals | Child expansions |
| --- | ---: | ---: | ---: |
| 36 | 13 | 11 / 23 / 49 | 5 |
| 186 | 1 | 24 / 64 / 176 | 6 |

Both exposed roots are absent and outside the recognized syntactic families.
Fallback currently repeats propagation of a source for which discovery already
holds a checked unit trace. The next concrete candidate is to reuse that prefix
even after a failed lookup or rejected guard, then solve the unknown residual.
Its residual search cost remains unrestricted. No avoided-work estimate here
has been executed or timed as a fallback improvement.

A read-only structural diagnostic also finds that case 36's three clauses wider
than two all contain canonical variable 6. Assigning either value leaves only
clauses of width at most two. The artifact retains both restrictions and checks
their source equivalence on all 2,048 full assignments. Exhaustively checking the
eleven single-variable candidates costs 1,078 literal visits in this diagnostic;
case 186 has no such candidate (24 candidates, 8,448 visits). A future selector
could recognize this restricted decomposition, charge its discovery and compare
checked two-branch acquisition against the current proof. No row or timing saving
is claimed for this unexecuted route, nor a bound on conditioning size in general.
Cold replay remains the largest measured complete-time component; shared checking
and compact source references remain supporting total-cost targets.

## Validation and resume point

All 1,085 tests and 21 focused tests pass, including 512 forced mixtures in two
representations, cached positive/negative residuals, model lifting, native leaf
admission, no-hit fallback and corrupted traces. Independent validation rebuilds
the 21 control prefixes, regenerates the fresh catalogue, checks each selection
and certificate, and replays all results cold without acquisition.

Resume `experiments/results/cnf-propagated-reuse/checkpoint.json`: 22,259 native
keys, all 22,036 previous payloads preserved, 597 new composed records alongside
1,230 earlier composed records, 2,957 ordinary decisions and six projections.
There are no alternative payloads. All 483 prior sources, 5,222 artifacts and
90 manifests are unchanged. Ready/pending frontiers remain 132/38, 140/67, 84/92
and 84/119. Original and supplemental structural authorities are unchanged.
The evidence union uses 71,503,872 database bytes and 5,163,292 compressed bytes;
it retains all arms, rather than describing one policy's working storage.
No new Lean theorem or unrestricted-SAT efficiency claim is established.
