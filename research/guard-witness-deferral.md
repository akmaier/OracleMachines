# Prepare local guard proofs only for contradiction witnesses

24 November 2026. The preceding live gate eagerly transported and checked every
short consequence before asking whether the graph contradicted. This experiment
reverses that order: first look for a tentative witness, then prepare only the
local certificates that witness needs. The existing native publication boundary
and ordinary fallback remain unchanged.

## Why the filter is sound

Let B contain the original unit/binary clauses of the actual local CNF C, Q the
short clauses suggested by matching source guards, and Q_valid the locally
supported subset. Before local checking, Q is only a candidate collection.
Because Q_valid is a subset of Q, any model of B and Q is also a model of B and
Q_valid. A satisfiable tentative graph therefore rules out this particular
short-guard contradiction opportunity. It supplies no SAT verdict for C.

For a contradictory tentative graph, both selected implication paths must be
supported by original clauses or checked local consequences. Every selected
nonoriginal clause undergoes the existing source-restriction, coordinate,
component-containment and RUP checks. Only then does the previous unit/split
compiler construct a native refutation of C. An empty candidate requires its
own local unit certificate. The tentative graph never authorizes pruning.

An unsupported witness candidate is removed and the graph reconsidered within
an allowance. Alternative supports for the same clause remain available. Checked
supports are shared within this local attempt; no such hint cache is carried
to another component, assignment or query. The native proof remains persistent.
These rules avoid inferring component independence from a disconnected guard
graph or applying a full-source reason to a component missing its support.

The implementation preserves the previous tier order: opposite unit candidates,
units with original binary clauses, then binary guards. It retains the first
tentative opposite pair and considers surviving alternatives after a failed
support. Selection among tentative paths can differ from selection after eager
filtering, so equality of final payloads and counters is measured rather than
assumed. It is not an assertion about an identical ordered execution trace.

## Scope of the comparison

The frozen protocol uses all eight exposed chronological edits and two serial
repetitions in opposite arm order. The four arms are ordinary lazy binary search,
guided certificate reuse, eager binary-guard closure and deferred witness
checking. Each worker restores only its causal origin prefix and that origin's
support bank. The cumulative union and later local census never seed a query.

The worker and its accounting are reused unchanged from the previous comparison.
Setup and solve include bank loading/checking, tracking, recognition, graph work,
selected support transport, native composition and fallback. Complete-worker
time also includes prefix restoration, state accounting, warm/cold replay,
serialization and compression. Imports, source hashing, protocol/case loading,
earlier acquisition/extraction and final preservation checks remain additional.

The native query cap remains 256 dispatches. Existing gate allowances remain
100,000 candidate checks, 1,000,000 reserved support literals, 4,096 compiled
witness edges and 256 edges per path. The deferred policy additionally permits
at most 32 rejected candidates per site and 1,024 tentative graph checks per
query. Exhausted allowances retain ordinary fallback. These counters do not
bound total verification cost, full retained state or process memory.

## Measured results

Two alternating repetitions give the following sums of per-case means. Times
are seconds; endpoint bytes are sums across separate runs, not simultaneous
space. All four arms leave all eight whole queries unresolved at 256 dispatches.

| Arm | Solve | Complete worker | Checked native bytes | SQLite bytes |
|---|---:|---:|---:|---:|
| Ordinary | 8.23359 | 92.92351 | 154,443,458 | 719,503,360 |
| Guided certificate | 8.33761 | 92.99237 | 156,832,198 | 721,047,552 |
| Eager guard closure | 9.55177 | 95.64075 | 164,001,110 | 723,243,008 |
| Witness-first closure | 8.88176 | 93.97898 | 164,001,110 | 723,243,008 |

Deferral reduces solve time **7.01%** and complete-worker time **1.74%** relative
to the eager gate. Against ordinary search it still costs **7.87%** more solve
time and **1.14%** more complete-worker time; against guided certificate reuse
it costs 6.53% and 1.06% more. Keep it optional. Seven of eight per-case solve
means improve against eager closure; edit 64 regresses 1.46%, despite requiring
no local proof transport. Both raw repetitions, including individual regressions,
are retained. These exposed diagnostics establish neither fresh performance
nor a distribution-wide speedup.

The deferred gate checks **87** local consequences instead of **1,218**, a
**92.86%** reduction. Consequence-normalization literal visits fall from
1,286,336 to 82,753; position-map clause visits fall from 496,901 to 60,938.
Candidate checks remain 33,006 and guard-pair checks remain 142,003. The gate
finds the same 34 local closures: 15 opposite-unit, one unit/binary and 18
binary-guard closures. There are still 635 inconclusive sites among 669 sites.
The 649 tentative graph checks include 615 satisfiable graphs and 34 witness
attempts. No unsupported selected edge occurs in these measured cases; rejection
and alternative-support behavior are exercised by the tests below.

