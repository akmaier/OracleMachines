# Binary refutations inside unit-consistent probes

The preceding lifetime study left eight fresh roots unresolved. We inspect
whole-clause probes on the hardest random-three attempt, case 37, and the two
unresolved mixture edits, cases 61 and 67. The existing probe only accepts an
already checked negative result or a unit conflict. Its remaining cofactor can
still contain an inconsistent binary subsystem.

## Exact census before changing search

The observer replays the preceding 120/144 stream from an empty database through
case 67. It records only actually attempted nonconflicting whole probes on the
three selected queries. It does not enumerate unattempted assumptions or change
the original polarity order. The observer uses a separate counter, retains no
mutable search object, and publishes its candidate certificates in a separate
database. Search results, metrics and all six retained table payloads match the
preceding worker exactly at this chronological prefix.

| Target | Observed probes | Binary refutations | Inconclusive binary SAT | Uniform binary subset |
|---|---:|---:|---:|---:|
| 37, random-three edit | 112 | 7 | 105 | 0 |
| 61, disjoint-mix edit | 115 | 6 | 109 | 0 |
| 67, shared-mix edit | 126 | 6 | 119 | 1 |

There are **19 negative cofactors among 353 observed probes**, not 19 newly
decided whole inputs. Discovery takes 0.0790, 0.0599 and 0.0547 seconds on the
three queries, excluding record copying, serialization and separate proof
checking. These are exposed diagnostic measurements and not speedup estimates.
The complete census time and raw records are preserved separately.

For each cofactor, discovery reuses the existing unit assignment and trace.
If any variable was forced, it restricts and canonicalizes the residual once.
It extracts clauses of length two, skips a subset satisfied by a uniform
assignment, and otherwise invokes the existing SCC solver. A contradiction
supplies two implication paths whose clause indices are mapped back to the
residual CNF. The existing native implication certificate checks that residual;
an existing unit certificate links it to the original cofactor when needed.
No proof schema changes. Binary SAT remains inconclusive for the larger formula.

The argument is local. Every satisfying assignment of the cofactor must satisfy
its forced units, hence the remaining clauses and their binary subset. An
inconsistent subset therefore refutes that cofactor. One excluded parent
polarity does not refute the whole parent: the other polarity still needs a
checked result, and a positive lift must satisfy the full source. Existing
native split and unit rules perform that composition.

## Prospective policy and charged costs

The optional policy runs this closure after a whole probe's ordinary unit pass
is inconclusive. A hit publishes fully checked native nodes, reusing an existing
negative node when available, and returns the original cofactor key. A miss
retains the previous prepared-offer and ordinary search path. It does not
replace higher-priority proof/model pools, change the native certificate reader,
or change production defaults. A shared subset's SAT model is never treated as
a full-CNF witness.

The measured configuration is
`BinaryClosureSolver(..., handoff_bytes=2*1024*1024)`; the inherited constructor
default remains 256 KiB. Implementation, census, comparison, profiling and
validation scripts use the `cnf_probe_binary_*` names under `experiments/`.
The frozen raw results and resumable checkpoint are in
`experiments/results/cnf-probe-binary-census/`.

Four alternating serial repetitions compare this policy with the preceding
2 MiB pending-handoff policy on the exposed 120/144 stream and a fresh 126/150
stream, seed 202611240303. Each has 72 queries and 48 distinct roots across six
construction families; only the source CNF enters solving. The fresh corpus and
implementation are frozen before evaluation, without outcome filtering. Each
arm starts empty with the same 256 native-dispatch cap. This cap does not bound
the new compiled proof nodes, checking, total runtime or memory.

Misses pay for residual restriction, normalization, binary extraction and SCC
work too. For `b` binary clauses and `v` supported variables, the current graph
routine takes `O(b + v log(v+1))` expected word operations, including its explicit
variable sort, and `O(b+v)` graph space. This is only one part of the gate:
normalization, literal bit lengths, source-key serialization, proof construction,
source checking and persistence remain charged. A hit can store both residual
and cofactor CNFs, increasing proof bytes despite avoiding native dispatches.
The number and size of unresolved search residuals keep their unrestricted
costs. These local certificates do not yield an efficient partition of all SAT.

The initial positive test fixture failed to exercise its intended guard because
the existing frequency tie-break selected a smaller variable. The preserved
failure and original fixture are in `development-guard-tie.json` and
`closure-development-tests-initial.log`. Correcting the fixture to use the
smallest variable as its guard changed the test only; the policy was unchanged.

## Matched result: keep the gate experimental

Every query has the same verdict status in both arms. Distinct-root coverage
stays **40/48 on both streams**, with no gained or lost roots. On fresh inputs,
six random-three roots and two shared-mix edits remain unresolved. The same
native-dispatch cap is used, but its count is not a complete measure of work.

| Measure | Exposed current | Exposed closure | Fresh current | Fresh closure |
|---|---:|---:|---:|---:|
| Mean solve seconds | 17.6587 | 19.2216 (+8.85%) | 17.2597 | 18.7885 (+8.86%) |
| Mean complete-worker seconds | 36.4318 | 38.3534 (+5.27%) | 34.9515 | 36.7112 (+5.03%) |
| Native dispatches | 4,676 | 4,618 | 4,762 | 4,701 |
| Native proof records | 6,974 | 7,090 | 6,558 | 6,730 |
| Native key-plus-payload bytes | 76,527,327 | 78,134,638 | 76,026,564 | 78,095,587 |
| Selected retained Python bytes | 315,074,010 | 321,475,244 | 315,842,093 | 324,328,237 |

