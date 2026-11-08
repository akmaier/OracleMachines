# Explicit affine extraction with exact leftover clauses

Checkpoint: 8 November 2026. This extends the previous pattern inventory with
a versioned optional analysis policy, not a new SAT decision engine. All five
modes still run the same ordinary solver on every source. Labels never select
a recognition method.

## Exact representation and checked recognition

Normalized clauses are grouped by their variable support and the parity of the
assignment they forbid. A group containing all 2^(q-1) distinct sign patterns
of one parity represents one XOR equation on those q variables. Both complete
halves give contradictory equations. An empty clause is the equation 0=1.
Counting present clauses suffices; discovery does not enumerate missing signs
or allocate a truth table. The new extractor has no eight-variable cap.

Every source clause ID occurs exactly once in an extracted equation or the
unchanged leftover list. Thus F(x) = (A x = b) AND R(x), pointwise for every
assignment, including shared variables. A separate checker validates supports,
signs, distinctness, counts and exact coverage without trusting the grouping
routine. The elimination certificate lists XOR operations against previous
reduced rows. Checking this triangular transformation preserves exactly the
equation solutions. A zero row with right-hand side one certifies a contradictory
subsystem, even when R is nonempty. Otherwise an empty R identifies a directly
encoded affine system. Consistent equations with nonempty R are **not** declared
tractable on this basis.

Two additional outcomes retain these distinct facts: `explicit_affine` means the
deterministic extraction leaves no clauses; `affine_conflict` means the extracted
system is inconsistent. Exclusion is relative to this explicit encoding/policy,
not all semantically equivalent affine descriptions. Old seven-outcome policies,
keys and rows are unchanged. New identities include `explicit-affine-v1`.
The Python extraction, checker and SQLite implementation are outside Lean's
existing refinement boundary.

## Matched coverage and costs

The 733 sources contain all 664 earlier inputs, three larger full cubes, four
growing overlapping-equation systems and four coupled variants, 48 fresh seeded
CNFs, and five edits with renamed/redundant variants. All small sources and
attempted decomposition alternatives are checked pointwise. SAT answers agree
across modes; larger SAT witnesses are checked against their full input.

| Policy | Closed beyond 512 tiny sources | Total analysis + solving (s) | SQLite bytes | Cold full audit (s) |
| --- | ---: | ---: | ---: | ---: |
| Solver alone | Not an inventory | 0.73642 | 2,322,432 | 0.11791 |
| Prior component policy, depth 0 | 65/221 | 1.45168 | 5,152,768 | 0.22990 |
| Affine extension, depth 0 | 88/221 | 1.24652 | 5,644,288 | 0.27341 |
| Prior policy, depth 2 | 145/221 | 3.30542 | 14,323,712 | 0.87050 |
| Affine extension, depth 2 | 171/221 | 2.90083 | 13,385,728 | 0.74019 |

These are single sequential timing samples, not significance estimates. In
particular, the depth-zero timing difference does not establish that extra
recognition is intrinsically faster. Each operation charges discovery, checking,
serialization, persistence and ordinary solving. Generation, truth tables,
inter-operation audit walks and offline compression are excluded. Initialization,
warm inventory reuse and cold full checking are reported separately in JSON.

On the original 152 non-tiny sources, depth-two closure rises from 102 to 116:
14 of the previous 50 unresolved inputs close. There are now 34 unresolved seeded
CNFs plus coupled matching/parity and its variant. The eight random gains arise
from contradictory unit/binary affine subsystems exposed by conditioning, not
discovery of large hidden parity systems. The 48 new seeded sources gain five
closures, also from equations of width at most two; ten remain unresolved.
No random source gains whole-input closure at depth zero. The full reasons and
remaining interfaces are saved in `mechanisms.json`.

Across the original 664 inputs, total time is nearly unchanged: 1.84691 versus
1.84100 seconds. Pattern nodes fall from 2,801 to 2,432, while new certificates
add checking and metadata. Across all 733 sources, depth-two pattern nodes fall
from 3,790 to 3,126. The growing controls explain much of the aggregate saving:
the twelve-variable full cube falls from 0.39176 to 0.17832 seconds, and the
32-equation overlapping system from 0.10898 to 0.05937 seconds. Full source CNF
and provenance remain stored; compact equations do not imply equally compact
total archives.

There are retained regressions. At depth zero, SQLite grows by 491,520 bytes.
At depth two, the 16-equation coupled control rises from 0.05067 to 0.07849 seconds
without closing; the 32-equation coupled control rises from 0.11845 to 0.12831.
The old coupled matching/parity source rises from 0.01691 to 0.02046 seconds and
still has 22 unresolved selected literal occurrences. Conditioning still uses
occurrence frequency and does not prioritize the affine/coupling interface.

Separate tracing on the same six earlier mixed/guarded cases gives depth-two
peak Python allocations of 205,370 versus 147,579 bytes. At depth zero the peak
increases from 116,883 to 133,517 bytes. This excludes native SQLite memory and
process RSS and is not a full-corpus peak. Warm inventory replay takes 54.73
versus 56.38 ms at depth two. Cold audit checks all nodes, including unsuccessful
alternatives, all sources and all solver certificates without new solving or
byte changes. All five previous final archives also pass unchanged.

## Bounds, limitations and the next target

For normalized input with L literal occurrences, m clauses and n variables,
grouping scans L occurrences and sorts supports and group keys. Conservative
comparison work is O(L log(L+1) + m log(m+1)); hashing and integer bit costs are
additional. With e extracted equations, elimination uses at most
e min(e,n) XOR operations on n-bit rows; checking has the same envelope.
Source clause references take O(m) integer entries, and stored reductions take
O(en) bits plus O(e min(e,n)) dependency indices. Preparation of each row from
its support also costs bit operations. These are per-profile costs, not a bound
on the potentially exponential number of residuals in general SAT.

Recognition of a direct q-variable equation reads q*2^(q-1) input occurrences.
Its semantic description can use q variables and one parity bit, while this
audited prototype also retains the source and certificate. It does not discover
all hidden affine equivalents, project away internal variables, update equation
systems incrementally, or integrate the representation into solving/history
repair. Existing general solving remains potentially exponential.

**Next target: exact projection onto the affine/coupling interface.** Each
growing coupled control has one leftover binary clause and just two shared
variables, although the 32-equation case has 66 variables. Preserve the affine
relation feasible on that interface, then compose it with R or condition the
interface first. This would address the failure that frequency-based splitting
misses. The result must retain exact existential semantics, a checked lifting
of satisfying assignments and refutations, and full discovery/projection cost.
Arbitrary leftover CNF remains hard in general. The matching/parity mixture and
all unresolved random inputs must remain in the comparison.

## Reproduction and verification

```
python3 -m unittest solver.test_cnf_affine_patterns solver.test_cnf_pattern_inventory -q
python3 experiments/compare_cnf_affine_patterns.py --output /tmp/new-affine-pattern-run
python3 experiments/analyze_cnf_affine_patterns.py /tmp/new-affine-pattern-run
```

The full Python suite passes 284 tests. New tests include all 512 two-variable
clause subsets, all 256 subsets of full-width three-variable clauses, random
mixtures, arbitrary renamings, class-changing edits, incomplete/forged extraction,
false elimination dependencies, cold corruption, and coexistence with old rows.
The five gzip SQLite files preserve exact evidence; `report.json` includes full
inputs, per-operation metrics, source fingerprints and archive hashes.
