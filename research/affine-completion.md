# Complete checked affine spaces against leftover clauses

The native acquisition stream and the existing affine pattern-discovery layer
previously ran separately. The costly saved coupled-parity targets contain
complete direct parity encodings with additional CNF clauses. The existing
extractor recognizes these equations without family labels and preserves every
leftover clause. This optional policy reuses that checked representation to
find native positive witnesses.

## Checked discovery and reuse

The preceding selector retains priority for known targets, native families,
models, guards and negative covers. Only unresolved targets or retained-prefix
fallbacks reach the affine bridge. Normalization, exact parity extraction and
Gaussian reduction are charged. The independent extraction checker verifies
complete, distinct sign patterns, full clause ownership and every triangular
row operation. Source bindings use the entire normalized key.

With n source variables and rank r, the total free dimension is d=n-r, including
variables absent from the extracted equations. Consistent systems with d<=8
reuse the existing particular-solution and complete-basis routines. The checker
validates the particular solution, every homogeneous direction, and identity
coordinates on all free variables. This proves that the basis spans the entire
affine solution set; a few convenient directions would not suffice.

Leftover clauses are converted once to positive and negative bitmasks. The
candidate walk uses Gray order: each next candidate XORs exactly one basis
direction into the previous assignment. Every failed candidate retains the
first falsified leftover clause. The winning assignment is transported to the
original variable names and checked against the whole raw source before
ordinary native model publication. Earlier guards retain their checked outer
recomposition. Cold replay uses the unchanged native
verifier. No new native proof kind or search inside model publication is used.

The prior discovery record is unchanged. A separate source-bound record retains
the extraction, rank, free dimension, checked basis where eligible, rejected
candidate clauses and accepted index/mask. No-equation, free-cap, inconsistent
linear-system and exhausted-space outcomes preserve the preceding native
fallback. The last two outcomes contain useful checked negative evidence, but
this version does not publish them as native refutations. Their integration is
an explicit next gap, not an unreported solver shortcut.

## Resource obligations

Let L be source literal occurrences, E extracted equations, r their rank,
m_l leftover clauses and n variables. Dense masks occupy B=max(1,ceil(n/W)) machine
words for word size W. Source normalization, sorting, full keys and actual
integer widths remain separate. Grouping scans L literals and sorts support
and group keys. Elimination and its checking use at most O(E r B) word work,
plus mask construction and source checks. These are bounds on this explicit
encoding, not recognition of all hidden affine structure.

A checked space costs O((d+1) r B + E(d+1)B) for back-substitution and equation
checks, plus mask construction. Packed leftovers cost O(L_l B) conservatively
with arbitrary-width integer operations. For t<=2^d candidates, the walk uses
t-1 direction XORs and at most t m_l packed clause tests, costing
O(t(m_l+1)B). Full raw-source model verification is charged once on success.
The d<=8 cap is checked before basis construction or enumeration. A cap miss
retains native fallback; it is not an efficient decision of every source.

The transient basis and packed clauses use O((d+1+m_l)B) words beyond
extraction, source and history; a transported model adds O(n) words. Certificates also retain row dependencies,
particular/basis masks and at most 2^d rejecting clause indices. Gaussian
row-operation history can itself contain O(E r) references. Native model storage,
canonicalization, serialization, historical archive growth and replay remain
separate costs. Explicit caps and exact checking do not establish uniformly
polynomial acquisition on arbitrary SAT.

## Validation design

The 29 preceding exact-prefix contexts are preserved and twelve saved coupled
inputs are added (41 contexts / 82 comparison arms). Target 57 repeats in reverse
order, for 84 arms total. A fresh sixty-query stream, selected by excluding prior
decision keys, compares native
baseline, cover-directed probing and affine completion in opposite serial
orders. All preparation, recognition, certificate checking, candidate work,
persistence, warm reuse and inherited cold replay are measured. Family labels
never enter selection. Truth enumeration and attribution run after timing.

Eight new tests include 512 exhaustive three-variable-support/coordinate
comparisons and 64 random affine mixtures checked against all assignments.
They exercise Gray traversal, positive publication, negative evidence, the cap
before basis construction, forged extraction and incomplete bases, forced
prefixes, signed coordinates, known nodes and unchanged cold replay.

## Measured outcomes

The eight saved satisfiable coupled inputs shrink **80 -> 8 native nodes /
82,179 -> 10,860 native bytes**. Their models require one to three candidates.
The other 33 saved contexts retain their native certificates. In particular,
four negative coupled controls still acquire 83 nodes: two have inconsistent
linear rows and two exhaust their small affine spaces. The reverse control
reproduces the same native model.

The fresh sixty-query stream returns **39 SAT / 21 UNSAT** in every mode.
All 48 family targets remain unfamiliar after shared preparation. Eleven
neighbours become known; neighbour case 4 remains unfamiliar behind two checked
guards and adds ten nodes in every mode. The bridge adds nine checked coupled-input models,
replacing 68 native expansions with nine model nodes. The preceding admitted
routes keep priority. All additional analysis is charged, including misses.

