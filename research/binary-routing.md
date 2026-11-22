# A cheap cofactor does not determine the best continuation

The preceding binary-frequency policy reduced an exposed branch from 61 to nine
expansions, but made a different branch grow from ten to 33. The first gap was
causal attribution: the compared streams had acquired different earlier proofs.
This study restores exactly the saved persistent state before the regressing
branch, starts each policy with empty transient caches and pools, and reproduces
**10 / 35 / 33 expansions** for original / four-target / binary-frequency routing.
All exploratory proofs and discovery traces are retained. This establishes a
policy effect under that state; instrumented diagnostic times are not speedup
measurements.

The branch has 327 clauses and 125 variables, including one unit. Its unit
closure fixes six variables, leaving 294 binary/ternary clauses on 119 variables.
The original policy then selects variable 75 by total frequency. The broader
target rankings instead derive variable 8 from binary implications. These names
are local to the normalized residual. Setting the original variable false yields
a unit contradiction, even though that variable is not forced by binary clauses
alone. This motivates checking the cheap default cofactor before committing to a
different binary consequence.

## Checked priority rule and accounting

The optional rule first runs the preceding binary-frequency recognizer, preserving
its contradictory-subset and whole-cover priorities. If it finds a forced variable
different from the ordinary frequency split, it checks the ordinary variable's
false cofactor. A cached native negative answer is reused directly. Otherwise one
unit-propagation run may produce a negative certificate. A cached model or a
no-conflict result grants no source-level conclusion and leaves the binary choice
in place.

Every new negative cofactor is canonicalized and checked through the unchanged
native unit-trace verifier before publication. Only then does the rule search the
true cofactor and combine the two through a native split. A positive result must
lift to a full source model. On a budget stop, the existing acquisition wrapper
can retain completed checked nodes while leaving the queried root unresolved.
Unexpected failures retain its previous transaction handling. Tests distinguish
these cases using a satisfiable source whose false cofactor is refuted.

The extra probe is admitted only for sources with at most 256 variables, 4,096
clauses and 16,384 literals. These are shape limits, not time or memory guarantees.
At most one extra cofactor is propagated per eligible native expansion. Frequency
ranking and restriction cost a scan; the current repeated-scan unit propagator
costs `O(V L)` in the worst case. The temporary cofactor and trace require
`O(L + V)` space. Normalization, historical proof checking, publication and the
surviving search are additional costs. A cached proof's dependency graph need not
fit these source limits.

Crucially, this probe is **not counted as an ordinary native expansion**. Its
literal visits, canonicalization, lookups, checking and direct publications are
charged separately. Moving a unit-refuted child into direct compilation can lower
the expansion counter without eliminating its computation. The shared limit of
256 ordinary expansions therefore does not bound all discovery work or all
published proof nodes.

## Frozen comparison

Three policies run in separate serial workers in two opposite orders: original
targeting, binary-frequency targeting, and the checked cofactor-priority rule.
The 14 targets comprise six prior edit controls, both exposed isolated branches,
and six new neighbouring edits generated before solving. New roots are absent
from the preceding cumulative union. Each isolated branch uses only its saved
pre-branch publications; other trials use the preceding cold seeds.

Whole-query streams retain the same eight-expansion probe and six-clause
first-false partition wrapper, including the shared 256-expansion budget.
Isolated branches use native acquisition. Candidate donors and variable maps
remain supplied; these are local residual comparisons, not automatic discovery
coverage or representative external SAT benchmarks. The process-local method
patch is an experimental adapter, not a thread-safe public API or default change.

The inherited harness measures preparation, checking, publication, serialization,
persistence, warm reuse, full cold replay and reconstruction. Complete-worker
time includes measurement/audit overhead; earlier acquisition is sunk. Individual
regressions and both order signs remain in the results. All earlier authority is
preserved; alternative trial proofs remain in their deltas.

## Result: reject the false-only guard as a speed optimization

All policies return UNSAT on all 14 targets. The following costs average the two
orders and sum independent case streams. Decision coverage is unchanged.

| Stream | Original expansions | Binary-frequency expansions | Priority expansions | Binary query seconds | Priority query seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Six prior controls | 122 | 88 | 86 | 0.23293 | 0.24299 |
| Exposed useful branch | 61 | 9 | 8 | 0.02409 | 0.02443 |
| Exposed regression | 10 | 33 | 32 | 0.06389 | 0.06435 |
| Six new edits | 108 | 53 | 52 | 0.18176 | 0.19052 |

