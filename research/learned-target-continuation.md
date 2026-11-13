# Continuing acquired learned-clause targets

The [retained-implication study](saved-implication-learning.md) strengthened two
sources but left its three acquired targets open. This experiment follows their
selected unresolved leaves, starting with the smallest: 27, 35 and 39 variables.
It keeps the old selected plans, the external paired-trace rewrite and all 39
external learning records when recomposing the same 83 development originals.

## Bounded work and exact reuse

`cnf_target_probe.search` advances at most eight times per target. Each call
acquires at most one four-variable probe block, reuses a saved forced block or
records that the ranked candidate pool is exhausted. Clear blocks continue on
the same source; forced blocks follow the exact acquired child. At most four
distinct sources are visited, and one 32-state admission budget covers the whole
pass on a target. It is not reset after each successful reduction.

A failed assumption, checked by unit-propagation reasons, entails its opposite
literal. Restricting the full source to that literal and the checked closure
preserves satisfiability, and a satisfying child assignment lifts back to the
source. The existing checker binds the precise canonical target and variable
transport. The continuation rule changes scheduling, not this logical rule.
An absent child remains pending; a clear attempt supplies no closed route.
Finite original-level coverage still requires all premises of a checked route.
Independent reference solutions are retained separately from that coverage.

Checked clear prefixes are referenced rather than rediscovered. Probe records
are committed before acquiring their targets, so an admission limit preserves
both successful reasoning and incomplete target acquisition. Export checks that
all eight parent tables retain identical old rows, and reconstruction is
idempotent. Both external proof layers remain part of cold verification.

For K selected targets, step cap s and block width w, there are at most K*s new
blocks and 2*w*K*s direct assumption attempts. This experiment uses K=3, s=8,
w=4, hence at most 24 blocks and 192 such attempts. Target recognition can perform
additional probes and elimination, which are counted separately. State admissions
are at most 32 per target, including entered but unfinished states. Neither cap
bounds state size, the old history, reference search, or whole-process memory.
Frontier traversal, ranking, checked-prefix replay, composition and persistence
remain additional work. The ranked pool itself is capped at 64 variables.

Reused forced blocks consume steps too. This makes replay work explicit, but a
long enough retained chain can consume a later pass before it reaches new work.
Resumption is not a fairness or completeness theorem. A later policy may need
to start at the persisted deeper frontier while retaining its proof dependencies.
The current target ordering uses the smallest old selected leaf, not a proof of
minimum acquisition cost or an inventory of every alternative frontier.

## Persistent evidence

The checkpoint is `experiments/results/cnf-target-probe`. Its diagnostic archive
retains exact selected roots, every visit, every new probe identity and before/
after leaves. The report binds all artifacts, implementation fingerprints,
resource counters and the parent report. The standalone validator independently
reconstructs the lineage and checks the coverage plan, new probe membership,
admission accounting and separate source/target reference proofs without new
probe discovery. SAT model lifting is checked against each complete source.

`compare_cnf_target_probe.restore_checkpoint` accepts either the learned-clause
base or a chain of these new checkpoints. A new run uses `--parent` to continue
the latest saved pass. Existing fingerprinted files and all prior artifacts are
immutable. All three targeted tests and the full 569-test suite pass before the
timed run. Full measurements and the resulting priorities follow below.

This is an additive comparison with the parent's saved coverage, not a matched
comparison against spending the same extra probe budget on unaugmented targets.
Any coverage gain establishes a successful composed route; it does not by itself
isolate the marginal benefit of learned clauses from that of additional search.
The earlier same-variable controls establish the narrower propagation finding
reported in the parent study.

## Measured result, 13 November 2026

Coverage increases **45/83 -> 46/83**. Case **58** (`fresh3`, n48, original 1340)
closes, and the independent reference archive proves the original **UNSAT**.
Removing the growth-exception routes still covers all 46 originals. These
historical group names do not make the reused development cases independent
holdouts. The earlier 902/985 full prepared study is unchanged.

| Original case | Starting selected leaf | Outcome | New states | Direct probes |
| --- | --- | --- | ---: | ---: |
| 32 | 27 variables, 109 clauses | 23 variables, 97 clauses; still open | 7 | 58 |
| 58 | 35 variables, 144 clauses | Closed; original independently UNSAT | 3 | 5 |
| 31 | 39 variables, 160 clauses | Still open, same leaf | 0 | 42 |