All eight solve and complete-worker pairs regress. Fresh solve increases range
from 8.38% to 9.49%; complete-worker increases from 4.04% to 5.74%. Four fixed
repetitions do not establish population performance, but provide no basis for
enabling the gate by default. More cofactor certificates do not translate into
more completed roots on these streams.

Fresh discovery makes 2,239 closure calls and 2,028 SCC calls. Eighty cofactors
are refuted, but 2,159 closure calls remain inconclusive. The gate scans 776,346
residual clauses and 353,414 binary literals, and publishes 158 native nodes.
It saves 61 native dispatches (1.28%) while the changed search and publications
add 172 native records (2.62%) and 2.72% native payload. All publication,
verification and miss costs are included in the comparison; the new compiled
nodes are not counted as native dispatches. This is why a smaller dispatch
count cannot be used as the expansion-cost conclusion.

Fresh SQLite grows from 116,924,416 to 119,922,688 bytes (2.56%); compressed
storage from 8,748,860 to 9,007,159 bytes (2.95%). Selected retained Python state
grows 2.69%, and mean worker RSS from 1,240.4 to 1,257.5 MB (1.38%). RSS also
includes replay and reconstruction, so it is not a discovery-only bound.
Fresh cold verification rises from 7.2417 to 7.3734 seconds; reconstruction
from 1.2102 to 1.2289. No persistent-space improvement accompanies the extra
recognition. Old native payloads remain untouched in the cumulative archive;
raw trials retain alternative valid proofs.

## Next target: defer work that cannot produce a stored result

The largest mean fresh query regression is case 38, a repeated random-three
source at construction size 150. It stays unresolved in both arms and rises
from 1.1528 to 1.3005 seconds (147.67 ms). Each profile reconstructs its own
exact chronological prefix, matches every query status/counter and checks all
retained payloads against the corresponding worker. Instrumentation and its
concurrent verification run outside the matched means.

The gate makes 100 closure calls on that attempt, all reaching SCC, but finds
only six refutations. It nevertheless normalizes and serializes 67 post-UP
residuals. All six hits have a forced assignment (twelve published nodes), so
**61 normalizations lead only to inconclusive results**. The ordinary profile
has 734 normalizations and 843 restriction scans; closure raises these to 852
and 958. Its helper contributes 0.3275 cumulative profiled seconds, including
0.1078 in normalization and 0.1228 in SCC. These overlapping instrumented times
are attribution evidence, not predictions of unprofiled savings.

The most concrete next candidate is to inspect the binary subset in the raw
post-UP coordinates first, and canonicalize the whole residual only when a
negative binary result needs a certificate. The existing SCC routine accepts
noncompact variable labels. A negative raw decision would still need canonical
publication and source-index transport; rerunning SCC on the canonical residual
can preserve the preceding certificate bytes if necessary. Positive binary
decisions must remain inconclusive, and misses must retain the exact ordinary
fallback. Measure this against both the preceding handoff policy and this slower
closure gate. The candidate has not been implemented or timed here.

This would address only part of the regression. Extra recognition still builds
100 binary graphs in the selected attempt, and altered acquisition accounts
for normalizations beyond the 67 direct calls. Reusing already discovered
binary models or graph structure is a secondary question, requiring explicit
coordinate handling and validation against every new binary clause. A cached
subset model cannot certify its full CNF. The eight unresolved roots still
need structural coverage beyond this local gate; no general compression or
polynomial acquisition bound follows.

## Validation and preservation

All 1,689 tests pass, including 78 focused checks. The native source checkers
validate unit-to-binary composition, corrupted paths/indices, small exhaustive
truth tables, stopped prefixes, disabled leaves and cold zero-budget replay.
Independent auditing covers 1,152 benchmark queries, the 68-query census
prefix, all 353 census observations, both readers for every candidate proof,
and the 342 previous partition records. A separate 68-query baseline replay
checks exact equality of all six prefix tables, not just inclusion in the
later full archive.

The first audit run stopped before cumulative replay because its local probe
parent variable shadowed the parent checkpoint. Only the audit variable was
renamed; the frozen discovery and measured policy were unchanged. Its failed
log is retained as `validation-run-initial.log`. The previous test-fixture
failure is also retained. Neither is silently replaced by the successful run.
The full suite retains 44 pre-existing SQLite ResourceWarnings; the focused
suite has none. The manuscript builds to 254 pages without warnings. All 64
earlier proof environments remain unchanged; no Lean theorem or unrestricted
complexity conclusion is altered by this optional recognition policy.
The complete successful audit takes 835.7 seconds outside the matched means.
It preserves 158 previous manifests and 14,286 artifacts, then adds 7,015 native
records and eight affine-negative records to the union. The cumulative totals
are 146,760 native and 139 affine-negative records; binary tables remain at
42, 53, 22 and 34 records. These totals include preserved research history,
not just the current policy's retained state. Multipart transport preserves
the checked database bytes; it does not establish bounded history growth.
