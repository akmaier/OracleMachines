# Binary equivalence substitution with shared proof trees

The optional top-level acquisition API now discovers one binary SCC equivalence
block, substitutes it throughout the full CNF, solves the quotient with the
unchanged targeted-backbone solver, and verifies the result against the source.
SAT models lift to ordinary native source witnesses. An UNSAT quotient uses an
explicit `binary-equivalence-negative-v1` record in a separate table. Its child
must be an ordinary native UNSAT certificate. Native recursive search never
consults this table, so old proofs cannot gain hidden extension dependencies.
Existing defaults, native formats and affine authorities remain unchanged.

The implementation closes the certificate bridge for this top-level experiment.
It does not yet integrate equivalence reduction into the prepared production
admission pipeline or every native recursive expansion. In particular, it runs
its own SCC computation; it does not yet share that computation with the
preceding binary recognizers. This limitation is included in the measured cost.

## Exactness and certificate compression

For a signed block of `k` literals, use a positive representative and two trees:
one reaches every member from the representative, the other reaches the
representative from every member. Each edge cites an exact binary source clause.
The checker verifies all edges, equal supports, unique variable identities,
rooted reachability and progress. Disconnected cycles, mismatched trees, wrong
clause indices and repeated/opposite members are rejected. Mutual implication
makes every member equivalent to the representative. Replacing each variable
with its signed representative in **every** clause preserves satisfiability;
quotient models lift by the same signed map. The UNSAT reader reconstructs the
exact quotient and requires its checked negative native dependency.

Two shared trees use exactly **2(k-1) edges**, instead of materializing every
representative/member path separately. The 24-variable cycle test needs 46 tree
edges; separate directed star paths would total 552 edges. This is established
implication/SCC reasoning and shared evidence, not a new tractability theorem.

Discovery costs `O(L + V_B log V_B + E_B)` adjacency operations in this
implementation, including deterministic block sorting; the two selected trees
cost `O(V_B + E_B)` and retain `O(k)` edges. Temporary graph space is
`O(V_B + E_B)`. Checking and full substitution cost `O(L+k)` before normalization,
child acquisition, persistence and cold replay. The record as implemented is
**not O(k) bytes**: it includes a full source key, source CNF and child key, so
its size also depends on source/quotient encoding length. General branching
remains unrestricted. No new Lean theorem or uniformly polynomial SAT bound follows.

## Matched reconstruction and edit pilot

Four serial workers compare the preceding targeted solver with the optional
quotient API in opposite orders. Both start from an **empty archive** and retain
results within the stream. Inputs comprise the eleven saved split residuals,
33 edits of them (one free clause, a two-clause coupling, or a binary-clause
deletion), and 24 unfamiliar generated controls across four families and three
sizes. Only the eleven saved roots occur in the parent archive. Family and edit
labels never enter search. These are counterfactual reconstructions and controlled
edits, not the historical production prefixes or a new arbitrary-SAT taxonomy.

Both policies decide all **68 inputs: 21 SAT / 47 UNSAT**. All decisions have
independent exhaustive truth tables, warm reuse and cold certificate replay.
The candidate selects 45 blocks, each merging **one variable** on this workload.
It produces three ordinary SAT lifts and 42 negative extension records. Only one
negative quotient child is already available before its query. Recursive native
recognition remains unchanged.

| Per worker, except mean times/RSS | Targeted baseline | Quotient API |
|---|---:|---:|
| Native certificates | 420 | 398 |
| Equivalence certificates | 0 | 42 |
| Total certificates | 420 | 440 |
| Native payload bytes | 525,136 | 465,733 |
| Equivalence payload bytes | 0 | 68,878 |
| Combined payload bytes | 525,136 | 534,611 |
| Native expansion calls | 364 | 358 |
| Additional substitution steps | 0 | 45 |
| Propagation visits | 61,517 | 51,326 |
| Query seconds | 0.29384 | 0.29752 |
| Complete-worker seconds | 0.45818 | 0.46408 |
| Cold replay seconds | 0.07173 | 0.07570 |
| Mean peak RSS bytes | 55,566,336 | 55,869,440 |
| SQLite bytes | 929,792 | 954,368 |
| Compressed bytes | 85,405 | 86,336 |

