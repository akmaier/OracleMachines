# Prefer a complete result before reconstructing a partial proof

The preceding checkpoint exposes a choice between two valid forms of reuse.
Two edited formulas already have complete reusable refutations, but partial
proof reconstruction takes 57 and 58 native dispatches to rediscover their
answers. The new policy checks the existing complete-result pools after the
same near-origin recognition and before partial extraction.

## Recognition, authority and continuation

`WholePoolPrioritySolver` inherits the preceding input snapshot, exact-root
checks, source limits and bounded pool. A partial plan becomes eligible only
when an earlier checked negative root shares clauses with the canonical target
and exactly one clause of that root is absent from the target. The condition is
`|origin_clauses - target_clauses| = 1`; it does not bound the number of added
target clauses. At that point, `cnf_pool_priority.try_pools`
tries the existing negative-support and witness pools once. No generator label,
supplied guard or future answer selects the route.

A negative hit publishes an ordinary checked native proof for the whole target.
A positive hit checks its assignment against every canonical target clause,
publishes a checked native model and verifies its lift against the raw input.
Both bypass partial extraction and use zero fresh native dispatches. A miss
provides no verdict and continues the preceding partial-plan policy with the
original shared search budget. Checked prefixes survive later budget stops.

The native proof formats and database tables are unchanged. Exact-root warm
reuse and independent cold replay need no policy metadata. No additional pool,
persistent plan or miss cache is introduced. The earlier sources remain frozen;
the new subclass mirrors the original selection method and adds this gate.
The inherited partial-composer adapter still requires exclusive serial use.

## Cost obligations

The gate runs at most once per eligible query, but is not a constant-time lookup.
The existing negative pool can scan candidates, discover causal support and
materialize its proof. Cold reads may verify the retained dependency graph.
Witness candidates require target-clause checks. A later native fallback can
repeat an unsuccessful lookup. These costs remain in the counters and measured
wall time, even when the native-dispatch counter stays at zero.

Complete-first priority is a policy, not a proof that complete recognition is
always cheaper than partial acquisition. The gate can spend time establishing
that a whole prior refutation does not transfer while a useful partial plan
would find a target model quickly. No optimal arbitration rule, efficient
arbitrary-CNF partition or uniform polynomial expansion bound follows.

## Frozen comparison

The previous 102/126-variable-generator holdout becomes exposed. A new
108/132 stream with seed 202611240001 is frozen before evaluation. Each stream
contains 72 base/edit/repeat queries and 48 distinct roots from six construction
families. Only CNFs enter search. Every worker starts empty; parent-archive
novelty is recorded without supplying its answers.

Four alternating serial repetitions compare whole-input affine completion,
the previous partial-proof policy and the new pool-priority policy, with the
same 256-dispatch cap. Setup, discovery, checking, publication, warm and cold
reuse, reconstruction, serialization, retained state and compression are charged.
Cumulative preservation and posthoc profiling are recorded separately. As in
the inherited harness, the complete-worker timer starts after module imports,
frozen-source hash checks and case loading, and stops before final report
bookkeeping. It measures the recorded worker phases, not total process lifetime.

A separate single paired replay of the earlier 96/120 stream checks whether the
useful case-70 partial transfer survives the new gate. Its observations are a
regression diagnostic, excluded from the four-repeat timing means.

## Measured result

| Mean or retained measure | Exposed partial reuse | Exposed priority | Fresh partial reuse | Fresh priority |
|---|---:|---:|---:|---:|
| Solve seconds | 12.5034 | 12.2321 | 14.9766 | 14.9645 |
| Complete-worker seconds | 24.8953 | 23.7854 | 29.5536 | 29.0708 |
| Native dispatches | 3,400 | 3,269 | 4,121 | 4,037 |
| Native records | 4,954 | 5,114 | 5,864 | 5,960 |
| Native key + payload bytes | 51,885,888 | 49,050,424 | 59,658,671 | 57,848,807 |
| Selected retained Python bytes | 220,309,248 | 208,356,454 | 251,933,437 | 244,928,957 |
| SQLite bytes | 80,752,640 | 76,447,744 | 93,483,008 | 90,742,784 |
| Compressed SQLite bytes | 5,932,827 | 5,716,796 | 6,928,122 | 6,757,657 |

All three policies complete **42/48 distinct roots** on each stream. On exposed
inputs, priority improves solve mean **2.17%** and complete-worker mean **4.46%**
against partial reuse, with all four pairs faster. Fresh solve mean changes
only **-0.08%**, with two pairs faster and two slower; this does not establish a
reliable solve-time improvement. Fresh complete-worker mean falls **1.63%**,
with all four pairs faster. Native payload falls **5.46% exposed / 3.03% fresh**,
and selected retained Python state falls **5.43% / 2.78%**. More, smaller proof
records replace some larger reconstructions; record count alone would hide the
space saving. These reductions apply to the empty-start study workers. The
cumulative union preserves earlier authoritative payloads and keeps alternate
proofs in raw archives; it does not retroactively shrink older stored results.

