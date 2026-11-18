# Probe a missing condition to complete a negative clause cover

The previous [cover compiler](negative-cover.md) only uses conditions admitted
by the fixed ranking of four variables. Its fresh cases 51, 55 and 59 each
have a source clause with exactly one missing negative condition. These literals
lie outside that ranking. The new optional policy spends at most one additional
probe on such a literal, chosen from the narrowest eligible source clause and
then by original clause index. Family labels are never inputs to selection.

## Recognition and exact reuse

The entire previous discovery pass remains unchanged. If it has already found
a model, cover or another admitted route, that route keeps priority. Otherwise,
the selector gathers retained negative SCC conditions, scans source clauses,
and selects a nontautological clause with at least one covered literal and
exactly one uncovered literal. The missing literal must not have been probed
before. There is no general search in candidate discovery.

The extra probe canonicalizes the source with that literal asserted, propagates
units, and examines the residual. A binary residual is passed to the existing
SCC solver. A negative result supplies the missing cover condition; the existing
compiler checks and transports all conditions into ordinary native proofs.
A positive result supplies a model which must satisfy the whole raw premise,
then passes ordinary native model publication. It never becomes a negative
parent conclusion. Unit conflicts and nonbinary residuals are recorded as
explicit misses in this version, retaining the preceding fallback choice.

The original discovery record is not mutated. A separate record binds the
chosen clause, extra assumption, unit trace, residual and SCC outcome. The
compiler receives a shallow combination of old and new conditions. Source
indices, canonical variable maps, unit reasons and both contradiction paths
are checked again before publication. Existing payloads and alternative native
proofs remain preserved; cold replay uses the unchanged native verifier.

## Resource obligations

The additional budget is one premise, separate from the existing eight possible
signed probes on four ranked variables. It does not make the original search
budget disappear. With k retained records, m source clauses and L literal
occurrences, recognition has a conservative O(k + m k + L + sum_c w_c log w_c)
expected word-operation bound. This charges dictionary-key set operations per
clause and sorting candidate literals. The new tautology check uses a set;
the preceding cover recognizer's list-based opposite-sign check still has its
separate quadratic-width cost.

The new premise copies O(L) literals, canonicalizes and creates a full key.
The existing scan-based unit propagation can take O(nL). A binary residual then
costs O(n_i log n_i + L_i) expected word operations for SCC construction and
paths. Raw positive-model checking costs O(n+L). Negative compilation retains
its width-w bound of at most 3w-1 planned native nodes, with separate canonical
rebinding, reason/path verification, cofactor transport and possible unit
repair. Extra transient state and diagnostic payload can use O(n+L+k) words,
beyond the prior discovery records and native archive. Integer widths,
serialization, full-key storage, retained history and cold replay are charged
separately. Failed probes add overhead; there is no all-input dominance bound.

## Validation design

Twenty-nine exact-prefix contexts retain all earlier controls and add the
three motivating cases from the negative-cover stream. Two policies give
58 arms; target 59 repeats in reverse order for 60 arms total. A further
excluded sixty-query stream compares baseline, cover-only and cover-directed
probing in opposite serial orders. Discovery, checking, compilation, persistence,
warm reuse and full inherited cold replay are included. Truth enumeration and
independent certificate/counter analysis happen after timed workers.

Eight new tests include all 64 four-vertex graphs in two coordinate systems,
with independent exhaustive colourability checks. They also exercise positive
completion, failed probes, candidate ranking and overlaps, corrupted extra
conditions, forced prefixes, preservation of known nodes and cold replay.

The first production attempt overlapped the end of preflight. It was stopped
and retained as an excluded timing pilot. After preflight completed, the full
comparison restarted with unchanged runtime sources and no concurrent tests,
builds or profiling. Only the clean run supplies reported comparisons.

## Measured outcomes

All three motivating parents now close with one additional condition each.
One older saved control also benefits, taking the four changed contexts from
**52 -> 32 acquired nodes / 63,028 -> 38,503 native bytes**. The other 25 saved
contexts retain their native certificates. The reverse target reproduces its
same compiled proof. All sixty preserved pilot-control deltas match their
clean-run counterparts; excluded timings are not used below.

The fresh sixty-query stream returns **40 SAT / 20 UNSAT** in every mode.
All 48 family targets remain unfamiliar after shared preparation, and twelve
neighbours become known. Four added probes complete covers on cases 31, 43,
55 and 59. Each publishes eight native nodes, replacing 56 fallback expansions
in total. Fourteen existing positive model publications remain unchanged.

