# Selective learned knowledge after source edits

The previous transport rejected the whole collection when any referenced source
clause disappeared. The new filter keeps independently valid resolution records,
drops their invalid descendants, and composes retained knowledge with fresh
search while producing a certificate checked against the edited target alone.
This is an experimental reuse extension; production defaults remain unchanged.

## Recognition and exact composition

The old proof is checked before any filtering, including records that will be
discarded. Canonical original clauses are mapped to identical target clauses or
marked absent. A derived record survives when its starting clause and every
recorded resolution parent survive. Induction through the acyclic proof graph
shows that this is exactly survival of all recorded original-premise paths.
Runtime uses a mapping and absence flags; the independent audit constructs
explicit transitive premise sets instead.

This is exact recognition of syntactic proof survival, not recognition of every
semantic consequence. A discarded clause may have an alternative valid proof.
Filtering and substitution are polynomial in the supplied source and proof
lengths; that does not bound acquisition or proof size by the target input alone.
Surviving exclusions may overlap, but their conjunction with the target preserves
exactly its models. A checked empty clause grants UNSAT; otherwise transported
knowledge remains unknown. No old SAT answer is inherited.

Expansion runs the unchanged learner on the target plus surviving clauses, with
the same target-only initial proposal as fresh search. Original augmented-clause
references are replaced by target clauses or earlier retained derivations; new
resolution steps are remapped in order. The resulting certificate uses the
unchanged checker. SAT needs a complete target model, UNSAT a checked empty
clause, and budget exhaustion remains unknown. Replay needs only the edited
target and final certificate, not the parent proof or transport algorithm.

## Controlled edits and measurement

Every exposed parent loses the original clause that starts its first retained
derivation. A second target additionally receives a binary bridge through an
existing variable and a fresh negative unit. The selection rule and code hashes
were frozen before target outcomes. This intentionally attacks a required guard;
it is not a representative or external holdout. Thirty-two targets come from
sixteen already exposed parents. Transport is audited on all targets; matched
expansion uses the sixteen edits of eight previously refuted parents, avoiding
trivial reuse of old SAT models after pure deletion.

Both expansion policies have a 2,000-context budget. They use the unchanged
learner, but retained constraints alter its propagation and activity, and work
per context differs. Two alternating pairs run in fresh processes. Historical
parent learning is a separately recorded sunk cost. Input/hash reads, candidate
parent proof reads and checks, filtering, target checks, augmentation, expansion,
proof composition, writes, three compressions, warm replay and two cold replays
are charged. Imports/startup, reports and independent audits are additional.
Operating-system caches are not flushed. No end-to-end amortization claim is
made. Full surviving knowledge remains persisted even for SAT and unknown results.

The whole-collection guard rejects all **32/32 targets**. Selective transport
retains nonempty knowledge on **32/32**, keeping **89,746 of
102,954 derivation occurrences (87.17%)** across the two edits per
parent. These occurrences are not distinct clauses or independent samples.
Each target retains between 403 and 6,406 records.
All 32 transported results remain unknown; no old refutation survives intact.

On the **16 expansion targets**, fresh search certifies **0/16**
and reuse certifies **3/16**, all UNSAT, leaving thirteen unknown. There are
3 new answers and 0 lost answers; the union leaves
**13 unresolved**, all reference-UNSAT (not yet project-certified).
The three new refutations actually depend on 1,400, 1,600 and 3,037 retained
derivations, respectively. All 32 targets remain connected in the variable
incidence graph; no bounded interaction-width certificate is claimed.
Reference results over all 32 targets are
16 source-checked SAT models and 16 trusted UNSAT verdicts; reference verdicts
are kept distinct from project certificates.

| Measured expansion quantity | Fresh target search | Selective reuse |
| --- | ---: | ---: |
| Entered contexts | 32,000 | 30,395 |
| Mean complete seconds | 25.37461 | 173.46278 |
| Mean acquisition including internal checks, seconds | 21.01470 | 150.84327 |
| Mean explicit checking, seconds | 0.71316 | 3.73680 |
| Mean warm reload/check, seconds | 0.84674 | 4.45722 |
| Mean two cold reload/checks, seconds | 1.64005 | 8.64779 |
| Mean writes, seconds | 0.06956 | 0.34262 |
| Mean three compressions, seconds | 1.05286 | 5.39648 |
| Proof JSON bytes | 21,961,855 | 110,545,079 |
| Combined gzip bytes | 805,149 | 4,114,583 |
| Maximum observed process RSS bytes | 95,682,560 | 371,867,648 |

Mean complete cost changes **+583.61%**; paired changes
are +595.34% and +572.43%. This is a
coverage gain with greater charged cost, not a speedup. Retaining all available
knowledge enlarges both propagation and proof replay. Historical parent discovery
is additional; these measurements cannot establish a total-cost saving.


## Verification and open gaps

All **2,640 full and 22 focused tests pass**. The reproduced small-case audit
checks **13,624 edited targets**, with 10,955 SAT and 2,669 UNSAT composed answers.
It covers all 512 two-variable clause sets with every canonical-clause deletion,
3,304 three-variable clause sets of at most three clauses with a fixed deletion,
and 128 fresh sparse signed mixtures. Additions and empty targets are included.
Explicit transitive premise unions independently validate survival. The audit
performs 1,270 learned-clause semantic checks with 1,715 satisfying extensions;
these are cumulative checks, not distinct models. Zero-budget expansion retains
2,329 refutations and leaves 11,295 cases unknown.

Tests cover independent proof branches, transitive invalidation, old-proof
corruption even in discarded records, proof-index changes, empty targets,
new variables, shared-variable mixtures, duplicates, tautologies, partial budgets,
proof substitution and checking with search disabled. Historical SQLite
ResourceWarnings remain in the full-suite log.

Validation preserves **250 prior manifests, 84,291 artifact entries, 1,362
scientific sources and all 89 preceding manuscript proofs**. Five new scientific
files and one proof are added. Old panels, prior failed probes, counterexamples
and cumulative tables remain intact. Resume
`experiments/results/cnf-selective-learning/checkpoint.json`, key
`selective_learning`.

Largest remaining gaps: fresh frozen external transfer; alternative proofs for
consequences discarded because their recorded support disappeared; economical
selection of surviving knowledge; growing active propagation indexes; and compact
source guards. Recognition, source-dependent preprocessing, retained evidence and
unrestricted expansion remain charged obligations. Finite coverage is not an
efficient classification of arbitrary CNF or a polynomial SAT algorithm.