Relative to binary-frequency routing, the guard increases mean query time
**4.32% on controls and 4.82% on new edits**, with both orders worse. The isolated
branches also have higher means, although their order signs are mixed. Complete
measured time changes little: controls rise **0.01%**, new edits **0.52%**, and
the two isolated branches improve about 0.3--0.4%. These small complete-time
differences do not establish a useful overall gain.

The guard performs twelve extra propagation probes on controls, six successful,
and ten on new edits, five successful. They add **26,736 / 23,815 propagation
literal visits**, besides normalization, lookup, checking and publication. On new
edits, native key/payload bytes grow **467,415 -> 481,103**, endpoint checked
objects **3,044,975 -> 3,104,476 bytes**, and compressed deltas plus raw sidecars
**150,586 -> 151,648 bytes**. The raw sidecars stay unchanged. Endpoints are sums
of separate states, not peak-memory bounds. One fewer expansion is therefore
not evidence of less total work or memory.

The two-query case-31 control stream falls only **80 -> 78 expansions**. Its
deletion changes **29 -> 28**, and its replacement **51 -> 50**. The regressing
replacement branch remains expensive at 32 expansions. Direct compilation saves
an ordinary visit, but does not cure the bad continuation. Keep the original and
binary-frequency policies; retain this implementation and experiment as an
unsuccessful optimization rather than promoting it.

## Precise remaining gap: choosing the probe polarity

The first later common residual has 285 clauses and 784 literals. The original
policy splits variable 76 there; the priority policy instead forces variable 8.
For variable 76, the false cofactor produces no unit assignment and no conflict.
The true cofactor produces 39 forced assignments followed by a contradiction.
The latter has an independently checked native unit certificate. The false-only
guard misses this available deduction.

`next-target.json` records this source and exact preceding proof availability.
An instrumented run stops before visiting the residual, captures the one earlier
checked publication (still pending in the live transaction), then aborts that
diagnostic transaction. A fresh snapshot restores the saved regression prefix
plus that one checked row, verifies it, and confirms that the target root is
absent. Neither the target's later proof nor any target search enters the seed.
The cofactor certificate is checked separately without writing to the snapshot.

**Next experiment:** compare both-polarity probing or a justified polarity choice
from this identical state. Include signed variants and fresh edits so the gate is
not selected for a particular false/true convention. Charge the additional probe
and retain successful cofactor evidence instead of rediscovering it. Even finding
a forced value is not a guarantee of the cheapest continuation; that larger
routing question remains open.

This study closes the persistent-state confound for the saved regression and
establishes a concrete polarity counterexample. It does not add a tractable SAT
class, automatic donor discovery, source-level coverage, or a polynomial bound
for arbitrary expansion.

## Measurement and preservation notes

A 0.34-second diagnostic briefly overlapped the final timing stratum. Both orders
and all policies for novel case 61 were repeated together after it finished;
the original samples remain in `first-pass-report.json` and their directories.
Proof deltas, decisions, partitions and expansion counts match exactly. The
replacement was by stratum, never by choosing the faster sample. A failed first
diagnostic assertion compared SQLite tuple rows to JSON list rows; its source and
log are preserved. Normalizing row representations fixed the diagnostic without
changing any timed solver policy.

Validation passes: **1,402 full / 84 focused tests**, 84 chronological comparative
attempts, and 12 retained first-pass attempts whose proof bytes and decisions
match the serial repeat. Both native readers recheck the cumulative authority and
24 new / 90 preceding partition sidecars. The union preserves all earlier
payloads and now contains **75,062 native records**, adding 183 unique records
across the trials and exploratory runs. Alternative payload observations remain
in the trial deltas. All 703 prior sources and 9,515 artifacts in 129 manifests
are unchanged; older unrelated audits remain manifest-bound. The full suite has
44 existing SQLite warnings; focused tests have none. The manuscript builds to
238 pages without warnings, with all 64 existing proof blocks unchanged.
Final source ledger: 712 files. Resume
`experiments/results/cnf-binary-routing/checkpoint.json`.
