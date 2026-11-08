# Reusing a refutation or one surviving model across clause additions

This comparison extends the prepared-state interface in
`experiments/cnf_positive_history.py` with `append_decision`. It keeps the
previous `append` operation unchanged. All **3,894 decisions** over 22 histories
are correct; all 66 compressed result archives are retained. All **313 earlier
candidate archives** replay with unchanged row digests and no new expansions.
The production solver and its archive are not modified.

## Two reuse conditions

- A checked UNSAT base remains UNSAT after any well-formed clause addition,
  including signed, empty, novel and tautological clauses. No subset discovery
  or model evaluation is needed.
- A checked SAT base supplies a fixed total assignment: the sparse stored model,
  with all omitted variables false. If that same assignment satisfies the new
  clause, it still satisfies the whole history. This preserves one model and
  the SAT answer; it does not preserve every base model. Failure supplies no
  verdict and writes no version. Fresh solving can still find another model.

New `append-unsat` and `append-model` records contain the exact added clause and
SQL parent/base references, without a subset witness. Cold replay independently
checks the base certificate, the complete parent chain and the applicable rule
for every record. Old positive-subset records can occur in the same history;
the fixed base model satisfies them too. The same append-only, single-writer,
archive-local identity and in-session immutability assumptions apply. Removing
or replacing clauses requires a newly acquired base.

These are elementary semantic reuse rules, already reflected in the project's
witness/refutation work. The contribution here is avoiding full-source and
positive-containment work in this separate CNF history interface. No new
tractable class or polynomial arbitrary-SAT constructor is claimed.

## Matched runtime and retained storage

`full_source` receives each complete CNF through the unchanged residual solver.
`positive_history` uses the previous positive-subset append interface and
explicitly reconstructs/solves a fresh base when it cannot represent an addition.
`decision_history` uses the new rules and the same fallback. The two history
modes share the same verdict and optional witness-export contract.

Sizes 4, 8 and 16 use matching bases, with 8/32/128 additions each. SAT additions
contain a fresh negative literal, so the stored default-false assignment still
works even though the clause is not implied by the base. UNSAT additions cycle
through a fresh positive unit, negative unit, tautology and empty clause. The
empty clause makes the old normalized residual trivially UNSAT after step four;
that favorable control for the old solver is deliberately retained. Four other
histories cover repeated events, incompatible fresh units, an actual SAT-to-UNSAT
transition, and a model failure that remains SAT.

| History (128 additions) | Full source logical bytes / seconds | Positive history logical bytes / seconds | Decision history logical bytes / seconds |
| --- | ---: | ---: | ---: |
| UNSAT, size 4 | 3,938 / 0.01113 | 149,566 / 0.13573 | 9,506 / 0.03821 |
| UNSAT, size 16 | 203,805 / 0.23594 | 3,670,847 / 0.71682 | 109,468 / 0.05710 |
| SAT, size 4 | 402,292 / 0.16191 | 650,390 / 0.27330 | 9,310 / 0.03358 |
| SAT, size 16 | 9,235,556 / 2.78069 | 15,195,873 / 3.61103 | 99,170 / 0.04691 |

Seconds sum base acquisition and all additions, including rejected attempts,
materialization and new-base solving. Database initialization is recorded
separately. These are single sequential samples, not statistically established
speedup factors or competitive CDCL measurements. The run began after the test
suite and Lean audit finished.

For size-16 SAT, the new mode retains one base instead of 129, reducing logical
payload by about 153 times versus the previous history interface and operation
time by about 77 times. Physical SQLite size falls from 26,513,408 to 200,704
bytes; the full-source file is 14,286,848 bytes. The last two-literal append
performs four syntax-validation literal visits and two model-literal probes
(discovery plus independent record check), serializes 47 JSON bytes plus SQL
references, inserts one version and does no residual-solver work. Its measured
operation takes 0.237 ms versus 37.395 ms for the positive-history fallback.

At size-16 UNSAT, the new mode retains 109,468 logical bytes and a 221,184-byte
SQLite file, versus 3,670,847 and 7,708,672 for positive history. Every appended
clause avoids containment and model probes; syntax and persistence still cost
work. Across all modes, snapshots occupy 83,165,184 raw SQLite bytes and
5,970,913 gzip bytes. Gzip is an offline archival operation, not online storage.

