# Checked common consequences of probe assumptions

9 November 2026. Optional structural-discovery policy; ordinary solving remains
unchanged. The full comparison finds one additional closure and higher total
cost. This result is retained as evidence against enabling the policy by default.

## Rule, recognition and checking

If both assumptions x=false and x=true imply literal l, then every model of F
satisfies l. This is the established **necessary-assignment** rule, described
by Heule and van Maaren in *march_hi*, SAT 2009 competitive events booklet,
pp. 27--28, Section 4. [Primary source](https://www.cril.fr/SAT09/solvers/booklet.pdf).
The rule itself is not a new result.

The implementation preserves the existing failed-literal phase, including every
attempt and its candidate order. Only if every attempted assumption is
inconclusive does it intersect the unit consequences of each false/true pair.
It chooses the first pair with a nonempty intersection and applies all common
literals from that pair. One pair's assignments are consistent; consequences
from separate pairs are not silently merged. The common restriction receives
one checked unit closure and one exact child edge. Remaining pairs stay in the
record. Family, component, simplification and projection priorities are unchanged.

The checker rebuilds the restricted source for every assumption and independently
checks both unit traces and every inconclusive fixed point before trusting their
intersection. It verifies the first-pair selection, all common literals, retained
closure, strict support reduction and exact child binding. Model lifting restores
common and closure assignments and checks the full parent. An inconclusive
attempt alone remains neither a refutation nor a satisfiability certificate.

For the common assignment C and remaining variables Y, the child represents
exactly `exists h, F(C,y,h)`. Because F entails C, this is also the existential
projection of F onto Y. All satisfying parent assignments restrict to child
models and all child models lift. Recognition overlaps remain in the original
profile; `common` is an additional reduction outcome, not a universal tractable
class. Policy-specific identities preserve earlier records. Source edits require
the exact new dependency/checking context; deleting a reason clause can destroy
the implication, as retained tests demonstrate.

The Lean lemmas `common_condition_forces` and `satisfiable_common_condition` in
`Residuals.lean` formalize the literal consequence and SAT reduction from the
two implication hypotheses. They do not refine the Python trace checker or
SQLite, or bound acquisition resources.

## Matched comparison and regressions

The study retains all 1,025 previous inputs and adds 64 fresh seeded random
formulas and 12 growing component, signed-renaming and edit controls. The new
random inputs include 40 pure 3-CNFs (16 each at 20/32 variables, eight at 48)
and 24 mixed-width CNFs (12 each at 20/32 variables). Depth two, four arbitrary
conditioning candidates and four probe candidates are identical. Generator
labels never select routes. Structural closure is separate from the SAT answer.

| Mode | Closed / 589 non-tiny | Fresh random / 64 | Total seconds | SQLite bytes | Cold seconds | Pattern nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ordinary solving alone | -- | -- | 9.22197 | 33,730,560 | 1.94389 | -- |
| Failed-literal baseline | 536 | 40 | 32.12172 | 104,435,712 | 12.03279 | 8,011 |
| Common-consequence policy | 537 | 40 | 32.75928 | 107,757,568 | 12.56291 | 8,220 |

There is one gain, old case 968, and no lost closures on this corpus. It was
already one of the two gains from the previous cap-64 diagnostic. Old coverage
rises 484/513 -> 485/513; all 12 new controls close in both modes. Fresh pure
3-CNF closure is 16/16 at size 20, 10/16 at 32 and 2/8 at 48 under both modes.
Fresh mixed-width closure remains 12/24. Fifty-two non-tiny cases stay unresolved.

There are 477 common rewrites, fixing 663 literals; 349 rewrites occur at depth
zero. All 355 common nodes whose CNF/depth pair also occurs in the baseline
retain byte-equivalent probe-attempt lists. Intersecting those lists requires no
fresh probing, but each common restriction has a new closure and later residuals
can restart probing. Across the entire run, probes rise 29,280 -> 31,745 and
checked attempts 54,016 -> 63,755. Arbitrary conditioning candidates fall
2,036 -> 1,957. This is a counterexample to treating fewer branch candidates or
smaller selected residuals as sufficient evidence of lower total acquisition.

Selected unresolved literal payload falls 9,728 -> 8,101, while logical node
bytes grow 38,929,223 -> 40,749,002. Probe-node payload grows by 2,410,587 bytes;
the common witnesses and closures themselves occupy only 34,415 JSON bytes.
The main added cost is the changed collection of residuals and their profiles,
keys and checking, not just the compact witness. Policy metadata adds 159,645
exact-source bytes. No earlier records or unsuccessful attempts are deleted.

The six-case traced Python peak slightly increases, 1,968,173 -> 1,970,626 bytes.
Warm replay also rises slightly, 0.14092 -> 0.14217 s. All modes retain the same
7,393 ordinary solver residuals. Timings charge recognition, discovery, checking,
serialization, persistence, original-source solving and successful root lifts.
Generation, truth tables, summary walks, compression and initialization are
separate; full cold checking covers all alternatives and original sources.
These are single sequential synthetic samples, not significance estimates.
The allocation diagnostic excludes native SQLite memory, RSS and full-corpus
peak. It uses the same six case IDs as the previous study.

The post-selected 29-miss pilot is preserved: in-memory inventory time
5.65210 -> 5.84250 s, logical node payload 12,048,758 -> 12,871,372 bytes, one
additional closure. It excludes ordinary solving, root lifts, disk persistence
and cold audit; it is not a fresh holdout result.

## Costs, remaining structure and next target

With at most k probe variables and v source variables, intersecting saved traces
visits at most 2kv unit entries. Python sets give expected O(kv) set work, plus
O(v log v) for sorting the selected intersection. The added witness uses
O(v log(v+k+2)) bits. The retained unit closure still costs O((v+1)L) with the
existing scan algorithm, for L literal occurrences, and contributes its own
reason trace. Child reconstruction, recognition and persistence are additional.
Strict support reduction bounds a single rewrite chain by v; it does not bound
all acquired branches or guarantee compact classification of arbitrary SAT.

The separate profile of the largest remaining discovery case, 1061 (48
variables), again points to restriction, unit propagation/checking, normalization
and their literal-processing helpers. Instrumented time 2.92383 s must not be
compared with the uninstrumented 0.95485 s main measurement. Probe nodes account
for 23,646,748 of 40,749,002 logical node bytes. Avoid enabling more reductions
without measuring their downstream state and replay costs.

The next discovery candidate is **signed equivalence between variables** from
opposite implications in the same two probe traces. On common-policy unresolved
nodes, 269 archived nodes have a relation not already represented by a direct
complementary binary pair. Selected-path analysis narrows this to 16 distinct
unresolved nodes on 16 of the 52 missed source paths, accounting for 799 of
8,101 selected unresolved literals. These are opportunities, not extra closures.
They include unproved implementation obligations: complete substitution in the
parent CNF, signed representative transport, independent proof checking and
source invalidation. Start with these selected residuals and measure whether
quotienting equivalent variables exposes a family or component before extending
the policy to every archived alternative. It will not by itself explain the
remaining larger 3-CNF misses. Occurrence-driven scans and shared rewrite chains
remain supporting cost work.

## Validation and reproduction

All 326 Python tests pass, including exhaustive small fibers, multiple common
literals, trace reuse, mixtures, signed/source edits, omitted/forged witnesses,
model transport, cold corruption and old-policy coexistence. All three new
complete archives and four preceding archives replay byte-identically without
new solver expansion. The Lean build/audit passes at 4,091 declarations and
1,950 theorem declarations. Full source inputs, metrics, digests, failed
alternatives and regressions are retained in `report.json`; `mechanisms.json`
and `gap-profile.json` distinguish archived opportunities from selected paths.

Run from the repository root with a new destination:

```sh
python3 experiments/compare_cnf_common_consequence.py --output /tmp/new-common-study
python3 experiments/analyze_cnf_common_consequence.py /tmp/new-common-study
python3 experiments/profile_cnf_common_gaps.py /tmp/new-common-study
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
