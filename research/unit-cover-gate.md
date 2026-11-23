# Preserve cheap unit conflicts before learned covers

The 23 November experiment checks unit propagation before extracting a learned
cover, after a static-template and existing-pool miss with an eligible descriptor.
It fixes the preceding worst regression and preserves the two useful cover
transfers. The gated learner still costs more query time than the shared baseline,
so the default policy remains unchanged.

## Gate and proof obligations

The gate reads the already prepared canonical cofactor. A unit conflict goes
through the existing screened native publisher, which rechecks source identity,
the retained trace and the complete certificate. No learned-cover extraction is
needed. If propagation does not conflict, cover matching proceeds; after a cover
miss, native fallback reuses that prefix rather than propagating it again. An
unmatched outer guard skips the screen. Candidate metadata only schedules work.

The native expansion budget counts dispatches, not propagation or verification.
A checked unit conflict can therefore publish with zero expansion budget. A
bounded fallback stop remains unresolved and does not register an incomplete
result. Source/model checking, publication transactions, rollback and native
proof formats are unchanged.

## Four-policy comparison

The nineteen preceding sources are followed by four fixed-seed single-clause
deletions from cases 16 and 7. No outcomes were filtered before measurement.
Every source receives the same six supplied guards: 138 queries per worker.
Four policies in four alternating serial orders produce 2,208 attempts. Each
worker agrees on 125 UNSAT and thirteen SAT cofactor answers. Historical prefix,
donor acquisition, static hints and native fallback are matched.

| Policy | Expansion dispatches | Preparation + query | Native payload | Proof delta + hints | Selected retained Python containers |
|---|---:|---:|---:|---:|---:|
| Shared baseline | 55 | 414.48 ms | 1,551,836 bytes | 156,321 bytes | 8,460,643 bytes |
| Ungated learned covers | 45 | 468.43 ms | 1,575,964 bytes | 228,469 bytes | 8,668,024 bytes |
| Gate only, covers disabled | 46 | 417.47 ms | 1,551,836 bytes | 200,871 bytes | 8,531,930 bytes |
| Gated learned covers | 39 | 442.51 ms | 1,535,146 bytes | 218,158 bytes | 8,493,876 bytes |

The gated learner improves preparation plus query **5.53%** against ungated
learning, with lower native payload and retained containers. It remains **6.76%
slower** than the shared baseline and retains 0.39% more selected-container
memory. Its native payload is 1.08% smaller, but its hints are 76,533 bytes
against the baseline's 11,505. Native certificate size alone misses this cost.
The learner improves against its ungated version in all four paired repeats,
and remains slower than baseline in all four. The small complete-worker
differences do not establish a robust general speedup.

The nine screens cost about 5.30 ms in the first gated order. Three find unit
conflicts. At case 6/guard 3, mean query time falls **17.77 to 3.30 ms**, restoring
the ordinary unit proof; baseline takes 3.32 ms. Case 9/guard 5 avoids an unused
first extraction and falls 9.00 to 2.90 ms. The two case-16 cover transfers remain.
Misses still cost: the SAT case 7/guard 4 takes 16.88 ms against baseline 8.07 ms,
and case 15/guard 3 takes 23.53 against 16.72 ms after deferred extraction moves
to that later failed match.

The gate-only ablation has **byte-identical native proofs and chronological
additions** to baseline. Its 55-to-46 dispatch reduction bypasses nine top-level
calls; it does not remove branching proof obligations. Its mean is 0.72% slower,
and maintaining descriptor metadata grows hints without acquiring covers. This
separates routing counters from genuine search and resource savings.

Complete-worker means are 3.541 s (baseline), 3.644 s (ungated learning), 3.590 s
(gate only) and 3.510 s (gated learning). They include restored state, hashing of
frozen sources, donor/hint preparation, queries, checking, persistence, warm
reads, cold answer replay and reconstruction. Persisted hint checking is timed
separately. Selected-container figures omit other Python state, temporary and
native allocations. The existing bank caps encoded storage, not total memory.
This local comparison adds no external benchmark or unrestricted complexity claim.

## Next structural gap: a broken leaf discards intact branches

The new edits expose an exact limitation of all-or-nothing cover matching:

| Target / guard | Earlier origin / guard | Intact leaf supports | Broken leaf supports |
|---|---|---:|---:|
| 19 / 3 | 4 / 3 | 2 of 3 | One leaf loses one clause |
| 19 / 3 | 15 / 3 | 3 of 4 | One leaf loses one clause |
| 20 / 3 | 4 / 3 | 1 of 3 | Two leaves each lose one clause |
| 20 / 3 | 15 / 3 | 2 of 4 | Two leaves each lose one clause |
| 20 / 3 | 19 / 3 | 3 of 4 | One leaf loses one clause |

These are posthoc matches of checked covers from strictly earlier origins,
not free discoveries or new solver hits. The current route pays for extraction
and then falls back on the entire target when any support is missing. The two
new hard queries take 24.83 and 31.48 ms under gating, against baseline 17.67 and
22.71 ms. Their remaining conditional branches deserve investigation.

Retain the intact branch refutations and acquire only failed leaves, preserving
the tree's exact partition and every path assumption. A negative root still
requires all reachable branches; a positive child requires a lifted full-target
witness. Reuse the checked unit prefix where it makes branches unreachable or
shrinks their residuals, but charge discovery, residual construction, checking,
full recomposition, storage and cold replay. The nearby SAT cases must remain
controls. Partial matching by itself is not a verdict, and no speedup from this
proposed branch repair has yet been measured.

`next-target.json` retains exact missing clauses, path guards, source and origin
bindings, the chronological query log and the measured costs. Automatic guard
selection, general variable correspondence, compact closure under arbitrary
edits and worst-case cover-size bounds remain open.

## Reproduction and checks

Runtime: `experiments/cnf_unit_cover_gate.py`. Resume from
`experiments/results/cnf-unit-cover-gate/checkpoint.json`. The comparison includes
both no-learning baseline and gate-only ablation; the validator checks every
screen, transfer, chronology and persisted bank with both native readers.

Nine new tests cover unit conflicts without discovery, retained prefixes,
guard misses, surviving cover hits, the disabled-cover ablation, invalid traces
and identities, budget stops, all 512 two-variable clause subsets and rejected
candidates. The first invalid-trace fixture accidentally hit an existing checked
answer from its donor; that source and failure are retained. An added unrelated
clause makes the corrected target uncached and exercises trace rejection.

Validation passes 1,559 full tests and 70 focused tests. All 2,208 comparative
queries are audited, including every screen, chronological origin and native
proof. Both readers check 76,481 cumulative native records, the unchanged
extension tables and all 342 prior partition records. Forty native identities
are added without replacing earlier authoritative payloads. All 12,813 prior
artifacts across 145 manifests remain unchanged; the new seal binds 827 source
files. The full suite retains 44 unclosed-SQLite warnings, with none in the
focused suite. The 247-page manuscript builds without LaTeX/layout warnings and
preserves all 64 preceding proof environments.
