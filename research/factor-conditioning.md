# Conditioning checked factor covers and restoring original roots

Checkpoint: 27 November 2026. Conditioning small sets of variables in the saved
factor frontiers supplies original-source SAT witnesses for **both remaining
roots**. Together with 180 independently rechecked retained authorities, the
certificate union now covers **182/182 queries on the existing synthetic panel**.
This closes a finite-panel gap, not arbitrary SAT or a new external distribution.
One of the three internal frontiers remains unresolved beneath an already-SAT
root.

The gain spends more work. The new incremental stage costs **1.39737 s**, versus
**0.59316 s** for width-ten continuation and **0.61057 s** for unconditioned exact
covers: **135.58% and 128.87% more**, respectively. All eight paired signs are
unfavorable. These matched stages include old-context validation and full root
transport; they cannot be compared directly with the previous smaller stage
that stopped at frontier verdicts. Production defaults remain unchanged.

## One reusable description, an exact Boolean partition

`cnf_factor_conditioning.py` first independently checks the saved source-bound
projection prefix and reconstructs its active factors. It discovers and checks
exact same-variable width-four CNF covers, requiring every active factor exactly
once. The shared clause list describes the conjunction of those factors.

A deterministic greedy rule selects at most four vertices of highest degree in
its primal graph, deleting each selected vertex before ranking the next. IDs
break ties; the heuristic is not invariant under all renamings. It consults no
family, source ID or truth label. It is a heuristic cutset selection, not a
certificate of minimum separator size or guaranteed graph disconnection.

For each assignment to the chosen variables, the certificate retains a semantic
bucket program for the corresponding clause cofactor. Every Boolean assignment
must appear exactly once, in a fixed order. An unfinished or unattempted branch
is explicitly unresolved. One SAT branch suffices for SAT; UNSAT requires checked
refutations of every branch. No work limit is interpreted as a refutation.
The checker accepts any valid bounded cutset without rerunning the ranking.

The old prefix and covers are stored once and shared by all branches. New
projections remain at width nine. The old prefix's reserved projection work is
deducted once from the original **262,144-unit allowance**, with all new branches
sharing what remains. It is not reset per branch. The separate cover search cap
is 65,536 candidate clauses/completions per frontier; normalization, restrictions,
ranking, support reduction, bit operations and verification are additional work.
The old prefix costs sum to 30,736 reserved probes across the three inputs;
new cut-four projection reservations sum to 318,206. These are work-accounting
units, not runtime or memory bounds.

The SAT witness is first restored through every earlier projection choice. A
separate adapter checks the original whole-root context and reconstructs the
exact target frontier from its pair-learning rounds and terminal reductions.
It lifts the model through those rounds, incoming relation/preprocessing edges,
conditioning parents and the original prefix, checking the final assignment
against the original root CNF. Only an actual full source witness upgrades a
root. A frontier UNSAT result alone is not promoted to a whole-root refutation.
No fresh solving or trusted truth label participates in this transport.

The identity behind the method is exact: a conjunction H is satisfiable iff
some cofactor H restricted to an assignment on S is satisfiable. Exact local
covers and existential projection prefixes preserve that equivalence. All
2^|S| assignments form a partition, but finding a small useful S and solving
its cofactors are separate obligations. This is not a polynomial procedure for
unrestricted SAT or an efficient universal partition into tractable classes.

## Coverage and unresolved branches

| Policy | First frontier | Second frontier | Third frontier | Newly closed roots |
| --- | --- | --- | --- | ---: |
| Original factors, width ten | unresolved | unresolved | unresolved | 0 |
| Exact covers, no conditioning | unresolved | unresolved | unresolved | 0 |
| Condition two variables | SAT | unresolved | unresolved | 1 |
| Condition four variables | SAT | SAT | unresolved | 2 |

The frontiers are `d-d-d-j06:1`, `d-d-k09:0` and `d-d-k09:3`, respectively.
The cut-four pivot lists in their own normalized coordinates are
`[15,25,14,24]`, `[7,19,1,21]` and `[27,6,31,12]`. All 48 branches are retained:
**six SAT, seventeen UNSAT and twenty-five unresolved**. Their three aggregate
reserved-work totals, including the old prefixes, are 24,018, 167,548 and 157,376;
they add 96, 181 and 98 projections. The third frontier's sixteen branches all
remain unresolved. The second frontier closes its original root through another
conditioning path, so this does not prevent a root SAT certificate.

The initial diagnostic screen is retained, including cut sizes zero through four.
Size two first closed the first frontier; size four first closed the second.
The chosen maximum is therefore **screen-guided exploratory work**, not a
held-out validation of a previously fixed policy. The screen also found that
size three decides all eight branches of the first frontier; larger cuts are
not monotonically cheaper or better. The final matched comparison uses fixed
sizes zero, two and four and attempts the same three inputs in every mode,
including the third even after its root has a witness.