| Cost across sixty queries | Native baseline | Cover only | Extra cover probe |
| --- | ---: | ---: | ---: |
| New native nodes | 463 | 431 | 407 |
| New native payload bytes | 567,221 | 542,374 | 512,936 |
| Expanded nodes | 451 | 397 | 341 |
| Base premise probes | 0 | 99 | 99 |
| Extra cover probes | 0 | 0 | 4 |
| Discovery/acquisition propagation visits | 72,247 | 104,544 | 98,303 |
| Mean query seconds | 0.39099 | 0.42943 | 0.38553 |
| Mean complete worker seconds | 25.43236 | 25.46195 | 25.48478 |
| Mean full cold replay seconds | 12.34822 | 12.37654 | 12.41804 |

Additional recognition reads 72 completion records and 32 attempts, scanning
268 source clauses / 561 literal occurrences and finding eight eligible clause
candidates. Only four additional premises are probed, copying 565 literals.
Their residuals have 112 clauses / 224 literal occurrences and create 224
implication edges. All four are negative; there are no added positive, nonbinary
or unit-conflict outcomes in this timed sample. The tests separately exercise
those possibilities. Both old and extra evidence, compiler costs and native
checking remain charged.

Relative to cover-only, query time falls 10.22% and total propagation visits
5.97%. Paired query deltas are -0.07650/-0.01128 seconds. Paired complete-worker
deltas are +0.10821/-0.06255 seconds, with a mean increase of about 0.023 seconds.
Cold replay averages 0.042 seconds more. These two orders support the measured
query reduction but not an end-to-end speedup or a general scaling claim.

Diagnostic sidecars grow about 0.82%: 1,832,278/1,832,314 ->
1,847,288/1,847,287 bytes. Trial SQLite falls 81,268,736 -> 81,231,872 bytes
and compressed archive size 6,097,153 -> 6,093,833 bytes. Mean peak process RSS
rises about 1.61 MB, from 782.844 to 784.450 MB. The preservation union additionally
retains comparator proofs and historical entries; its growth is separate from
the smaller per-policy acquisition.

A retrospective view of the four selected clauses finds that their required
old conditions were available after 8, 5, 7 and 4 base probes, respectively,
out of eight executed for each. For these particular chosen clauses, earlier
admission could therefore avoid eight later base probes in total. This is a
feasibility observation, not an implemented early selection policy or a measured
saving: prefix-dependent candidate choices, maintenance costs and failed early
probes still need evaluation.

## Remaining limitations

**Largest remaining measured acquisition cost:** coupled parity and random
three-CNF still add **308 native nodes / 52,385 acquisition propagation visits**,
unchanged across policies. Coupled parity alone adds 163 nodes / 25,354 visits;
random three-CNF adds 145 / 27,031. These dominate the remaining native work.
The existing pattern-discovery layer already extracts explicit affine equations
and preserves leftover clauses, whereas this native acquisition path currently
has uniform and binary leaves. The next broad-coverage investigation should
measure a source-checked bridge from that existing affine extraction to native
acquisition on unlabelled coupled inputs: record rank, free dimension and
leftover interaction before choosing a completion rule. Charge extraction,
projection, checking and any enumeration; a 2^d free-coordinate search is only
cheap when d is small, not uniformly polynomial for arbitrary CNF. Positive
models require full-source verification and negative results require their own
checked recomposition. This is a concrete integration target, not an already
measured improvement.


The one-probe policy cannot seed a cover without existing negative conditions,
complete clauses missing several conditions, or retry an already attempted
condition. Unit-conflict conditions and clauses exposed by baseline propagation
still need a unified certificate interface. It is also possible to finish a
cover earlier within the original pass, avoiding probes instead of adding one.
Random three-CNF, coupled parity and general nonbinary residuals remain outside
this extension's structural guarantee. Cover construction does not establish a
uniform polynomial bound on arbitrary SAT expansion or oracle construction.

## Verified checkpoint

All **1,161 tests**, 24 focused tests, 300 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-cover-probe/checkpoint.json`:
**26,279 native keys**, preserving all 25,757 earlier payloads, with 240 new
composed records alongside 4,479 inherited records, 2,957 ordinary decisions
and six projections. The union uses 81,416,192 database bytes / 6,113,510
compressed bytes. Fourteen roots have alternate certificates in 27 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 534 earlier sources,
6,641 artifacts and 100 manifests remain unchanged. The 216-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.

New manifest: **230 artifacts**. Next preservation audit: **6,871 artifacts / 101 manifests**. Final source ledger: **539**.