For every target, eager and deferred runs have identical native metrics,
checked-native-state bytes, six-table payload digests and complete SQLite hashes.
Thus this experiment changes local preparation without adding durable solver
state or whole-query coverage. It does not record an ordered execution trace.
Native checked bytes remain 6.19% above ordinary search and SQLite totals 0.52%
above it. Template/record graphs remain 226,503–367,731 accounted bytes per
worker. That counter excludes transient candidate lists and local checked-hint
caches; process RSS includes broader activity. Per-target mean peak RSS ranges
from 212.63 to 1,005.13 MiB for deferral, versus 204.91–998.48 MiB for the eager
gate. No peak-memory reduction is established. The largest local candidate list
has nine entries on these runs; the aggregate counter sums per-query maxima
and must not be interpreted as one maximum.

## Next cost: compose over the actual contradictory support

The adaptive profile chooses edit 28, the largest remaining deferred/ordinary
solve regression at 15.49%. On that input, eager preparation checks 147 local
consequences, deferral 21, and both close seven contexts. The gate's cumulative
profile time falls from 0.35083 to 0.22224 seconds. Support transport falls from
0.15604 to 0.02386 seconds, including local RUP checking from 0.13909 to 0.02147.
The **seven native closure compilations now take 0.17224 seconds**, about 77.5%
of deferred gate time. Full-query native verification takes 0.75619 cumulative
seconds and normalization 0.61663. These nested profile times overlap; they
must not be added or substituted for the unprofiled worker comparison.

The next experiment should collect the actual source-clause supports of the
chosen contradiction paths and attempt composition on their union H, with
H a checked subset of the local CNF C. Include the original clauses used by
path edges and all local clauses required by their transported certificates.
A native refutation of H can then lift to C through the existing negative
`component` rule. That rule already accepts any contradictory clause subset;
this use requires no independence of support variables and asserts no positive
component join. Full source membership and native checking remain mandatory.

This is an identified opportunity, not an implemented saving. First measure
whether H is substantially smaller than C. Current path compilation builds
full-context cofactors repeatedly; a small H could reduce those copies and
permit exact reuse across different enclosing formulas. Recognition, support
extraction, canonicalization, local variable maps, verification, wrapper storage
and cold replay must all be charged. Guards may mention variables absent from
H after restriction: handle those cases explicitly instead of assuming every
split variable survives. A large H, expensive discovery or duplicated wrappers
can remove the saving. No small support is guaranteed for arbitrary SAT.

Core-body sharing in the separate hint bank remains a secondary memory target.
Automatic origin discovery and fresh inputs remain necessary to assess whether
this narrow composition improvement broadens useful structural coverage.

## Checks and remaining obligations

The focused tests include all 256 subsets of the eight nonempty unit/binary
clauses over two variables, each presented with the full candidate bank so
missing supports are exercised. They compare satisfiability with independent truth tables
and publish every returned refutation through the native checker. Other cases
cover zero-transport rejection, absent local support, alternative proofs for one
clause, empty candidates, allowance exhaustion, live routing, unlabelled small
CNFs and cold native replay. No new proof rule or Lean refinement is introduced.

Preservation distinguishes new verification from reuse of earlier verification.
An exact previously audited compressed archive, with the same database hash,
same-case verdict and six-table digest, may reuse its manifest-bound two-reader
audit. Novel archives must replay through both readers and append any new rows
without replacing old payloads. Every timed worker still performs cold native
replay. Sharing an earlier archive audit is not described as rerunning it.

Origin discovery, general coordinate transport, fresh unlabelled performance,
wider guards and uniformly efficient closure of arbitrary CNFs remain open.
This filter can avoid preparing unused evidence; it cannot guarantee that a
useful short-guard witness exists for every CNF.

## Preserved checkpoint

Validation passes: 46 focused tests and all 1,768 solver tests. The full suite
retains 43 pre-existing unclosed-SQLite ResourceWarnings; the focused suite has
none. The 262-page manuscript builds without warnings and its 64 previous proof
blocks remain unchanged. No Lean sources changed.

The preservation audit rechecks 167 prior manifests, 15,847 artifact entries and
all 966 previously frozen sources. All 32 current target/arm archives match
prior audited identities, so their two-reader audits are reused explicitly;
there are zero novel archive audits and no new cumulative rows. Worker cold
native replay still runs in all 64 timed trials and the three profiles. The
160,165 native records and all five other authority tables remain unchanged.
The exact cumulative union remains the preceding multipart archive.

Resume from `experiments/results/cnf-guard-witness/checkpoint.json`. Its protocol,
comparisons, profiles, analysis, decision, validation and sealed manifest retain
both repetitions and all four arms. The new solver, test and comparison sources
were frozen before timed comparison; profile selection was explicitly adaptive.
No previous source, archive or failed comparison is replaced.
