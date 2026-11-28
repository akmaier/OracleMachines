# Expansion budgets and the marginal value of retained clauses

The faster watched-propagation implementation preserved three checked answers
but left thirteen edited targets at the 2,000-context cap. This experiment asks
whether a fixed larger allowance expands certified coverage, and whether retained
knowledge helps compared with the same watched engine starting fresh.

## Frozen policies and exact composition

Before the runs, `protocol.json` freezes all scientific sources, unchanged panel
bindings, target-only proposal policy, the 2,000/8,000 caps, and two reversed run
orders. All sixteen edits of eight already refuted parents are included; the
other sixteen edits of SAT parents remain separate. No reference label enters
discovery. This is development on exposed inputs, not unseen external transfer.

Reuse reads and checks the original parent proof, retains derivations whose
recorded source-premise paths survive the edit, and activates all surviving
clauses. Search runs on the equivalent augmented CNF. Substituting each learned
premise back into its retained derivation yields a certificate checked against
the target alone. SAT requires a complete target model; UNSAT requires an empty
clause. Unknown retains consequences without asserting a decision. Existing
proofs justify these operations; this checkpoint adds no new tractability theorem.

Every trial starts from empty search state. The 8,000-context run does not resume
the measured 2,000-context run, and its cost is not a suffix cost. Source, seed,
decision order and active-clause policy stay fixed within a reuse pair. Direct
validation checks that every small-budget derivation is a prefix of the larger
proof and every completed small answer survives. Context caps count iterations,
not equal amounts of work, time or memory. Production defaults remain unchanged.

## Coverage and cost

| Quantity | Reuse, 2,000 | Fresh, 8,000 | Reuse, 8,000 |
| --- | ---: | ---: | ---: |
| Checked answers / 16 | 3 | 9 | 16 |
| Entered contexts | 30,395 | 96,697 | 50,713 |
| Mean complete seconds | 71.89307 | 68.52685 | 110.25145 |
| Acquisition including checks, seconds | 49.72763 | 54.73619 | 84.39776 |
| Explicit checks, seconds | 3.68775 | 2.31896 | 4.29532 |
| Warm reload/check, seconds | 4.19454 | 2.66518 | 4.90081 |
| Two reload/check rounds, seconds | 8.60082 | 5.24295 | 9.94906 |
| Writes, seconds | 0.33664 | 0.21310 | 0.38054 |
| Three compressions, seconds | 5.30534 | 3.30862 | 6.28907 |
| Proof JSON bytes | 110,545,079 | 69,378,039 | 125,646,317 |
| Combined gzip bytes | 4,114,583 | 2,493,833 | 4,734,568 |
| Maximum observed RSS bytes | 465,846,272 | 263,913,472 | 487,063,552 |


Additional answers from the larger reuse budget: **s004, s005, s006, s007, s012, s013, s014, s015, s020, s022, s028, s029, s030**.
At 8,000 contexts, reuse-only answers: **s006, s012, s014, s015, s028, s029, s030**; fresh-only answers:
**none**. The historical union covers **16/16** and leaves
**0 unresolved**. Individual outcomes, exact certificates, retained
knowledge and diagnostics remain in `analysis.json`, `coverage-union.json` and
`remaining.json`. Overlap is reported explicitly; the union has no combined runtime.

Larger reuse changes mean complete cost by **+53.35%**
relative to small reuse (paired changes +55.76% and
+51.03%). Against equal-cap fresh search the change
is **+60.89%** (paired changes
+60.61% and +61.17%).
These policies can enter different contexts and return different sets of answers;
the ratios are workflow-cost comparisons, not equal-answer speedup guarantees.

A separately charged post-hoc census checks all final proofs and traverses the
ancestors of their empty clauses. Every target is connected and has 125–151
variables. Larger-reuse refutations reach 43,740 of 59,480
imported derivation occurrences, ranging from 1,322 to
5,057 per target. Their recorded original-premise supports cover
98.14–100.00% of canonical source clauses and every source
variable. These counts include proof ancestors: they are not minimum supports,
minimum active sets, or bounds against smaller alternative decompositions.
The full records remain in `support-census.json`; they did not guide the runs.

Complete cost includes source reads/hashing, required parent reads/checks,
transport, proposal preparation, augmentation, search, substitution, checks,
writes, three compressions and replay. Original acquisition and historical
append-only storage remain additional; imports/startup, report encoding and
independent audits are excluded. Maximum RSS is an observed process peak.
Retaining all evidence can grow proof storage and checking even when search
benefits. No end-to-end acquisition amortization is inferred.

The two rounds labelled cold in inherited report fields reread sources and parse
fresh proof objects in the same worker after a warm round. They are not independent
cold-start processes, and OS caches are not flushed. A separate new worker per
policy reproduces target-only answers and checking counters with all search,
expansion and transport disabled; this is additional correctness validation.

## Validation and remaining gaps

All 2,689 full and ten focused tests pass. The independently repeated truth audit
covers 512 two-variable clause sets, 3,304 three-variable clause sets of at most
three clauses and 128 signed sparse mixtures with duplicates and tautologies.
Deletion and shared-variable-addition edits give 7,888 targets. Fresh/reuse at
caps 0, 2 and 8,000 gives 47,328 checked outcomes: 23,240 SAT, 8,918 UNSAT and
15,170 unknown. Independent truth verifies 8,228 consequence occurrences;
31,552 budget-prefix and 23,664 retained-prefix checks pass. These repeated
policies, budgets and edits are not independent problem samples.

The first audit reproduction completed its assertions but failed to write to a
missing output directory. The error log is retained. Creating the directory and
rerunning reproduced the complete audit; frozen scientific sources were unchanged.
All six measured workflows and their operation counters are reproduced, including
exact agreement of the small-budget control with the previous checkpoint.
Lineage validation preserves 253 prior manifests, 84,766 artifact entries, 1,377
scientific sources and all 92 previous proof blocks. Four scientific files are
added; the earlier three published snapshots and their manifests remain unchanged.

The next steps are frozen external transfer and explanation of the seven
fresh-search misses, including alternative supports after deleted premises
and cheaper proof retention. General recognition, preprocessing, compact reusable
interaction descriptions and unrestricted expansion remain open. Raising a fixed
cap and completing finite cases does not establish an efficient class covering
arbitrary CNFs.
