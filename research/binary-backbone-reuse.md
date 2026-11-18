# Reuse partial binary backbones before splitting

A failed whole-clause cover can still contain useful checked implications.
A path `l → ¬l` in the binary clauses entails `¬l`. Consequently the full source
is satisfiable exactly when its cofactor under `l=false` is satisfiable. The new
optional policies reuse these paths, rather than discarding them when some other
literal prevents a whole-clause cover. Whole covers retain priority.

The recognizer makes no additional reachability queries on a given residual;
it inherits the eight-root/four-wide-clause policy and returns successful paths
from otherwise unresolved covers. Changed child sources can change total discovery
work. Every selected path is checked against the full source's binary clause
indices. The surviving cofactor is searched normally. A SAT result lifts to a
checked full-source model and needs no excluded-branch certificate. If the survivor
is UNSAT, retained path reasons compile directly into a unit-refutation trace for
the excluded cofactor. This compilation does not rerun propagation or search.
An ordinary native split proof combines both negative children. Existing native
readers remain the authority; no new proof format is introduced.

## Choosing when to reuse a path

Two policies are retained. **First** chooses the first successful path returned
by the cover search. **Frequency** accepts a path only if its variable has the
largest total literal frequency, breaking ties by smallest variable identifier.
That is the ordinary splitter's variable rule. It is an admission gate, not a
guarantee of identical control flow: ordinary solving may first simplify,
recognize a leaf or decompose the source. Neither policy guarantees minimum cost.

In sixty separate empty-archive mechanism checks on the preceding source catalog,
first reduces propagation visits **135,075 -> 125,509** but increases stored nodes
**619 -> 632**, payload **881,160 -> 903,225 bytes**. Frequency retains **618 nodes /
879,804 bytes** and 133,065 propagation visits. Old case 56 grows five -> seven
nodes under first; frequency leaves it unchanged. These untimed mechanism checks
have no shared preparation and are not historical-prefix comparisons. They retain
the regression rather than treating fewer expansions as sufficient evidence.

The initial negative-transport test wrongly expected the frequency gate to select
a low-frequency variable in a source with a separate, denser UNSAT component.
The gate correctly skipped it. The corrected fixture exercises that compiler
through first; separate tests still cover frequency hits/misses and both policies'
truth. The old test, protocol hash and failure explanation are preserved before
any production worker runs. No production results were overwritten.

## Fresh matched comparison

Six serial workers compare two opposite orders of cover-only, first and frequency.
The sixty new queries exclude all inherited query/native roots. Twelve neighbours
become known after preparation; all 48 family targets remain unfamiliar. All
policies return **42 SAT / 18 UNSAT**. Each candidate preserves all 120 paired
preceding discovery traces and probe-counter sets. Labels never enter selection.

| Per worker, except mean times/RSS | Cover only | First path | Frequency gate |
|---|---:|---:|---:|
| Native additions | 255 | 260 | 253 |
| Native payload bytes added | 351,260 | 352,723 | 349,493 |
| Ordinary expansion calls | 167 | 163 | 164 |
| New backbone proof children | 0 | 9 | 1 |
| Child propagation visits | 29,379 | 27,699 | 28,982 |
| Discovery propagation visits | 43,877 | 43,877 | 43,877 |
| Selected backbones | 0 | 11 | 2 |
| Positive lifts / negative splits | 0 / 0 | 2 / 9 | 1 / 1 |
| Query seconds | 0.33351 | 0.32412 | 0.32338 |
| Full cold replay seconds | 13.39064 | 13.33751 | 13.31080 |
| Complete worker seconds | 27.77028 | 27.78939 | 27.77590 |
| SQLite bytes | 85,229,568 | 85,241,856 | 85,225,472 |
| Compressed bytes | 6,536,252 | 6,536,875 | 6,536,192 |
| Mean peak RSS bytes | 787,038,208 | 784,523,264 | 769,753,088 |

All modes retain seven whole-clause covers with fourteen compiled children and
add four affine extensions / 8,927 bytes. Changes occur only in random three-CNF.
Frequency accepts two candidates, in cases 36 and 52, and rejects twelve other
residuals after 1,607 ranking-literal visits. It checks six path edges, transports
four source literals into one forced unit, and publishes one excluded child.
It saves **two stored nodes / 1,767 bytes / 397 child propagation visits**.
First adds **five nodes / 1,463 bytes**, despite four fewer expansion calls and
1,680 fewer propagation visits. Its nine compiled children remain real work.

