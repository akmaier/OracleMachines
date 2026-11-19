# Retain source-variable maps for checked residual reuse

`ResidualTransportSolver` composes the normalizer's variable maps along native
search visits. It keeps bounded hints linking a negative residual's compact
variables to the original input variable IDs. A later query can use those IDs to
propose containment even when compact numbering changes. Every accepted result
still passes the existing native proof checker. This is an optional experiment;
the input-safe affine policy remains the performance baseline.

## Recognition and proof authority

The first source normalization records its sorted external variable names. Each
native search visit composes its own sorted names with its parent's map. The
stack is scoped to search visits; nested proof-checker normalizations cannot
change it. Quotient targets retain their representative variable names, so the
same composition applies before the existing quotient recomposition check.
The native visit's decision, model-lifting, storage and budget semantics are
otherwise unchanged. The eleven tests include quotient mixtures and comparisons
with truth tables and the preceding solver; this is not a Lean refinement proof.

Completed nonterminal negative residuals can propose hints. Only hints whose
native origin survives the batch commit are admitted after the query succeeds
or stops at its native expansion limit. A failed query discards staged hints;
a stopped query filters out its rolled-back suffix. Candidates become available
on later queries, not immediately within the same query. No branch assumption
is silently discharged into the source formula.

For a candidate, map its clauses into external variable coordinates and require
full containment in the current residual expressed in the same coordinates.
A longest clause, with lexical ties, filters candidates. The exact selected
target subset must normalize to the candidate's original native key. The native
origin must then verify as UNSAT, and the original subset proof rule checks the
published target. Stale or positive origins give misses. Persisted maps are
untrusted proposals; forged maps cannot bypass these checks.

The justification is restricted and direct. For an injective variable map,
an assignment satisfying the renamed core would induce an assignment satisfying
the original core. An UNSAT core therefore stays UNSAT under that map, and any
CNF containing it is UNSAT. The implementation handles order-preserving maps,
which retain the existing canonical proof identity. It does not discover general
renamings, sign flips, graph isomorphisms or semantic equivalence.

This distinction matters for the preceding counterexample. If the acquired core
already used external variables 4,5,6, retaining that map recovers it inside a
later formula that also introduces variables 1,2,3. If the acquired source used
1,2,3 and an unrelated target renames it to 4,5,6, the map is unknown and this
policy can still miss. Tests preserve both cases; the supplied-map example from
the previous study is not claimed to be automatically solved in full generality.

## Bounded hints, durable metadata and costs

Default limits are 32 staged hints per query, 32 retained hints, at most 32 probes
per query and four anchor-matching candidates per probe. Stage and retained pool
each have a conservative 512 KiB charge. An origin has at most 1,024 literals.
Maps contain at most 256 variables, use positive IDs of at most 64 bits, and have
depth at most 128 and a separate 512 KiB live tuple charge. Exceeding a map limit
disables optional retrieval on that path; the original SAT input remains valid.
No causal support extraction is added to this policy.

Admission is incremental and does not scan the native archive tail. A separate
mutable hint table stores bounded origin/map payloads after native publication
has finished. Evictions delete only hint metadata. A metadata-commit failure
leaves the old in-memory pool and metadata transaction intact while preserving
already committed native proofs. Cold restart reconstructs hints from this table;
origin checking still happens before reuse. Identical limits preserve the hint
order in the measured workers. All trial archives retain their own metadata.
The cumulative union merges proof authority only; use the checkpoint's
`hint_resume_archive` when the last mapped policy's hint state is needed.

The caps apply to retained structures and selected operations. Eligibility scans,
input/root normalization, decode and insertion transients, shallow pool copies,
empty container shells, prerequisite proof checking, the complete checked graph
and native fallback have separate costs. Native and affine proof storage is
uncapped. SQLite allocation and scanning a hostile enlarged metadata table are
also outside the retained Python-object charge; normal owned writes keep at most
the configured number of hint rows.

If P probes inspect residuals of at most L literals, R retained hints and C
candidates per probe with at most H literals each, ordinary hash-based matching
costs O(P(L+R+CH)) elementary operations, with integer/hash costs included by the
implementation. This is not a deterministic worst-case hash-table theorem.
Map composition adds work proportional to the mapped variables over all visited
nodes. Admission can scan each eligible negative node before deciding it is too
large; the hint-count cap is not a cap on that scanning. The number of native
visits and proof-checking work remain unrestricted by these hint limits.

## Frozen comparison

Three arms compare the preceding affine baseline, map-based matching, and an
ablation that captures and persists maps in the same way but matches in compact
coordinates. Representation charges and resulting evictions can differ, so this
is not a comparison with identical retained candidate sets. Twelve serial workers
run two opposite orders. All start empty and
share the 256-native-expansion cap. The fresh holdout uses sizes 144/150/156, six
designs, two samples and base/edit/repeat variants: 108 attempts and 72 roots.

A separate mapping diagnostic uses width-3/4/5 complete contradictory cubes,
followed by a numbering-shifting edit, deletion of a required premise and repeat.
It has twelve attempts. Affine discovery is capped at one variable equally in
all three diagnostic arms so that native map transport is exercised. The holdout
retains the preceding affine limits. These tiny constructed cases demonstrate
the mechanism, not representative performance or wider tractable closure.

