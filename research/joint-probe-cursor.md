# Probe the combined failure frontier with exact schedule reuse

Checkpoint: 26 November 2026. Probing the four changed joint banks discovers
**21 failed assumptions**. Twenty belong to `(28,19)`; composing their checked
consequences yields a source-only refutation accepted by both independent native
readers. Sampled structural recognition increases from **229/246 to 230/246**,
leaving **16 open cases**. The reference snapshot already classified this root as
UNSAT; this adds a structural route, not a previously unknown SAT answer.

Exact reuse on thirteen unchanged banks avoids **1,878 repeated probes**. Complete
matched census time improves only **1.49%**, and native certificate reconstruction
on the gained root is **67.29% slower** and uses **52.21% more record bytes** than
fresh solving. These regressions are retained; the primary gain is coverage.

## Recognition, reuse and proof obligations

The input is the previous mixed B6/B7 proof history and its complete checked joint
closure. The joint bank is B8. Its preparation validates both original histories
on their respective reason banks, then verifies every closure step and the fixed
point before constructing a residual occurrence index.

A B7 schedule can be imported only when the full B7 and B8 clause tuples, closure
assignments **and reason trace**, and trace allowance agree. Both schedules use the
same original-source ordering restricted to active residual variables; identical
banks and closures give the same residual and active order. The implementation
also binds the full source, current bank, closure, order, policy and trace bound
in an exact serialized value. Changed banks start fresh. Resuming a saved B8
cursor rechecks that binding, its deterministic schedule and every failed probe.

The frozen B7 search engine is reused with an explicit view placing the actual
B8 bank in its bank slot. An external B8 cursor has a distinct format and policy;
its envelope is translated internally only after format checking, and the engine
still checks the exact B8 binding. Imported B7 failures would be independently
checked on the identical bank. No old proof is validated against a changed bank.
Open completed assumptions remain scheduling history: accepting an invented open
completion could reduce discovery, but it cannot justify SAT or UNSAT. The
measured saving assumes honestly produced history, as in the existing cursors.

For a failed assumption `l`, the residual trace is lifted through the checked
closure prefix back to B8. A contradiction proves the unit `(-l,)`. The separate
feedback step adds these units to form B9 and checks propagation there. For the
new case it closes a contradiction even though the bounded search itself found
no pair of opposite failed assumptions. Every source-native reconstruction
follows a B9 exclusion back to its original B8 failed-probe proof; all earlier
origins keep their original smaller bank indices. Dependencies strictly decrease.
The native records contain only source residuals and existing empty, units and
split rules. Direct propagation shortcuts inspect only source clauses with a
shared 262,144-work and 256-step allowance. Full portable checking precedes warm
lookup. Decreasing bank indices prove termination of this reconstruction, not a
polynomial bound on its number of contexts.

## Discovery and matched total cost

There are three controls, each paying full preparation and recognition. Restart
allows 64 fresh attempts per case. Reuse imports exact histories and allows up to
64 new attempts. Matched fresh adds the imported completion count to its allowance
and scales the work budget, so it reaches the same frontier. The reuse and matched
results, including all cursor payloads, are identical on all seventeen inputs.
The restart control has less search coverage on unchanged inputs and is an
ablation rather than the matched baseline.

Two isolated repetitions in opposite order give these summed per-target means:

| Census measurement | Restart | Matched fresh | Exact reuse |
| --- | ---: | ---: | ---: |
| Source reconstruction (s) | 0.33947 | 0.33939 | 0.33935 |
| Preparation and discovery (s) | 0.28099 | 0.28804 | 0.27569 |
| Independent cold verification (s) | 0.26908 | 0.26874 | 0.26820 |
| Persistence/reload (s) | 0.00630 | 0.00662 | 0.00611 |
| Complete census (s) | 0.89894 | 0.90588 | 0.89239 |
| Assumed probes | 1,088 | 2,326 | 448 |
| Probe occurrence visits | 38,693 | 65,935 | 20,604 |
| Serialized result bytes | 194,035 | 198,336 | 198,336 |
| Peak process RSS (bytes) | 98,336,768 | 98,254,848 | 98,369,536 |

Reuse reduces assumed probes by **80.74%**, occurrence visits by **68.75%**, and
preparation/discovery time by **4.29%**. Complete measured saving is **1.49%**;
two repetitions do not establish a robust total speedup. There is no measured
memory improvement. Source reconstruction plus final verification takes **68.08%**
of reuse time, with more preparation inside discovery. Input loading/startup,
historical acquisition and final archive audits are additional.

Feedback composition and independent verification take a further **0.55497 s**
over seventeen cases. Complete checked closures on the remaining sixteen take
**0.28195 s** separately. These diagnostics are outside the census totals. They
must be charged when comparing a full expansion workflow against another solver.
The four changed banks receive 64 fresh attempts each. Three unchanged histories
continue with 64 additional attempts; ten are exhausted and make no new attempts.

