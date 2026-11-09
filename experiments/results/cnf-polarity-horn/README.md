# Checked terminal Horn renaming: 35 leaves become 29 source closures

Implementation checkpoint **86d603b**. The same **1,497 inputs** and budgets
(depth two; four conditioning, probe and learning candidates) compare the
one-pass inventory with an additional, independently checked terminal renaming.
The ordinary SAT solver is unchanged. This is broader structural coverage, not
29 previously undecidable SAT queries.

All **35** positive leaves from the previous saved frontier close in the targeted
integration test. Full ancestor recomposition closes **29 additional sources**,
all satisfiable, with no lost closures. Non-tiny closure rises **869/985 ->
898/985**. Sources still unresolved fall **116 -> 87**; selected distinct unresolved
leaves fall **148 -> 106**, with **33,651 -> 32,404 literal occurrences**. The selected
plans change when an earlier alternative closes, so the global leaf difference
is not simply 148 minus 35. Full acquisition creates 188 checked renaming edges;
every edge's independently solved endpoints agree, and every child model lifts.

| Cost / retained state | Baseline | Terminal renaming |
| --- | ---: | ---: |
| Discovery, checking and persistence (s) | 84.99193 | 80.78495 |
| Total, including ordinary solver and root lifts (s) | 126.02211 | 122.78419 |
| Ordinary solver time (s) | 40.95733 | 41.92352 |
| Cold complete archive replay (s) | 54.89246 | 51.32492 |
| Warm inventory replay, no insertions (s) | 0.26877 | 0.29138 |
| Fresh SQLite archive (bytes) | 437,620,736 | 417,370,112 |
| Pattern nodes | 25,047 | 22,071 |
| Logical pattern-node bytes | 179,395,726 | 165,625,292 |
| Logical source-binding bytes | 6,032,748 | 6,375,558 |
| Six-case Python peak (bytes) | 24,073,154 | 20,286,004 |
| Six-case Python retained (bytes) | 23,447,581 | 19,660,919 |

Discovery falls **4.95%**, total **2.57%**, cold replay **6.50%** and fresh SQLite
**4.63%**. Warm replay and ordinary-solver time regress. These are single sequential
synthetic-corpus samples, with no significance or universal speed claim. Python
allocation covers the same six earlier cases, not native SQLite, RSS or full-corpus
peak. Only the gains' discovery sum falls 8.62578 -> 2.90980 s; this selected subset
must not replace the full comparison.

## Recognition, checking and persistence

The policy attempts 3,233 exhausted leaves: **188 recognized**, **3,045 excluded**,
zero cap stops. It constructs **1,183,603 auxiliary pairs**, checks certificates
6,466 times and charges **3,695,682 source-literal visits** across discovery and
checking. Successful flips occupy 10,517 JSON bytes; negative source-linked paths
occupy 424,918 bytes. They do not persist the quadratic auxiliary pair formula.
Original sources, old failed attempts, child records and full canonical keys
remain charged. Most calls exclude the class, so negative evidence is essential.

A positive certificate reconstructs a Horn child and an exact model lift.
An auxiliary contradiction excludes only renamable-Horn membership. It does not
certify original UNSAT. Pair limits produce an explicit unresolved result. The
[correctness and resource account](../../../research/polarity-horn.md) gives the
reduction, involution, proof boundary, source invalidation and per-attempt bounds.
Recognition is established prior work; the contribution here is its integration.

The old archive is preserved and the new policy has distinct keys. The baseline
recreates the [previous archive](../cnf-implied-subsumption/archive-implied.sqlite3.gz)
byte for byte. The [new archive](archive-polarity.sqlite3.gz) has raw SHA-256
`04ab610d1867896b47e05a91977302764cc63b3b160a9b5b371776a1cb11232c` and compressed
size **28,167,033 bytes**. Retaining both means **854,990,848 raw bytes** for these
two snapshots alone, not a reduction of total historical retention. Full
mixed-policy migration size is unmeasured; small coexistence tests preserve old
rows exactly. Both audits verify all alternatives, source bindings and all 21,838
ordinary solver certificates with empty ephemeral caches and unchanged database
bytes. Warm replay inserts neither nodes nor sources (1,465 distinct bindings).

## Remaining discovery and cost gap

All **106** selected remaining leaves have checked exclusions from the renaming
class; none stopped at the pair cap. Of these, 92 have maximum clause width three,
13 width four and one width eleven. The 87 unresolved sources consume **57.02871 s**,
or **70.6%** of candidate discovery time. Closing the 35 small leaves explains only
a modest part of the remaining literal interaction.

A separate checked probe normalizes and tests all original inputs in **0.57908 s**:
555 recognized, 941 excluded, one capped. Every recognized root already closed
under the baseline. In particular, **none of the 29 new closures comes from a
whole-source Horn renaming**; they use exposed residual structure and existing
composition. Empty-clause normalization may collapse the original syntax, so the
root counts describe normalized inputs. This is a read-only opportunity probe,
not an implemented earlier-routing experiment or a total-cost saving claim.

Current source 1448 is the slowest unresolved discovery query. A separate
instrumented acquisition spends 1.76956 s. The largest named own-time costs are
reconstruction (909 calls, 0.16950 s own / 0.24526 s cumulative), normalization
(566 calls, 0.12614 / 0.32228 s) and indexed subset certificates (118 calls,
0.11573 / 0.15694 s). Polarity discovery itself has 31 calls / 0.04967 s cumulative,
and checking 62 / 0.02690 s. Nested cumulative costs cannot be added.

The next coverage experiment should use source-linked auxiliary conflict paths
to identify shared obstruction variables or small interfaces, then test exact
conditioning/component decomposition at matched budgets. Renaming again on the
same remaining leaf cannot help: its exclusion is already checked. Earlier cheap
recognition may reduce acquisition on already-covered roots, but does not alone
explain the unresolved frontier. Normalization/reconstruction reuse is a supporting
cost opportunity. No small backdoor or uniform polynomial SAT bound follows.

## Validation and reproduction

All **441 Python tests** pass, including 3,816 exhaustive formula recognition
checks, all saved leaves, exhaustive small decomposition/model checks, random and
signed edits, forged certificates, caps and cold/mixed-policy persistence. The
full Lean build audits **4,136 declarations / 1,977 theorem declarations**; new
lemmas prove polarity evaluation and SAT/UNSAT transport, not the Python checker.
The manuscript retains all 59 earlier proof blocks and adds one proposition/proof.

`report.json` holds all cases, rows, archives, frontiers, 78 code fingerprints,
memory measurements and separate every-edge diagnostics. `summary.json` contains
paired totals and the 29 exact gain indices. `mechanisms.json` binds its input
report and analysis script, retains every original-root certificate and the
separate profile. Full timing includes preparation, recognition, checks,
serialization, persistence, ordinary solving and root lifts. Input loading,
summary walks, compression/hashing, initialization, all-edge diagnostics and
cold replay are excluded or recorded separately. The
[pilot](../cnf-polarity-horn-pilot/README.md) remains retained, including its timing
contamination and exact source snapshot.

```sh
python3 experiments/compare_cnf_polarity_horn.py --output /tmp/polarity-full
python3 experiments/analyze_cnf_polarity_horn.py /tmp/polarity-full
python3 -m unittest discover -s solver -p 'test_*.py' -q
cd formal
lake build
```