## Costs that remain, and preserved losses

Let B0 and K0 be the base-source and acquired-certificate bit lengths. For T
accepted additions of bit lengths D_t, fixed-base history payload remains
O(B0 + K0 + sum D_t + T log(N+T+1)) bits, where N bounds preceding IDs/record
counts. Parent/base references grow; SQL page/index overhead and resident Python
objects are additional. The base source and model are shared instead of copied
per version. These are payload and file-size results, **not peak-RSS results**.

A warm append reads the complete clause for syntax validation. SAT additionally
uses at most twice its literal count in model probes, across admission and record
checking. UNSAT uses no model probes. Serializing exact input charges its bit
length; dictionary, big-integer and SQL operations are not asserted constant.
No full-base scan or subset-candidate factor remains on the warm accepted path.
Base acquisition, its currently eager positive index, and proof validation remain
charged. Cold loading validates all needed ancestors; it is not a constant-cost
verdict lookup after restart. Full-source reconstruction and witness exports are
recorded separately and checked against the exact input recipe.

| Control | Full-source logical bytes / seconds | Positive-history logical bytes / seconds | Decision-history logical bytes / seconds |
| --- | ---: | ---: | ---: |
| Same signed clause repeated 128 times | 1,396 / 0.01329 | 159,865 / 0.10679 | 8,926 / 0.03256 |
| 32 fresh positive units | 30,657 / 0.01755 | 58,812 / 0.03892 | 58,812 / 0.03815 |
| SAT to UNSAT, then 31 additions | 9,202 / 0.01060 | 20,145 / 0.02905 | 2,366 / 0.00912 |
| SAT with one necessary model change | 12,235 / 0.01097 | 24,326 / 0.02925 | 2,383 / 0.00988 |

Repeated events are still retained exactly; full-source normalization deduplicates
them. Fresh positive units fail the default-false assignment and force 32 fresh
bases in both history modes. In each transition control the new mode falls back
once, then shares the newly acquired base; the preceding mode falls back 32 times.

Size-16 UNSAT cold query takes 10.13 ms for decision history, 5.94 ms for positive
history's final isolated fresh base, and 1.57 ms for the full-source cache with
its normalized empty clause. Size-16 SAT cold times are 8.19, 8.18 and 13.80 ms.
Cold opening times are separate in the report. Warm expansion gains therefore
do not imply proportional restart gains.

The full-source API retains its per-query archive-size scan and model output;
history modes make final statistics and witness export optional and separately
timed. Input recipe assembly, offline gzip, digest checks and compatibility
auditing are outside operation timings. Python and SQLite remain outside Lean's
acceptance boundary. General acquisition, model repair and successful-transfer
frequency have no polynomial guarantee here.

## Verification and reproduction

All **235 Python tests** pass. New tests enumerate 320 base/clause combinations,
check truth-table answers, reject a failed model without calling it UNSAT, show
that accepted additions can shrink the model set, preserve sparse/default-false
assignments, mix legacy/new records, and reject forged rules, cross-base parents
and invalid literal tails. A 1,200-step arbitrary UNSAT history replays iteratively
without changing its rows. Earlier tests remain intact.

Lean checks four semantic lemmas in `Residuals.lean`: `unsatisfiable_conj_extension`,
`fixed_model_history`, `satisfiable_fixed_model_history`, and `unsatisfiable_history`.
The audit passes **4,071 declarations / 1,933 theorem declarations** with only the
standard allowed axioms. It does not verify the parser, Python checker, SQL
protocol, compiled runtime or cost bounds.

```sh
python3 -m unittest discover -s solver -v
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
python3 experiments/compare_cnf_decision_history.py --output /tmp/oracle-decision-history-new-run
```

Use a new directory. `report.json` contains fingerprints, exact source recipes,
per-operation counters, final archive-local handles and all replay results.
`archive-replay.json` independently reopens every compressed new archive, checks
the source and final answer/witness, and records unchanged row digests. Old
artifacts are left untouched. `tests.log` and `lean.log` preserve the checks.

Next opportunities are shared source structure across fresh bases, small checked
model repairs (especially genuinely fresh variables), repeated-event compression,
and cheaper cold validation. A model repair must respect every prior constraint;
changing a default value without checking its occurrences would be unsound.
