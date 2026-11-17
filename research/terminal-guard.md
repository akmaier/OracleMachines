# Terminal proof admission does not broaden this fresh batch

The optional terminal-conflict selector passes its controls but adds **no new
transfer** on 192 fresh neighbours. Both policies use **68 fresh expansions,
23 splits, 66 materialization rows and 309 new proof rows**, with 31 cofactor
hits and 99 SAT / 93 UNSAT answers. The resulting proof databases are identical.
This is a retained negative coverage result, not evidence of a faster solver.

## Policy and comparison

Both arms run the previous frozen query pipeline. The candidate substitutes only
its selector: after the same bounded ready-only search misses, it scans matching
pending supports under the already examined alternative guard. It checks the
actual negative origin and accepts only a unit certificate with a non-null
conflict. The appropriate legacy or causal extractor derives the core, binds its
root and checks the negative certificate. Derivation publishes at most one core
row. The ordinary guard, subset-publication and child-check path still follows.
An origin with a child reference is not terminal. Existing ready proofs always
take priority. The rule bounds publications, not trace length, bytes or time.

Four alternating process pairs start from the same **20,340-key** union and the
same 207-entry legacy / 176-entry causal portfolio. Input selection excludes
2,496 prior sidecar answers and cached whole-query roots, taking 64 new neighbours
per template and visiting each twice. The larger optional causal bank is retained
but not loaded. Neither policy acquires new origins. No tests, builds or profiles
overlap timed workers; independent validation runs afterwards.

There are initially **nine legacy and eleven causal pending entries** with
terminal unit-conflict origins. None is contained in any of the eight unresolved
alternative targets. The candidate therefore performs **zero origin reads and
zero terminal derivations**, while adding 3,064 containment-candidate inspections
and 95,624 clause units. The single pending hint seen by the initial ready-only
scan belongs to a query that finds a later ready proof. Repeated visits add no
rows. New terminal filtering does not change any selected guard or query answer.

Mean complete times are **13.93276 / 13.72331 seconds**, a 1.50% lower candidate
mean. Paired changes are **+1.35%, +27.06%, -27.90%, +2.31%**; no stable speedup
is established. Mean query time rises 1.58%, and peak RSS averages 0.73% higher.
Full cold replay and compression consume 46.37% and 28.66% of candidate time.
Both trials occupy 64,897,024 SQLite / 4,793,284 gzip bytes. Gzip plus first-trial
sidecars grows by 300 bytes, from 12,217,506 to 12,217,806. Historical acquisition,
input selection and independent validation remain separate costs. Complete time
includes the frozen pipeline and wrapper reporting through the penultimate
write; imports, initial CLI reads and the final timing rewrite are excluded.

## Controls and the next structural gap

The integrated selector is exercised separately on exact historical prefixes.
It admits old case 85 with one derived core and one target row, with fresh search
disabled. It rejects recursive cases 23 and 103 without publication. Every new
control payload was already retained by the preceding diagnostic checkpoint.
These controls validate the policy; they do not add fresh coverage.

The current unresolved cases are **41 (8 expansions), 56 (17), 98 (4), 107 (7),
139 (1), 155 (3), 176 (24), and 179 (4)**. Cases are local to this new stream.
Of the 68 expansions, **67 belong to template 12** and one to template 8;
65 belong to UNSAT queries and three to the SAT query 155. None of the 31 hits
uses a removed-clause assignment absent from all recorded origins of its core.

A read-only check identifies a precise next possibility. Suppose a checked
UNSAT core K is contained in T together with one missing clause C. Then T and C
is UNSAT, so every model of T falsifies C. This justifies restricting T by the
complements of all literals in C; it does **not** justify declaring T UNSAT or
dropping C from the proof. Exhaustive two-variable truth tables check this
restriction, including satisfiable T and a counterexample to premature UNSAT.

| Current case | Expansions | Target clauses / literals | After justified restriction |
| --- | ---: | ---: | ---: |
| 56 | 17 | 79 / 218 | 67 / 172 |
| 98 | 4 | 79 / 215 | 75 / 195 |
| 107 | 7 | 75 / 205 | 69 / 185 |
| 139 | 1 | 69 / 190 | 56 / 149 |
| 155 (SAT) | 3 | 82 / 223 | 76 / 199 |
| 176 | 24 | 86 / 240 | 77 / 209 |

Several bank entries propose the same restriction. None of the restricted
targets is already known or contains a ready or pending retained support.
Cases 41 and 179 need at least three and two missing clauses respectively among
overlapping ready cores. The probe excludes empty-clause and no-change cases.
Availability is reconstructed from each pre-query append prefix, so later solved
targets cannot create a diagnostic hit. No new proof is published by this probe.

**Next target:** build checked composition for the extra restriction and compare
the remaining solve cost for cases **56 and 176**, which account for **41/68
expansions**. Charge recognition, the negative strengthened-formula premise,
restriction, proof publication, remaining solving and later reuse. Retain case
155 as a SAT control. A smaller residual alone is not a runtime bound. Future
generalization must use new inputs; these cases are now retained.

## Retained evidence

The source modules, all eight complete trial archives, query records, phase
measurements, controls and unsuccessful missing-clause endpoint search are in
`experiments/results/cnf-terminal-guard/`. The selector remains optional.
The full solver suite passes **1,013 tests**, with the older unclosed-SQLite
ResourceWarnings retained in its log. Fifteen focused selector/publication tests
and two subsequent missing-clause condition tests pass without warnings. No new
Lean or unrestricted-SAT theorem is claimed. Exact composition of the additional
restriction is still implementation work, not an already enabled inference.


## Validation and resume state

Independent validation passes eight complete trial archives / 3,072 query
replays, every union node, all 2,765 inherited decisions and all 192 new decisions.
The union contains **20,649 keys**, preserving all 20,340 prior payloads and
adding 309. There are no alternate certificates. New decisions have 144 direct
roots / 48 negative guards. The separate original structural authority remains
2,614 patterns / 259 pairs, 17/24 coverage with 999 steps; supplemental authority
remains 24/24 with 208 steps. No old discovery pointer is replaced.

Resume `experiments/results/cnf-terminal-guard/checkpoint.json`. It adds only
`terminal_guard_study` and `terminal_guard_decisions` to the prior semantic fields.
All prior diagnostic archives and proof deltas remain preserved. Retained support
ready/pending counts are **129/41 original, 136/71 legacy, 74/102 causal and
74/129 optional expanded causal**. All four complete lineage checks pass; no
support origins were acquired. The source ledger binds 416 files. Prior
preservation checks cover **408 sources / 4,513 artifacts / 79 manifests**.
The paper builds to **202 pages**, with all 64 existing proof blocks unchanged.

Checkpoint SHA-256: `cf7f56eddae920bef8474b92311f37caa65cb635d36973d7adab5d616d7a3358`.
Report SHA-256: `a462fccce08165e759429c6ac3a9ada5e3e1a9f0f8799177d49438fb2c0cdbc5`.

New manifest: **66 artifacts**. Next preservation audit: **4579 artifacts / 80 manifests**.