Frequency improves mean query time **3.04%**, with paired deltas
**−0.01508 / −0.00520 s**. Complete-worker deltas are **+0.38675 / −0.37551 s**,
leaving the mean **0.02% higher**. First has mixed query signs and a 0.07% higher
complete mean. Historical replay and setup variation outweigh the small query
saving. Neither candidate establishes an end-to-end win. Frequency's trial SQLite
falls 4,096 bytes and gzip only 60 bytes; sidecars grow about 1.3 KB. Its observed
mean RSS falls about 17.29 MB, which is not a scaling guarantee. Both policies stay
optional, with first retained as a measured storage regression.

## Resource bounds and correctness limits

The earlier bounded reachability costs remain. The frequency gate adds `O(L+v)`
work and a frequency map when paths are available. Checking and transporting a
path of length `p` takes `O(p)` reason work; constructing, normalizing and binding
the excluded cofactor still reads the source. The transported proof stores a full
cofactor/key plus at most `p` unit reasons. Its independent native checker remains
charged. A cache hit may reuse an older, larger derivation, whose replay is also
charged. No fixed-point propagation or general solving occurs during new
excluded-child compilation.

The surviving cofactor can still be hard. At most `v` consecutive forced-variable
steps are possible, since each removes a source variable, but this does not bound
later unrestricted branching. Source/model copies, stacked pending evidence,
normalization, serialization, retained history and cold replay remain costs.
Persistent reuse is through native canonical keys; binary backbones are not yet
indexed across different whole sources. This is a sufficient structural rule,
not an efficient partition covering all SAT.

## Preservation and next target

Resume `experiments/results/cnf-binary-backbone/checkpoint.json`. It preserves all
**27,600 prior native payloads and eighteen extensions byte-for-byte**, reaching
**27,888 native keys / twenty-two extensions**. It adds 168 native and twelve
negative chain records to 5,350 inherited records. The union retains all three
policies, growing **712,704 SQLite / 78,123 compressed bytes**. Eight roots have
alternative native models/proofs retained in trial archives; first payloads remain
in the union. The checkpoint lists both optional solver classes explicitly; affine
extensions retain the `TerminalStore` reader. No default solver is replaced.

Independent validation checks **360 chronological queries**, 24 affine-publication
counter records, 48 exhaustive family truths, all warm answers and full historical
replay for every worker and the union. All 567 prior source hashes, 7,517 artifacts
and 106 manifests remain unchanged.

**Next recognition gap:** cover-oriented candidates omit useful split-variable
backbones. An uncapped posthoc census of the 253 new stored nodes finds 118 mixed
satisfiable binary cores: 43 have forced literals and 75 have none. Fourteen stored
sources have a forced frequency-selected variable that the current candidate
search misses. Six are ordinary split nodes whose recorded split variable matches
that variable exactly: cases **20, 28, 32, 44, and two residuals of 52**. Their exact
root hashes and forced literals are in `attribution.json`. The other eight include
seven models and one subsumption node, so fourteen is not an expansion-saving count.

Test one targeted implication query for the chosen split variable, using the
binary model to choose its opposite premise. Preserve the old cover budget and
charge extra recognition, path transport and proof storage; do not assume a win
from this uncapped diagnostic. New cases **32/44/56** still cost
**5,494/4,114/3,894 child propagation visits**; case 56 has no selected partial
candidate. Graph discovery costs 27,451 visits, versus 2,606 in acquisition.
Empty binary cores, the 75 cores with no forced literals, growing sizes and broader
encodings remain substantive coverage gaps.

All **1,204 tests** and **35 focused tests** pass. The 221-page manuscript builds
with a clean final log and all 64 existing proof blocks unchanged. The full suite
retains 44 existing SQLite resource warnings; focused tests have none. No new
Lean theorem is claimed.

Final source ledger: **574**. New manifest: **51 artifacts**. Next preservation
audit: **7,568 artifacts / 107 manifests**.
