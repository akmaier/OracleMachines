# Reusing original implication proofs as subset witnesses

The optional policy closes five additional sources: **857, 1185, 1289, 1368 and
1467**, with no losses. Across **1,497 queries**, including 512 exhaustive tiny
CNFs, non-tiny closure rises **864 -> 869 / 985**. The old subset improves **837 ->
841 / 949**; new-query closure **27 -> 28 / 36**, including **15 -> 16 / 24** fresh
random 3-CNFs. All independent solver answers agree. Structural closure means a
plan with recognized leaves, not satisfiability or a faster decision solver.

Original signed-subset exposures retain priority. On failure, the policy uses
all distinct absent binary consequences from the already acquired original probe
traces, including binary-transitive consequences excluded by learning selection.
A redundant propagation consequence can still remove a longer clause and expose
a basic family. The checker replays original reasons before reconstructing each
implication origin, signed subset certificate, classification and child binding.
It adds no propagation phase. Failed pools/searches persist. Earlier priorities
and depth-two/four-probe/four-learned-clause caps remain fixed; the additional
subset-witness pool is separately charged and is not capped at four clauses.

| Measurement | Signed baseline | Implication subsets |
| --- | ---: | ---: |
| Total operation seconds | 169.84716 | 169.80609 |
| Discovery seconds | 127.44196 | 126.71711 |
| Unchanged solver seconds | 42.32325 | 43.00260 |
| SQLite bytes | 438,288,384 | 437,620,736 |
| Pattern nodes | 25,752 | 25,047 |
| Logical node bytes | 178,289,290 | 179,395,726 |
| Source-binding bytes, 1,465 records | 6,028,353 | 6,032,748 |
| Cold replay seconds | 71.70525 | 69.97623 |
| Warm inventory seconds | 0.29428 | 0.28194 |
| Initialization seconds, separate | 0.07203 | 0.32459 |
| Six-case Python peak bytes | 20,390,278 | 21,161,046 |
| Selected unresolved literals | 33,911 | 33,651 |

The full single sample has essentially unchanged runtime, slightly smaller
SQLite and larger logical state and traced Python peak. Twelve-query ABBA BAAB
controls average **6.99619 -> 6.17832 s** total and **6.69275 -> 5.88519 s** discovery.
They deliberately include three of the gained sources. Four observations per
mode do not establish significance or repeated full-corpus performance. Answers
and summaries agree with the full run; counters, storage and database hashes
repeat within each mode. Keep the candidate optional; no general SAT speedup or
memory reduction follows.

## Indexed search and archive compatibility

For clauses with distinct literals, equal-width different sets cannot subsume
one another. The new search checks strictly shorter retained clauses and uses an
exact lookup for duplicates, preserving the old first-retained witness. Repeated
literals use the old fallback. Expected work is O(L + m log(m+1) + P w), with P
tested shorter pairs and maximum width w; temporary space is O(L+m). P remains
O(m²) in the worst case. Verification independently checks signed witnesses and
reconstructs the deterministic search. No worst-case SAT bound improves.

The indexing-only mode uses the original policy identity and accepts unchanged
old certificates. The [complete old-archive control](index-control.json) replays
all 24,122 pattern nodes and 1,429 source bindings with no inserts or byte changes.
Across its 3,753 terminal checks, subset comparisons fall **33,367,619 ->
6,284,481**, removing the known **27,083,138 (81.17%)** futile equal-width pairs.
This exact-work/compatibility control is separate from the changed implication
policy and is not an end-to-end speedup estimate. Ordinary solver certificates
are checked by the full and prior archive audits.

## Costs and the next gaps

The new full policy has **3,916 terminal searches**, with **110** exposures:
28 original and **82 implication** exposures. Of 3,888 original failures,
3,684 have a nonempty implication pool. Across these pools, it retains **29,897
binary clauses**. Original and augmented searches perform **6,744,712** and
**8,990,250** subset tests respectively; checking repeats both. The baseline
performs **35,880,691** tests in each phase. Logical probes fall **118,511 ->
115,074**, verified probes **255,701 -> 247,554**, and conditioning candidates
**4,883 -> 4,722**. Different acquired alternatives prevent attributing all total
cost differences to indexing alone.

Search fields grow **3,962,842 -> 9,029,905 bytes**, including **5,086,738 bytes**
of implication data. Pool enumeration costs expected O(L+U) for U original trace
units, with b<=U distinct additions. Augmented search uses m+b clauses and L+2b
literals. Original proof checks, origins, classifications, normalization and
persistence are additional costs. Isolated archive size does not bound lifetime
state when previous policy archives are retained.

The offline [relevance control](mechanisms.json) filters every encountered
nonempty pool to proved binary clauses contained in a long clause of the original
minimal core. It reduces the pool **29,897 -> 7,505 (74.90%)**, preserving all **82**
encountered implication exposures and losing none. It exposes **no new selected
frontier leaf**. This is not an integrated policy or a theorem preserving every
syntactic family. Its **2,278,253 relevance comparisons** are explicit; augmented
subset tests fall **8,990,250 -> 7,138,675** per search/check. Smaller pools alone
do not establish a total-cost or storage saving after integration.

There remain **116 open sources / 148 distinct selected leaves / 33,651 literals**.
Source **1194** is again the largest unresolved discovery case, at **1.67226 s**.
Its separate profile has **5,763 restrictions, 4,657 simplification checks and
2,221 propagations**, which dominate own-time costs. The next broad runtime target
is exact reuse of prepared clause/assumption and proof-checking state, with source
binding and invalidation. Broader coverage requires new entailed relations or
exact decompositions: filtering existing pools did not supply it.

## Validation and scope

All **403 Python tests** pass. The new Lean semantic composition lemma proves
that an entailed batch followed by checked signed-core coverage preserves every
model; the full audit passes **4,130 declarations / 1,972 theorem declarations**.
It does not refine Python's encoding, checker, persistence or resource accounting.
All three full, three pilot and three prior archives replay byte-identically,
including every alternative and source; warm replay inserts nothing. Each full
mode retains **21,838 ordinary solver residuals**. Both new reports have **59
matching fingerprints**, with independently hashed diagnostic scripts and inputs.

Operation timing charges recognition, checking, serialization, persistence,
solving and successful root lifts. Generation, truth tables, summary walks,
compression and initialization are excluded or measured separately. Cold replay
is separate. Allocation diagnostics cover six fixed cases and exclude native
SQLite, RSS and full-corpus peak. Benchmark modes, allocations, profiles and
repeated timing controls ran sequentially after verification completed. Synthetic
workloads and selected controls do not establish industrial performance, optimal
expansion, compact closure or an efficient solution for unrestricted SAT. Prior
results, including regressions, are preserved.

Reproduce with a new destination:

```sh
python3 experiments/compare_cnf_implied_subsumption.py --output /tmp/new-implied-study
python3 experiments/analyze_cnf_implied_subsumption.py /tmp/new-implied-study
python3 experiments/recheck_cnf_implied_timing.py /tmp/new-implied-study
python3 experiments/audit_cnf_subset_index.py /tmp/new-implied-study
```
