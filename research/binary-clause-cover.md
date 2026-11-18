# Cover a wider clause with binary implications

A satisfiable binary core can force every literal of a wider clause false. This
is a useful distinction from the preceding binary-subset refutation: the binary
core alone has a model, but it is incompatible with a source clause.

For a source `F = B ∧ W`, let `C = l₁ ∨ … ∨ l_w` be a clause of `W`. If `B`
contains a path `l_i → ¬l_i` for every literal of `C`, then `B` entails `¬C`,
and `F` is UNSAT. The recognizer uses this sufficient condition. A satisfiable
core or a failed path search never decides the full source.

## Recognition, proof reuse and costs

The optional solver retains the earlier negative binary-subset rule. On a
satisfiable binary core, its model filters possible covered clauses: a clause
entailed false must be false in that model and have all its variables in the
core. Uniform core models avoid SCC construction. Source clauses wider than
four are outside the new rule. At most eight distinct literal reachability
queries are made per fresh residual; completed results are shared between
candidate clauses. A budget miss remains unresolved. No source-family labels
or historical case identifiers enter recognition.

The compiler checks the source clause and every binary path. It then emits the
existing native split, unit and implication proof kinds. Covered literals are
split until only two remain. For those literals `y,z`, retain `y → ¬y` and use
`¬y → z → ¬z → y` for the opposite path. The two new edges come from the
now-binary source clause. When the path variables survive the stronger assignment,
clause-index transport reuses the original paths without fresh SCC work.
Unit conflicts can close earlier branches. A conservative binary SCC repair
remains available if a path vertex was fixed; no such repair occurs in the
fresh comparison. The unchanged native verifier checks every stored child and
root, so no new proof format or authority is introduced.

A width-`w` cover constructs at most **`2w−3` native nodes**, including its root.
A reused older node may reference a larger history; its replay remains charged. The rejected compiler continued splitting to one literal
and could use `2w−1`; its source and measurements are preserved in the diagnostic
script. This distinction matters: compiled children still consume time and space.
Counting only calls to ordinary expansion would overstate the saving.

For `m` clauses, `b` binary clauses, `v` variables and literal payload `L`, extra
source/model filtering costs `O(m+L)` and the eight reachability queries cost
`O(8b)` graph work. Temporary graph/path storage is `O(m+b)` for these fixed caps.
The inherited SCC routine also sorts variables, costing up to `O(b log b)` in
the comparison model. Compilation normalizes and retains up to `O(wL)` full
source/key payload, with identifier encoding additional. Its inherited repeated
scan unit propagation can cost `O(wvL)`; normalization, checking, serialization,
persistence and any repair are also charged. The source-bound path cache lasts
for one residual; persistent reuse is still through exact canonical native keys.
The number of remaining search residuals can be exponential.

## Retrospective evidence and rejected work

The previous trial's stored nodes contain 116 satisfiable mixed binary cores,
44 residuals with forced binary literals, and nine with a covered wider clause.
Thirteen binary models also admit a checked whole-source completion, but positive
completion is not enabled by this policy. These counts include direct publications
and are not native-expansion opportunity counts. Ordered binary normalization
gives 102 distinct keys, fourteen repeated; this does not establish a profitable
persistent graph cache. Diagnostic reachability is uncapped, unlike the policy.

Seven untimed empty-archive checks preserve baseline, rejected unfused and final
compiler results. Old case 44 reduces propagation visits **5,117 -> 4,435**, while
retaining its 22 native nodes. Old case 56 is unchanged and pays added recognition.
The unfused version increased node counts on old cases 40 and 55; final-pair reuse
removes that increase. Old graph case 35 falls **12 -> 10 native nodes** and
**1,942 -> 1,399 propagation visits**. These mechanism checks are separate from
fresh stream timings and do not reconstruct historical query prefixes.

## Fresh matched stream

Both policies use affine sessions and the preceding binary-subset recognizer.
The new sixty-query catalog excludes all inherited query and native roots.
Ten neighbours become known after preparation; two neighbours and all 48 family
cases remain unfamiliar. Both policies return **38 SAT / 22 UNSAT**. All 120
paired discovery traces and probe-counter sets agree.