The two exposed regressions now take zero dispatches instead of 57/58. Their
mean solve times fall from 249.58/308.72 ms to 93.65/140.30 ms. Another fresh
edit drops from 77 dispatches and 404.80 ms to zero dispatches and 137.36 ms.
Each stream has five checked negative-pool hits. The exposed stream has three
gate misses, and the fresh stream two. Positive witness reuse passes focused
truth and raw-label tests but does not occur in these measured gates.

Misses remain material. Exposed positive edit 61 still takes nine dispatches,
but mean solve time rises from 121.56 to 240.39 ms. Fresh cases 62/67 retain
35/110 dispatches while their means rise from 217.83/543.62 to 344.76/654.27 ms.
Complete-result recognition is sometimes more expensive than the work it avoids.

The earlier case-70 transfer survives: both paired regression runs produce a
checked refutation in 223 dispatches using 22 of 27 surviving support leaves.
The added lookup misses and raises that single attempt from 820.28 to 963.05 ms.
This is one replay per arm, not a repeated timing estimate. Preserve the useful
coverage result and its added lookup cost together.

Against whole-input affine completion without partial plans, the new policy
still increases solve mean **0.45% exposed / 0.98% fresh**, and complete-worker
mean **1.17% / 1.01%**. The paired signs are mixed. This narrower arbitration
improvement therefore remains optional, with no new general default.

Cold checking drops from 4.9750 to 4.6182 exposed seconds and 5.7590 to 5.6215
fresh seconds. Reconstruction drops from 1.1614 to 1.0158 and 1.5901 to 1.4620
seconds. Mean peak RSS falls from 774,012,928 to 749,871,104 exposed bytes and
841,195,520 to 820,326,400 fresh bytes. Selected solver-graph sizes exclude
transient plans and retained query-log objects; RSS and sidecar sizes are
separately reported. These measurements are not asymptotic memory bounds.

## Next target and preservation

Random-three attempts consume **69.70%** of fresh solve time. All six distinct
roots still unresolved at the stream's end belong to that family. One additional
disjoint-mixture base attempt stops, but its later repeat completes. Keep these
attempt-level and distinct-root gaps separate.

The next investigation should test reuse of the preparation already performed
by inconclusive whole-clause probes when ordinary search reaches that exact
cofactor. Establish the producer/consumer correspondence first. Existing
`cnf_cofactor_handoff.py` already provides a solver-owned, single-use frame and
an identity-bound propagation result; its earlier experiment had mixed total
costs and must remain a control. The broader whole-clause path is a different
integration opportunity, not evidence that the earlier miss costs disappear.
Retain higher-priority structural discovery, bound live preparation, charge
unconsumed offers, and never interpret nonconflicting propagation as SAT.

Resume `experiments/results/cnf-whole-pool-priority/checkpoint.json`. Growing
cumulative archives above 96 MiB use 48 MiB transport parts. Use
`experiments.cnf_archive_parts.restore_archive(checkpoint['reference_union'], destination)`;
this reader also accepts the earlier single-gzip entries. The descriptor binds
each part, the concatenated gzip and the entire database. Reconstruction must
be byte-identical before opening SQLite; ordinary SAT verification remains a
separate obligation. Old archives are unchanged. Splitting files does not reduce
total retained bytes or the cost of rebuilding the cumulative union.

Exact-prefix profiling selects fresh case 40, the largest mean unresolved
attempt at 1.19421 seconds. Its raw input has 561 width-three clauses. Both
controls reach the same 256-dispatch stop. The priority run makes 131 specialized
cofactor preparations, records 126 nonconflicting bipolar probes and has
48 whole-clause lookahead misses among 72 candidates. It also performs 779
general normalizations visiting 793,951 literals; native and probe propagation
visit 486,760 and 523,067 literals respectively. These are candidate reuse costs,
not automatically avoidable work. A probe's prepared child still has to be the
child ordinary search actually uses. Instrumented cumulative times overlap and
are excluded from the comparison; the raw profiles are preserved.

All 1,661 tests pass, including 88 focused checks without warnings. The full
suite retains 44 existing SQLite resource warnings. The 252-page manuscript
builds without warnings. The profiling script's initial assumption that all
legacy extension tables exist failed; its log is retained. The corrected script
treats absent optional tables as empty and checks that every captured prefix
payload is already preserved in its corresponding matched archive.

The cumulative audit passes for 1,728 matched and 144 regression query records,
45 complete-pool routes and 56 successful partial plans. Two readers check all
six authority tables in 26 trial archives. All 342 earlier partition records,
155 earlier manifests and 13,851 earlier artifacts remain valid and unchanged.
The union adds 6,171 native and eight affine records, reaching 127,201 native,
115 affine, 117 equivalence and 34 binary-discovery records. All old authoritative
payloads are unchanged; 424 alternative-payload observations remain in the raw
trial archives.

The cumulative database is 1,520,734,208 bytes; its gzip stream is 108,952,833
bytes. The three transport parts contain 50,331,648, 50,331,648 and 8,289,537
bytes. Their reconstructed stream and database match the original hashes.
Full validation takes 726.30 seconds, including 77.63 seconds for compression,
0.12 seconds for splitting and 2.37 seconds for the byte-identity round trip.
These preservation costs are separate from the online worker measurements.
