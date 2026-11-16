# Incremental checking of persisted conditioning routes

Updated 2026-11-16. This experiment addresses the repeated verification identified
in [the broader conditioning comparison](bootstrap-conditioning.md). It changes
route maintenance while preserving candidate selection and inference. The
optional implementation is `experiments/cnf_split_registry.py`; all previously
bound implementation files and results remain unchanged.

## Result and comparison

The two arms enumerate the same candidates on the same 24 adaptive development
inputs, from the same checked 85-pattern seed. Both retain the 40-state recognition
allowance, explicit source-assumption charges and complete row-preservation audits.
Three repetitions alternate execution order. A common lightweight wrapper counts
split-verifier calls; profiling is separate from these timings.

| Measurement over 24 queries | Rebuild all routes | Incremental registry |
|---|---:|---:|
| Mean query seconds | 7.41290 | 4.26395 |
| Mean setup plus query seconds | 7.67315 | 4.52933 |
| Mean route-maintenance seconds, within queries | 3.23709 | 0.09428 |
| Split-verifier calls during queries | 3,913 | 258 |
| Route-record verification calls | 3,741 | 86 |
| Fresh probes | 3,946 | 3,946 |
| Fresh explicit source assumptions | 172 | 172 |
| New patterns / total patterns | 558 / 643 | 558 / 643 |
| Persisted source pairs | 86 | 86 |
| Structural coverage | 5/24 | 5/24 |

Query time falls **42.5%**, or **41.0%** when charged setup is included. The registry
avoids 3,655 verifier calls. The remaining 258 calls consist of the unchanged two
local checks per acquired pair and one registry check per new persisted record.
The original full builder checked `86*87/2 = 3741` records during route rebuilds.
The registry checks 86. No source-trace generation or inference is skipped.

Every query matches the frozen baseline's chosen variables, admitted/stored state
identities, probe counts, cap status and pending branches. All six archives are
**byte-identical** to the prior enumeration database: **12,156,928 SQLite bytes**,
compressed to **629,031 bytes**. Positive proofs match exactly, and the nineteen
uncovered originals remain uncovered. This experiment improves a measured cost;
it does not expand structural coverage or reduce the number of SAT subproblems.

Cold positive checking remains unchanged. Its means are 2.08123 and 2.12079 seconds
for the two arms; gzip compression adds 0.21896 and 0.21982 seconds separately.
These small timing differences do not indicate a cold-replay improvement. Common
seed acquisition was already charged in the previous study at 0.76235 seconds.
Report construction and diagnostic metadata serialization are outside query time.

## What is reused, and when it remains valid

The registry is tied to one live inventory, connection and serialized recognition
policy. It reads each newly persisted pair from SQLite and runs the original
checker before retaining only its source, ordered child identities and insertion
order. It does not retain another copy of the unit certificates. It checks child
availability and indexes missing children back to their dependent pairs. Later
pattern inserts notify only affected pending pairs. Once both children exist,
the route becomes available; ordinary composition still requires justified plans
for both children. No cached closure bit decides an answer.

An immediate SQLite transaction stabilizes each refresh. Data/schema versions,
total writer changes, suffix row IDs and table cardinalities constrain updates
to committed appends to the pattern and split tables. Updates, deletion,
replacement, rolled-back writes, unrelated writes, policy changes and detected
external changes invalidate the registry and require reopening checked state.
The workflow uses the inventory's standard SQLite tables and automatically
allocated positive row IDs. It assumes exclusive ownership and immutable Python
inventory state; it is not a defense against raw-file tampering or deliberately
rewritten pragmas. The independently checked cold proof remains authoritative.

Route order is restored to insertion order when an older pending pair activates.
Repeated child identities retain both AND premises. A caller mutating its own
record object cannot alter the registry, which reads the persisted payload.
Composition runs again on the current graph, so newly available routes cannot be
hidden by stale negative closure results.

The maintenance invariant is equality with a full rebuild of the persisted pair
catalog. It holds initially by checking every pair. An accepted append cannot
change an earlier source or record. New records are checked before indexing, and
every missing-child dependency is removed only after the appended child loads
successfully. A route is therefore present exactly when its two checked premises
are available, with the same order and multiplicity as the full builder. Ordinary
composition and the independent positive checker then retain their obligations.

For K acquired pairs, route-certificate verification falls from K(K+1)/2 calls to
K. This is a call-count bound, not a linear total-runtime theorem. Checking costs
depend on trace sizes; count guards read index pages, suffix processing reads new
pattern IDs, per-source route ordering may sort alternatives, and composition
and complete row audits remain. Total recognition work can still be exponential.

## Memory and persistence

The final live registry holds 86 records: 85 active and one waiting for one child.
Its metadata serialized for size accounting occupies **2,141,339 bytes**, including
repeated expanded identifiers in several indexes. This is not peak RAM or a lower
bound on exclusive additional heap memory: Python shares some objects, and the
serialization itself is temporary. The optimization exchanges live metadata for
less repeated checking; it establishes no memory reduction. No new persistent
table, cached trust bit or archive format is introduced.

Cold construction checks all 86 pairs anew. Six comparison archives, a separate
profiled archive, the seed and the unchanged 1,154-pattern parent union pass cold
validation. For each comparison/profile archive, sixteen unchanged registry
refreshes perform zero split-verifier calls and preserve the complete route
catalog. The full positive checker is run separately with fresh acquisition
disabled. All **341 inherited and new tests pass**. Targeted tests cover delayed
children without a new pair, interrupted acquisition, reversed completion order,
duplicate children, caller mutation, non-append writes, changed policy/schema,
an external payload edit, cold reconstruction and forged evidence. An initial
test used a no-op external SQL update that SQLite did not physically write; the
corrected test performs an actual payload edit. Both test logs are preserved.

## Next discovery target

The separate profile reproduces the graph and bytes. Fresh cofactor acquisition
and its recognition/checking layers now dominate querying; route maintenance
accounts for about 0.094 seconds of the 4.264-second unprofiled stream. Profiled
cumulative times overlap and include cold replay, so they must not be added.

The largest mean unresolved query is **case 16**, at **0.31922 seconds / 205 probes
/ 27 admissions**. It is not capped. Its selected residual has **59 variables,
245 clauses and 743 literals**, with width at most four. Its saved pivots are
7, 37, 5 and 51; all eight child records exist, but none has coverage under the
complete preserved union. Cases 17 and 22 are useful controls: they take 0.31322
and 0.29388 seconds, with 224 and 235 probes, and are also uncapped.

`experiments/results/cnf-split-registry/next-discovery.json` binds case 16's exact
source, all eight branches and their checked status to the prior union checkpoint.
Continue from that union, following existing reduction edges before acquiring
deeper splits or testing interaction summaries. Increasing the current admission
allowance alone will not change an uncapped fixed four-choice policy. Treat the
four unsuccessful choices as retained evidence, not candidates to reacquire.
This remains a finite adaptive study; no unrestricted-SAT efficiency bound or
new SAT/UNSAT verdict is claimed.
