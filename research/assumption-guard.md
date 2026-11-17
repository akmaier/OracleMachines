# Price one forced guard before choosing a partition

The single-assumption candidates from the previous diagnosis now have complete
acquisition and replay measurements. Two cases improve and one regresses. The
result narrows the next discovery question: a forced assignment is valid, but
its proof, residual search and retained record can still cost more than ordinary
solving. Candidate origin and trace reuse need separate accounting.

## Checked, bounded acquisition

The optional probe first runs unit propagation on the unsplit target. A terminal
conflict is reused directly. Otherwise it examines at most two supplied candidate
clauses, in the original order, and stops at the first unit-refuted strengthened
premise. Empty, already contained, duplicate and foreign-variable candidates are
skipped. The interface uses non-tautological clauses in target coordinates.
Failed probes are retained and charged; they establish no satisfiability or
entailment conclusion. They do not launch general search or publish anything.

If `T AND C` is refuted, every model of `T` falsifies every literal of `C`.
Publication sends the saved unit trace through the unchanged native verifier,
then constructs an existing clause-deletion guard. The restricted target is
solved normally. Existing guard-chain checking verifies the full composition and
lifts any SAT model. No native proof or sidecar schema changes. Warm and cold
reuse require checked stored roots; a proposal alone never certifies an answer.

These are the failed-literal/look-ahead ideas already discussed in the paper,
now applied after the two existing guards and priced against the saved partition
controls. The experiment does not claim a new inference rule or tractable class.

## Nine exact-prefix arms

Each case restores the original pre-query state from the earlier stream and
repeats its preparation and accepted guards. Baseline proof payloads and records
match the previous comparison exactly. Both candidate arms perform the same
bounded probing. The direct arm solves the selected premise natively; the trace
arm publishes its retained refutation. Both solve the same remaining child.

| Case | Selected assumption | Premise probes | Baseline rows / guard rows | Baseline / guard native bytes | Baseline / trace-guard propagation visits |
| --- | --- | ---: | ---: | ---: | ---: |
| 43 | `[-230]` | 1 | 10 / **7** | 9,798 / **5,641** | 1,611 / 1,734 |
| 172 | `[-40]` | 2 | 9 / **8** | 13,839 / **12,226** | 1,952 / 2,565 |
| 70 | `[-40]` | 2 | 4 / **5** | 5,978 / **6,715** | 938 / 1,608 |
| Total | | 5 | **23 / 20** | **29,615 / 24,582** | **4,501 / 5,907** |

The native and retained-trace arms have byte-identical deltas, identical composed
records and identical child metrics. Reusing traces avoids 1,166 repeated premise
propagation literal visits: total visits fall 7,073 -> 5,907 between these arms.
It replaces three expansion calls with three checked trace publications, so
expansion counts fall 20 -> 17 while stored rows stay at 20. Against baseline,
rows fall 13.04% and native bytes 16.99%, but propagation visits rise 31.24%.

Case 43 matches the best previous partition's seven rows and reduces its native
payload from 8,797 to 5,641 bytes. Its former forward partition needed eight rows
and 6,932 bytes. Case 172 improves on either previous order. Case 70 improves on
the six-row partitions but remains worse than four-row ordinary solving. Keep
it as a rejection/fallback control. The best posthoc choice would keep baseline
for 70, but an affordable selector for that choice has not been established.

The extra guard stores another full strengthened source in its sidecar. Across
the matched arms, serialized delta-plus-record bytes rise **88,960 -> 98,668**
(10.91%), despite lower native payload. These totals exclude diagnostic reports
and are not peak live memory. Complete single samples range from 6.33 to 6.96
seconds, including 5.16--5.63 seconds of cold replay. Probe/premise/child timings
and operation counts are retained separately; noisy single samples establish no
stable total-runtime gain. All totals sum independent historical arms, not a
stream whose later prefixes reflect a new policy.

The candidate list still comes from the earlier conditioned-core scan, which
cost roughly 32,000 restriction literal visits per case across two passes. Its
discovery cost is retained separately. A two-candidate bound does not remove that
upstream work or make the measured policy a cheap general recognizer.

## Next discovery target: proposals from the target alone

A read-only follow-up avoids scanning the stored core bank at this stage. It
excludes variables already forced by baseline propagation, ranks remaining
variables by binary-clause incidence with identifier tie breaks, and permits
both polarities of at most four variables. A second variant scores the residual
after baseline units. This is bounded local failed-literal discovery, not a
guarantee that the first forced variable gives the cheapest expansion.

| Case | First refuted assumption | Actual premise probes | Discovery plus probe propagation visits | Remaining child at original prefix |
| --- | --- | ---: | ---: | --- |
| 43 | `[-20]` | 1 | 1,759 | Absent |
| 172 | `[-140]` | 1 | 871 | Absent |
| 70 | `[50]` | 2 | 1,499 | Absent |

Both ranking variants select the same first conflict on these three cases;
later candidate orders differ in 43 and 70. Residual scoring adds a restriction
pass without changing the selected guard. The diagnostic
charges both discovery propagation and the probe's repeated baseline pass;
sharing that checked result remains a possible follow-up. It independently
reconstructs each choice and checks its unit proof with the native verifier,
with SQL read-only and search/publication disabled. Existing prefix preparation
remains paid. Propagation visits and the earlier scan's restriction visits count
different operations and must not be turned into a runtime speedup ratio.

These are different forced variables from the priced guards. No premise, child
or composed decision is acquired by the diagnostic. Next, price these local
candidates at the same prefixes and then test the fixed policy on excluded
queries and adversarial edits. Retain case 70's regression. The main open cost
obligations are candidate discovery, the chosen residual's search, duplicated
sidecar sources and full cold replay. A forced assignment need not eliminate
enough work to repay its discovery and evidence.

## Persistence and validation

Resume [the checkpoint](../experiments/results/cnf-assumption-guard/checkpoint.json).
It preserves all **21,525 previous native payloads** and has **21,528 keys**.
Only three keys are new to the combined history; remaining children were acquired
in earlier arms, but were correctly unavailable at these historical prefixes.
No alternative native payload is introduced. Nine new composed records are
retained alongside 2,957 ordinary decisions, 429 prior composed records and six
projection records. All pass independent cold checking. Ordinary and composed
catalogs remain separate.

The combined database grows **67,989,504 -> 67,993,600 bytes**, compressed
**4,980,892 -> 4,981,685 bytes**. This preserves all previous experimental results,
not only a selected policy. All **1,064 tests** and 21 focused tests pass, including
512 exhaustive two-variable truth tables, SAT witness lifting, tampering,
bounded rejection, persistence and warm reuse. The full suite retains 44 existing
SQLite ResourceWarnings; focused tests emit none. All **462 prior sources,
5,008 artifacts and 86 manifests** pass preservation. Four frontier counts,
structural authorities and the 64 prior manuscript proof blocks remain unchanged.
No fresh structural coverage, new Lean theorem, minimum-cost guarantee or
unrestricted-SAT resource bound is claimed.
