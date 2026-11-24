# Apply short guard contradictions during ordinary search

24 November 2026. This experiment takes the preceding offline guard interaction
compiler into live search. It tests whether avoiding local acquisition repays
support transport, consequence checking and proof composition on whole queries.
The conditional support banks are still explicitly provisioned.

## Exact scope of the gate

The gate runs only at an ordinary whole-probe site, after the existing structural
discovery attempt. It uses the existing source-coordinate tracker. Each query
checks its saved templates and original source containment. At a local residual,
an incompatible guard is discarded; only guards with zero, one or two unfixed
assumptions are considered. Wider guards remain preserved in the original bank.

The remaining assumptions form a candidate consequence clause. Before admitting
that clause, the implementation restricts the saved support by the source
assignment, maps its coordinates, and requires every surviving clause to occur
in the actual local CNF. It transports the unit trace and independently checks
the resulting clause by reverse unit propagation. A full-source certificate
cannot supply a missing component-local reason.

An empty consequence directly supplies a local unit refutation. Otherwise the
gate tries opposite units, then unit consequences with original binary clauses,
then supported binary consequences. The `units` arm stops before the last tier.
An SCC pass supplies two implication paths only when the graph contradicts.
Each path is compiled with the preceding source-level unit/split compiler, using
only hints on those paths. Native verification checks both cofactor proofs and
the final split. A satisfiable graph supplies no source verdict. Missing support,
unbound coordinates and exhausted allowances retain ordinary probing and branch
order.

The native 256-dispatch budget is shared across each whole query. Separate gate
allowances are 100,000 template checks, 1,000,000 reserved support literals,
4,096 compiled witness edges, and 256 edges per path. These are specific counters,
not limits on total time, native certificate storage or process memory. Source
validation, guard-pair scans, canonicalization, proof checking, retained prefixes
and cold replay remain additional work. The tracker and handoff adapter require
an exclusive synchronous session.

## Comparison and accounting

The protocol freezes all eight exposed edits and two serial repetitions in
opposite arm order. Every worker starts from the causal prefix immediately after
its origin and loads only that origin's support bank. The cumulative union,
later repeats and posthoc local hint bank never seed search. The four arms are
ordinary lazy binary probing, the preceding guided certificate-reuse policy,
the unit-guard gate, and the binary-guard gate. The latter two use ordinary
fallback ordering. There is no additional tracking-only arm; the previous
tracking experiment remains historical comparison evidence.

Setup includes loading and copying the provisioned bank. Solve includes source
checking, coordinate tracking, guard matching, local transport, graph work,
native compilation and fallback. Complete-worker time also charges prefix
restoration, accounting, warm replay of new native nodes, cold replay of all
native nodes, serialization and compression. Imports, frozen-source hashing,
initial source acquisition/extraction and the final preservation audit are outside
that worker interval. Memory measurements separate checked native state, bank
graphs, SQLite files and process peak RSS.

## Measured result: valid closures, higher total cost

All 64 timed workers stop at the 256-dispatch limit; no policy completes an
additional whole input. The unit policy closes 25 local contexts: 24 from
opposite unit guards and one from units plus original binary clauses. The binary
policy closes 34: 15 from opposite units, one from unit/binary interaction and
18 requiring binary guards. These are events on different live paths, not an
additive decomposition of the previous offline 61 closures or new solved inputs.

| Policy | Sum of solve means | Sum of complete-worker means | Local closures |
|---|---:|---:|---:|
| Ordinary | 8.02247 s | 93.68631 s | No added gate |
| Guided certificate reuse | 8.13361 s | 94.18340 s | No added gate |
| Unit guards | 8.61624 s | 95.58210 s | 25 |
| Binary guards | 9.53052 s | 96.52998 s | 34 |

Relative to ordinary search, unit guards add 7.40% solve time and 2.02%
complete-worker time; binary guards add 18.80% and 3.04%. Relative to guided
certificate reuse the solve regressions are 5.93% and 17.17%. Every binary-gate
case regresses in solve mean, from 5.98% on edit 1 to 36.38% on edit 40. Edit 64
has no closure and still costs 9.07% more. Two repetitions do not establish a
stable population estimate, but these results provide no basis for adoption.
Both gates remain explicit experimental policies.

Units admits 364 consequence occurrences across 670 sites, with 212 graph calls
and 645 inconclusive sites. Binary admits 1,218 occurrences across 669 sites, with
634 graph calls and 635 inconclusive sites. The latter reserves only 188 witness
edges for compilation, but visits 496,901 clauses to construct position maps and
charges 1,286,336 literal visits to consequence normalization. All current local
misses, including two unsupported binary-policy candidates, remain explicit.
Preparation is being paid far more often than a useful witness is compiled.

