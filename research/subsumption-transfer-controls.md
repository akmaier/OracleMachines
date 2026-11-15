# Check family exposure before attributing gains to reuse

2026-11-15. A checked subsumption lookup can transfer the selected eighteen-variable
proof to twelve new variants, but this is not evidence of reuse beyond known
families: its reduced core is **16 variables / 18 clauses / 36 literals**, all
binary. A separate control that recognizes existing families immediately after
subsumption performs better and requires no prepared proof. Keep both the initial
result and this control; the first proposed interpretation was too strong.

## Frozen inputs and valid transfer

The initial protocol fixes seed **20261115184918**, 42 inputs, two repetitions,
three modes and the existing planner options before acquisition. Six inputs each
cover redundant extensions, order-preserving renamings, arbitrary permutations,
disconnected mixtures, connected mixtures, invalidating edits and random CNFs.
Extensions add up to 64 redundant clauses and grow the raw support from eighteen
to 82 variables. All 42 normalized source formulas are distinct and absent from
the **1,196 distinct canonical historical inputs** and **11,641 distinct CNFs in
the selected prepared proof rows**. This is not a search of every earlier trial.
Most inputs deliberately derive from the selected motif, so the sample is an
applicability test rather than an unbiased holdout or industrial workload.

The source template is the previously shared **18/22/48** node, identified by
`a9e2ae2f969428ac5ad0f7d71f8860d398c056b212b85826fc16014be83fa3cc`.
Its extracted positive proof has **twelve steps**, occupies **3,691 compressed
bytes**, and reconstructs **118,784 SQLite bytes**. Extraction costs **0.24176 s**;
prepared arms independently verify the template once before answering queries.
The earlier acquisition remains a prerequisite.

For query F and template C, the candidate index computes their minimal signed
clause sets and compares the normalized results. An independent checker verifies
that every removed clause has a retained signed subsumer, checks both complete
clause partitions and checks the variable-name maps. Thus each reduction preserves
its Boolean function, and equality of the reduced formulas gives equivalence
under the explicit maps, with discarded variables free. A template model lifts
through those maps and satisfies the original query. The template's positive
coverage proof is verified separately; neither a dictionary hit nor a digest
supplies that proof. General permutations and semantic equivalences are not
searched. Failed matches remain eligible for ordinary discovery.

For a source with m clauses, maximum width w and L literal occurrences, the
minimal-clause stage has a conservative word-operation bound
O(1 + L log(L+1) + m²(w + log(m+1))) under expected constant-time hash operations.
This charges normalization, candidate sorting and subset checks; classification,
template preparation and positive-proof verification are additional terms. The
subsumption witness and variable maps use O(m+n) index/identifier slots, alongside
the input and any retained template proof. These are not bit or Python-memory
bounds: long labels, hashing behavior, serialization and object overhead remain
charged. Equality of minimal normalized clause sets is a sufficient reuse test,
not a complete test of Boolean equivalence.

The initial generator failed before protocol freezing or acquisition because it
used compacted core variable IDs when removing an original source clause. The
failure log and exact producer snapshot are retained under
`cnf-subsumption-transfer-preflight-failure`. The corrected generator works in
original source coordinates and checks that every added weak clause contains an
original signed clause. The transfer checker itself was not changed by this fix.

## Initial result and its limitation

Each arm starts with empty ordinary discovery history and retains fallback results
across the fixed stream. Prepared arms additionally receive the checked template.
There are twelve subsumption hits and no exact-template hits. Those twelve cases
avoid 192 probe attempts and 25 recorded admissions, but later disconnected
mixtures lose some incidental warm ordinary-history reuse: they need three extra
admissions and sixteen extra probes. The net saving is **22 admissions / 176
probes / 22 stored rows**. Coverage stays **41/42** in all arms.

Mean preparation-plus-query cost is **0.48613 s** for the empty control,
**0.49639 s** for exact-template lookup and **0.47214 s** for subsumption transfer.
The approximately 2.9% aggregate difference in two repetitions is not strong
statistical evidence of a general speedup. New working SQLite size falls from
**2,510,848 to 2,244,608 bytes**, excluding the separate prepared template database.
Signed-subsumption lookup is sound, but this chosen template does not demonstrate
reuse of a reduced core outside recognized families.

## Supplemental early-family control

After observing the 2-CNF confound, a separately frozen control compares ordinary
discovery, template subsumption and early family recognition on the same inputs.
This control was chosen after the first result; it is not presented as part of the
original preregistration. Early recognition uses the existing classifier on the
reduced CNF and independently checks the source reduction and claimed family.
It does not reuse or acquire a stored template.

