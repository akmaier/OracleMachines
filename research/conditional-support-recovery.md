# Recovering from one missing reason: fewer expansions, higher total cost

The 23 November follow-up identifies a useful conditional pattern, but rejects
unconditional use of its recovery policy. The proof rule is already represented
by the repository's clause-deletion guards and failed-literal reasoning. This
experiment uses compact conditional unit certificates to select the value and
compiles the result into ordinary native proofs. It changes no default policy.

## The structural restriction

Let a checked template refute K AND C under assumptions a. Suppose K is contained
in an edited target G and C is its only missing template clause. Every model of
G extending a must falsify C: a model satisfying C would satisfy the refuted
strengthening. Thus each literal of C must be false. This gives an exact reduced
SAT obligation, not an UNSAT verdict for G. A returned model must satisfy the
whole target cofactor, and a negative answer needs all excluded alternatives
checked.

There is a sharper restriction for these unit templates. Saturate G under a by
unit propagation, without conflict. In that fixed point, C cannot be satisfied
or contain two or more unassigned literals: adding it would then introduce
neither an empty clause nor a unit, so it could not make a unit-refutable
strengthening. Consequently C is already false, or exactly one literal remains.
The first case gives no new value; the second identifies one failed literal.
The added direction is therefore a supplied candidate for existing failed-literal
reasoning, not an additional tractable class. This argument depends on a complete
unit fixed point and a unit-refutable strengthening; it does not apply to an
arbitrary UNSAT proof. Exhaustive two-variable tests check the restriction.

The implementation accepts a checked unit prefix and at most three literals in
the missing clause after the original guard. It checks source containment,
assumptions, variable presence and every retained unit reason. It solves the
remaining restricted formula with a shared native expansion budget. On SAT,
it lifts and checks a full cofactor witness. On UNSAT, each excluded alternative
satisfies the missing clause, so that clause disappears: the old unit template
then refutes a cofactor of G itself. Native split nodes and the checked unit
prefix reconstruct the requested root. A budget stop remains unknown and retains
only completed checked nodes. No new sidecar authority or native rule is added.

## What the exposed misses reveal

Trying other existing templates under stronger compatible guards closes none
of the fourteen earlier fallback queries. This failed candidate is preserved.
Three nonterminal queries instead expose one useful extra forced value:

| Case / guard | Status | Additional forced value | Earlier expansions | Recovery probe expansions |
|---|---|---|---:|---:|
| 4 / 3 | UNSAT | variable 1004 = true | 4 | 2 |
| 4 / 4 | UNSAT | variable 1004 = true | 5 | 4 |
| 7 / 4 | SAT | variable 3598 = true | 6 | 2 |

Case 5 / 5 already derives all missing-clause values by unit propagation, so
this pattern adds nothing. The independent probes restore the exact historical
prefix plus original preparation and preceding proof additions. Their rebuilt
warm pools may differ from the original process; their timings are exploratory.
The subsequent matched streams below charge their own preparation and pool state.

## Matched costs and preserved regressions

The frozen main comparison uses the previous eleven sources and four fixed-seed
additional deletions, each under six supplied guards. Four policies in two
opposite serial process orders produce 720 attempts. All agree on 81 UNSAT and
nine SAT cofactor answers per worker. Every worker pays nine donor expansions.

| Policy | Fresh query expansions | Preparation + query mean (ms) | Native payload bytes | Compressed delta + active hints (bytes) |
|---|---:|---:|---:|---:|
| Native | 99 | 292.36 | 994,561 | 94,018 |
| Previous compact cache | 36 | 299.82 | 889,261 | 94,374 |
| Compact cache + unit screen | 29 | 340.66 | 1,073,895 | 109,588 |
| Screen + missing-clause recovery | 17 | 336.39 | 1,003,888 | 104,108 |