| Cost across sixty queries | Native baseline | Cover-directed probe | Affine completion |
| --- | ---: | ---: | ---: |
| New native nodes | 442 | 395 | 336 |
| New native payload bytes | 523,148 | 482,568 | 424,272 |
| Expanded nodes | 431 | 336 | 268 |
| Discovery/acquisition propagation visits | 70,338 | 95,711 | 83,024 |
| Mean query seconds | 0.37155 | 0.38629 | 0.34381 |
| Mean complete worker seconds | 26.03394 | 26.25352 | 26.14046 |
| Mean full cold replay seconds | 12.63493 | 12.75802 | 12.70730 |

The bridge inspects 29 targets, grouping 5,222 literals and checking 156
extracted equations. Seventeen targets have no extracted equations, one has
inconsistent rows, two exhaust their complete spaces, and nine yield models.
There are no dimension-cap misses in this sample. Eleven bases contain 44
vectors in total. The candidate walks test 36 assignments with only 25 basis
XORs and 186 packed clause checks; packed leftover construction visits 261
literals. Gaussian elimination uses 219 XORs, independently checked again;
space construction visits 571 rows and space checking tests 143 particular
and 433 homogeneous equation instances. Winning raw-model checks visit
1,566 literals. None of these costs is treated as free oracle preparation.

Relative to the preceding probe policy, native additions fall 14.94%,
propagation visits 13.26%, and mean query time about 11.00%. Paired query deltas
are -0.05365/-0.03129 seconds. Complete-worker deltas are -0.36826/+0.14212
seconds: their mean falls about 0.113 seconds, with about 0.051 seconds explained
by mean cold-replay variation. The total timing result is therefore mixed and
the native baseline's mean complete worker is still lower. Two orders and finite
generators do not establish a general scaling advantage.

Diagnostic sidecars grow about 7.86%, from 1,828,812/1,828,777 to
1,972,634/1,972,600 bytes. Trial SQLite falls 82,288,640 -> 82,169,856 bytes;
compressed archive size falls 6,206,880 -> 6,192,625 bytes. Mean peak RSS falls
about 2.87 MB, from 797.458 to 794.591 MB. The preservation union also retains
old and comparator proofs, so cumulative growth differs from these trial savings.

Fresh negative evidence remains actionable. Case 29 has an inconsistent linear
system and still inserts seven fallback nodes. Cases 41 and 57 exhaust four
and eight candidates, yet still insert eight and 36 fallback nodes. Together
these three already checked negative analyses retain **51 native fallback nodes /
7,829 acquisition propagation visits**. A compatible published certificate
could avoid that acquisition, but its checking, storage and replay costs have
not been measured. Random three-CNF and the no-equation cell remain separate
larger-coverage obligations.

## Remaining gaps

The fresh base discovery agrees on all 49 locally unfamiliar queries across
the two policies. Eleven neighbour queries become known after preparation;
neighbour case 4 remains unfamiliar behind two checked guards and adds ten
nodes in every policy. This is a shared control miss, not an affine regression.
Random three-CNF still adds 169 nodes / 28,452 acquisition propagation visits.
Fresh graph case 47 retains incomplete covers with two missing conditions per
candidate clause, beyond the one-extra-probe rule. These misses are preserved
alongside the negative affine publication target.


Negative publication is still missing: inconsistent affine rows and exhausted
checked spaces leave the native fallback active. A compatible source-bound
certificate must preserve row/basis checking, leftover interaction and native
history rather than assume a negative diagnostic is already published.
Inputs with large free dimension or no extracted equations remain unresolved.
Projection onto leftover variables, shared affine kernels, early admission,
and cheaper failure recognition are further opportunities; their own discovery,
maintenance and validation costs must be measured.

## Verified checkpoint

All **1,169 tests**, 24 focused tests, 324 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-affine-completion/checkpoint.json`:
**26,743 native keys**, preserving all 26,279 prior payloads, with 264 new
composed records alongside 4,719 inherited records, 2,957 ordinary decisions
and six projections. The union uses 82,378,752 database bytes / 6,217,639
compressed bytes. Twenty-six roots have alternate certificates in 67 retained
evidence occurrences. Ready/pending banks remain 132/38, 141/66, 87/89 and
87/116, with no new support activation. Original structural coverage remains
17/24 and supplemental positive coverage 24/24. All 539 prior sources,
6,871 artifacts and 101 manifests remain unchanged. The 217-page manuscript
builds with all 64 existing proof blocks unchanged. No new Lean theorem,
native proof kind or unrestricted-SAT resource guarantee is claimed.

New manifest: **300 artifacts**. Next preservation audit: **7,171 artifacts / 102 manifests**. Final source ledger: **544**.
