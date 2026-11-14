# Selecting retained split evidence before extending clear probes

2026-11-14. The next structural coverage case, **1160**, can be completed using
two already recorded split pairs. The previous scheduling policy performs ten
additional clear probe advances before using those same pairs. An optional early
selection policy avoids those advances, retains the same sixteen new pattern
keys, and reduces complete worker time by **44.31%** in the matched comparison.
An earlier forcing control also improves, by **24.83%**. These are two development
cases, not a general prediction that splitting beats further probing.

## Exact reuse and scheduling

A saved pair contains checked source-linked unit-propagation traces for both
values of one variable. The existing checker reconstructs both restricted
formulas, their simplifications, canonical keys and variable transports. This
already defines an exact case split. Exhausting an ordinary probing pool is a
search-policy condition, not a condition needed for the split's correctness.
A clear pair means neither limited propagation attempt found a contradiction;
it does not mean either cofactor is satisfiable.

`EarlySavedExpansion` first resumes a pending split or a known forced target.
Otherwise it ranks the saved pairs using the existing rank: number of unique
unclosed children, number of unacquired children, largest child support, total
child literal count and variable number. It acquires the first pair, even when
neither child is closed. Both children remain structural proof obligations. A
missing pair falls back to ordinary continuation. Recognition, checking and
failed candidate searches are charged; no similarity score or reference answer
supplies a proof.

The caller establishes one shared state allowance. The new policy never resets
it, and a partial pair remains pending with its exact source and both target
bindings. Cold resumption uses that same pair without reranking. The old policy,
`EarlyClosedExpansion`, already allows an early split when a saved pair has a
closed child. The new policy removes that eligibility restriction while retaining
the ranking and pending/known-forcing priority. Existing pattern policies and
records are unchanged. No new semantic tractability theorem is claimed.

## Matched experiment

The current case starts from the complete projection-acquisition checkpoint;
its selected leaf has **37 variables / 151 clauses / 456 literal occurrences**.
The forcing control, original **1189**, starts from its preserved earlier
local-forcing checkpoint, with a **22 / 88 / 272** selected leaf. Comparing it
from today's completed authority would leak later results, so each worker gets
an independent copy of the appropriate earlier seed.

Two serial repetitions per case reverse policy order; case order also reverses
the first policy. Each worker has **12 advances / 32 new states**, uses the same
recognizers, exact pair checks and full route refresh, and seeks closure of the
same case-specific source. No tests or builds run during these measurements.
Reference solving is separate and never guides scheduling or structural closure.

| Quantity | 1160 ordinary | 1160 early saved | 1189 ordinary | 1189 early saved |
|---|---:|---:|---:|---:|
| Source structurally closed | yes | yes | yes | yes |
| Advances | 12 | 2 | 8 | 3 |
| New states, all completed | 16 | 16 | 21 | 20 |
| External continuation assumption attempts | 80 | 0 | 51 | 0 |
| Mean expansion, seconds | 13.62996 | 2.24986 | 8.18419 | 3.04871 |
| Mean acquisition and ranking, seconds | 1.01369 | 0.13746 | 0.28161 | 0.11861 |
| Mean full route refresh, seconds | 12.60103 | 2.10985 | 7.89854 | 2.92588 |
| Mean worker, seconds | 26.38845 | 14.69517 | 20.45091 | 15.37364 |
| Compressed pattern/probe delta, bytes | 17,693 | 13,199 | 15,484 | 12,050 |
| Delta database, bytes | 397,312 | 270,336 | 397,312 | 307,200 |
| Complete history database, bytes | 773,586,944 | 773,459,968 | 770,707,456 | 770,600,960 |

Warm expansion falls **83.49% / 62.75%**, while complete worker time falls
**44.31% / 24.83%**. Preparation and delta export remain substantial. Expansion
sums selection, acquisition, route refresh and local coverage phases; operation
archive serialization is outside that sum but inside worker time. Worker time
also includes independent preparation, checking and persistence. Full authority
restoration and combined global verification are separate costs.

External continuation counts exclude recognizer-internal probing, which remains
charged in acquisition time and counters. No fresh external probes are needed
in these early runs, but acquiring their children still involves recognition.
Compressed delta sizes exclude split/bridge sidecars, reference archives and
logs. Complete history sizes use different case-specific seeds and must be
compared within each case. They are retained disk bytes, not peak RAM.

The forcing control demonstrates the tradeoff concretely: ordinary continuation
finds a forced reduction before splitting; the early policy takes a different
route through three splits. It happens to win on this control, but there is no
bound on how much better a future undiscovered forced reduction could be. The
policy remains optional. Both directions and all probe records are preserved,
including ordinary work that the early policy avoided.

## Checked structural paths

