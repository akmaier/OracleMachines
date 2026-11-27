# Checked witnesses from signed choices

Checkpoint: 27 November 2026. A constructive choice proposal closes the edited
`hole10` control with a complete SAT assignment. On the **already exposed**
external panel, original coverage remains **24/25**, while derived controls rise
**11/12 → 12/12**. The aggregate is 36/37, not 37 independent external inputs.
No previous verdict is lost. This is an exploratory follow-up to
[capacity cores](capacity-core-certificates.md), not a fresh external holdout.

A new matched comparison against the previous capacity/expansion pipeline lowers
mean complete cost **25.55132 → 23.38105 seconds (8.49%)**. All four paired signs
are favorable. Discovery, validation, persistence and warm/cold replay are
charged. One input remains unanswered, and there is no general fallback solver;
this is not total time to solve every input or a fresh-CDCL comparison. Production
defaults and all previous certificates remain unchanged.

## Extracting choices, retaining all source obligations

The proposer reuses the existing native augmenting-path matching helper. It tries
two fixed greedy selections of variable-disjoint source clauses: width at least
three, then all nonempty clauses, ordered by decreasing width and literal tuple.
Each selected variable has one signed choice literal. No labels, filenames or
publisher answers reach the algorithm.

Binary clauses of the form (¬a ∨ ¬b), for selected choice literals a,b, supply
conflict edges. Connected conflict components become candidate resources. A
matching chooses one literal per demand and at most one per component. Unselected
signed choices are set false, selected choices true, and other source variables
false. This constructs a complete assignment on the raw source's variable set,
including variables occurring only in tautologies.

**Connected is weaker than clique.** Treating a whole component as capacity one
can impose stronger restrictions than its clauses. It is safe for proposing a
model, but may discard valid assignments. Failed matching therefore grants no
UNSAT authority. A successful matching is also only a proposal: clauses outside
the selected structure can reject it. The checker validates the complete variable
list, Boolean values and **every original clause** before accepting SAT. Duplicate
clauses, tautologies, mixed signs and constraints sharing selected variables keep
their full verification obligations. Malformed input is rejected.

The certificate is an ordinary complete model, not a trusted structural label.
Cold replay checks it without matching or discovery. Reuse after edits requires
checking the complete current source and its variable support again; neither a
cached matching nor a prior satisfied-clause list can authorize a changed input.
There is no new persistent matcher cache or arbitrary-isomorphism mechanism.

For each proposed graph, D*E reserves an upper bound on the unchanged matcher's
edge visits, where D is its number of demand vertices and E its number of
demand/resource edges. The two attempts share an allowance of 300,000 reserved
visits. Input scans, sorting, graph construction, copies, checking and storage are
outside this allowance but included in timing. The 37-input run reserves 119,627
visits and records 2,303 actual matching edge visits. These are not total primitive
operation counts or unrestricted resource bounds.

## A useful classification boundary

For a fixed extracted structure, three cases have different obligations:

| First-attempt category on this panel | Inputs | Meaning |
| --- | ---: | --- |
| Strict signed choices | 6 | Every normalized clause is a selected demand or a conflict exclusion, and every conflict component is a clique. |
| Fully represented nonclique choices | 5 | The clause syntax is covered, but capacity-one components strengthen its actual exclusions. |
| Choices with unclassified clauses | 26 | Additional source constraints still interact with the proposed choices. |

In the strict class, signed variable flips give disjoint positive demand clauses
and complete exclusion cliques. Satisfiability is equivalent to a matching that
covers every demand: any satisfying assignment supplies distinct resource
representatives, and a covering matching supplies a model. This is the signed
form of the repository's existing restricted matching method, not a new
unrestricted SAT reduction. The new gate still routes failed matching to the
existing portfolio rather than introducing another UNSAT proof authority.

For nonclique components, selecting compatible representatives is a stronger
interaction problem than matching to capacity-one components. On the five fully
represented nonclique inputs, all choices collapse into one connected resource;
these are nevertheless SAT according to their already checked baseline witnesses.
An explicit six-variable path-conflict example independently demonstrates this
false-negative behavior. Thus syntax coverage alone is not a tractability claim.

These categories are disjoint outcomes of the fixed first extraction, not
canonical semantic SAT classes. Other extractions or prior recognizers can
overlap. The remaining clauses and nonclique interactions are explicit, and the
unrestricted remainder is not assumed easy. The gate's only new authority is a
complete source witness.

## The newly certified edit and the surviving original

The edited `hole10` has 110 variables and 560 clauses. Its first extraction has
eleven demands and eleven components, but some components are not cliques and
**ten clauses remain unclassified**. The complete proposed model satisfies all
560 clauses with ten variables true. Its JSON wrapper is **2,644 bytes**. It also
satisfies the formula after restoring the deleted first exclusion, so the literal
edit alone suffices for this particular SAT witness. The same assignment fails
the original unedited formula; that failure is not a separate UNSAT proof.

