# Advance probe discovery through shared checked prefixes

The preceding [window study](probe-window.md) left 51 clear windows with later
binary-frequency candidates. Repeating their source/width keys reused the old
answer without advancing. The continuation implementation keeps those records
and adds a bounded next block, retaining negative results as useful discovery
history.

## Identity, checking and resumption

`cnf_probe_continuation.py` adds `cnf_probe_continuations_v1`. Each row binds the
complete canonical source (including configuration and depth), width four, an
offset, new attempt traces and the exact residual/name binding if forced. The
previous block is determined by the same source and width at offset minus four.
Offset zero refers to the existing window table. Previous traces are referenced
through this identity, rather than copied into every later row.

A cursor is not accepted by itself. The checker requires a complete clear
predecessor, recursively reaching the checked original window. Offsets strictly
decrease, preventing cyclic justification. The next candidates are reconstructed
from the original binary-frequency order, with original profile probes removed;
the order is still limited to its first 64 variables. Missing predecessors,
different sources, skipped blocks, forced predecessors and empty continuation
blocks are rejected. A final partial clear block exhausts that source's ranked
pool without creating further records or proving satisfiability.

By induction over blocks, every skipped candidate has two independently checked
no-conflict unit-propagation fixed points on this exact source. Those checks
justify the discovery cursor, not a SAT answer. A failed assumption has its own
checked conflict trace; all models must use the opposite value. Its independently
checked unit closure supplies an equisatisfiable residual with a model lift.
Continuing to that residual uses the existing structural recognizer and finite
route composition. This reuses established failed-literal reasoning; it does not
define a new tractable family.

Rows persist before recognition of a forced residual. An admission stop leaves a
pending transformation that restart can resume without repeating probe discovery.
Only a present, checked target becomes a route premise. Refresh also catches a
target acquired through another path, keeping resident and cold route availability
consistent. Earlier rows, identities, failed trials and ordinary solver proofs
remain unchanged.

## Work bound and comparison

Search visits at most four distinct unresolved sources per original and admits
at most 32 new recognition states, including descendants and unfinished parents.
At each visited source it acquires at most one new block of four candidates. A
shared source may advance again when visited by a later original; the ordered
input stream is therefore part of the experiment. An existing forced block
resumes its residual instead of advancing past a known failed assumption.

New probing uses at most eight single-assumption attempts per block, stopping at
the first conflict, plus propagation of its opposite value. Previously clear
attempts need no discovery in a warm checked session. Cold loading validates all
retained blocks once; resident reuse depends on this paid validation and immutable
source/policy identities. Ranking, reconstruction, checking, canonicalization,
recognition, route composition, serialization and persistence remain costs.
The implementation still ranks from the whole source and stores full canonical
keys in new rows; prefix sharing is not a claim of constant space or constant
total expansion time.

The experiment restores all seven earlier tables, adds the eighth and processes
the 83 selected development originals in their saved order, skipping roots already
covered. It retains the four-source/32-state caps and compares coverage against
the previous 36/83 result. A separate matched warm microbenchmark repeats the
same candidate work with and without rediscovering earlier clear blocks; both
modes independently check their new traces. It excludes persistence and target
recognition from both measurements, and reports full cold and end-to-end phases
separately. These reused cases, including ones historically named `holdout`, do
not establish independent evaluation or performance on arbitrary SAT.

Implementation checkpoint: `6671637`. All 547 tests pass, including missing or
foreign prefixes, exact forced residuals, interrupted acquisition, cold reuse,
pool exhaustion and eight-table preservation/conflict rollback. No formal sources
or manuscript claims have changed.

## Measured outcome

The [preserved run](../experiments/results/cnf-probe-continuation/README.md)
raises coverage **36/83 -> 39/83**. Independent reference solving confirms the
three gained 48-variable originals: case 39 (`selection_holdout3`, original 1229)
is SAT; cases 68 (`activity_holdout3`, 1412) and 79 (`implied_holdout3`, 1480) are
UNSAT. Removing growth-exception routes still leaves all 39 covered. Historical
group names do not make these reused development sources independent holdouts.