On case 1160, both policies choose source local variable **19**. Its true cofactor
reaches the retained empty-CNF terminal after four failed-literal reductions.
The false cofactor first exposes binary implications and variable elimination,
then leaves **34 / 135 / 404** unresolved. A second split on that leaf's local
variable **14** produces a refuted branch and a SAT branch ending in a
**6-variable / 7-clause / 14-literal 2-CNF**. That terminal is neither Horn nor
dual-Horn. The independent reference checks both first-level cofactors as SAT
and verifies every saved SAT model lift. The two policies reach the same checked
patterns; extra clear probing contributes no new structural proof on this case.

The early forcing-control path starts with local variable **13**, then splits
the remaining **14 / 53 / 163** leaf on local variable **12**, and the next
**13 / 48 / 148** leaf on local variable **5**. Binary implications, elimination
and failed-literal reductions connect these splits to empty-CNF and 2-CNF
terminals. This is an alternative certified decomposition, not reuse of identical
new pattern keys from the ordinary control route. Local variable numbers refer
to their own canonical source; transports must accompany any cross-source use.

The timing target is complete structural classification of the retained source.
A single checked SAT branch can decide satisfiability earlier. Requiring both
branches for this coverage experiment must not be confused with a requirement
for the fastest SAT decision procedure.

## Preserved coverage and continuation

The combined authority raises original coverage **63/83 -> 64/83**, also without
the old growth-exception routes. The historical control was already covered in
the latest authority, so its alternative adds no artificial second coverage gain.
The union adds **36 patterns**, nine continuation blocks, one probe window and
five split records. It retains the sixteen frontier patterns and all twenty
new control alternatives; the control's ordinary results were already present.
The two control arms' new pattern key sets are disjoint relative to their older
common seed. Both acquired bridge targets and all **31** retained split sources
close. The positive proof has **3,190 steps** and nineteen originals remain open.

Full SQLite history grows by **573,440 bytes**, to **773,828,608 bytes / 41,962
patterns**. The combined delta is **27,393 compressed bytes / 634,880 SQLite
bytes**, retaining the probe work avoided by the early policy. This experimental
union is not a single 32-state run. Each arm's complete result folder, including
its report, operation records and proof sidecars, uses approximately **82.9 vs
50.0 kB** for case 1160 and **53.5 vs 39.4 kB** for the control; the separate global
proof and reference archives are additional.

The complete producer takes **334.32398 seconds**. Current authority restoration
costs **57.71801 seconds**, historical control restoration **25.38864 seconds**,
and preparation/checking of final global coverage **68.76609 seconds**. Combined
delta export takes **5.52745 seconds**. Reference certification preserves all
**3,022** earlier nodes among **3,203** verified nodes. These separately recorded
costs prevent interpreting a warm expansion saving as an equal startup saving.

Resume `experiments/results/cnf-early-saved/report.json` with
`compare_cnf_early_saved.restore_checkpoint`. Report SHA-256:
`995476297ac2e99710b26b67d9ecc3e95963ab624e68282e7b5108da077999d3`.
Keep its five evidence lists **(1, 42, 156, 31, 1)** and separate two-bridge archive;
use the bridge-aware `routes_for` and `cnf_projection_bridge.verify_positive`.
The ordinary split frontier is empty; both entries in `projection_frontier`
are closed, with no leaves. The next original is **1263 / index 42**, leaf
**37 / 152 / 470**, SHA-256
`746b92609a26b66fe74b529bdeb36a5a46ca58129c1bcca04c5088bd23d02eeb`.
Its remaining ordinary variables are **32, 33, 34, 37**.

The next comparison should test this new source while looking for forcing
regressions on broader inputs. Full route
refresh remains most of warm expansion even after early selection. A maintenance
change must preserve newly available pairs, pending targets and later forced
routes exactly. Identifying an efficient partition of every valid CNF, or a
uniform bound on all resulting interactions, remains open.

## Validation

Independent cold reconstruction passes in **305.04269 seconds**, including
multiple seed reconstructions and deliberately redundant checks; this is audit
cost, not ordinary worker latency. It forbids fresh pattern recognition and
fresh reference expansion. All eight arms, both branch bindings and SAT lifts,
repeated logical results, 32-state limits, idempotent delta applications,
**3,203 reference nodes**, original coverage and exact next selection check.
All original seed rows remain unchanged.

All **204 relevant tests pass**, including five new scheduling tests. The
manuscript builds at **157 pages** without overfull boxes or undefined references,
and all **64 existing proof blocks** remain byte-identical. Hash checks preserve
**533 earlier artifacts across 17 manifests**. The new experiment retains
**127 manifested artifacts plus the manifest / 4,127,037 bytes**. Reproduction:
run `compare_cnf_early_saved.py OUTPUT`, then `validate_cnf_early_saved.py OUTPUT`;
continuation uses the existing report's restorer instead of rerunning the study.

The next selected leaf retains **16 saved pairs**, none with an acquired child
root. Its best existing rank is **[2, 2, 35, 817, 6]**, providing an exact initial
candidate for the next matched policy comparison.
