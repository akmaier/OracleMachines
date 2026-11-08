# Exact affine projection through shared variables

8 November 2026. This implements the next discovery target from the affine
extraction study. The optional `affine-projection-v1` policy retains the earlier
profiles and exact sources, eliminates affine variables absent from leftover
clauses, and analyzes a smaller exact residual. Ordinary SAT decisions are still
computed separately by the same unchanged residual solver.

## Exactness, recognition and persistence

For extracted F = A AND R, let H be the variables of A absent from R. Checked
elimination pivots on H first. Every row operation uses an earlier reduced row;
the checker verifies each dependency and resulting row. Rows without an H
variable give the projected relation B. Internal pivot equations can always be
solved in decreasing pivot order after choosing free internal variables. Thus,
for each assignment y outside H,

    (exists x_H, F(x_H,y)) iff B(y) AND R(y).

This is existential equivalence, not pointwise equivalence on the eliminated
variables. A feasible reduced assignment is lifted by back substitution and
checked against the full parent CNF. A reduced refutation is valid because
every parent witness would restrict to a reduced witness. All leftover clauses
remain; overlapping supports are never treated as independent components.

The projected rows use direct CNF encoding with a default budget of 4,096
literal occurrences (empty contradiction clauses cost one budget unit). Required
cost is checked before assignment enumeration. A miss records `encoding_cap`
and retains the original bounded planner. Successful rewrites remove at least
one variable and consume no conditioning depth. A checker verifies the exact
residual identity, variable binding, strict decrease and summary. Pure or already
recognized families keep their old routing; components precede projection.
All unsuccessful alternatives, cap failures and exact originals are retained.

New Lean theorems in `AffineCoupling.lean` compose the existing executable affine
projection theorem with an arbitrary leftover predicate invariant under changes
to H. They establish fiber equivalence, SAT equivalence and UNSAT transfer.
They do **not** refine the Python CNF extractor, sparse row-trace checker, CNF
encoder, lifting routine or SQLite. Those have independent executable checking
and exhaustive/seeded tests, not a claimed end-to-end Lean proof.

## Matched 775-input study

The study includes all prior 733 sources, coupled 64/128-equation systems, four
projection controls with variants, and 32 seeded affine mixtures. Labels never
select recognition. The previous implementation's full archives also replay
unchanged. Every mode retains the same 1,332 ordinary solver residuals.

| Policy | Closed beyond 512 tiny inputs | Operation seconds | SQLite bytes | Cold audit seconds |
| --- | ---: | ---: | ---: | ---: |
| Solver alone | No inventory | 1.62143 | 7,409,664 | 0.32689 |
| Affine inventory, depth 0 | 104/263 | 2.17737 | 11,157,504 | 0.51743 |
| Projection, depth 0 | 123/263 | 2.26272 | 11,419,648 | 0.52175 |
| Affine inventory, depth 2 | 209/263 | 4.47144 | 22,913,024 | 1.40055 |
| Projection, depth 2 | 215/263 | 3.75039 | 19,030,016 | 0.98692 |

Operation time includes discovery, certificate checking, serialization,
persistence, original-source solving and successful root-projection model lifts.
Input generation, truth tables, diagnostic walks and offline compression are
outside timing. Warm inventory replay, initialization and cold full audits are
separate. These are single sequential samples, not significance estimates or a
representative unrestricted-SAT workload distribution.

The six new depth-two closures are precisely the coupled 4/8/16/32/64/128-equation
controls. All also close at depth zero. Each projects to two variables and one
binary clause. At 32 equations, operation time falls from 136.38 to 44.52 ms;
at 128 equations/258 variables, from 870.78 to 578.51 ms. In the latter case,
discovery falls from 390.46 to 13.13 ms, while the ordinary solver still spends
564.84 ms on the original source and model lifting adds 0.52 ms. Integration
into actual solving is therefore a substantial remaining opportunity, separate
from this discovery result.

There is **no additional depth-two closure on the original 664 inputs**:
116/152 non-tiny sources remain explained; 34 seeded CNFs and the matching/parity
pair remain open. The latter projects from 13 variables/61 literals to 10/29,
but its strict matching recognizer still rejects the mixed remainder. Selected
unresolved literals fall only from 22 to 18. The original case costs 31.74
rather than 21.68 ms in this sample. Our initial test assumption that projection
alone would close it was false; the retained test now records this miss.

On the 32 new mixtures, depth-zero closure rises from 14 to 21, but depth-two
closure remains 31. Whole-input closure on the seeded non-affine CNFs does not
increase. A wide projected equation exceeds the encoding budget. Conditioning
later closes the original cap control, while its arbitrary renaming remains
unresolved with 283 selected literal occurrences. Frequency order and tie breaks
are not invariant under all renamings; no such claim is made.

At depth two, pattern nodes fall from 3,389 to 3,221 and node payload from
9,983,460 to 6,669,670 bytes. Source metadata grows from 1,305,669 to 1,369,994
bytes. At depth zero, SQLite increases by 262,144 bytes. The separate six-case
memory diagnostic increases peak traced Python allocation from 147,595 to
153,395 bytes at depth two and from 133,405 to 138,610 at depth zero. This small
diagnostic excludes native SQLite and RSS; archive reduction is not a claim of
uniform peak-memory reduction. Warm replay is essentially unchanged at 68.05
versus 68.13 ms for depth two. Full original sources are never deleted.

The selected unresolved-literal aggregate falls from 31,924 to 1,579 at depth
two, dominated by the repeated growing controls. It counts distinct selected
leaves per input, not globally unique archive data or runtime. This large drop
does not demonstrate broad coverage of random or arbitrary SAT.

## Bounds and remaining gaps

With e equations, n variables and h eliminated variables, discovery and checking
each need at most e min(e,h) XORs on n-bit masks, in addition to extraction,
mask construction and row scans. Reduced masks and dependency lists remain
stored. A projected equation of width w requires w*2^(w-1) direct-CNF literal
occurrences. The encoding budget bounds this materialization; the semantic
projection itself remains an affine relation without that exponential encoding.
Lifting scans reduced rows, checks original equations and checks the source CNF.
Integer bit work, normalization, identity copies and archive operations are also
charged in the implementation. These per-rewrite bounds do not establish an
efficient completed decomposition or compact universal state for arbitrary SAT.

The next discovery target is the mixed leftover: the matching/parity residual
contains a positive-only variable in its bridge clause. Assigning it true removes
that clause, exposing the existing matching family. Compare checked pure-literal
and unit simplification with interface-aware conditioning on all current misses,
including cases where couplings constrain both polarities. Separately, preserve
native affine boundary rows to avoid exponential CNF re-encoding, and integrate
checked projected decisions to avoid solving an already-reduced original source.

## Reproduce

```
python3 -m unittest solver.test_cnf_affine_projection -q
python3 experiments/compare_cnf_affine_projection.py --output /tmp/new-projection-run
python3 experiments/analyze_cnf_affine_projection.py /tmp/new-projection-run
```

All 292 Python tests pass. New coverage includes every two-variable equation
system with every boundary, all 512 two-variable CNF clause subsets, random
mixtures, exact existential fibers, successful/infeasible lifting, budget checks
before enumeration, forged row dependencies, missing boundary equations,
incorrect encodings, cold corruption and old/new archive coexistence. Raw
sources, traces, failures, hashes, fingerprints and metrics are preserved in JSON
and five gzip SQLite archives. `mechanisms.json` identifies root projections,
interfaces, budget misses and all remaining open inputs.