## Charged incremental costs

Eight cyclic process orders use the same bounded verified-operator bank. Each
acquisition, warm pass and each of two cold passes starts with an empty bank.
Operating-system file caches are not flushed. Every replay loads the new JSON,
checks source/prefix/cover/branch bindings, validates the retained root context,
and transports and checks any root witness.

| Policy | Complete stage seconds | Warm | Two cold passes | New certificate bytes, compressed |
| --- | ---: | ---: | ---: | ---: |
| Width ten | 0.593162 | 0.142615 | 0.282858 | 730 |
| Cut zero | 0.610566 | 0.137842 | 0.276247 | 5,439 |
| Cut two | 0.897760 | 0.202715 | 0.394629 | 8,847 |
| Cut four | 1.397372 | 0.297694 | 0.590465 | 15,980 |

Cut four is **55.65% more costly than cut two**, which is **47.04% more costly
than cut zero**. All eight signs for these comparisons are unfavorable too.
Cut four projects 31,311 rows versus 2,048 for width ten and 768 for cut zero.
Its uncompressed new evidence is 403,656 bytes versus 2,262 for width ten.
Peak RSS is 56,426,496 bytes versus 55,803,904: no memory saving is established.

Cut-four acquisition/internal checking costs 0.352807 s, explicit checking/root
transport 0.141721 s, warm replay 0.297694 s and the two cold passes 0.590465 s.
Input/context loading, evidence writes and compression are also included. Earlier
root acquisition, process startup, final metadata and independent audits are
additional. This is **not a new full-pipeline comparison or a gain over fresh
solving**. The preceding full-pipeline study was still slower than fresh solving.
The existing native fallback already answered all 182 inputs; the change is that
all now have structural certificates in the retained union.

## Validation and preserved failures

All **2,431 full and 16 focused tests pass**. Existing unclosed-SQLite
ResourceWarnings are retained; no deadlines or assertions changed.
Sixteen focused tests cover exhaustive two-variable CNFs at multiple cut sizes,
seeded edits/mixtures, SAT and UNSAT composition, missing/duplicated assignments,
changed factors/source/model, shared-budget resets, exhausted and unavailable
covers, nonempty-prefix transport and original-root recomposition. Cold replay
runs with discovery and ranking disabled.

An independent semantic audit retains complete certificates for **632 inputs**:
all 512 two-variable CNFs, forty seeded cases, forty signed permutations and forty
edits or disjoint mixtures. It checks 2,486 branches, 18,230 direct cofactor
assignments and 481 earlier prefix steps; all answers match direct truth-table
labels (212 SAT, 420 UNSAT). Some prefixes are deliberately left unresolved after
a checked terminal, making this a semantic stress audit, not a coverage benchmark.
It does not estimate external or unrestricted coverage.

Two development failures are preserved. Initial root transport attempted to
concatenate a stored JSON clause list with a tuple of learned clauses; the type
conversion was corrected before the benchmark was frozen. The first lineage
validator compared serialized integer-key model dictionaries with string-key JSON
dictionaries as text, whose sorting order differs. It now compares parsed JSON
values; all timed code and evidence are unchanged. Failed logs and source snapshots
remain in the result directory. Neither failure is discarded or counted as a
successful verification.

All prior 239 manifests, 80,405 artifact entries, 1,308 scientific sources and 81
proof blocks remain unchanged. Four scientific sources and one composition proof
are added. Full-suite and manuscript verification are recorded in `checks.json`.
Resume `experiments/results/cnf-factor-conditioning/checkpoint.json`, key
`factor_conditioning`; `coverage-union.json` records each retained/new authority.

## Next gaps

1. **Generalization and economical cutset recognition.** This panel's coverage
   ceiling is reached. Freeze new inputs before tuning: broader graph structures,
   adversarial edits and genuinely external CNFs, with overlaps and unresolved
   cases explicit. Determine when a compact separator/cutset description predicts
   manageable cofactors. Four selected variables still leave twenty-five branches
   unresolved, and the third frontier is retained as a concrete stress case.
2. **Expansion cost.** Branch count grows exponentially with cutset size. Test
   selective or adaptive branching and avoid exploring additional paths after a
   checked root witness, while preserving every necessary UNSAT obligation and
   charging recognition and replay. There is no measured saving from such a policy
   yet; this experiment intentionally paid for all branches and frontiers.
3. **Verified preparation and transfer.** The prior full-pipeline profile still
   identifies repeated normalization/restriction. Exact validated source contexts
   could reduce replay overhead, but construction and invalidation must be charged.
   Broader nonconstant sharing across distinct structures remains weak; completing
   one fixed panel does not resolve it.
