# Positive cores reduce redundant expansion work

8 November 2026. This is a checked extension of the research CNF candidate, not
a change to the production solver or a uniform polynomial solution for SAT.
The report retains **39 matched static inputs, four nine-query histories,
450 decisions and 86 compressed result archives**. Both modes receive the same
queries, with acquisition, warm reuse and cold reconstruction measured separately.
All answers agree with the expected labels. All **179 earlier candidate archives**
also reload with unchanged row digests and zero new expansions.

## Pattern and invariant

If a required positive clause C is contained in D, D is redundant. Process
positives in increasing length, index retained clauses by a least frequent
literal, and check full containment before deleting any clause. Every deletion
records a retained source-clause witness. The reduced core gets its own exact
normalized key. Negative source nodes retain the witnesses and refer to a checked
negative core; positive source nodes retain a full source witness. No old key or
certificate changes its meaning.

The inclusion-minimal positive members of a laminar family are disjoint. With
complete negative exclusion cliques this exposes the existing matching leaf.
Crossing redundant supersets also work when their minimal members are disjoint.
Irreducible positive overlap is retained: the indicator encoding of arbitrary
SAT still prevents drawing a universal bound from this recognized class.

This is standard syntactic subsumption, as described in Section 3 of
[Een and Biere, SAT 2005](https://www.cs.toronto.edu/~fbacchus/csc2512/Readings/EenBiere-SAT05.pdf).
The contribution of this experiment is the checked integration and accounting
in our candidate, not the invention of subsumption or a new general SAT method.

## Matched static acquisitions

`previous_matching` disables only the new reduction, reproducing the preceding
portfolio. `positive_core` enables it. The first 26 cases retain the previous
repeated/novel component, 2-CNF, pigeonhole and seeded 3-CNF controls. New cases
add nested unions of positive choices, crossing redundant supersets, and a
satisfiable irreducible-overlap counterexample.

| Input | Prior nodes | Core nodes | Prior logical bytes | Core logical bytes |
| --- | ---: | ---: | ---: | ---: |
| Laminar pigeonhole, 3 holes | 8 | 2 | 4,848 | 1,359 |
| Laminar pigeonhole, 4 holes | 11 | 2 | 13,074 | 2,711 |
| Laminar pigeonhole, 6 holes | 17 | 2 | 64,065 | 7,918 |
| Laminar pigeonhole, 8 holes | 23 | 2 | 201,735 | 17,538 |
| Laminar SAT matching, size 8 | 9 | 2 | 52,420 | 11,992 |
| Laminar SAT matching, size 16 | 17 | 2 | 953,804 | 107,116 |
| Crossing redundant supersets, 8 holes | 23 | 2 | 183,164 | 15,872 |
| Irreducible positive overlap, 5 variables | 4 | 4 | 925 | 925 |

Two nodes mean one source record and one reusable matching core. Recognition,
key construction and source payload still grow with the input. All normalized
CNFs, modes, counters, timings and archive hashes are in `report.json`.

## Growing histories: reuse across different source formulas

Each history starts from one matching core and appends eight clauses. Each new
clause contains a retained positive choice plus a fresh variable. These are
different growing formulas, not repeated identical queries or mere renamings.
The new variables can be false; the original requirements already imply every
added clause. Every older archive row is compared byte-for-byte after each step.

| History | Prior total new nodes | Core total new nodes | Prior final logical bytes | Core final logical bytes |
| --- | ---: | ---: | ---: | ---: |
| UNSAT, 4 holes | 254 | 9 | 225,401 | 13,699 |
| UNSAT, 8 holes | 23,046 | 9 | 84,546,940 | 82,514 |
| SAT, size 4 | 62 | 9 | 32,814 | 7,449 |
| SAT, size 8 | 211 | 9 | 611,694 | 49,007 |

For all four optimized histories, the first query acquires the core and every
later query adds exactly one source record, with no further matching search.
On the eight-hole UNSAT history, the preceding portfolio expands
1, 23, 162, 728, 2,147, 4,076, 5,191, 5,359 and 5,359 nodes. The new mode expands
one at each step. Its final cold replay verifies two nodes, versus 5,359 for
the preceding portfolio; cold SAT replay verifies one source model in both modes.
Every exact warm/cold replay creates zero new nodes.

The eight-hole UNSAT history takes 30.286 seconds of summed acquisition time in
the preceding mode and 0.01983 seconds with the core reduction in this run.
These are single samples on a synthetic ablation, not competitive SAT timings.
The associated final SQLite files occupy 170,311,680 and 143,360 bytes. Logical
bytes count serialized keys plus records, not RAM. All 86 snapshots total
177,430,528 raw SQLite bytes and 7,527,881 gzip bytes. Snapshot compression is
offline archival compression; it is not used for live query execution.

## Costs and retained failures

For p positive clauses of width at most w, discovery has at most O(p^2) candidate
tests and O(p^2 w) containment probes, plus the full source scan, frequency/set
construction, sorting and index/bit costs. Direct witness checking charges the
sum of deleted and supporting clause widths. There is no free semantic-equivalence
lookup. The last optimized eight-hole extension still charges 720 discovery
literal occurrences, 80 posting lookups, eight candidate tests, 64 containment
probes, 136 containment-check literal occurrences and 12,646 serialized key bytes. It
inserts 9,776 logical bytes despite doing no new core search. Cold checking
also reconstructs and verifies the source and matching core.

Reduction is **not always beneficial**. In seeded case 20 (12 variables), it
increases acquisition from 12 to 20 nodes and logical storage from 12,029 to
18,637 bytes. Cases 17, 21 and 24 also gain wrapper nodes without enough search
savings. Thirty-two novel components keep the same 107 nodes and 40,719 bytes,
with extra discovery work. The irreducible-overlap case keeps four nodes and
925 bytes. All these results are retained. A policy that enables reduction only
when it exposes a useful leaf or a previously acquired core is a next experiment,
not an established universal improvement.

The current implementation rebuilds the containment index and stores a full
record for each source. A linearly growing source can therefore accumulate
quadratic copied payload over its history even with an unchanged core. Negative
wrappers also repeat the full core key and store containment witnesses. A source
delta representation and incremental witness index could reduce these costs,
but must handle deleted/changed support explicitly. Changing conflicts or
removing a supporting clause requires fresh reduction and exact identity checks;
a retained test changes UNSAT to SAT after such a deletion.

Reported solve time includes normalization, discovery, checking, serialization,
SQLite lookups/writes and the final full-archive size scan. Initialization is
reported separately. Test execution, archive compatibility auditing, row digests,
gzip snapshots and report writing are outside these solve timings. The benchmark
ran after the Python and Lean suites completed. No process peak-RSS, competitive
CDCL comparison or machine-level Lean cost refinement is provided.

## Validation and reproduction

All **224 Python tests pass**. The new tests check every one of the 2,048
positive-clause families of widths 2--4 on four variables against all 16
assignments, plus deterministic cores, prepared SAT/UNSAT reuse, cold replay,
source witness reconstruction, malformed/circular containment certificates and
changed dependencies. Existing random/general CNF and exhaustive small tests
still pass. Lean checks three new semantic lemmas and audits **4,066 declarations
/ 1,928 theorem declarations**, with only the permitted standard axioms.
The Python code, parser, persistence and checker remain outside the native Lean
acceptance path.

```sh
python3 -m unittest discover -s solver -v
PATH=/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin:$PATH lake -d formal build OracleMachines
python3 experiments/compare_cnf_subsumption.py --output /tmp/oracle-positive-core-new-run
```

The output directory must not exist. `report.json` records the preceding commit
and exact candidate/driver SHA-256 values. `tests.log` and `lean.log` retain the
completed check outputs. Old compressed archives and production results were
not rewritten.

The manuscript adds Proposition 12.28 and the measured benefits and regressions.
All 39 older proof blocks are preserved. Its 79-page PDF builds without warnings;
the revised pages and bibliography were rendered and visually checked.