Screening can bypass cheap recognizers or change the residual on which the
native policy selects consequences and reuses its pools. A separate frozen
follow-up therefore keeps ordinary native acquisition whenever recovery finds
no new forced value. Compact and gated policies run in two opposite orders,
adding 360 attempts on the same inputs. The gate reduces expansions **36 to 30**,
but preparation plus query time rises **297.36 to 329.05 ms (10.66%)**. Native
payload grows **889,261 to 1,005,314 bytes (13.05%)**. Compressed delta plus hints
grows 94,374 to 104,397 bytes. The narrower gate also remains optional.

On the original 66-query controls, query means barely change, 208.87 to 208.45
ms, while expansions fall 28 to 21. On the 24 additional queries, time rises
75.59 to 107.85 ms and expansions rise eight to nine. Full-worker means move
2.600 to 2.511 seconds; reconstruction and instrumentation variation prevent an
end-to-end speedup attribution from these two orders. The selected-container
Python endpoint grows 5,092,347 to 5,550,849 bytes, but excludes set contents,
native allocations and other live state. It is not total memory. Hint reload and
validation are separately audited; the main worker timer includes cold answer
replay, not that reload.

## Why the extra reasoning loses

Later queries already have cheaper evidence. In additional case 12 / guard 3,
the compact baseline reuses a negative core, publishes one node and serializes
4,086 proof bytes. Recovery publishes nine nodes and serializes 22,101 bytes,
even though both spend one fresh expansion. First-order time rises from 3.25
to 10.81 ms. Case 12 / guard 4 similarly grows from one node to four. Additional
SAT cases 13 / 4 and 14 / 4 already hit the witness pool; forcing another value
and rebuilding its context supplies no useful shortcut. The original hard SAT
case does improve locally from six expansions to two and 8.32 to 6.73 ms in the
first gated order. That improvement does not repay the other costs.

**Next priority: let cheap checked negative-core and witness reuse run before
preparing a recovery route.** Preserve their source coordinates and charge the
check. Where recovery still helps, compare ordinary native reconstruction with
an already checked guard composition; repeated full-CNF serialization is a
separate cost. Do not rank these routes by fresh expansion count alone. The
current data does not justify replacing the compact-cache or native defaults.

## Bounds, validation and persistent continuation

Recognition scans the target and checks the template. The current repeated-scan
unit propagator can cost O(vL) literal work for v variables and L literal
occurrences, before native solving. The fixed width cap bounds the number of
explicit extra forced values and excluded alternatives, not verification,
normalization, database traffic, model search or retained proof size. With a
complete unit fixed point, this template class contributes at most one new
forced value. There is still no uniform small bound for the residual SAT problem,
automatic donor/guard/map discovery, or polynomial storage under arbitrary edits.

`experiments/results/cnf-conditional-recovery/` preserves the failed cross-template
census, three probes, both frozen protocols, all twelve comparison workers and
resource counters. Runtime source is `experiments/cnf_conditional_recovery.py`.
The previous solver, compact cache and native checker remain byte-identical.
The validator replays the native union and earlier partition records with both
readers, checks chronological prerequisites and source-bound recovery, and keeps
alternative valid payloads in their original deltas. Resume from its
`checkpoint.json`; `analysis.json` ranks per-query costs, including the regressions.
No new whole-input decision coverage, novel inference rule, unrestricted-SAT
complexity result or Lean refinement theorem is claimed.

Validation passed 1,519 full tests and 227 focused tests, plus 1,080 matched
conditional attempts and three independently reconstructed probes. Both readers
replay 76,361 cumulative native records, unchanged extension-table counts and
342 previous partition records. The union adds 89 native identities while
preserving every earlier payload. All 12,521 preceding artifacts across 141
manifests remain unchanged. The seal binds 804 source files. The full test suite
retains 44 unclosed-SQLite resource warnings; focused tests have none. The paper
builds without LaTeX or layout warnings, and all 64 earlier proof environments
remain unchanged. No new Lean proof is claimed for the unit-fixed-point argument.
