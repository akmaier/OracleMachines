# Checked UNSAT supports: less search, higher total cost

The new extractor derives independently checked UNSAT clause subsets from saved
refutations. On 192 unseen double deletions, the full support bank answers **40
negative queries** through containment and reduces fresh expansions **524 ->
355 (32.25%)**. It nevertheless increases complete runtime **28.51440 ->
39.96590 seconds (40.16%)**, peak RSS **28.15%**, and SQLite size **23.74%**.
Keep this as an optional research path and a retained cost regression. A smaller
number of expansions is not sufficient evidence of a faster system.

## What the new pattern certifies

A checked unsatisfiable clause set `K` certifies every query `G` containing `K`
in the same variable coordinates. This is an exact upward-closed family of
UNSAT inputs, including compatible combinations of deletions and additions.
Recognition checks actual clause containment; a failed match gives no answer.
The bank is not complete for arbitrary UNSAT formulas, and no minimality claim
is made about its cores. Nontrivial variable renamings are not searched.

Proof-based core extraction and independent proof checking are established
methods. Zhang and Malik describe recovering an unsatisfiable subset from the
original clauses used by a refutation in their [DATE 2003 paper](https://www.princeton.edu/~chaff/publication/DATE2003_validating_sat_solver.pdf),
Section 4. Our contribution here is the implementation-specific support
transport and measured resource tradeoff, not a new complexity result.

`SupportExtractor` follows the existing negative certificate graph. It retains
unit-trace antecedents and conflicts, the clauses on implication paths, the
selected positive Hall groups and negative matching constraints, or the
necessary component/subsumption child. At splits, it lifts both residual
supports to actual parent clauses, preserving variable renaming and clause
normalization. Unit traces are conservative: irrelevant earlier forced units
can remain. The implementation does not solve a new SAT instance to minimize
a support.

Every derived core uses the existing residual certificate format and is checked
by its frozen verifier. When a core lies inside a query, publication uses the
existing contradictory-subset certificate (`component`) with exact source
clause indices. An error in extraction cannot bypass that checker. Cold replay
needs the resulting certificate graph, not the extraction algorithm. This is
Python certificate checking, not a new Lean proof of the implementation.

## Fixed comparison

The prior checkpoint retains 9,104 reference keys and decisions for all single
clause deletions of three UNSAT templates. We enumerate all **11,202 double
deletions**, rank each template's candidates by a salted hash of the complete
canonical query, and choose 64 per template. Selection consults neither core
containment nor the new query's answer. None of the candidate roots is already
cached. The resulting 192 queries interleave template ranks. These remain
constructed development inputs, not an independent benchmark collection.

All three modes start from the full parent union and the same 260 known
single-deletion templates. They share direct query lookup, checked SAT witness
transfer and checked UNSAT guards. The candidate modes additionally extract
supports from either the three original templates (`three`) or those templates
plus 185 previously known negative single deletions (`all`). Repeated raw cores
are deduplicated. No prospective double-deletion outcome chooses a support.

Three fresh-process triples rotate mode position; every stream visits the same
queries twice. All modes return **102 SAT / 90 UNSAT**, and every repeat adds
zero rows. Each candidate process pays its own extraction cost. Full setup,
recognition, checking, publication, solving, bookkeeping, cold replay, sidecar
writing and compression are inside the complete clock. Process launch, imports, command-line protocol/catalog reads and final report
writing are excluded. Selection takes **1.47029 s** separately, with a measured
139,001,856-byte peak RSS; historical acquisition remains separately retained.
No tests, build or profiler overlap the timed streams.

| Measurement | Guarded control | Three supports | Full support bank |
|---|---:|---:|---:|
| Distinct raw cores | 0 | 3 | 145 |
| First-visit core hits | 0 | 7 | 40 |
| Fresh expansions | 524 | 519 | 355 |
| Decision splits | 161 | 161 | 114 |
| New preparation nodes | 0 | 148 | 4,102 |
| All new stored rows | 623 | 773 | 4,596 |
| Mean extraction seconds | 0 | 0.12728 | 4.92563 |
| Mean query-stream seconds | 18.64218 | 18.66493 | 22.56550 |
| Mean cold-check seconds | 7.74113 | 7.80129 | 9.80278 |
| Mean complete seconds | 28.51440 | 28.72597 | 39.96590 |
| Mean peak RSS bytes | 327,745,536 | 328,302,592 | 420,014,763 |
| SQLite bytes | 34,680,832 | 34,963,456 | 42,913,792 |
| Database gzip bytes | 2,694,977 | 2,724,556 | 3,438,879 |
| Gzip database + raw sidecars, first trial | 9,161,674 | 9,132,335 | 10,222,438 |

The small bank saves only five expansions despite seven hits; several guarded
cofactors are already cheap or cached. Its 0.74% mean whole-time increase is
small, and paired signs differ. The full bank's whole-time regression occurs in
all three repetitions. It avoids 169 fresh expansions but adds 4,102 checked
preparation nodes, so total new rows rise sharply. All modes also publish 99
SAT witnesses. Hit counts, publications and avoided expansions are distinct.
No query needs more fresh expansions under the full bank on this fixed order,
but neither whole time nor retained memory follows that local improvement.

## Costs and compression limits

Extraction is bounded by the traversed refutation DAG and emitted certificate
payload, not just the original CNF length. The screen traverses 4,961 negative
nodes and emits 4,102 derived nodes, including 1,918 subset wrappers. Its three
original supports shrink 82 clauses to 64 and 63, and 96 to 80. Across all 188
negative sources there are 145 distinct raw supports. The original DAG itself
can require exponential acquisition or space. This supplies no polynomial
construction for every CNF.

With ordinary hashed clause sets, bank recognition costs the query clause-set
construction plus, in the worst case, containment checks across all stored
cores. Publication also normalizes, serializes and checks an entire query
certificate. Warm proof checks can reuse verified nodes; cold verification must
validate the reachable graph. The benchmark's bookkeeping reads the complete
database before and after each query, and the underlying solver recomputes
archive size with a full-table aggregate. These measured operations grow with
retained history and must not be mistaken for fresh SAT branching cost.

The post-hoc containment audit safely reduces **145 cores to 121**: every
removed core contains a retained checked core. Thus the union of recognized
superset families is unchanged for every query, not only these 192 examples.
This is a diagnostic candidate bank, not a measured faster implementation.
Its required preparation proof nodes fall **4,092 -> 3,804**. The current full
bank and query proofs leave only **10 preparation nodes / 8,250 key-plus-payload
bytes** unused. Simple removal of unused derived nodes cannot explain away the
regression; almost all new proof nodes support a retained result. No rows were
deleted. Any future active-cache projection must retain historical results in
an independently bound archive.

All 90 negative double deletions remain correctly classified by checked cores
or guarded fallback. After the full bank, they account for **328 of 355** fresh
expansions; the three positive fallback cases account for 27. Separately safe
single deletions still do not justify a simultaneous deletion: a common
remaining checked core is sufficient evidence, while absent evidence requires
another exact route.

## Next target and durable state

The next comparison should reuse the **persisted core bank**, rather than
re-extracting it, on further unseen compatible edits. Charge the observed
4.93-second initial extraction and retained proof growth explicitly when
computing amortized cost. Use the same complete initial reference union for
both arms; the control must also benefit from exact residual reuse. The
121-core antichain is a certified coverage-preserving candidate, but its runtime
and persistence effects still need measurement. Do not claim a break-even point
from this run: even repeated-query time currently increases with the full bank.

The larger accounting gap is repeated work proportional to the whole archive.
A warm-query profile is retained separately in `warm-profile.json`. Over 192
read-only queries, full row snapshots take **5.80760 s** and archive-size
aggregation **3.45805 s**, together **84.55%** of the **10.95876 s** instrumented
loop. These two call categories do not overlap. Core-bank matching takes only
**0.01618 s** on 53 misses. This profile follows proof warming and is outside
the matched timings; it measures overhead, not an optimization speedup.
Investigate exact append-only delta accounting and a maintained archive-size
ledger before attributing future savings to a faster SAT algorithm. Certificate
sharing remains relevant, but the unused-node audit rules out a large immediate
gain from simple pruning alone.

The durable union preserves earlier payloads and all distinct new results:
**13,869 keys / 43,380,736 SQLite bytes / 3,479,528 gzip bytes**. All 21 occurrences
of alternative valid certificates remain in trial archives. The 192 new
decisions include **139 direct query certificates** and **53 explicit guarded
cofactor records**. For the latter, a cofactor key is not the complete query key;
the exact source, guard, child proof and lifted model remain bound together.
The old twelve and 257 direct decisions are retained unchanged.

Resume `experiments/results/cnf-unsat-support/checkpoint.json`; its report binds
`all-0/cores.json` for reuse. Preserve all prior study and decision fields, plus
`unsat_support_study`, `unsat_support_decisions` and `reference_union`. Structural
authority is unchanged: **2,614 patterns / 259 pairs / seventeen missing
children**, original **17/24 / 999 proof steps**, and separate supplemental
**24/24 / 208 proof steps**. These reference decisions do not redefine structural
coverage.

All **403 tests** pass, including all 512 two-variable CNFs, three-variable truth
table checks, every negative proof kind, wrong premises, raw-coordinate transport
and cold persistence. Independent validation checks nine trial archives, **3,456
query replays**, the preparation screen, all derived cores, every union node,
269 inherited decisions and all new decisions without fresh expansion.

```sh
python3 experiments/compare_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/validate_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/analyze_cnf_unsat_support.py /tmp/cnf-unsat-support
python3 experiments/profile_cnf_unsat_support.py /tmp/cnf-unsat-support
```