The run processes all 47 previously open originals and retains **51 continuation
blocks: 43 clear, eight forced**, plus five initial windows for newly reached
sources. It performs **409 new assumption attempts**, references **408 saved
attempts** without rediscovering them, and adds **45 recognition nodes**. Three
immediate continuation targets close; a forced value alone still need not close
a source. No admission stop occurs; the largest input uses 13 new states and
three distinct source visits. No continuation target remains pending.

On the same 51 new continuation blocks, the matched warm ranking/discovery/checking
microbenchmark needs **373 attempts with sharing versus 781 with rediscovery**.
Five alternating-order repetitions give median **0.13230 versus 0.27631 seconds**,
approximately **2.09 times faster for this substep**. The remaining 36 acquisition
attempts belong to the five new initial windows and are outside this comparison.
Both modes return exactly the same traces after concatenating the saved prefix.
Prior prefix verification, target recognition and persistence are outside both
microbenchmark timings; this is not a solver or end-to-end speedup.

| Cost or storage | Measured value |
|---|---:|
| Resident search, checks, persistence and per-input composition | 0.56578 s |
| Eligibility checks / final recomposition | 0.04648 / 0.05112 s |
| Paid-history preparation | 64.40934 s |
| Full cold inventory / separate route replay | 110.38830 / 63.12532 s |
| Complete acquisition/validation pipeline before final report write | 257.42807 s |
| Working database increase over seed with empty eighth table | 1,359,872 bytes |
| Delta SQLite / compressed | 1,429,504 / 82,368 bytes |
| Coverage witness JSON / compressed | 663,957 / 98,652 bytes |
| Separate reference solver nodes / database | 513 / 4,546,560 bytes |

The complete history now contains **41,461 pattern nodes, 75 initial windows and
51 continuation blocks**, together with all 563 pivot trials, 25 coupled trials,
one growth trial, 1,548 source bindings and 21,838 earlier solver proof rows.
The reference archive is additional paid evidence. Full cold verification still
dominates runtime, and peak process RAM is unmeasured. The earlier full prepared
result remains 902/985; this experiment does not rerun that entire corpus.

Resume with `restore` in `compare_cnf_probe_continuation.py`, verify/unpack the
new delta, then apply that module's **eight-table** `apply_delta` and compare
logical digests. `ContinuationRoutes` checks all prefix dependencies and older
trial kinds before composition. Never substitute an unchecked cursor or load
only the latest delta: earlier inconclusive windows are required evidence.

## Remaining gaps and next target

The independent validator reconstructs the eighth table and all predecessors,
replays coverage with new probe discovery disabled, and retains a discovery-free
`continuation-opportunity.json`. Of the 43 latest clear blocks, **42 still have
2--20 ranked candidates available**; one has exhausted its pool. Of eight forced
continuation targets, three close locally and a fourth closes by finite route
composition. The other four remain open. All five targets that are locally open
have one selected old-plan unresolved leaf; alternative routes remain available.

1. **Continue the remaining checked streams before broadening admission caps.**
   The mechanism can now advance without implementation changes. Resume the
   complete eight-table history, keep bounded new work and report gain per new
   attempt as windows move deeper. Stop when a source is forced or its ranked
   pool is exhausted. Later candidates are an opportunity, not evidence of a
   closure. This run's state/source budgets did not bind.
2. **Explain the four forced-but-open targets.** Their retained selected leaves
   give concrete residuals for studying why a consequence does not expose a
   known family. Compare further probing, compatible consequences and exact
   interactions before paying for another broad expansion. Local and composed
   closure differ on one successful target; use the finite route witness.
3. **Reduce cold verification cost without treating unchecked records as facts.**
   Cold history/replay dominates the measured pipeline; warm probing is already
   subsecond. Profile reachable proof checking and repeated reconstruction before
   choosing a smaller dependency-checked replay or indexing change. Persisting a
   cursor does not discharge this cost. Peak RAM and independent evaluation are
   still unmeasured gaps.

The new rows and negative traces are all retained. These results supply three
additional structural-coverage witnesses, not efficient coverage of every CNF,
a new tractable class or a P-versus-NP result.
