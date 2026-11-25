# Resume the probe frontier across cold reloads

Checkpoint: 25 November 2026. A persistent cursor now records the actual completed
probe sequence and its failed-probe proofs. Cold resumption avoids **2,624 repeated
probes** relative to restarting with a larger budget. Every final cursor and
proof matches a single 128-probe run on the same input. Later candidates produce
**142 additional failures in 31 cases**, including 116 failures in 27 cases whose
closure had not changed. The old fixed prefix had concealed these opportunities.

Two refutations appear within the first 64 probes on changed B3 closures. Their
distinct native roots pass both independent readers, bringing sampled recognition
to **205/246**, with **41 unresolved**. Both were already UNSAT in inspected
snapshots, and fresh local solving also proves them. Resumption beyond the first
64 adds no immediate refutation in this sample. Its gain is retained evidence
and avoiding repeated acquisition, not a new tractability theorem.

## Cursor contract and correctness

The cursor binds the full exact normalized source, B3 bank, saved closure trace
and assignment, ranked active-literal order, trace limit and policy identifier.
Equality uses full serialized content, not a digest-only match. A different bank,
closure, order, trace limit or policy identifier rejects reuse. Search-semantics
changes require a new policy identifier; version discipline remains part of the
contract. Different valid lower-layer proofs of an identical B3 bank may be used,
but all current source/guard/layer obligations are checked again.

The cursor contains completed literals in execution order and the corresponding
failed-probe proofs. Reload replays the deterministic scheduling decisions,
including complement promotion, rejects duplicates or an invalid prefix, and
independently checks every saved failure on B3. A failed probe's transported trace
includes the checked closure prefix. Opposite failures establish UNSAT and are
expanded through the earlier proof banks into ordinary native rules. No new
unchecked native axiom or reader rule is introduced.

Only completed probes advance the frontier. Work- or trace-interrupted probes
are not recorded as completed; resumption reconstructs and retries the interrupted
candidate, including a promoted complement. Partial propagation state is not
saved, and its repeated work remains charged. A permanently insufficient budget
can therefore keep interrupting the same candidate. Per-call work/probe limits
may change, but changing the bound on retained proof length invalidates reuse.

Open-probe history is scheduling data, not a proof of search exhaustion. Reload
does not rerun each claimed open probe. A fabricated open history can skip useful
search and lose coverage; tests explicitly preserve this counterexample. It
cannot certify SAT, and any returned UNSAT still requires checked failed traces
and native proof verification. Even honestly testing every single-literal probe
without a conflict remains unresolved. The equivalence claim is for honestly
produced cursors, unchanged semantics and nonbinding differing work limits.

No unrecorded historical prefix is inferred from an old unresolved program.
The first 64 candidates are reacquired with the new recorder, and their cost is
included. All previous sources, guards, proof layers and closures remain intact.

## Matched cold-reload experiment

All 43 retained B3 closures run in three modes. Single uses up to 128 assumptions.
Restart runs 64, writes and reloads its result, then starts over with 128 if still
unresolved. Resume runs 64, writes and reloads its cursor, then attempts 64 more.
Both chunked arms retain first-stage refutations without another search. Each
64-probe chunk has 262,144 occurrence visits; a 128-probe call has 524,288. No work
or trace interruption occurs in these measurements. The pilot was exposed before
timing; two opposite orders per target and mode give 48 isolated workers.

| Summed target mean | Single | Restart | Resume |
|---|---:|---:|---:|
| Discovery (s) | 0.26394 | 0.47999 | 0.45926 |
| Prefix reconstruction (s) | 0.77077 | 0.76792 | 0.76837 |
| Serialization/reload (s) | 0.01407 | 0.02301 | 0.02297 |
| Final semantic validation (s) | 0.22096 | 0.21951 | 0.21919 |
| Complete census (s) | 1.27489 | 1.49648 | 1.47595 |
| Assumed probes | 5,271 | 7,895 | 5,271 |
| Occurrence visits | 208,190 | 298,387 | 208,190 |
| Initialization clause visits | 2,029,906 | 3,036,626 | 2,029,906 |

