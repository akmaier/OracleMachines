# Prefer an already checked quotient before fresh acquisition

The optional `KnownQuotientSolver` compares at most two native targets when a
source has multiple discovered equivalence blocks. It constructs and checks the
complete quotient first. If its exact native certificate is already available,
that target is selected. Otherwise it constructs the previous first-block quotient
and checks its exact native key. A hit selects that target; two misses retain the
complete reduction and ordinary acquisition. Single-block inputs and disabled
answer reuse keep the previous path.

Selection uses certificates available in the current history, never future
results or family labels. Every hit passes the existing native reader. SAT models
are transported from canonical quotient variables back to their original IDs,
then lifted using the actually selected block map and checked against the source.
UNSAT results publish the corresponding checked v2/v3 source evidence with the
native negative dependency. Extension-only targets do not qualify as native hits.
No new proof format or proof authority is introduced, and previous records remain
readable. Warm full-source answers bypass quotient selection entirely.

This recovers the two opportunities diagnosed in the previous pilot: taking a
known one-block quotient can be cheaper than acquiring a smaller, unfamiliar
complete quotient. It does not find a minimum-cost subset of blocks. In particular,
the complete target is preferred when both targets are known without comparing
their cold proof costs, and extra choice work can outweigh avoided acquisition.

## Pilot and excluded fresh continuation

Six serial workers compare the cached single-block policy, cached all-block policy
and known-quotient policy in opposite orders. Each starts empty on the previous
68-source pilot, followed by **24 generated sources and twelve wide-clause edits**.
All 36 appended source roots are excluded against the parent's native and v1/v2/v3
archives. The generated controls cover four existing families at nominal sizes
12/16/20; graph colouring uses up to 21 Boolean variables. The edits deliberately
become tautologies under the first block and preserve both quotient identities.
These are designed reuse controls, not an independent representative SAT sample.

All policies return **42 SAT / 62 UNSAT**. The original single/all comparator
acquisitions reproduce byte-for-byte on the first 68 queries. Known-quotient
selection makes 24 choices: ten complete-target hits, four first-target hits and
ten two-target misses. It performs **38 native lookups** and constructs fourteen
extra first-block alternatives. All fourteen hits are present before their actual
query, independently checked in both worker orders; none performs fresh native
expansion. Both SAT and UNSAT first-target hits occur.

| Per worker, except mean times | Single block | All blocks | Known quotient |
|---|---:|---:|---:|
| Native expansions | 503 | 511 | 505 |
| Propagation visits | 74,980 | 74,713 | 74,503 |
| Native certificates | 550 | 560 | 552 |
| Negative extension certificates | 53 | 53 | 53 |
| Native payload bytes | 618,602 | 621,319 | 618,043 |
| Extension payload bytes | 32,339 | 33,871 | 33,741 |
| Combined payload bytes | 650,941 | 655,190 | 651,784 |
| SQLite bytes | 1,163,264 | 1,208,320 | 1,179,648 |
| Compressed bytes | 124,641 | 128,431 | 125,493 |
| Query seconds, including metadata | 0.47380 | 0.48080 | 0.48852 |
| Complete-worker seconds | 0.70695 | 0.71722 | 0.72442 |
| Cold replay seconds | 0.09687 | 0.09556 | 0.09585 |

Against always taking all blocks, the policy saves **eight native certificates,
3,406 combined payload bytes, 28,672 SQLite bytes and 2,938 compressed bytes**.
It avoids six native expansions and 210 propagation visits. On the original pilot,
queries 7 and 34 again choose the first quotient, recovering the diagnosed eight
native additions. The pilot ends with 400 native nodes versus 408 for all blocks
and 398 for single-block acquisition. Two earlier history-dependent extra nodes
remain; known-target selection does not undo every effect of quotient choice.

The fresh continuation adds **152 native nodes under every policy**. Queries 94
and 103 reuse the corresponding first targets; ten other designed edits reuse
complete targets. The fresh segment saves 65 extension bytes against all blocks,
but no further native acquisition. Do not credit the eight pilot savings as a
new held-out solving gain. Single-block acquisition still has two fewer native
nodes and 843 fewer combined bytes over the full stream.

The extra alternatives raise substitution/verification scans **13,237 -> 14,312
literal units** (+1,075). Selection also charges canonicalization, reading and
checking exact native targets. Candidate-key traces add about **22.8 KB** to trial
sidecars versus all blocks. Both policies retain the same 46-entry discovery cache
(14,619 encoded key/value bytes; 35,779 Python-object bytes). The policy adds no
persistent selection index. Mean process RSS is about 59.2 MB for known selection
versus 59.4 MB for all blocks, a finite observation rather than a scaling claim.

