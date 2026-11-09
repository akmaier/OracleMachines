# Bounded local learning from saved implication proofs

9 November 2026. Three additional sources gain structural closure, including
one fresh 48-variable UNSAT input, but total acquisition and memory cost rise.
The policy remains optional. Ordinary source solving is unchanged.

## Recognition, checking and exact composition

After failed-literal, common-consequence and signed-equivalence probing are all
inconclusive, scan saved attempts/unit reasons in deterministic order. An implied
literal l under assumption a licenses the binary clause (not a or l). Skip
explicit duplicates and implications already reachable in the binary graph,
including paths through earlier accepted batch clauses. Accept at most four
clauses, append them in recorded order and run one further four-variable probe
pass. Only a forced/common assignment or signed equivalence that strictly reduces
support can acquire a child. Otherwise, retain the failed attempt and continue
ordinary planning on the original CNF. No clause-only expansion recurses.

Every original assumption and reason is checked before any learned addition is
trusted. This prevents circular justification by the new batch. The checker
then reconstructs the augmented source, verifies the whole continuation, outcome,
strict support reduction and exact child. Lifting restores forced values or the
signed representative map and checks the original parent. All earlier recognition
priorities and overlapping family certificates remain available. The policy has
its own versioned identity; earlier records coexist unchanged. An edit/deleted
reason needs the exact new source dependency context.

If every F-model satisfying a_i also satisfies l_i, then every F-model satisfies
(not a_i or l_i). Thus F and H=F AND all learned clauses have **identical models**.
Composing this with the checked reduction of H yields `G(y) iff exists h, F(y,h)`
on retained variables Y, with exact model lifting. An unsuccessful pass proves
neither SAT nor absence of useful implications.