All other 36 gated certificate payloads are exactly equal to the corresponding
baseline payloads. Every baseline payload equals the earlier capacity checkpoint.
The new hit previously had no verdict, so this panel has no overlap with prior
SAT authority. The earlier synthetic 182/182 union remains separate and intact.

Only `uf50-01000.cnf` remains unresolved. Both choice attempts select fifteen
disjoint ternary demands over 45 variables, leaving **203 clauses outside the
extracted structure**. They produce the same complete assignment, which violates
**26 of the 218 source clauses**. Both rejected candidates, the exact violated
clause indices and the unchanged incomplete baseline proof are retained. These
assignments are explicitly not SAT certificates. Publisher labels do not close
this remaining case.

## Measured workflow and checks

Four paired process orders compare the new gate with the unchanged previous
pipeline. Both arms use the same outer certificate wrapper. Every warm and cold
pass reloads JSON and reparses the source; verified-operator banks start empty
per phase. Operating-system caches are not flushed. Startup, final metadata and
independent audits are additional. The timing includes failed proposals on all
other inputs and subsequent fallback to the previous structural pipeline.

| Metric | Previous pipeline | Choice gate |
| --- | ---: | ---: |
| Complete seconds | 25.55132 | 23.38105 |
| Acquisition/internal checks | 12.06243 | 11.21854 |
| Explicit checks | 2.56325 | 2.26089 |
| Warm replay | 3.51878 | 3.18429 |
| Two cold passes | 7.04633 | 6.38322 |
| JSON proof bytes | 28,734,671 | 26,634,915 |
| Compressed proof bytes | 445,436 | 419,935 |
| Maximum process RSS bytes | 101,466,112 | 90,587,136 |

Paired complete-cost reductions are **6.88%, 9.89%, 8.41% and 8.73%**.
Wrapper indentation changes raw JSON counts relative to the earlier experiment;
the matched comparison uses identical encoding in both arms. RSS figures are
process observations, not memory bounds. The new runner uses shallow standalone
JSON/hash helpers rather than extending the long historical comparison-import
chain; this affects both arms and leaves previous scientific files unchanged.

An independent explicit truth-table audit covers **5,457 inputs**: all 512
two-variable normalized CNFs; 3,304 three-variable CNFs with at most three
distinct clauses; 576 domain restrictions; 1,000 newly seeded random small CNFs;
64 fresh signed/edited/mixed controls; and one nonclique conflict counterexample.
All **1,700 emitted witnesses** agree with independent truth tables. A repeated
audit reproduces the semantic records exactly. Cold checks disable matching.
All 158 strict-class attempt diagnostics agree with truth; these count attempts,
not distinct recognized formulas. Five satisfied additions permit checked witness
reuse, and five contradicted additions invalidate the old witness.

The negative evidence limits the result: the gate finds only **19 of 247** SAT
three-resource domain restrictions and **5 of 47** SAT fresh controls. It retains
all 228 missed SAT domain inputs and all fresh controls, including the satisfiable
nonclique example. These are gate-only misses; the existing portfolio may still
decide them. Greedy demand selection, signed orientation, conservative components
and fixed model completion remain incomplete. The fresh generated controls are
not a representative external evaluation.

All **2,485 full and 18 focused tests pass**. The tests cover signed sparse
renaming, variable completeness, changed assignments/sources, malformed inputs,
unclassified constraints, conservative false negatives, admission limits, cold
replay and unchanged fallback. Existing unclosed-SQLite warnings remain retained.
The validator rechecks all eight runs, regenerates deterministic proofs and
counters, repeats warm/cold schedules and preserves all 242 prior manifests,
81,349 artifact entries, 1,321 scientific sources and 83 manuscript proof blocks.

## Next priorities

1. Investigate the remaining random formula through the 26 failed clauses and
   their shared variables. Test bounded repair or conditioning that preserves
   already satisfied constraints, with complete source verification and all
   failure/UNSAT obligations explicit. This candidate is a diagnostic, not proof
   that repair is cheap or that a useful partition exists.
2. Separate genuine exclusion cliques from general conflict interaction, and
   improve demand selection against the 228 retained SAT domain misses. Matching
   is adequate for the strict class; collapsing arbitrary connected conflicts
   to capacity one is an incomplete sufficient condition.
3. Freeze unseen external encodings before making broader transfer claims.
   Auxiliary descriptions, overlapping choices, ternary interactions, source
   context reuse and unrestricted expansion bounds remain open.

Resume `experiments/results/cnf-choice-witness/checkpoint.json`, key
`choice_witness`. Completing the derived controls does not establish an efficient
classification or solution of arbitrary SAT.
