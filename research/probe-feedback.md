# Feed retained probe exclusions into one propagation pass

Checkpoint: 25 November 2026. The [support compiler](probe-support.md) reduced
certification cost but left 180 all-guard events unresolved. A single propagation
pass using their saved exclusions now refutes 64 events, representing 53 distinct
roots absent from the earlier recognized set. It performs no new assumed probes.
All 53 roots have native proofs, including six with unknown prior snapshot status.
The other 116 events remain unresolved.

## Checked feedback and exact reconstruction

Each retained failed assumption l already has a checked conflict trace over the
original source-plus-guard bank. Thus that bank implies not-l. Validate every
seed trace and its guard provenance before adding these complements as unit
clauses. Propagate once through the augmented bank. This is one feedback step,
not a new failed-literal search or an iteration to a stronger fixed point.
A propagation conflict refutes the source; an open closure is never a SAT verdict.
All learned units have independent original-bank proofs, so their dependencies
are acyclic and cannot justify themselves.

The native compiler expands any used learned unit through its saved failed-probe
proof. On the branch falsifying that unit, its original assumption holds. The
current branch may already fix other variables: skip a saved forced step if its
value agrees, or terminate at its reason clause if the value is contradicted.
Before the first disagreement, all earlier saved reason assignments remain
consistent. Source and guard leaves therefore retain their checked justification
under the stronger context. If normalization removes a variable, an excluded
branch must have exactly the current cofactor key; no split on an absent name is
introduced.

Causal slicing selects the final feedback reasons and the original source
supports of the failed probes they use. Transport and independently check the
compact seed and feedback trace, compile their native empty/unit/split proofs,
and lift the refuted subset with the existing component rule. Binary-prefix
lifting is unchanged. No learned unit becomes a native axiom, and every portable
check precedes archive reuse or publication. Source edits require renewed binding.

## Matched remaining-case discovery

The pilot exposed all 180 outcomes before the fixed matched timing study; this
is not an independent holdout. Two alternating isolated repetitions over eight
targets compare the original bank with the same bank plus feedback units: 32
workers. Both arms validate the saved seed and run one unconditional propagation
pass, bounded by 262,144 occurrence visits and 256 unit steps.

| Arm | Refuted / open | Discovery | Reconstruction | Complete census |
|---|---:|---:|---:|---:|
| Original bank | 0 / 180 | 0.60281 s | 3.35849 s | 3.97325 s |
| With feedback | 64 / 116 | 0.61321 s | 3.33529 s | 3.95921 s |

Times are per-target means of two repetitions, summed over targets. Reconstruction
binds the event and replays the saved binary prefix. Discovery includes seed and
guard checks, bank/index construction and propagation. The small timing difference
does not establish a stable speed benefit. Earlier seed acquisition/discovery,
loading, process startup, native compilation and final audits are additional.

All 851 saved exclusions add distinct units. Bank literal occurrences rise from
199,744 to 200,595 and initialized clause slots from 70,430 to 71,281. Both arms
make 180 unconditional probes and zero assumed probes. Feedback performs 30,683
occurrence visits and 2,611 unit assignments; the control performs 3 and 1.
No occurrence or trace cap stops this sample. Peak census RSS is about 82.8 MB.
The earlier 66 event refutations are retained separately: the two continuation
steps now recognize 130 of the original 246 post-binary events. This is not a
coverage statement about arbitrary SAT.

## Native costs and persistent evidence

The 64 gains contain 53 distinct roots with no overlap with the previous 60
recognized roots. Of these, 47 were already UNSAT in inspected snapshots and six
were unknown there. Fresh local solving and feedback reconstruction both refute
all 53 in 212 isolated trials, with two alternating repetitions per method.
Both independent cold readers accept all 106 unique archive/root pairs.

| Summed per-case mean | Fresh local solver | Feedback compiler |
|---|---:|---:|
| Solve or compile | 4.55241 s | 4.73235 s |
| Warm check | 0.09275 s | 0.58074 s |
| Cold readers | 5.00175 s | 3.53210 s |
| Persistence | 1.65163 s | 1.07833 s |
| Complete local trial | 11.51819 s | 10.05090 s |
| Encoded record bytes | 21,544,173 | 10,752,547 |
| Records | 1,739 | 4,086 |

Compilation is faster on 18 cases, complete local trials on 21, and record bytes
are smaller on 38. All other cases remain explicit regressions. Aggregate bytes
roughly halve, while aggregate compilation is slightly slower. Cold verification
and persistence make the aggregate local trial cheaper. Charging the 53 chosen
events' additional discovery/reconstruction adds 1.01808 seconds, giving a partial
feedback total of 11.06898 seconds against 11.51819 for fresh local trials. This
small exposed-case subtotal excludes seed acquisition, unresolved-case fallback,
startup/loading, closure diagnostics and final audits. It is not a complete
workload or whole-query comparison.

Selected source literals fall from 54,000 to 8,954 across these proofs. The
compiler expands 226 used exclusions, makes 3,627 native splits, reuses 264
cofactor results, and handles 93 already-fixed trace steps. There are 53 support
wrappers and 94 unchanged binary-prefix splits. No coordinate fallback occurs.
Peak trial RSS is 76.45 MB for fresh solving and 61.57 MB for feedback compilation.
These input/interpreter-inclusive maxima are not a general memory bound, and
isolated byte sums can duplicate shared subproofs. The cumulative bank is
unchanged; supplemental archives preserve all new proofs.

For the 116 open cases, a separate scan-based diagnostic reconstructs and checks
the complete unit closure, including each reason and absence of another unit or
conflict. Its extra work and time are recorded separately from timed discovery.
The artifact retains 656 assignments and their traces, including 308 variables
beyond the recorded exclusion variables. These are source-bound portable facts,
not separate native verdicts or SAT certificates. Future work can replay them
without losing the deductions made in an unsuccessful refutation attempt.

Validation preserves 183 prior manifests, 23,915 artifacts and 1,055 source files;
the new checkpoint binds 1,060 sources. All 1,897 tests pass, including 32 focused
tests, signed guard transport, malformed-proof rejection before warm reuse,
small exhaustive checks, stronger-context reconstruction and cold replay.
The initial context-test fixture did not exercise the intended branch; its code
and failure log are retained before the corrected fixture. All 64 manuscript
proof blocks remain unchanged. Existing full-suite SQLite warnings are recorded;
focused tests have none.

## Remaining boundary

Of 116 open events, 96 retain 348 exclusions and 20 have none. The next coverage
experiment is to condition on the checked closure and spend a bounded budget on
new failed probes, preserving an acyclic proof dependency between rounds. Repeating
propagation on the unchanged bank cannot yield more: the retained closure is
already checked to be a unit fixed point. The 20 no-exclusion cases need a
separate interaction or search-budget analysis.

For C original-bank clauses, L literal occurrences and U learned units, index
construction and an unbounded complete unit pass use O(C+L+U) expected word work/space under the existing dictionary model,
plus retained traces. Bank sorting and all seed/guard verification are additional. Prior proof acquisition
and native proof expansion remain additional. This finite checked feedback step
does not bound future discovery rounds, the number of distinct contexts, total
history growth or unrestricted-SAT complexity.

Resume [the checkpoint](../experiments/results/cnf-probe-feedback/checkpoint.json).
The [protocol](../experiments/results/cnf-probe-feedback/protocol.json),
[analysis](../experiments/results/cnf-probe-feedback/analysis.json),
[support plans](../experiments/results/cnf-probe-feedback/support-plans.json) and
[open closures](../experiments/results/cnf-probe-feedback/remaining-closures.json)
retain successes, limitations and reusable deductions.