| Per worker, except mean times/RSS | Binary subset | Clause cover |
|---|---:|---:|
| Native additions | 226 | 224 |
| Ordinary expansion calls | 132 | 124 |
| New compiled cover children | 0 | 6 |
| New native payload bytes | 293,179 | 291,005 |
| New affine extensions / bytes | 5 / 14,184 | 5 / 14,184 |
| Child propagation visits | 23,611 | 23,069 |
| Discovery propagation visits | 42,344 | 42,344 |
| Query seconds | 0.39359 | 0.38860 |
| Full cold replay seconds | 13.56349 | 13.56625 |
| Complete worker seconds | 27.98359 | 27.87186 |
| SQLite bytes | 84,561,920 | 84,557,824 |
| Compressed bytes | 6,463,477 | 6,462,729 |
| Mean peak RSS bytes | 759,504,896 | 769,032,192 |

Three covers in **two random-three-CNF queries, 32 and 52**, replace eight search
expansions with six compiled children. Actual storage falls by only **two nodes /
2,174 payload bytes**. Other categories have unchanged native node counts.
The recognizer pays 2,634 clause checks, 5,481 model-literal visits, 1,474 constructed
graph edges and 891 traversed edges. It makes 126 reachability queries and reuses
35 completed literal queries. Three residuals find a cover, 44 remain unresolved,
and seven have no model-filtered candidate. One final pair reuses eight path
edges; 38 selected path edges are checked before compilation. No reachability
budget or repair is needed on this finite stream.

Mean query time improves **1.27%**, with paired changes **−0.00823 / −0.00175 s**.
Mean complete-worker time improves **0.40%**, with changes **−0.01748 / −0.20598 s**.
Full historical replay remains about 13.6 seconds. Diagnostic sidecars grow about
5.4 KB and peak RSS grows about **9.53 MB**. These are small finite gains with a
memory tradeoff, not broad runtime or memory dominance. The rule remains optional.

## Preservation and next investigation

Resume `experiments/results/cnf-binary-clause-cover/checkpoint.json`. The union
contains **27,600 native keys / eighteen extensions**, preserving all **27,368
prior native payloads / thirteen extensions byte-for-byte**. It adds 110 native
and ten negative chain records to 5,230 inherited records. Comparator and alternate
history grow the union **569,344 SQLite / 66,325 compressed bytes**. Three roots
have alternative native proofs retained in the trial archives. The union keeps
its first payload for each key and adds six candidate-only native keys alongside
all 226 baseline additions.

Use `experiments.cnf_binary_clause_cover.AccountedBinaryClauseCoverSolver` for the
optional new leaf. Existing native readers still verify every resulting proof;
affine extensions retain the explicit `TerminalStore` reader. All 560 inherited
source hashes, 7,478 artifacts and 105 manifests remain unchanged. Validation
checks 240 chronological queries, twenty affine-publication counter records,
48 exhaustive family truth tables, warm answers and full historical replay of
every trial and the union.

**Next:** new random-three cases **32, 40 and 52** still cost **4,377, 3,020 and
2,880 child propagation visits**. Reuse partial binary backbones even when they
do not cover an entire clause: a checked forced literal may remove an expensive
branch and expose new binary structure. Price graph discovery, transport and
compiled child storage against the existing split choice. Graph cover discovery
still costs 24,645 propagation visits, versus 953 in child acquisition. Historical
replay dominates total runtime. Efficient handling of empty/uninformative binary
cores and unrestricted SAT remains open; this rule supplies no uniform bound.

All **1,196 tests** and **27 focused tests** pass. The 220-page manuscript builds
with a clean final log and all 64 existing proof blocks unchanged. The full suite
retains 44 existing SQLite resource warnings; focused tests have none. No new
Lean theorem is claimed.

Final source ledger: **567**. New manifest: **39 artifacts**. Next preservation
audit: **7,517 artifacts / 106 manifests**.