Complete worker time includes map capture and misses, metadata transactions,
native proof checking/publication, retained-object measurement, warm/cold proof
replay, hint reconstruction, sidecars and compression. Posthoc validation is
separate. The first test run incorrectly indexed an absent zero-work metric after
an exact cache hit; its source and failure log are preserved. The assertion was
corrected, without changing the solver implementation.

## Results: a supported mechanism, no broad saving

| Measurement | Holdout baseline | Compact ablation | Mapped policy |
|---|---:|---:|---:|
| Mean query seconds | 28.49598 | 29.53542 | 29.99474 |
| Mean complete worker seconds | 56.35679 | 57.57355 | 57.53659 |
| Recorded native expansions | 10,249 | 10,249 | 10,249 |
| Native records | 10,572 | 10,572 | 10,572 |
| Native key/payload bytes | 122,831,571 | 122,831,571 | 122,831,571 |
| SQLite bytes | 191,037,440 | 191,094,784 | 191,082,496 |
| Checked graph and candidate bytes | 508,299,426 | 508,724,542 | 508,742,179 |
| Final hint rows | 0 | 14 | 11 |

Holdout native and affine proof digests, outcomes and expansion counts are
identical across all three arms: 33 SAT / 38 UNSAT / 37 unresolved attempts.
Mapped mean query time rises **5.26%** against the baseline and **1.56%** against
compact matching; both query comparisons regress in both orders. Complete time
rises 2.09% against the baseline. Its 0.064% mean decrease against compact has
mixed paired signs and is not evidence of a stable total saving. Native proof
space is unchanged; hints raise SQLite storage 0.024% and checked-object space
0.087% against the baseline. Mean cold time falls 0.49% with unchanged proof
bytes, and warm time is effectively unchanged; do not infer a structural replay
improvement from these small timing differences.

Mapped holdout peaks are 523,558 retained-pool bytes, 524,194 staged bytes and
165,240 charged live-map bytes, under their separate 512 KiB caps. It composes
1,056,464 variable entries, stages 1,204 hints, and writes 1,411,176 metadata bytes
over 45 commits. Fourteen staged origins are correctly rejected after their
native batch suffix is rolled back. Admission scans 4,038,113 origin literals;
the stage count cap does not remove this eligibility cost. Every timed archive
retains its hint table, and cold reconstruction/replay preserves that table.

The tiny diagnostic produces **five mapped hits versus zero compact hits**,
reducing native records and recorded expansions from 17 to 16, with all three
SAT and nine UNSAT outcomes unchanged. Mapped mean query time is 0.01291 seconds
versus 0.01034 baseline and 0.01383 compact. It is 24.83% slower than baseline;
the 6.63% mean decrease against compact has mixed paired signs. Mean complete
time remains 12.64% above baseline. These results establish the automatic map
mechanism and a cold-restart capability, not a net performance win or additional
certified family coverage.

## Mismatch audit and next target

On holdout, both hint policies make 1,479 probes. Maps increase anchor-matching
candidates from 31 to **1,758**, but there are **zero accepted transfers**. A
separate census reproduces every query result/counter and native/affine digest.
Every mapped candidate lacks at least seven source clauses in its target: the
missing count ranges from **7 to 220**, with median **89**. Therefore merely
enabling the earlier one-missing-clause support path cannot help these observed
candidates. Overlap of an anchor is a weak signal of compatible residuals.

The audit selects at most one minimum-missing candidate per query, yielding
eighteen proposals. Existing causal-plan extraction is tried with 32-node,
8,192-literal and 128 KiB limits, without fresh solving. Six plans stop at budget;
twelve finish but still need **3–19 absent clauses**. No new refutation is
published. This is not exhaustive search over possible supports or variable
maps. The exact target residuals, origin keys, maps, costs and failed attempts
are retained in `mismatch-analysis.json` and its independently checked archive.

The most concrete next target is to apply the repository's existing
[first-false clause partition](clause-partition.md) and
[prepared guard recognition](premise-guard.md) to **transported, extracted cores
with a few missing clauses**. The residual selected from holdout case 61 has a
30-clause support missing three clauses; cases 25 and 31 each miss five. These
are residual targets, not declarations that the original queries are UNSAT.
The target conjoined with the missing clauses contains the negative core,
so only its region where all those clauses hold is excluded. The other regions require checked first-false branches;
a SAT branch must lift correctly. Check cheap branch signals and price the
complete plan before expansion. Earlier partition studies include regressions,
so larger overlap alone is not a reason to enable this path.

Random/shared mixtures consume 81.26% of first-order holdout query time. Stopped
attempts consume **27.627 of 30.091 seconds**. This is the remaining acquisition
cost to attack. General renaming discovery, alternative support selection,
representative external workloads and efficient unrestricted closure stay open.
Resume `experiments/results/cnf-residual-transport/checkpoint.json`; keep the
preceding affine policy as the default performance comparator. The final ledger,
historical preservation, tests, build and unchanged proof blocks are bound in
`checks.json`. No new complexity-class conclusion follows.