Resume avoids 2,624 repeated probes and 90,197 occurrence visits. It reduces
discovery time **4.32%** and complete census time **1.37%** against restart.
Preparation, binding, schedule replay and retained-failure checking limit the
saving. Against uninterrupted single-pass search, resume is **74.00% slower in
discovery** and **15.77% slower overall**. Use the cursor for interruption and
continued acquisition; it is not a reason to split a known single-pass budget.
Two orders are descriptive timings, not a production speed guarantee.

Input loading, startup, earlier seed acquisition and the final audit are additional.
The measured total includes original prefix reconstruction, discovery, JSON
write/read, final semantic validation and event reporting. Neither chunks nor
the cursor avoid rebuilding checked source/layer preparation in this experiment.
That remains a substantial cost target.

## Retained evidence and native certificates

The first prefix finds 29 failures overall; continuation raises this to 171.
The 41 unresolved events retain **161 failures in 31 cases**, with 4,948 unit-trace
steps and 5,224 completed candidate entries. Ten open events have no failure.
Four open events exhaust this single-literal order and remain unresolved; the
other 37 stop at the 128-probe cap. All records preserve B3 clause provenance.
A checked feedback pass over these 161 failures is the next coverage target.

The two newly refuted roots receive eight isolated fresh/native trials in two
opposite orders. All four unique archive/root pairs pass both cold readers.

| Summed case mean | Fresh solving | Layered native proof |
|---|---:|---:|
| Solve/compile (s) | 0.91352 | 0.48771 |
| Warm checking (s) | 0.00435 | 0.03391 |
| Cold readers (s) | 0.91707 | 0.36400 |
| Persistence (s) | 0.34026 | 0.13974 |
| Complete trial (s) | 2.18668 | 1.03376 |
| Encoded record bytes | 4,414,607 | 1,188,542 |
| Records | 318 | 477 |

Aggregate compilation falls 46.61%, complete local trials 52.72%, and bytes
73.08%. Both byte counts improve, but only `new-40-46` improves in compile and
complete time; `new-67-48` regresses in both. These are different roots from the
previous study and do not reverse its preserved regressions. This positive-only
comparison excludes discovery, prior acquisition and unresolved fallback; no
full-workload advantage over fresh solving is established.

## Space, bounds and validation

For a fixed bank with n active variables, completed history contains at most
2n literals and at most 2n failed-probe records. With trace cap T, the latter
use O(nT) trace entries; the exact binding adds source/bank/closure/order storage.
Loading reconstructs the schedule and copies retained proofs, while rechecking
all failure reasons and earlier provenance. Serialization, reason-clause lengths,
sorting and integer encoding costs remain additional. Across changing banks,
there is no bound on the number of retained contexts or lifetime storage.

Final cursors total 543,300 bytes in the audit's compact encoding. The complete
remaining-state export is 1,329,458 bytes, including all earlier layers and the
new cursor/program data; the two case files total 93,417 bytes. This format favors
self-contained evidence and duplicates some proof content between program and
cursor. No compression or general memory-saving claim follows. Peak census RSS
is 97.12/97.09/96.99 MB for single/restart/resume. Native-trial peak RSS is 96.98 MB
fresh and 60.98 MB layered, a two-case observation rather than a memory bound.
Cumulative authority tables remain untouched; supplemental archives can duplicate
shared content.

All 1,945 tests pass, including 80 focused tests. New tests cover promotion across
chunk boundaries, cold JSON reload, interruption/retry, exact-binding invalidation,
malformed histories and proofs, the forged-open-history counterexample, native
support/full compilation, warm rejection, both cold readers, guards, budget stops
and generated small-formula truth checks. All 64 earlier manuscript proof blocks,
1,081 earlier source fingerprints, 189 manifests and 25,722 prior artifact entries
are preserved. Resume `experiments/results/cnf-probe-cursor/checkpoint.json`, with
`remaining.json` retaining both the new cursor and all previous evidence.