Runtime does not establish a total benefit. Against all blocks, query deltas are
**-0.01425 / +0.02968 seconds** and complete deltas **-0.01613 / +0.03052 seconds**;
mean complete time rises **1.00%** and mean query time **1.60%**. Against single
block, complete time rises in both orders (0.00161 / 0.03333 seconds; mean 2.47%).
The reduction in repeated acquisition is real, but the full implementation remains
optional. Recognition and certification overhead must be included in its value.

Worker timing includes setup, discovery, extraction/keying, both checked
transformations, canonicalization, lookup, acquisition, publication, metadata scans,
warm answers, cold proof replay, sidecars and compression. Imports/source audits,
truth/chronology/history audits, posthoc profiling and final reports are outside
timing. No study tests/builds/audits overlapped the six completed workers. Public
`solve` times are recorded separately from metadata-inclusive query times.

## Next target from the measured cost profile

A separate instrumented replay produces identical decisions, counters and archive
payloads. It profiles only the 104 public `solve` calls, excluding setup, metadata
scans, warm replay, cold verification and compression. Its 0.679-second instrumented
time is not a comparator measurement. The largest exclusive entries are **605
SQLite transaction exits (0.116 s)**, **1,715 normalization calls (0.098 s self,
0.244 s cumulative)** and **1,591 SQLite executions (0.064 s)**. Cumulative times
overlap and must not be summed. Propagation itself is 0.023 s self / 0.041 s
cumulative in this replay, despite being a useful deterministic work counter.

**Highest-value structural reuse target: reuse normalization results within one
source query.** An exact-input census finds **505 repeated calls among 1,715**;
**469 repeats occur within a single query**. Those local repeats account for
50,817 input literal units, **96.39% of all repeated normalization input** and
29.01% of the total input units. At most 53 distinct inputs occur in one query.
The largest query's encoded input-plus-result footprint is 73,860 bytes, compared
with 1,448,226 bytes for retaining every distinct input/result over the stream.
These are serialization sizes, not Python-memory bounds or measured cache savings.

Test a bounded per-query cache of the immutable input snapshot and the complete
result triple: normalized CNF, original-variable name map and exact canonical key.
Retaining only the normalized formula would lose correct model-coordinate
transport. Validate nonzero integer literals before a hit, including rejecting
booleans and floats that can compare equal to integer keys in Python. Charge the
snapshot, validation, hashing, lookup, retained objects and eviction. Preserve
canonical identities and all certificates; reset at the next query. This should
be measured against both the present known-target policy and the simpler
single-block baseline. The census is an opportunity, not an implemented saving.

Per-record SQLite commits are a second large cost. Grouping publications would
change transaction and interruption boundaries, so it needs its own durability
and partial-result design. It is not part of this change. Broader semantic coverage
still needs work: the highest-propagation queries are random-three cases 49/48/47
(4,908 / 4,063 / 3,399 visits) and fresh cases 72/71 (2,775 / 2,744). Cheap known
quotient choice does not explain these residual interactions or yield an efficient
partition of arbitrary CNF.

## Persistence, failures and validation

Resume `experiments/results/cnf-known-quotient/checkpoint.json`. All **28,736 native,
26 affine, 42 v1, 42 v2, eleven v3 and 34 discovery records** are byte-identical.
The union adds **150 native keys, eleven v2 and eleven v3 records**, giving
28,886 native / 53 v2 / 22 v3 records. No old payload or alternative is replaced.
Union growth is **311,296 SQLite / 42,212 compressed bytes**, retaining every arm's
fresh results. All 5,650 old composed records and 340 prior pilot decisions remain
readable, with 104 new explicit decisions.

The initial benchmark stopped at cold-reader dispatch because a wrapper was
unwrapped twice. Its source/protocol and failure record are retained under
`failed-reader-dispatch/`; no completed sample is claimed. The temporary acquisition
database was already removed by the old cleanup path. The corrected harness now
archives partial records and the database if cold replay fails. A first posthoc
profile comparison also failed on runtime integer model keys versus JSON string
keys; its source/failure record is preserved. The successful comparison normalizes
JSON representation, then checks outputs, counters and full archive digests.

Eight new tests cover cold/warm positive and negative known targets, correct
variable-name transport, corrupt native records, full-target preference, two
misses, disabled reuse, warm-source bypass, 510 signed/wide mixtures and edits.
Validation checks **624 chronological queries, 104 exhaustive source truths,
36 parent-root exclusions, 48 exact prefix choices and 28 known hits** across both
orders, plus all old/new proof authorities and complete history. All 601 earlier
executable sources, 7,761 artifacts and 112 manifests remain unchanged. No new Lean
theorem, recursive production integration or unrestricted-SAT bound follows.

The **225-page manuscript** builds cleanly with all **64 earlier proof blocks**
unchanged. All **1,253 full / 84 focused tests** pass. Final executable source
ledger: **607**. New manifest: **46 artifacts**, including the retained failed
setups and posthoc profile. Next preservation audit:
**7,807 artifacts / 113 manifests**.
