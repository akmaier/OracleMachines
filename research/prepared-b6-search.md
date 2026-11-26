# Own checked preparation across incremental B6 search

Checkpoint: 26 November 2026. Repeated chunked continuation spent most of its
time rebuilding and checking the same source/proof/closure data. A prepared
session now owns one checked input snapshot, occurrence index and live search
frontier. On eighteen retained cases, it produces **identical intermediate and
final results** while reducing continuation time **80.40%** and complete measured
time **44.32%** against repeated standalone chunk calls.

This is a benefit for incremental work. A single uninterrupted pass remains
**2.61% faster in complete time** than the prepared chunked session. Cold recovery
and peak process memory do not improve. No new refutation is found: sampled
recognition stays **228/246**, with **18 open**. Continuation exposes **15 additional
failed assumptions**, bringing the retained set to **24 in seven cases**.

## Why this bottleneck was selected

The preceding gap record proposed composing nine B6 failures. The preserved
composition diagnostic checks all nine, appends their exclusion units and runs
unconditional propagation on B7. It finds no contradiction. Six closures gain
ten assignments, only one beyond the nine explicit exclusions. These complete
closures and their original proof histories are retained for future B7 work;
no B7 compiler or B7 probing is introduced here.

The main experiment instead addresses repeated preparation, the dominant
avoidable cost in earlier runs. It continues the same existing B6 cursors using
up to 64 additional assumptions, so its failure discoveries are independent of
the diagnostic B7 closures. A fresh single pass and ordinary chunk continuation
reach exactly the same results.

## Ownership, checking and invalidation

`PreparedB6Search` deep-copies caller inputs before validating them. It checks
the source, guards, all earlier banks, complete closure and the supplied cursor's
exact binding, schedule and failure proofs. It retains the exact binding string,
fixed closure prefix, residual bank/index and mutable continuation state. Unused
older proof-layer objects are dropped after checking. Every returned result is
a deep copy, so edits to caller input, imported history or returned results cannot
alter subsequent search.

The session describes its original snapshot. It does not track later edits to
caller data. A different source, guard, proof, closure or trace allowance requires
a new checked session; `advance` cannot change these inputs. A serialized cursor
is portable, but a new session must validate it against the original provenance.
There is no global cache keyed only by a digest. Python private fields are not
a security boundary against reflection or concurrent internal mutation.

Within the fixed snapshot, the occurrence index is read-only during probing:
per-probe clause counts, XOR accumulators and satisfaction flags remain fresh.
The live queue preserves the same occurrence order and complement-first
promotion rule as the standalone implementation. A candidate consumed at a
chunk boundary is retained as pending; an interrupted candidate is also kept
pending and never marked completed. Serialization stores only completed history;
cold schedule replay reconstructs the same next candidate. An induction over
completed assumptions therefore preserves the standalone sequence, with the
same per-call work/trace allowances. Open history supplies no proof axiom and
neither exhaustion nor an open result decides SAT.

Native publication still uses the existing compiler and its full provenance
checks. The new object accelerates discovery only. Cold validation cannot assume
that a process-local session survived or that untrusted persisted data is valid.

## Matched costs

Each of eighteen exposed cases runs twice in opposite arm order:

* `single`: one standalone call allowing up to 64 additional assumptions.
* `chunks`: up to eight standalone calls of eight assumptions each, resuming the
  returned cursor; stop immediately on completion, refutation or a budget stop.
* `prepared`: the same chunks and stop rule within one owned prepared session.

Each call allows 262,144 occurrence visits and 256 trace steps. Chunked arms
could consume more aggregate allowance; none hits a work or trace limit here,
and all arms perform exactly the same probes and propagation. Both chunked arms
make 100 calls across the cases; six already exhausted orders stop on their first
call. Setup, input copies and result copies are charged. Each arm reconstructs
the source prefix once, persists/reloads its final result, performs full semantic
verification, and constructs a new checked session from that cold cursor. Process
startup/loading, earlier acquisition, diagnostic work and final audit are extra.