The failed assumptions are preserved in full, including original clause reasons:
`(28,18)` yields `-62`; `(28,19)` yields
`29, -57, -47, 39, -38, -30, 4, 61, -17, -11, 10, 21, 33, 36, -46, -18, -16, 58, -52, -51`.
Only the latter case is refuted. The former gains one additional assignment under
feedback. Lack of further failures or exhaustion is never reported as SAT.

## Native cost and the retained regression

All three trials use the same complete newly recognized root, including prefix
reconstruction, warm checking, both cold readers and persistence. They exclude
previous acquisition, search census, feedback discovery and unresolved fallback.

| Positive certificate measurement | Fresh solve | Shortcut disabled | Direct reconstruction |
| --- | ---: | ---: | ---: |
| Initial solve/compile (s) | 0.06330 | 2.83232 | 0.11783 |
| Warm check (s) | 0.00110 | 0.01504 | 0.01518 |
| Both cold readers (s) | 0.07159 | 2.43898 | 0.10460 |
| Persistence (s) | 0.02010 | 0.73677 | 0.02709 |
| Complete trial (s) | 0.16007 | 6.03835 | 0.26778 |
| Native records | 49 | 1,832 | 67 |
| Record bytes | 288,318 | 8,227,848 | 438,852 |
| Peak RSS (bytes) | 54,984,704 | 157,663,232 | 57,360,384 |

Direct source propagation avoids much of the disabled reconstruction's expansion,
but fresh solving remains better on this root. Its 49 records include one binary
equivalence record and 48 residual records; direct reconstruction uses 67 residual
records. This suggests testing reuse of existing equivalence reasoning and source
support selection, rather than assuming that a new provenance layer is cheaper.
This is an experimental lead, not an attribution of the entire difference to one
record type. Warm validation overhead remains substantial.

## Bounds, retained state and next work

For a fixed checked residual with `L` literal occurrences and `n` active variables,
index storage is `O(1+L+n)` word slots excluding incoming histories, exact serialized bindings,
and output proofs. The deterministic order has at most `2n` assumptions. Each call
attempts at most its explicit probe allowance, uses bounded occurrence work, and
retains at most the trace allowance per failed probe. Each attempt also initializes `O(m)` counters for `m` residual clauses; the
occurrence allowance does not cap that initialization. Index construction, exact
comparison, closure transport, serialized binding construction and independent
validation are separate charged work. Exact reuse saves previously completed
probes only under its equality conditions. It does not bound the cost of acquiring
new banks or the native reconstruction tree for arbitrary CNF.

The checked open export grows from **1,973,910 to 2,070,735 bytes (4.91%)**, despite
removing the gained case. It retains the previous histories, new B8 cursors and B9
closures; the export before adding B9 closures is 2,066,036 bytes. Three distinct
supplemental native archive/root combinations are preserved, and all old files
remain. There is no lifetime-space bound or cross-case provenance compression.

Next coverage target: the newly strengthened `(28,18)` residual. Six remaining
B8 orders have later candidates: `(1,15)`, `(28,18)`, `(37,39)`, `(40,0)`, `(61,61)`
and `(67,63)`. Ten are exhausted under their current banks and require a changed
bank or stronger interaction, not another identical restart. Next cost target:
share checked common-prefix preparation/source reconstruction; the new native
regression also motivates equivalence reuse and smaller source supports.

## Validation and reproduction

The audit preserves **1,137 prior source fingerprints**, **28,925 prior artifact
entries in 202 manifests**, cumulative tables, the reference union and all **64
original manuscript proof blocks**. It reconstructs each source prefix, replays
all three search arms and both repetitions, independently checks every failed
probe and closure, and reopens three unique native archives with both readers.
All **2,057 full tests** and **46 focused tests** pass. The nine new tests cover unchanged/changed bindings, continuation after interrupted
probes, malformed proofs and schedules, original-bank feedback, direct/disabled
native paths, warm-cache rejection, bounds, all sixteen subsets of the four signed
binary clauses on two variables and seventy generated small truth tables.

The initial case exporter collided with the existing `closure` input field; it was
renamed `joint_closure`. The original source, protocol and failure record remain.
The measured census portion is byte-identical before and after that correction.
An initial focused-test command named a nonexistent module; its log is preserved,
and the corrected command covers the five actual relevant test modules.

Resume `experiments/results/cnf-joint-probe-cursor/checkpoint.json`, especially
`joint_probe_cursor.remaining-closures`. Run `prepare`, `run_census`, `cases` and
`run_trials` with `experiments/compare_cnf_joint_probe_cursor.py`, then `validate`
and `seal` with `experiments/validate_cnf_joint_probe_cursor.py`, in a fresh output
directory with the preserved pilot. No production defaults or unrestricted SAT
bounds change.
