# Bounded active knowledge with complete proof retention

The previous selective-reuse policy activated every surviving learned clause.
This experiment caps the imported active set while keeping all surviving proof
evidence. It addresses the measured propagation cost of thousands of valid
clauses, rather than changing the checker or claiming a new tractable SAT class.
Production defaults remain unchanged.

## Exactness and scope

The fixed policy admits at most 128 distinct learned clauses not already present
in the target. Smaller literal width ranks first; newer retained records break
ties. Duplicate claims use their newest record. Selection uses proof syntax and
was frozen before these matched trial outcomes; the inputs were already exposed.
It does not consult target labels or truth results.

Every selected clause is implied by the target. Any subset, including none,
therefore preserves exactly the target's model set when conjoined with it.
Inactive clauses remain in the certificate and can support the derivations of
active ones. New expansion proofs substitute checked derivations for imported
premises and use the unchanged target checker. SAT needs a full target model,
UNSAT a checked empty clause; a capped result remains unknown. Overlapping
exclusions remain valid constraints, not disjoint recognized families.

Both policies use the same target-only initial proposal and unchanged learner
with 2,000 entered contexts. Admission changes propagation, activity and branching.
The 128 limit applies only to imported clauses; newly learned clauses remain
unbounded except indirectly by the search budget. It does not bound total proof
size or eliminate source-dependent preprocessing. This is not a watched-literal
implementation or proof-pruning experiment.

The matched panel is the same sixteen exposed edits of eight previously refuted
parents. The other sixteen edits of SAT parents receive admission checks but
remain outside this search comparison. Prior sources, reference outcomes and
all earlier knowledge are preserved. No fresh external transfer is claimed.
A historical coverage union preserves earlier answers; it is not a measured
combined dispatch policy.

## Measurements

Full admission certifies **3/16** targets; the 128-clause policy
certifies **1/16**. It adds 0 checked answers and loses
2 baseline answers within the cap. The preserved historical union is
**3/16**, with **13 unresolved**. All sixteen targets have earlier
trusted reference-UNSAT outcomes, kept separate from project-certified coverage.
New gains: none. Lost baseline answers:
s021, s031. These individual cases remain in the record.

| Quantity | All surviving clauses active | At most 128 imports |
| --- | ---: | ---: |
| Initial imported clauses across 16 targets | 59,480 | 2,048 |
| Entered contexts | 30,395 | 31,224 |
| Assignment occurrence updates | 319,681,345 | 43,207,707 |
| Mean complete seconds | 172.53374 | 60.19492 |
| Mean acquisition including internal checks, seconds | 150.20742 | 38.04885 |
| Mean explicit checking, seconds | 3.67809 | 3.71559 |
| Mean warm reload/check, seconds | 4.43460 | 4.25510 |
| Mean two cold reload/checks, seconds | 8.44631 | 8.56907 |
| Mean writes, seconds | 0.33188 | 0.33501 |
| Mean three compressions, seconds | 5.39486 | 5.23202 |
| Proof JSON bytes | 110,545,079 | 111,384,453 |
| Combined gzip bytes | 4,114,583 | 4,080,695 |
| Maximum observed process RSS bytes | 468,467,712 | 463,896,576 |

Mean complete cost changes **-65.11%**; paired changes are
-65.15% and -65.07%. Search choices and outcomes can change,
so this is not an equal-search representation comparison. The complete prior
proof prefix remains identical in both modes; final size differences come from
new expansion records. The active cap is not a proof-size cap.


Two alternating pairs run in fresh processes. Target input/hash reads, parent
reads and proof checks, selective transport, ranking, augmentation, search,
substitution, checking, writes, three compressions, warm reload/check and two cold
reload/checks are charged. Historical parent acquisition is additional; imports,
startup, reports and independent audits are additional. Operating-system caches
are not flushed. The two rounds labelled cold in the counters deserialize fresh
objects in the same worker after its warm round; these are not independent
cold-start process measurements. A separate fresh Python worker for each policy
reproduces every target answer and checker counter with search, expansion and
parent transport disabled; this correctness check is outside benchmark costs.
The complete retained proof prefix survives every output,
including inactive knowledge and budget-exhausted cases.

## What the lost answers reveal

A post-hoc trace of the full-admission refutations counts distinct retained
clauses used directly by reachable new derivations. The two lost cases `s021`
and `s031` use 630 and 292 such clauses; the short-clause policy admits only
122 and 95 of them, omitting 508 and 197. This describes the earlier proof
routes, not clauses necessary in every possible refutation. In particular,
`s023` still succeeds while admitting only 112 of the 578 clauses on its
baseline route. A changed search can find another proof. The next useful
comparison is selective activation informed by proof use or cheaper propagation
with broader admission, with ranking frozen before new trials. This result
does not justify increasing the budget until the exposed answers return.

## Verification and remaining gaps

All **2,659 full and 19 focused tests pass**. The reproduced audit covers 13,624
edited small targets from all two-variable clause sets, bounded three-variable
sets and 128 fresh sparse signed mixtures. Admission budgets 0, 1 and 128 receive
**40,872 independent ranking checks, full model-set equalities and composed-answer
checks**, yielding 32,853 SAT and 8,019 UNSAT outcomes. Every certificate retains
the full old proof prefix. At zero expansion budget, 11,285 cases remain unknown;
2,339 retain already checked refutations. These are cumulative checks, not
independent samples.

Focused tests exercise corrupted inactive evidence, duplicates, target clause
exclusion, recency ties, zero budgets, the 128-clause cap, proof substitution,
source edits and search-independent checking. Four initial test fixtures used
unremapped indices after target edits and were correctly rejected. That failure
log is preserved; fixtures now use checked transport, with an explicit regression
for the rejected usage. Existing SQLite ResourceWarnings are retained.

Validation preserves **251 manifests, 84,515 artifact entries, 1,367 scientific
sources and all 90 prior manuscript proofs**. Five scientific sources and one
proof are added. Resume `experiments/results/cnf-admitted-learning/checkpoint.json`,
key `admitted_learning`. Earlier coverage unions and unknowns remain intact.

Remaining obligations include fresh frozen external transfer; economical active
admission and propagation; proof retention costs; alternative derivations for
consequences whose recorded supports vanished; and general recognition,
preprocessing and unrestricted expansion. Small active sets do not imply small
proof support or efficient coverage of every CNF.