| Cost / result | Ordinary | Template subsumption | Early family |
| --- | ---: | ---: | ---: |
| Covered inputs | 41/42 | 41/42 | 41/42 |
| Early successful queries | 0 | 12 | 33 |
| Recorded discovery admissions | 190 | 168 | 100 |
| Actual new pattern rows | 197 | 175 | 107 |
| Fresh probe attempts | 1,022 | 846 | 503 |
| Mean preparation + queries (s) | 0.49636 | 0.47493 | 0.38107 |
| Working SQLite bytes | 2,510,848 | 2,244,608 | 1,466,368 |
| Mean compressed archive bytes | 133,172.5 | 122,761.5 | 79,484 |

Early family recognition avoids **519 fresh probes and ninety stored patterns**.
Observed preparation-plus-query time falls **23.23%** and working SQLite size
falls **1,044,480 bytes**. These are two reversed-order fresh-process repetitions
with shared OS caches and one stream order. The family worker includes ordinary
inventory initialization in preparation; the two inherited workers include it in
the query interval. The combined preparation-plus-query measure is the appropriate
comparison. Measurements include normalization, lookup/classification, independent
checking, semantic journal insertion, fallback acquisition and persistence. Timing
metadata updates are excluded from individual operation timers but included in
stream totals. Generation, archive compression and cold replay are separate.
Peak process memory is unmeasured. Old histories are preserved and the study's
saved archives add persistent storage.

Early family recognition handles all six cases in each of the first five groups
and three of six invalidating edits. The other three edited cases and all six
random inputs reach ordinary discovery. A changed query can still belong to a
simple family; recognizing it is distinct from asserting equivalence to the old
template. All twelve experiment archives and 504 recorded query outcomes pass
independent cold replay with fresh acquisition disabled. The seven transfer tests
include all 512 two-variable CNFs; five family tests include pointwise checks of
all three-variable formulas with at most two clauses. All **318 relevant tests**
pass. There is no new Lean theorem or unrestricted-SAT complexity claim.

The saved bundle contains **55 manifested artifacts / 4,669,881 bytes**, excluding
the manifest itself. All **2,851 prior artifacts / 45 manifests** and **155 prior
frozen sources** remain unchanged. The updated manuscript builds to **174 pages**,
preserving all **64 existing proof blocks**, without undefined references or
overfull boxes. The new validation binds 162 source files. In the family arm's
inherited per-group schema, `reuse_hits` means early family recognitions, not
stored-proof hits.

## Correct the admission interpretation

The inherited protocol's phrase “32 states” overstates what the counter controls.
`BudgetedInventory._discover` caps entries through that method. Fused conditioning
can call `_discover_profile` and `_record_node` directly. A separate observed rerun
reproduces the initial experiment and finds **eighteen recorded nodes outside that
admission ledger in every arm**. Eleven admitted states remain unstored at the last
cap, giving 190 + 18 - 11 = 197 stored states for the ordinary arm. The audit does
not claim that stored counts measure every partially computed profile.

This is an accounting limitation, not an invalid proof acceptance. Every stored
node and completed positive query still replays. Do not interpret earlier or
current ledger counts as a global bound on all recognizer work. A future strict
resource cap must cover every acquisition entry point before performing its work;
repairing only the final counter would not do so. Historical archives and reported
counters remain frozen, with this correction attached.

## Next target

The largest remaining cost is **case 41**, a fresh **48/204/612** random CNF. It
uses 272 probe attempts, hits the admission allowance and remains structurally
unknown in every arm. Its normalized source fingerprint is
`511dd0f7c367b2af3e9f447f8411ef8ed10e0265dfcde5666b7d35f0b4aa1a22`.
The six random cases consume about **0.315 s of the 0.378 s** family-arm query
stream. Further optimization of the already easy motif would miss the dominant
cost. Inspect the stored unfinished frontier and its interactions, keeping this
new sample frozen rather than tuning it into a claimed holdout win.

Before a further budget comparison, cover the fused-conditioning acquisition
entry point with explicit accounting. For reuse research, choose templates whose
reduced core is outside existing terminal families, and compare them against
cheap family exposure. Any new ranking or component-transfer policy must charge
recognition, proof transport, invalidation and cold checking. The old 83-source
checkpoint remains complete and unchanged; do not restart its null selection.