The rule is established local learning. Heule et al. (2005), *March_eq*, discuss
binary clauses learned from look-ahead and selective constraint resolvents in
Sections 1/4; their Figure 1 supplies the small forced-literal test pattern.
[Author PDF](https://www.cs.cmu.edu/~mheule/publications/35420345.pdf).
The unmodified example is already recognized by our all-true family. Flipping
variable 2 preserves its reasoning while making the learning path reachable.
That failed fixture choice is retained as a recognition-priority test. Our
implementation/accounting experiment does not make the inference new.

## Matched comparison

The corpus preserves all 1,137 previous inputs and adds 24 fresh seeded random
3-CNFs (eight each at 20, 32 and 48 variables) plus twelve growing, signed and
edited controls. The 512 exhaustive tiny sources are separated from the remaining
661. Labels never select routes. Both policies use depth two and four arbitrary
conditioning candidates; learning adds one extra bounded probe pass. **Total
probe budgets are not equal.** Preparation, checking and that extra work are
charged, rather than presenting the second pass as free reuse.

| Mode | Closed / 661 | Fresh / 24 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving alone | -- | -- | 12.52000 | 50,573,312 | 2.73431 | -- |
| Signed-equivalence baseline | 604 | 18 | 48.17697 | 163,532,800 | 20.78528 | 11,410 |
| Bounded learning | 607 | 19 | 52.69690 | 168,267,776 | 22.01280 | 11,406 |

Gains are old cases **956** (20 variables, SAT), **1057** (48 variables, UNSAT),
and fresh **1155** (48 variables, UNSAT). No baseline closure is lost on this
corpus. All twelve new controls close in both modes. Fifty-four sources remain
structurally unresolved: 49 old and five fresh. The separate solver still decides
every original input, retaining exactly 9,760 residuals under every mode.

The [37-source pilot](../cnf-probe-learning-pilot/README.md) selected old misses
with non-binary-path implications on their chosen unresolved paths. It gains
only 1057, at higher time/storage cost. Case 956 was not in that selection: gains
can arise through changes elsewhere in the acquisition graph. The full comparison
and all failed alternatives are retained, not only selected opportunities.

## Costs and remaining interaction

Discovery rises 35.64804 -> 39.96872 s; total time rises 9.38%, database bytes 2.90%
and cold checking 5.91%. Warm replay is 0.16795 -> 0.16063 s. Logical node bytes
rise 63,465,538 -> 66,573,092 despite four fewer pattern nodes. Exact-source bytes
rise 3,866,927 -> 4,109,738. Probe nodes occupy 41,131,705 bytes; unresolved nodes
9,416,388 bytes. The six-case traced Python peak rises 18,466,093 -> 20,377,761
bytes (cases 858, 875, 907, 970, 1042, 1061), excluding native SQLite, RSS and
full-corpus peak. The subset differs from the preceding study.

There are **1,938** learning attempts proposing **4,909** clauses. Of these,
**1,709** remain inconclusive. The 229 successful continuations are 150 forced
reductions, 53 equivalences and 26 common consequences. Immediate child kinds
are seven recognized families, twelve component splits, thirty OR nodes,
112 further probe reductions and 68 unresolved nodes. These include unselected
alternatives and must not be treated as source coverage gains.

All **1,780** exact parent CNF/depth pairs shared with the baseline keep identical
original probe lists. Total attempts nevertheless rise 47,286 -> 62,784, with
15,052 in the additional continuation phase. Checked attempts rise 101,066 ->
122,476. Batch/continuation JSON alone occupies 1,945,661 bytes. Conditioning
candidates fall 2,348 -> 2,247; selected unresolved literals fall 12,686 -> 11,106.
Eighty selected distinct unresolved nodes remain, 48 with an inconclusive learning
attempt and 32 without one. Smaller selected remainders and fewer nodes do not
ensure smaller acquisition or proof storage.

Timings are single sequential synthetic samples, not significance estimates or
industrial comparisons. Operation times include recognition, discovery, checking,
serialization, persistence, original-source solving and successful root lifts.
Generation, truth tables, summary walks, initialization, compression and diagnostic
profiles are excluded. Timed full-study modes ran without concurrent tests or
Lean builds. Cold checks include all alternatives, sources and solver certificates.

## Attribution: added strength versus changed choices

`learning-mechanisms.json` fixes each successful continuation's variable choices
and repeats the bounded pass on the original source without learned clauses.
It still produces a reduction in **49/229** nodes: 39 forced, five common and
five equivalence reductions. The other 180 passes remain inconclusive.

The selected learning nodes on both old gains (956/1057) still force a value
without additions under the changed choices. The selected node on fresh gain
1155 remains inconclusive without additions. Thus stronger propagation explains
that local fresh gain, but the three source gains should not all be credited
solely to the clauses. Obtaining the changed choices is not free. Local reductions
do not prove counterfactual whole-source closure, and a clear pass does not prove
semantic necessity of the learned clauses.

A separate replay of the preceding archive's 77 selected leaves finds thirty
without a batch, 41 unsuccessful continuations, five forced reductions and one
equivalence. This distinguishes local opportunity from root closure and retains
the old failed candidates for future comparison.

## Resource bounds and next experiment

Let k be the probe cap, q the batch cap, v variables, m2 binary clauses and L
literal occurrences at this node. At most 2kv saved unit entries supply candidates.
The current selector may traverse the binary graph for each candidate, costing
expected O(L + kv(v+m2+q)) with hash sets. A batch adds at most 2q occurrences.
Continuation propagation costs O(k(v+1)(L+q) + v log v) with the current scan
routine, in addition to checking, normalization, recognition and persistence.
Both original and continuation traces are retained. Every successful learning
edge reduces support, limiting such edges to v on a support-decreasing path;
the cap is not a global bound on acquired nodes, alternatives or total storage.

The largest remaining discovery case is now **1063**, at 1.20829 s main discovery
and 4.07290 s under a separate profiler. Restriction scans, unit checking,
propagation and literal helpers dominate own time. The continuation contains
**13,194 repeated assumptions**, of which **10,018 reproduce identical complete
certificates**, out of 15,052 probes. Repeated assumptions have 35,515 original
unit entries versus 37,719 continuation entries. Do not simply skip them: added
clauses can strengthen propagation, as the fresh gain demonstrates.

**Next target:** reuse a checked original closure when the added batch has no
unit or conflict under that closure and assumption. Original clauses/reasons
are unchanged and added clauses alone need the incremental fixed-point test.
Otherwise resume propagation or fall back to a full pass; new choices still
need fresh probing. Preserve clause-index transport and exact source/batch
bindings. A shared certificate representation could avoid both repeated scans
and duplicated proof JSON. Measure matched plans, fibers, cold checking and total
space before enabling it; the observed opportunity is not a measured saving.
This supports further structural discovery without raising the global probe cap.
Unrestricted efficient SAT construction and compact coverage remain open.

## Verification and reproduction

All **341 Python tests** pass (28.55 s). The new tests cover all 512 two-variable
CNFs and 3,304 subsets of at most three of the 27 three-variable clauses, at caps
0/1/4, including full model equality before/after learning and exact reduction
fibers. Additional cases check forced/equivalence continuations, unchanged failed
attempts, binary redundancy, disabled mode, signed mixtures, source edits,
circular/forged/omitted witnesses, invalid lifts, cold corruption and old-policy
coexistence. All three full new archives, three pilot archives and three preceding
full archives replay byte-identically.

Lean adds `probe_implication_entails_clause` and `entailed_signed_batch_models`
with explicit original-source hypotheses. The full build and axiom audit pass
at **4,103 declarations / 1,959 theorem declarations**. The lemmas prove the
semantic rule and batch model preservation; they do not refine Python, SQLite
or resource bounds. The unchanged full solver and earlier proofs remain intact.

`report.json` stores sources, fingerprints, times and counters; `summary.json`
aggregates the comparison. `mechanisms.json` records all outcomes and a separate
profile. `learning-mechanisms.json` preserves the fixed-choice counterfactual and
old selected-leaf replay, including unsuccessful traces. SQLite snapshots retain
all witnesses and alternatives. Use new destinations to preserve results:

```sh
python3 experiments/compare_cnf_probe_learning.py --pilot --output /tmp/new-learning-pilot
python3 experiments/compare_cnf_probe_learning.py --output /tmp/new-learning-study
python3 experiments/analyze_cnf_probe_learning.py /tmp/new-learning-study
python3 experiments/analyze_cnf_learning_mechanisms.py /tmp/new-learning-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
