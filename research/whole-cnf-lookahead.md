# Whole-CNF discovery and bounded lookahead

The 23 November investigation returns from supplied conditional guards to fresh
whole inputs. The solver receives only the CNF. Six generated designs, two
samples, and base/edit/repeat streams produce 72 exposed queries at sizes 36/60
and 72 prospective holdout queries at sizes 84/108. Seeds are 202611231956 and
202611241956. Inputs are frozen before evaluation, with no outcome filtering.
All 96 distinct canonical roots are absent from the parent archive. The
monotone relabelled repeats deliberately share their base root. These are small
synthetic workloads, not a representative sample of arbitrary SAT.

The baseline exploration completes all 72 exposed queries; random 3-CNF uses
66.8% of solve time. Its costly isolated case requires 224 expansion dispatches.
That profile motivates testing wider-clause unit propagation after the current
binary structural discovery has found no contradiction, cover or consequence.

## Exact recognition and recomposition

`experiments/cnf_whole_lookahead.py` selects the most frequent variable, breaking
ties by canonical ID, and probes false then true. It skips constants, existing
units and sources exceeding 256 variables, 4096 clauses or 16384 literals.
The existing `probe_child` checks a cached cofactor or attempts unit propagation.
A miss implies nothing. A checked negative cofactor forces the opposite branch;
that branch still consumes the common native expansion budget. A positive
continuation lifts its assignment. Two negative branches use the existing split
certificate. Native publication independently checks every retained result.

This is established failed-literal probing, not a new tractable SAT class. See
[Li and Anbulagan (1997)](https://ijcai.org/proceedings/1997/54) on unit-propagation
heuristics and [Heule and van Maaren's chapter](https://www.cs.cmu.edu/~mheule/publications/p01c05-lah.pdf)
on lookahead. Our experiment concerns its bounded placement and complete cost in
this persistent solver. The existing binary policy retains priority. No
production default or proof format changes.

For each eligible residual there are at most two probes. With V variables and L
literal occurrences, the current scanning propagation takes O((V+1)L) work;
canonicalization, exact key lookup, certificate checking and publication add
their own costs. The fixed limits bound the propagation input; they do not bound
cached proof replay, total solver work or retained history. The 256-dispatch cap excludes probe proof
publication and is not a wall-time or memory cap. Unknown remains unknown.

## Matched measurements

Four alternating serial repeats start with empty databases, retain completed
results across queries, and charge both failed and successful recognition.
Every completed root is checked on warm replay and cold reconstruction without
fresh expansion. Independent cold readers also check persisted negative prefixes.

| Measure | Exposed current | Exposed lookahead | Holdout current | Holdout lookahead |
|---|---:|---:|---:|---:|
| SAT / UNSAT / unresolved queries | 36 / 36 / 0 | 36 / 36 / 0 | 36 / 33 / 3 | 37 / 33 / 2 |
| Distinct completed roots | 48 | 48 | 47 | 47 |
| Native expansion dispatches | 1,330 | 1,169 | 2,567 | 2,142 |
| Mean solve seconds | 2.2271 | 2.4516 | 5.7251 | 5.9373 |
| Mean complete-worker seconds | 4.8318 | 5.0361 | 11.8986 | 11.7463 |
| Native key + payload bytes | 8,509,761 | 8,296,965 | 24,141,249 | 22,362,613 |
| Selected retained Python bytes | 37,546,460 | 36,687,171 | 106,680,530 | 98,725,860 |

Exposed solve time rises 10.08%; held-out solve time rises 3.71%. Query time is
worse in all eight paired repeats. Held-out complete-worker mean improves
1.28%, with three faster pairs and one slower, partly from 7.46% cheaper cold
replay. The worker includes setup, query accounting, warm replay, cold audit,
reconstruction and compression; it excludes study preparation and the later
cumulative audit. This weighting does not establish a universal runtime gain.
Selected Python state excludes native allocations and transient objects; peak
RSS and logical/database/compressed sizes are reported separately in the raw
reports. Native payload falls 2.50% exposed and 7.37% held out.

The new completed query is held-out case 36: a fresh 108-variable base formula.
Lookahead finds a checked model in 251 dispatches; the baseline stops at 256.
Its subsequent edit takes one dispatch instead of 197. The baseline eventually
completes the same base root on its repeat, so this is earlier completion and
reuse, not an additional distinct completed root. The 84-variable base and edit
(cases 0/1) stop in both arms; the base repeat completes, leaving only the edit's
root without a verdict. Counting each stop as a distinct uncovered problem would
overstate the remaining root coverage gap.

Benefits differ across designs. Held-out random 3-CNF falls from 3.1021 to
2.9358 solve seconds, while shared mixtures rise from 1.9920 to 2.2981 seconds.
Family labels are used only for analysis, never for selecting solver actions.

## Remaining cost and next target

The additional policy selects a useful negative cofactor in 122 of 432 exposed
candidates and 207 of 706 held-out candidates. There are 310 and 499 inconclusive
candidate attempts. These still pay restriction, canonicalization, lookup and
propagation before ordinary search repeats related work. Fewer dispatches do not
imply less computation.

Chronological diagnostic profiles preserve the exact query prefix. In held-out
case 1, normalization calls grow from 777 to 978 and propagation calls from 241
to 350, while both policies exhaust the cap. In case 36 they grow from 747 to
869 and 244 to 341, respectively. Profile times include instrumentation overhead,
and cumulative times overlap; they are excluded from comparative means.

The next target is a cheap, source-derived gate and preparation reuse for these
whole-clause probes. Record which literals can start a unit chain, how much
restriction and canonicalization a miss repeats, and when a previously checked
cofactor can be reused. Avoid assuming that a syntactic propagation miss excludes
a cached negative answer. Price the gate and exact reconstruction on both random
and shared mixtures. Freeze another holdout before tuning the policy. Preserve
case 1 as an explicit unresolved root and case 36 as a positive early-reuse
example. Merely increasing the dispatch cap or selecting by generator label would
not explain their structure.

Keep the candidate optional: it reduces stored evidence and improves one query's
budgeted completion, but does not improve distinct root coverage or overall solve
time. Arbitrary-CNF efficient acquisition and compact reusable closure remain open.

## Reproduction and preservation

Use `experiments/results/cnf-whole-discovery/checkpoint.json`. The protocol binds
the source files, cases and parent checkpoint. Comparison, profiling, validation
and finalization scripts have matching names under `experiments/`. The cumulative
audit checks all six authority tables and the previous partition certificates;
the inherited per-query ID logs track four tables, so they alone are not a full
extension inventory. All earlier authoritative payloads remain unchanged;
alternative valid payloads stay in the complete trial archives.

Development logs retain a missing archive-directory error, an incorrect test
assumption that recursive probes would not change global counters, and audit
adapters that initially confused four-table and six-table orderings and assumed
that unused legacy tables existed in fresh databases. The final
tests isolate the root probe calls and the final audit names all six authorities.
These are harness/test failures, not counterexamples to the native proof rules.

Validation: 1,620 tests pass, including 29 focused checks with no warnings. The
full suite retains 44 existing unclosed-SQLite warnings. Both readers accept
1,224 query records and the cumulative archive: 82,603 native certificates and
83 affine certificates, with earlier equivalence/discovery authority unchanged.
The 342 prior partition records replay, all 13,361 earlier artifacts retain their
hashes, and 865 source fingerprints are sealed. The manuscript builds to 250
pages without warnings, preserving its 64 earlier proof environments.