The **16.57% propagation reduction** does not establish a total-cost gain. Total
certificates rise twenty, combined payload rises **9,475 bytes / 1.80%**, and
query/complete means rise **1.25% / 1.29%**. Complete-worker deltas are positive
in both orders: +0.00382 / +0.00797 seconds. Cold replay rises 5.53%; SQLite grows
24,576 bytes, gzip 931 bytes, sidecars about 42.8 KB, and mean RSS 303,104 bytes.
These small timing samples do not establish scaling, but they supply no reason
to enable the policy by default. The regression is preserved.

Discovery performs 68 top-level calls, builds 4,276 binary edges, visits 8,552
SCC edges and 547 tree-search edges, and emits ninety evidence edges. Full
substitution/verification scans 10,859 literals, with 174 evidence edges checked.
The six fewer native expansions must be read alongside the 45 new substitution
steps and 42 extension publications. No study tests/audits ran during measurement.

Saved-source acquisition alone grows **53 -> 62 certificates**, despite fewer
propagation visits. The two saved old-case-31 inputs behave differently, and
old-case-56 grows **six -> eight certificates**, even though propagation falls
2,043 -> 896 visits. Its coupling edit instead falls six -> three certificates.
Deleting binary clauses can invalidate the old equivalence; every edit is
recognized again. Group totals include differing within-stream reuse and must
not be treated as independent marginal costs. Fresh controls select only one
block and add one certificate. These contrasts constrain any admission rule.

## Next highest-value gaps

**First: remove redundant formula copies from the negative record.** Its 68,878
bytes comprise a 21,345-byte full source key and 47,533-byte payload. Within that
payload, serialized source CNFs occupy **20,673 bytes**, child keys **20,535**, and
equivalence evidence only **2,713**. The source is already encoded in its canonical
key; the child key is reconstructible from checked substitution. A new version
can test omission of these two redundant payload fields, while checking the exact
key format, canonical source and native child binding. Preserve version-one
readability and charge reconstruction work. The 41,208 bytes are a structural
opportunity, not a measured net saving; field overhead, checking and compression
still need measurement. This direction does not require collision-free hashing.

**Second: reuse binary discovery across wide-clause edits.** The 56 eligible
mixed inputs contain only 34 distinct exact binary keys: **22 repeat** a preceding
binary core. Both added-wide-clause variants preserve that core. Cached SCC/tree
facts would require transport of binary-local clause indices into each full
source, exact literal-coordinate matching, and invalidation when binary clauses
change. The census is not an implemented cache. It identifies duplicated work
without assuming semantic equivalence recognition is cheap.

**Third: quotient all useful blocks together.** Twelve inputs contain two
disjoint equivalence blocks, while this policy merges only one. A posthoc
all-block substitution removes two variables and eight literals on each of
these inputs; exhaustive truth is unchanged. None of those complete quotient
keys is already available at its query prefix. Multi-block certificates and their
acquisition costs remain unimplemented, so do not count them as reuse hits.

Only after pricing these changes should the quotient API be connected to the
prepared production pipeline or recursive native acquisition. The prior sixty-query
stream still has expensive random-three and graph-discovery residuals. Broader
coverage, cheap representation of arbitrary interactions, and uniform efficient
expansion remain open.

## Preservation and reproducibility

Resume `experiments/results/cnf-binary-equivalence/checkpoint.json`. The union
preserves all **28,145 native payloads and twenty-six affine extensions**
byte-for-byte, reaching **28,691 native keys**, plus **42 explicit equivalence
records**. It includes 136 new source decision records and retains 5,650 prior
composed records. Four alternative native roots remain in trial archives; the
union keeps its first payload. Archive growth is **1,327,104 SQLite / 127,289
compressed bytes**, including the comparator's histories. Native and affine
readers remain unchanged; new negative records require `EquivalenceStore`.

All **1,220 tests**, **51 focused tests**, 272 chronological query/dependency
audits, 68 exhaustive truth tables, warm answers, old native/composed/projection/
affine history and the new extension union validate. Eight new tests include
4,096 small formulas and quotient/lifting semantics, shared-tree compression,
corrupt/cyclic evidence, missing or positive children, signed names, disappearing
representatives and clause edits. Full tests retain 44 pre-existing SQLite
warnings; focused tests have none. All 581 prior sources, 7,608 artifacts and
108 manifests remain unchanged. The optional top-level API must not be passed
to old callers that assume every negative result is a native source root.

The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **586**. New manifest: **34
artifacts**. Next preservation audit: **7,642 artifacts / 109 manifests**.
