# Bounded reuse of exact successful probe checks

A 1 MiB logical cache avoids repeated proof checks while preserving **all 1,497
answers, structural profiles, source identities and database bytes**. Coverage is
unchanged at **869/985 non-tiny sources**, with **116 sources / 148 selected leaves /
33,651 literals** unresolved. The ordinary SAT decision solver is unchanged.
This improves acquisition cost on the measured workload, not structural coverage
or unrestricted-SAT complexity.

| Measurement | Existing checker | Exact-check cache |
| --- | ---: | ---: |
| Full operation seconds | 168.30879 | 150.39216 |
| Discovery seconds | 125.59834 | 108.60557 |
| Ordinary solver seconds | 42.63160 | 41.72166 |
| Cold replay seconds | 71.60183 | 62.58623 |
| Warm inventory seconds | 0.27219 | 0.26053 |
| Initialization seconds, separate | 0.00168 | 0.24030 |
| SQLite bytes | 437,620,736 | 437,620,736 |
| Logical pattern-node bytes | 179,395,726 | 179,395,726 |
| Six-case Python peak bytes | 21,161,086 | 22,258,162 |
| Maximum retained cache-string bytes | 0 | 1,048,576 |
| Replayed probe attempts during operations | 248,307 | 113,301 |
| Restriction literal visits during operations | 126,081,638 | 82,210,169 |
| Simplification reconstruction literal visits | 82,973,454 | 51,574,914 |
| Propagation literal visits | 105,860,805 | 105,860,805 |

Full single-sample time falls **10.65%**, discovery **13.53%**, and cold replay
**12.59%**. This trades extra bounded cache state for reduced replay. The six-case
Python peak grows by **1,097,076 bytes**; the logical cap excludes Python allocator,
LRU overhead, transient serialization and original graphs. It is not an RSS cap
or full-process memory bound. The default existing policy remains available.

## Conditions for reuse

Only successful calls to the complete existing probe checker enter the ephemeral
LRU cache. Every lookup serializes the complete source, proof and policy config;
full-key equality is required, so no hash-collision-free assumption or identity
shortcut is used. A hit decodes fresh output, isolating caller mutations. Source,
proof or policy edits miss; a restart is empty; evictions cause rechecking.
Oversized entries are checked without retention. Persistent proof records and
policy identities are unchanged.

The typed-input condition matters. JSON identifies tuple/list containers, but the
existing checker requires a list of original attempts. Non-list attempts bypass
the cache and go to the old checker before lookup. A regression test warms the
cache with a valid list and then rejects its colliding tuple. The preliminary
implementation/pilot, comparison-harness failure and interrupted full run remain
in the adjacent pilot/initial-check directories. Only the guarded full run and
[guarded pilot](../cnf-checked-probe-reuse-guarded-pilot/README.md) are final evidence.

The complete run has **57,798 lookups, 34,971 hits, 22,827 misses/admissions and
22,571 evictions**. It serializes **135,220,528 input-key bytes**, serializes
**22,273,703 result bytes**, and decodes **29,375,582 bytes** on hits. Total admitted
string volume is **78,031,066 bytes**, even though at most 1 MiB is retained. This
churn and recognition work are charged. Fewer logical replays do not make lookup
constant-time. No oversized entry occurs in the full sample; tests cover that path.

With input size K, result size R and old checker cost V, a hit replaces V with
encoding, hashing/equality and decoding work. A miss adds those preparation costs
to V. The cache retains at most B serialized string bytes, with object overhead
and temporary O(K+R) construction in addition. The bound does not constrain the
old acquired graph, solver or lifetime archive. The fixed implementation's cache
invariant is tested, not a Lean refinement or a new complexity theorem.

## Repeated timings and the next bottleneck

Twelve-query ABBA BAAB controls give mean total **6.17550 -> 5.33388 s** and
discovery **5.88231 -> 5.04230 s**. All four cached totals (5.27161--5.38252 s)
are below the four baseline totals (6.11412--6.22190 s). The unchanged solver
averages 0.29174 -> 0.29045 s. These selected synthetic queries and four trials
per mode do not establish industrial performance, significance or repeated
full-corpus estimates. Every trial matches full-run answers/summaries; counters,
storage and database hashes repeat within each mode.

In a separate profile of the largest baseline miss, source **1194**, restrictions
fall **5,763 -> 3,399** and simplification checks **4,657 -> 2,303**. Propagation
stays **2,221 calls** and is now the largest named-function own-time cost, narrowly
ahead of restriction. Instrumented total time is 4.99171 -> 3.99936 s; do not
compare it directly with uninstrumented acquisition seconds. First-time propagation
and remaining whole-source preparation/checks now deserve attention. Occurrence
indexes or affected-clause updates must retain explicit source/assumption bindings
and a documented proof-order policy; reordering discovery can affect later choices.

Coverage still requires new certified relations or exact decompositions of the
116 unresolved sources. The cache learns no new pattern. A separate memory
opportunity is to test 256 KiB against 1 MiB on the full corpus: the guarded pilot
gets 1,385 versus 1,387 hits, but this does not prove an optimal global budget.
The previous implication relevance-filter control also remains unintegrated.

## Persistent evidence and validation

Both full modes recreate the previous implication-study database **byte for byte**:
25,047 pattern nodes, 1,465 source records and 21,838 ordinary solver residuals.
The archive is retained once at
`experiments/results/cnf-implied-subsumption/archive-implied.sqlite3.gz`; report
archive paths are relative to the repository root. Both cold checks start empty,
verify every alternative/source/solver certificate and leave the bytes unchanged.
Warm replay inserts nothing. There is no duplicate full archive or new policy
namespace to inflate lifetime storage.

All **410 tests** pass, including exhaustive tiny fibers, saved unresolved probes,
source/proof/policy edits, tuple/bool distinctions, caller mutation, bounded LRU
and oversize behavior, old-format replay and corrupted cold evidence. Lean source
files are unchanged from the preceding 4,130-declaration/1,972-theorem audit; this
cache has no new formal Python refinement. The full report has **62 fingerprints**.
Pilot snapshots preserve earlier runner/implementation hashes without overwriting
failed or superseded experiments.

Operation timing includes discovery, checking, key construction and lookup,
decoding, serialization, persistence, solving and successful root lifts. Generation,
summary walks, hashing, compression, initialization and audits are excluded or
separate. Extra pointwise checks are outside the timed query stream so they cannot
warm this cache; tests and the identical previously checked archive retain that
validation. Allocation diagnostics use six fixed cases and exclude native SQLite,
RSS and full-corpus peak. Benchmarks and later diagnostics run sequentially.

Reproduce using a new destination:

```sh
python3 experiments/compare_cnf_checked_probe_reuse.py --output /tmp/new-checked-reuse
python3 experiments/recheck_cnf_checked_probe_timing.py /tmp/new-checked-reuse
python3 experiments/analyze_cnf_checked_probe_reuse.py /tmp/new-checked-reuse
```
