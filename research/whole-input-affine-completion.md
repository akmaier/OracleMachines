# Complete the affine space already found in a whole CNF

The preceding diagnostic found an unresolved formula with 112 actual variables,
111 extracted equations of rank 108, and 61 remaining clauses. The whole-input
probe already paid to extract and eliminate those equations. It used only
contradictory rows and discarded consistent spaces. This experiment connects the
existing bounded completion machinery to that acquisition gate.

## Recognition, checking and reuse

`experiments/cnf_whole_affine.py` reuses the extracted equations when they are
consistent and leave at most eight free coordinates. The independent affine
checker validates the source clauses, row operations and rank. The existing
space checker validates a particular solution and a complete independent basis.
A Gray-code walk then tests each candidate against the remaining clauses,
retaining a failed original-clause index for every rejected assignment.

A surviving model must satisfy the entire canonical formula and raw source. It
enters the unchanged native model checker and witness pool. Exhaustion enters
the existing `cnf-affine-negative-v1` authority, whose checker independently
reconstructs every candidate and verifies its failed clause. Native proof nodes
never depend on extension answers. This adds no proof rule or certificate format.

Known roots retain priority. No-equation inputs, high free dimension, source-size
limits and XOR-budget stops retain native fallback without an inferred answer.
Fallback uses the original extracted-input result rather than repeating affine
discovery. The completion gate is optional; production defaults are unchanged.
Input snapshots retain finite iterators, sparse labels and tautology handling.

## Resource bounds

Let the checked affine subsystem have rank `r` on `n` canonical variables and
`d = n-r`. Every full-CNF model belongs to its `2^d`-point affine space. Exhausting
that space against all leftover clauses is therefore sufficient for a negative
answer; testing only a sample is not. Complete coverage follows from the checked
basis and enumeration, not from the original generator's family label.

Charge extraction, elimination, space construction, independent checking, full
keys, serialization and persistence separately. With `m_L` leftover clauses and
machine word width `w`, packed candidate testing and independent exhaustion
replay have the conservative bound
`O(2^d (m_L + d + 1) ceil(n/w))`, in addition to those preparation and publication
costs. The producer updates a candidate with one basis XOR between consecutive
points; the independent checker reconstructs it from its Gray coefficients.
Source clauses are packed once. Packed integers are not constant-cost for
unbounded `n`.

Beyond the source and extraction evidence, a particular vector and basis use
`O((d+1)n)` bits, and exhaustion records use `O(2^d log(m+1))` bits for original
clause indices, where `m` is the full source clause count, with ordinary
representation overhead. Packed leftover masks use up to `O(m_L n)` transient bits;
these masks are not serialized with the certificate. The current gate retains
the existing cap `d <= 8`, source caps of 256 variables, 4,096 clauses and 16,384
literals, and 65,536 elimination XORs. Native dispatches exclude all of this
work. Without a small free dimension the enumeration remains exponential; an
arbitrary CNF need not contain any directly recognized affine subsystem.

## Frozen comparison

The preceding holdout becomes exposed: 72 queries at generator sizes 90/114.
Another 72-query stream at sizes 96/120 with seed 202611232157 is frozen before
evaluation. Each stream contains 48 distinct canonical roots, six construction
families, and base/edit/repeat queries. Only CNFs enter search. All workers start
empty, and novelty is recorded against all six parent authority tables without
seeding answers. Four alternating serial repetitions compare the original binary
policy, ordered whole-clause probing, and that policy with affine completion.
The common native budget is 256 dispatches; completion costs are additional.

| Mean or retained measure | Exposed ordered | Exposed completion | Fresh ordered | Fresh completion |
|---|---:|---:|---:|---:|
| Solve seconds | 13.6881 | 12.7384 | 14.4746 | 14.5413 |
| Complete-worker seconds | 26.4422 | 24.6727 | 27.4472 | 27.5057 |
| Cold checking seconds | 5.3787 | 4.9098 | 5.5481 | 5.5689 |
| Reconstruction seconds | 0.9700 | 1.0499 | 0.8089 | 0.8132 |
| Native key + payload bytes | 55,295,075 | 51,507,900 | 56,272,305 | 56,272,305 |
| Affine key + payload bytes | 166,670 | 194,805 | 207,976 | 207,976 |
| Selected retained Python bytes | 235,327,604 | 219,740,636 | 238,234,983 | 238,234,983 |
| SQLite bytes | 89,096,192 | 83,582,976 | 90,734,592 | 90,734,592 |
| Compressed SQLite bytes | 6,223,555 | 5,807,860 | 6,400,539 | 6,400,539 |

Exposed solve mean improves **6.94%** and complete-worker mean **6.69%**, with
all four pairs faster. The case-43 attempt changes from a 904.87 ms budget stop
to a 5.87 ms checked refutation on average; those outcomes differ, so this is
not a completed-solve speedup ratio. Recognition, space construction, checking
and persistence are included. Reconstruction increases despite smaller stored
proofs, and remains charged. Mean process peak RSS falls from 801,247,232 to
769,867,776 bytes on exposed runs, a measured process statistic rather than a
general space bound.

