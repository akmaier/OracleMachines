# Share common provenance preparation across independently checked histories

Checkpoint: 26 November 2026. Sharing the common B6 preparation inside joint
search and cold checking reduces complete measured census time by **22.07%** on
the sixteen current unresolved cases. Discovery improves **38.30%** and cold
checking **38.70%**, with identical prepared banks, proof origins, portable results
and search counters. Both stages improve on every measured case. Peak process
memory and serialized state are essentially unchanged.

This is a replay of the retained B8 frontier, not additional search. Structural
recognition remains **230/246**, with sixteen open cases. The strengthened
`(28,18)` residual, six unfinished orders and ten exhausted orders are preserved.
The previous native certificate regression also remains unchanged.

## What was duplicated and what is now shared

The old joint preparation validates the original B6 history while constructing
and checking B7, then independently prepares the same B6 source, prior proof
layers and closure to validate the comparison B6 history. It compares the resulting
common banks/provenance and appends the two sets of new exclusions. Both branches
receive exactly the same first fourteen original inputs.

The new implementation privately copies all input payloads and prepares that
common prefix once. It then independently checks:

1. the original B6 cursor, full program, deterministic schedule and failed probes;
2. the comparison B6 cursor, full program, schedule and failed probes;
3. the B7 closure and history built from the original B6 failures.

Each branch keeps its original proof bank. Original B6 failures still determine
B7. Comparison B6 failures are appended only at the joint stage, in the original
order before B7 failures, so duplicate clauses retain the same chosen reason.
No proof is moved to the augmented bank.

The two B6 programs can have different trace limits. The common bank, residual
and active literal order depend on the shared input prefix, not that limit.
Each history is therefore checked with its **own** limit and exact serialized
binding. Equal limits reuse the existing binding; differing limits construct the
appropriate second binding. B7 similarly retains its actual limit. The final B8
bank, closure, policy and search binding are unchanged.

The common constructor is deterministic on those identical original inputs.
Replacing its two evaluations with one therefore preserves the prepared bank
and provenance. All branch-specific bindings, schedules, trace checks and full
program/terminal comparisons still run. Subsequent append, conditioning and
search operations are the same. This establishes the preparation-sharing rule
for valid inputs; the finite experiments separately check its implementation.
Invalid original, comparison or B7 histories cannot supply an unchecked axiom.

There is no externally supplied prepared object, verified flag or digest-only
cache. The internal preparation is local to one call. Cold validation starts
from another private copy and prepares/checks the inputs independently again;
it receives no trusted state from discovery. The final experiment audit always
uses the frozen original validator as well and compares every bank and origin
entry it returns. Returned values do not borrow the mutable caller payloads.

## Matched end-to-end measurement

The three arms replay the same sixteen inputs, with two isolated repetitions in
opposite order. All use the existing 64-probe, 262,144-occurrence-work and 256-step
allowances and reproduce the parent's exact B8 cursor payload. No frontier is
advanced beyond that saved result.

| Measurement | Separate preparation | Shared discovery only | Shared discovery and checking |
| --- | ---: | ---: | ---: |
| Source reconstruction (s) | 0.34746 | 0.35393 | 0.35917 |
| Preparation and discovery (s) | 0.27873 | 0.17246 | 0.17199 |
| Independent cold checking (s) | 0.26977 | 0.27489 | 0.16536 |
| Persistence/reload (s) | 0.00591 | 0.00635 | 0.00580 |
| Complete census (s) | 0.90572 | 0.81140 | 0.70579 |
| Serialized result bytes | 177,042 | 177,042 | 177,042 |
| Peak process RSS (bytes) | 98,041,856 | 98,041,856 | 97,992,704 |

Changing discovery alone improves complete measured time **10.41%**. Its untouched
checking stage is **1.90% slower** in aggregate, with eleven case-level regressions;
this timing variation is retained. Sharing inside both independent calls improves
complete time **22.07%**, discovery **38.30%**, and checking **38.70%**. All sixteen
case-level means improve in the latter two stages. Two repetitions remain a
limited experiment, not a universal performance guarantee. The source
reconstruction differences concern unchanged code and are also included rather
than subtracted from the totals.

The census charges source-prefix reconstruction, ownership copies, full
preparation and recognition, the actual search, serialization/reload and complete
cold checking. Startup/input loading, previous acquisition, the pilot and final
lineage audit are additional. It introduces no new feedback discovery or native
compilation trial; those costs are neither hidden savings nor part of these replay
totals. Do not multiply the saving by earlier percentages from other workflows.

Each shared call performs one common-prefix preparation and three separate
history checks. Across sixteen discovery calls, common source-context preparations
drop from 32 to 16; the independent checking calls show the same reduction. All
search work, including index construction, probe initialization, occurrence visits,
trace transport and schedule reuse, stays equal across arms.

## Resource limits and next bottleneck

Let `P` be the work of the common prefix construction and `R` the remaining
branch-specific checking and joint processing. The old structure contains two
copies of `P`; the shared structure contains one, plus ownership copying and any
separate binding construction needed for unequal trace bounds. Sharing pays only
when the removed preparation exceeds that added work. It does not remove the
need to check either history or the final cold result.

Temporary duplicated preparations are avoided, but owning the input payloads
also allocates memory. The measured roughly 98 MB peak does not establish a
memory improvement, and neither retained proof size nor asymptotic context growth
changes. The complete **2,070,735-byte** open export and all native certificates
are referenced unchanged, avoiding another duplicate full export. New census,
source and audit artifacts still add to experiment storage; there is no lifetime
space bound or provenance compression result.

Source-prefix reconstruction is now **50.89%** of shared complete time, the largest
individual stage. It reconstructs contexts separately from the subsequent joint
preparation. Investigate a checked, owned common-prefix handoff there next. Keep
exact source, guard, prefix and context bindings and independent cold validation.
For coverage, retain the changed `(28,18)` bank and the six unfinished B8 orders;
ten exhausted unchanged orders need stronger interaction. Equivalence reuse and
source-support selection remain candidates for the prior native cost regression.

## Validation and reproduction

All **2,066 full tests** and **55 focused tests** pass. Nine new tests compare every current result and prepared bank with the frozen
implementation; reject malformed lower/current/comparison histories, closures,
schedules and forward reasons; exercise unequal trace bounds, an alternate valid
closure trace, cold continuation and interrupted probes; test private-copy
ownership under caller mutation; and check all sixteen subsets of four signed
binary clauses plus seventy generated small formulas against truth tables.

The audit preserves **1,142 prior source fingerprints**, **29,141 artifact entries
in 203 parent manifests**, all cumulative tables, reference bindings and native
archives, and the **64 original manuscript proof blocks**. It reconstructs every
source prefix, replays all three arms, verifies the exact saved outputs and search
counters, and independently invokes the frozen full validator on every result.
There are no new native records or changed proof rules.

Resume `experiments/results/cnf-shared-joint-preparation/checkpoint.json`, whose
`shared_joint_preparation.remaining` points to the unchanged checked frontier.
Reproduce `prepare` and `run_census` using
`experiments/compare_cnf_shared_joint_preparation.py` in a new directory containing
the preserved pilot, then `validate` and `seal` using the corresponding validator.
The optional shared API does not change production defaults, structural coverage,
or unrestricted SAT complexity claims.