The first target uses all eight advances, with a forced continuation at offset
12 on its starting leaf. Its smaller leaf then consumes all 13 remaining ranked
variables, including a final partial block. The recorded stop is `step_limit`,
but **no ranked candidate remains at that leaf**. Resuming the unchanged pass
would only replay the forced route and record exhaustion. The 39-variable leaf
also exhausts all 21 remaining candidates. Both leaves have minimum width two;
no target is pending and no admission cap binds. Exhaustion here concerns this
ranking and probe rule, not an UNSAT conclusion or the absence of stronger
learning, paired consequences or conditioning opportunities.

The run retains **15 new blocks: 13 clear and two forced**, comprising four
initial windows and 11 continuations. There are **105 direct assumption attempts**,
**87 additional target-recognition attempts**, and **258 saved-prefix attempt
references**. Reused prefix references count repeated references across calls,
not 258 distinct saved attempts or a measured net speedup. Independent source/
target checks prove one forced pair SAT and the other UNSAT; original-level
coverage and the new original UNSAT answer are checked separately.

| Phase | Seconds |
| --- | ---: |
| Restore parent history | 6.51509 |
| Prepare routes, baseline and selected targets | 65.96955 |
| Three bounded acquisition passes, including local checks/persistence | 0.11697 |
| Global recomposition and remaining-target diagnosis | 0.10449 |
| Additive export and compression | 5.14848 |
| Full cold inventory | 107.76294 |
| Cold routes, coverage and remaining-target diagnosis | 63.29837 |
| Independent reference solving / replay | 0.22976 / 0.08568 |
| Acquisition/validation pipeline before final report write | 256.68254 |
| Subsequent independent validator | 71.33144 |

The pipeline includes copying, serialization and reconstruction in addition to
the listed phases; tests and the subsequent validator are separate. Cold
verification remains much more expensive than the new local work. These costs
do not establish an end-to-end speedup over another SAT solver or a warm-runtime
reduction against a matched extra-search baseline.

The working SQLite history grows **327,680 bytes**, from 767,012,864 to
**767,340,544 bytes**. The additive delta occupies 397,312 SQLite bytes /
**18,000 compressed bytes**. Diagnostics add 165,194 JSON bytes / 11,348 compressed
bytes, and the finite coverage witness occupies 1,124,080 JSON bytes / 185,955
compressed bytes. The independent reference archive contains 180 proof nodes,
occupying 1,642,496 SQLite bytes / 96,760 compressed bytes. Report, logs and these
separate artifacts are additional to the working database. No peak-RAM claim
follows from persistent file sizes.

All **569 tests**, full cold inventory checks and the standalone validator pass.
Replay performs no new probe discovery or reference expansion and leaves database
bytes unchanged. The history now has **41,565 pattern nodes, 79 windows and 108
continuation blocks**; all earlier rows and external evidence remain preserved.
The manuscript and Lean sources are unchanged: this is an additional checked
experimental route, not a new tractable family or unrestricted complexity bound.

## Next highest-value gap

Start with the **23-variable, 97-clause leaf on case 32**, using the exact key in
`diagnostics.json.gz`. Its saved positive/negative traces now include the later
windows that the leaf's initial bounded learning did not consume. Test common
consequences, signed equivalences and additional checked implications on that
exact source; exclude nested augmented-formula traces from original-source
reason indices. If they give no useful reduction, compare a bounded two-variable
conditioning step with a fixed-budget augmented-source continuation. Retain
all unsuccessful evidence and compare equal extra work when attributing gains
to learning.

The 39-variable leaf is a secondary exhausted target. The parent's 36 clear
augmented trials also remain available, with their learned-clause dependencies.
Do not rerun the unchanged old implication graph or simply replay another
ordinary probe pass on these two exhausted leaves. The separate large cost gap
is dependency-local cold validation: the 0.11697-second addition still pays for
checking the accumulated history. Any reduction of that cost must preserve
explicit proof dependencies, byte-preserving reconstruction and total accounting.
