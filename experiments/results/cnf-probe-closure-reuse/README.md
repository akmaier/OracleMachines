# Checked reuse of unit closures: verbose policy identity trial

9 November 2026. Reusing checked fixed points avoids 14,705 continuation
propagations while preserving every acquired semantic plan. This first trial
also exposes a storage regression: repeated policy metadata outweighs the
smaller proof records. Keep this evidence and the separately versioned policy.

## Rule and independent checking

After an inconclusive original probe pass and an independently justified learned
batch, consider each continuation assumption. If that assumption was probed
before, extend it by the saved unit assignments and inspect the added clauses.
A clause is inactive if satisfied or if at least two literals remain unassigned.
When every addition is inactive, reuse the original trace by an integer reference.
Otherwise, or for a new assumption, perform the existing full propagation pass.
Forced opposite closures and common-consequence closures still run in full.

The checker first validates every original trace and fixed point against the
original source, then recomputes and checks the learned batch. Only then may a
reference resolve to an original certificate with the same assumption. It checks
the delta again. Restriction preserves concatenation and the surviving original
clause prefix, so old reason indices stay valid. Deleted/edited clauses or a
different source cannot silently inherit these dependencies. No recursive or
cross-source proof references are accepted. An inactive batch establishes a unit
fixed point, not satisfiability or absence of other semantic consequences.

There is no new inference rule or SAT family here. Related sharing of propagated
implications is established in Section 8 of Heule et al. (2005), *March_eq*,
[author PDF](https://www.cs.cmu.edu/~mheule/publications/35420345.pdf).
That tree-based procedure shares implications across look-ahead literals; this
experiment reuses a same-assumption closure after an append-only learned batch.
The published experiments also show that sharing need not improve every family.

## Matched study

All 1,173 prior sources are retained, with 24 fresh random 3-CNFs (eight each at
20, 32 and 48 variables) and twelve growing/signed/edited controls. The 512 tiny
exhaustive inputs are separated from 697 other sources. Both inventory policies
use identical depth-two plans, four conditioning choices, four probe variables
per pass and at most four learned clauses. Inputs are unlabelled to recognition.

| Mode | Closed / 697 | Fresh / 24 | Total seconds | SQLite bytes | Cold seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving | -- | -- | 14.72990 | 58,273,792 | 3.27413 |
| Full second pass | 634 | 15 | 62.75908 | 197,103,616 | 26.78483 |
| Closure references, verbose identity | 634 | 15 | 61.35989 | 200,323,072 | 26.49960 |

All 1,209 source summaries and selected DAGs match. All 13,066 CNF/depth nodes
have identical semantic plans, including alternatives, selected branches,
recognized outcomes, unit sets, learned batches and witnesses. The comparison
ignores unit order/reason choice only after independent archive checking:
2,015 continuation records use a different valid trace. Both modes make 73,101
logical probe attempts. All modes retain 10,856 ordinary solver residuals.
There are no gained or lost closures; 63 sources remain unresolved. The selected
remainder contains 94 distinct nodes, with 60 learning-clear and 34 clear outcomes,
and 14,871 literals. The previous learning gains remain intact.

The continuation has 17,548 attempts: 14,705 reuse an old fixed point, 672 repeat
an assumption with an active addition, and 2,171 probe a fresh assumption.
Full checking verifies 17,131 reused probes across acquisitions/lifts. Restrictions
fall 61,754,468 -> 52,954,154 literal visits; propagation falls 52,410,734 ->
44,540,235; fixed-point reconstruction falls 39,317,548 -> 34,969,051. Added delta
work visits 140,961 literals and constructs 122,155 assignment entries. These
are instrumentation totals, not wall-clock predictions.

Discovery is 48.01501 -> 46.25967 s; total time falls 2.23%, cold replay 1.06%.
Warm inventory replay is 0.18508 -> 0.17681 s. The same six-case Python peak falls
20,377,769 -> 20,080,017 bytes, excluding native SQLite, RSS and full-corpus peak.
The reference certificates replace 968,853 bytes with 161,755 bytes, saving
807,098 bytes locally. Yet logical node bytes rise 79,561,439 -> 80,448,229,
source bytes 4,282,300 -> 4,503,284, and SQLite rises 1.63%. The extra policy field
is repeated in every full key and referenced edge, including nodes without
learning. This failed representation choice is retained. A compact, distinct
replacement version tag is the follow-up; do not infer total storage saving
from local proof compression alone.

The largest remaining discovery case is fresh source 1194. A separate 4.36647 s
profile again identifies restriction, unit checking/propagation and literal
helpers as dominant. Original probes and active/new continuations remain costs;
most unresolved leaves still defeat the bounded learning round.

## Bounds and validation

For a saved closure with u unit assignments and q binary additions, the delta
costs expected O(u+q) time and O(u) temporary assignment space with dictionaries,
after charging the original check. It avoids a fresh source restriction, repeated
propagation and full fixed-point scan. A stored reference costs O(log k) bits for
probe cap k, excluding JSON framing and the original retained proof. With r
reused probes among at most 2k continuations, the probe portion is bounded by
O(L + v log v + r(v+q) + (2k-r)(v+1)(L+q)) for this scan implementation, before
retained reduction closures and all other planning/persistence costs. No gain is
guaranteed when every addition is active or every assumption is fresh. These
local bounds do not limit the number of arbitrary-SAT acquisition nodes.

All 348 Python tests pass, including 512 exhaustive two-variable inputs and
3,304 three-variable inputs of at most three clauses at learning caps 0/1/4,
full expanded-proof replay and exact model fibers, active/conflicting additions,
new assumptions, signed mixtures/edits, forged/circular or wrong-source references,
invalid lifts, cold corruption and coexistence. The older fixtures did not trigger
active repeated assumptions; a retained seeded eight-variable counterexample
now explicitly rejects that unsound reuse. Three new and three previous complete
archives replay byte-identically. Primary timing modes, memory diagnostics and
the separate profile ran without concurrent tests or Lean builds.

Timings are single sequential synthetic samples, not significance estimates.
Operation time charges discovery, verification, serialization, persistence,
original-source solving and root lifting. Generation, small truth tables, DAG
summary walks, initialization, compression and diagnostic profiling are separate.
Warm reuse adds no records. The independent decision solver remains unchanged.
The verbose namespace and all unsuccessful attempts are preserved.

Reproduce to a new destination:

```sh
python3 experiments/compare_cnf_probe_closure_reuse.py --output /tmp/new-closure-reuse
python3 experiments/analyze_cnf_probe_closure_reuse.py /tmp/new-closure-reuse
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