| Summed per-target means | Single pass | Ordinary chunks | Prepared chunks |
| --- | ---: | ---: | ---: |
| Source reconstruction (s) | 0.35887 | 0.35901 | 0.36200 |
| Continuation including setup (s) | 0.14066 | 0.80055 | 0.15688 |
| Of which prepared construction (s) | 0 | 0 | 0.14464 |
| Final persistence/reload (s) | 0.00658 | 0.00847 | 0.00577 |
| Full semantic checking (s) | 0.13138 | 0.13108 | 0.13263 |
| Cold session reconstruction (s) | 0.14318 | 0.14315 | 0.14385 |
| Complete census (s) | 0.78541 | 1.44732 | 0.80591 |
| Probe calls | 18 | 100 | 100 |
| New assumptions | 740 | 740 | 740 |
| Per-probe initialization clauses | 301,850 | 301,850 | 301,850 |
| Propagation occurrence visits | 23,090 | 23,090 | 23,090 |
| Occurrence index builds | 18 | 100 | 18 |
| Indexed literals | 19,880 | 117,959 | 19,880 |
| All checked binding bytes constructed | 744,249 | 4,568,141 | 744,249 |
| Schedule checks across retained layers | 7,960 | 46,036 | 7,960 |
| Standalone result bytes | 214,364 | 214,364 | 214,364 |

The prepared arm avoids 82 index builds and repeated source/provenance setup.
After its charged construction, its warm calls take 0.01224 seconds in aggregate.
It improves continuation on all twelve cases needing multiple calls, and regresses
on the six already exhausted cases where setup cannot be amortized. All eighteen
cases are slower than single-pass continuation. These regressions are retained.

Peak process RSS is 97,353,728 bytes prepared, 97,222,656 ordinary chunks, and
97,320,960 single: no memory reduction is demonstrated. Cold checks and recovery
remain approximately unchanged. The strongest measured use is an incremental
caller that must yield between chunks; use one uninterrupted call when possible.
No production default changes.

## Resource limits and remaining discovery work

For a fixed checked bank, session retention is proportional to its residual
clauses/occurrences, exact binding, closure prefix and accumulated cursor/proofs.
The queue and tested history hold at most two signed candidates per active
variable. Preparation is paid once per session, not once for every chunk; input
copying and checks remain nonzero. Each actual probe still initializes arrays
for all residual clauses. Export deep-copies growing history, and cold recovery
checks it again. Multiple sessions, changing banks, future feedback layers and
native proof contexts have no compact lifetime bound.

The full eighteen-case open export grows from **1,259,314 to 1,474,056 bytes**,
because it preserves every previous field and appends the new cursor. The three
arms' final standalone results are byte-identical. The separately preserved
B7 diagnostic is 1,285,949 bytes. This is computational reuse, not persistent
compression; historical artifacts still accumulate.

The retained B6 failures are `(1,15):2`, `(28,18):1`, `(28,19):5`, `(37,39):4`,
`(37,40):8`, `(40,0):3`, and `(61,61):1`. **Compose all 24 next**, rather than
repeating the earlier nine-failure diagnostic. Ten current orders are exhausted:
`(1,0)`, `(1,15)`, `(28,17)`, `(28,18)`, `(28,19)`, `(61,0)`, `(61,21)`,
`(61,50)`, `(61,51)` and `(61,74)`. Changed feedback can justify fresh probing;
unchanged exhausted banks require stronger interactions. None is certified SAT.

The largest remaining individual census stage is source-prefix reconstruction.
Cold result checking and session construction also repeat much of the same
validation; a checked handoff could remove that duplication without accepting
unchecked history. These are future targets, not savings claimed here.

## Validation and reproduction

All **2,013 full tests** and **148 focused tests** pass. New tests cover chunk
boundaries and promoted candidates, interruption/retry, cold continuation,
mutation isolation, independent sessions, changed-input rejection, terminal/open
verdicts, existing native cold readers, exhaustive binary inputs and generated
small truth tables. The audit replays every intermediate chunk against the old
API, independently rechecks final portable results and cold recovery, and checks
the composition diagnostic. All 1,116 prior sources, 27,695 artifact entries in
197 manifests and 64 manuscript proof blocks remain unchanged. There are no
new native archives or cumulative authority records.

Resume `experiments/results/cnf-prepared-b6-search/checkpoint.json`, especially
`prepared_b6_search.remaining` and `b6_prepared_cursor` in each row. The old
`b6_probe_cursor` is intentionally retained unchanged. Reproduce with `pilot`,
`prepare` and `run_census` in `compare_cnf_prepared_b6_search.py`, then `validate`
and, after tests/manuscript checks, `seal` in `validate_cnf_prepared_b6_search.py`.
Use a fresh output directory. No unrestricted-SAT conclusion follows.