Fresh solve mean instead regresses **0.46%** (three of four pairs slower), and
complete-worker mean **0.21%** (two pairs slower). Mean peak RSS changes from
797,683,712 to 798,089,216 bytes. There is no fresh structural or retained-space
gain. Keep these small timing differences and the optional status; four repeats
do not establish a distribution-wide performance guarantee.

The combined lookahead/completion policy still costs **11.50%** more solve time
than the original binary route on exposed inputs and **16.99%** more on fresh
inputs. Its native payload is also **5.10% / 8.35%** larger. The local completion
gain does not erase broader probing overhead. Complete-worker means include
querying, warm reuse, cold checking, reconstruction and compression; study
preparation and the cumulative history audit are separate.

## Coverage, retained evidence and the remaining interaction

Exposed case 43 is UNSAT: all 16 affine candidates fail a remaining clause. The
producer performs 400 packed clause checks and 15 basis XORs, with zero native
expansion dispatches. Independent verification reconstructs all candidates and
checks their recorded rejection clauses. The certificate adds 28,135 logical
key-plus-payload bytes through the existing affine table.

Across the exposed stream, ordered probing completes 39/48 distinct roots and
completion covers 40/48; the original binary route covers 38/48. Query outcomes
change from 27 SAT / 31 UNSAT / 14 unresolved to 27 / 32 / 13. Native dispatches
fall from 4,456 to 4,200, and native records from 6,433 to 6,138. Native payload
falls from 55,295,075 to 51,507,900 bytes while affine payload rises from 166,670
to 194,805 bytes. Combined logical proof storage therefore falls by 3,759,040
bytes. Selected retained Python state falls from 235,327,604 to 219,740,636 bytes;
this is not a process peak-memory bound.

The prospective stream triggers no bounded completion. Both ordered variants
retain identical native and extension payloads and selected Python state, and
complete the same 38/48 distinct roots. All eight parity-bridge roots are already
refuted by inconsistent affine rows. The remaining ten distinct roots have no
directly extracted equations: eight random-three roots and mixed edits 61/70.
The twelve random-three attempts all exhaust the native dispatch cap. The new
integration thus closes the exposed structural gap without establishing a new
coverage gain on this fresh sample.

The most concrete next reuse opportunity is fresh case 70. Its base, case 69,
has a checked refutation after 246 dispatches before the edit is queried. Yet
the edit still stops at 256. Test automatic source correspondence and extraction
of surviving proof branches, followed by the existing partial recomposition
machinery. A valid earlier refutation cannot certify the edited CNF by itself.
Charge the failed matches and extraction cost, and retain no-equation controls.
Case 61 is a second unresolved interaction, but its base finishes only on the
later repeat 62: that future result cannot be supplied to the earlier query.
Random-three accounts for 10.6075 of 14.5413 fresh solve seconds (**72.95%**).
It is the largest remaining runtime cost; the earlier mixed proof gives a more
specific immediate reuse hypothesis than simply increasing search on those
unstructured controls.

Exact-prefix profiles reproduce the timed decisions and counters. Fresh repeat
38 performs 774 normalizations and 355 publications; edit 70 performs 1,229
normalizations, 366 publications and 221 support-plan preparations. The latter
also performs 47,360 restrictions across those paths. These counts motivate
avoiding repeated acquisition through a useful earlier proof. They do not show
that the proposed partial transfer succeeds. Instrumented cumulative times
overlap and are excluded from comparative means.

## Reproduction and limitations

Resume `experiments/results/cnf-whole-affine/checkpoint.json`. The compare,
validate, profile and finalize scripts have matching names under `experiments/`.
The frontier inspector records checked extraction for every unresolved distinct
fresh root. Raw workers retain stopped native prefixes, alternative payloads,
warm replay, cold checking, reconstruction and archive sizes. The cumulative
archive preserves all earlier authority. Study preparation and the full history
audit are separate from worker timing.

Development failure is retained: the initial XOR-stop test incorrectly assumed a
complete four-variable cube needed more than one extraction XOR. Adding a second
cube produces the intended budget stop. Focused tests also reject changed affine
equations, invalid bases and missing rejection indices, check 256 small random
formulas against exhaustive truth, and replay both native and extension answers.
The integration establishes a useful bounded condition; it does not establish a
uniform polynomial construction or compact closure for unrestricted SAT.

Validation: 1,638 tests pass, including 47 focused tests without warnings. The
full suite retains 44 existing SQLite resource warnings. The 251-page manuscript
builds without warnings and preserves all 64 earlier proof environments.
Both independent readers audit all 1,728 trial-query records, every persisted
prefix and 342 earlier partition records. All 13,586 earlier artifacts remain
unchanged. The cumulative union retains 95,674 native and 99 affine certificates,
plus 34 binary-core discoveries and 42/53/22 equivalences in versions 1/2/3.
It adds 6,540 native and nine affine identities without replacing old payloads.

Historical storage still grows: the union occupies 1,009,664,000 SQLite bytes
and 71,198,214 compressed bytes, an increase of 6,452,835 compressed bytes over
the parent checkpoint. This archive preserves new workloads and alternative
trials; the exposed worker's smaller proof store does not imply a shrinking
cumulative history. The full preservation audit takes 549.73 seconds, including
its final union compression. The sealed inventory contains 879 source fingerprints.