The adaptive profile selects edit 40 after the comparison. Only the query is
profiled, and the run reproduces its unprofiled native state and counters. The
binary gate takes 0.98437 cumulative profiled seconds over 91 sites. Its 318
support transports cost 0.61726 seconds, including 0.56672 in local RUP checking.
Seven closure compilations cost 0.28442 seconds. Across the entire query,
normalization rises from 679 calls / 1.00074 seconds to 1,117 / 1.68123 seconds;
canonical native verification rises from 367 calls / 1.22318 seconds to
407 / 1.39205 seconds. These cumulative times overlap and must not be summed.
Profile timings are diagnostic, separate from the unprofiled comparison.

Summed checked-native-state endpoints grow from 154,443,458 bytes for ordinary
search to 156,982,934 for units (+1.64%) and 164,001,110 for binary (+6.19%).
Summed SQLite endpoints grow from 719,503,360 to 720,584,704 and 723,243,008 bytes.
The gate's measured template/record graph is another 226,503--367,731 bytes per
worker; tracker metadata overlaps and must not simply be added to that graph.
Mean peak-RSS totals are 5.008 / 4.876 / 4.938 GB for ordinary / units / binary,
but are noisy sums of separate processes and do not establish a peak-memory
saving. These are comparison endpoints, not simultaneous memory requirements.

The durable new native-row totals across workers are 2,829 / 2,872 / 3,022 for
ordinary / units / binary, respectively. Native insertion counters also include
work later rolled back by inherited search transactions; they are not durable
storage counts. Raw final databases and alternative retained proof payloads are
preserved, and only checked durable contents enter the cumulative authority.

## Next step: defer proof preparation until a graph witness exists

Constructing a tentative graph from matching short guards is a sound way to
reject unnecessary closure attempts. Let B be the original binary fragment,
Q the candidate guard clauses, and Q_valid the subset whose local support checks
succeed. Since Q_valid is a subset of Q, a model of B and Q is also a model of B
and Q_valid. Thus a satisfiable tentative graph cannot hide a contradiction in
its supported subgraph. This is only a rejection of this closure opportunity;
it says nothing about satisfiability of the full original CNF.

If the tentative graph contradicts, every nonoriginal edge on its two witness
paths must still acquire a valid local certificate. Only then may the existing
compiler publish the source refutation. A tentative empty clause instead needs
its own local unit certificate. An unsupported edge can be removed and
the graph reconsidered within an explicit allowance, or the attempt can fall
back immediately. The tentative graph has no authority to prune a source
branch. This separates cheap candidate discovery from expensive proof
preparation without weakening the publication check. It is a proposed next
experiment, not an implemented saving in this checkpoint.

The separate hint store's repeated core bodies remain a secondary memory
opportunity. Automatic origin discovery, general coordinate transport, wider
guard interactions, fresh unlabelled evaluation and uniformly efficient closure
of arbitrary CNFs remain open.

## Checks and reproduction

All 1,758 solver tests and 36 focused tests pass. Tests cover source-level binary
composition, live exception routing and tracker cleanup, opposite units,
exhausted allowances, missing component support, deleted source support,
corrupted templates, agreement with the preceding offline transport, small
unlabelled truth cases and cold native replay. The full suite reports 43 existing
unclosed-SQLite warnings; the focused suite reports none. No new Lean refinement
proof is claimed.

The persistence audit replays each target/arm archive through both existing
readers and compares both repetitions' payloads, counters and binary archive
hashes. Unchanged arms can share archive contents; target/arm files and distinct
database hashes are reported separately. The ordinary and guided certificate
controls reproduce their previous states. An initial audit attempt rejected
absolute versus relative spellings of the same profile source path; the revised
audit checks the resolved path and exact source digest. Its failed log is retained.
Solver and comparison sources stayed frozen throughout measurement.

All 166 earlier manifests and 15,614 artifact entries remain unchanged. The
cumulative six-table bank retains every old payload and gains 60 native records,
reaching 160,165; the other five tables are unchanged. The union is 2,101,862,400
SQLite bytes, or 152,585,215 compressed bytes, with a byte-identical archive
round trip. Alternative valid payloads remain in the raw trial archives. New
nodes and dependencies replay through both readers; earlier full-history and
342-partition audits remain hash-bound rather than repeated. The final audit
takes 662.26 elapsed seconds including preservation and archiving; the test suite
runs concurrently during part of that interval, so this is not an isolated
performance measurement. All 64 pre-existing manuscript proof blocks are
byte-identical, and the 261-page paper builds without warnings.

Resume `experiments/results/cnf-guard-closure/checkpoint.json` using the multipart
reader. Reproduction uses a new output directory, then
`compare_cnf_guard_closure.py prepare` and `run`, followed by
`profile_cnf_guard_closure.py` and `validate_cnf_guard_closure.py`. The profile is
explicitly adaptive after the frozen comparison. Never overwrite old artifacts.
