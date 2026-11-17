# Separate conditioned-core reuse from the choice of partition

Conditioning stored negative cores can expose useful missing clauses after guards
have restricted a target. This experiment implements checked acquisition of the
conditioned core and prices it against directly proving the same strengthened
premise. The direct control then solves exactly the same partition branches.
The comparison shows a branch-choice gain on case 43, but no branch-solving gain
from the additional cofactor certificate on these three historical cases.

## Acquisition and validity

A projection binds the checked negative parent in source coordinates, the exact
partial assignment, the restricted clauses and their canonical native root.
Cold checking requires both parent and cofactor certificates. It performs no
search or publication. A shared canonical identity alone cannot establish that
the clauses use the intended source variables.

The initial acquisition gate permits an absent cofactor only if it is two-CNF.
That gate correctly rejects case 43's seven-clause cofactor, which contains
ternary clauses. The rejected run and its completed baseline remain retained.
The extended gate first propagates units: it accepts a conflict, or a residual
whose clauses have width at most two. Its retained trace is checked by the
unchanged native verifier during publication. Unknown wider residuals are
rejected before search or insertion. Existing checked native cofactors remain
reusable regardless of width. Case 43's cofactor is refuted after 23 propagation
literal visits and acquired as one native row, with no expansion call.

The parent establishes provenance, not free native acquisition. Projection,
parent reads, normalization, trace checking, cofactor storage and strengthened
premise publication all remain charged. The partition still needs checked
negative branches or a lifted SAT witness. Recognition of a unit-exposed
two-CNF cofactor gives no efficient algorithm for every remaining target.

## Matched historical comparison

The fifteen arms restore the exact prefixes before cases 43, 172 and 70 in the
earlier stream. They repeat ordinary preparation and both accepted guards.
Each case tests baseline solving, conditioned-core acquisition and direct
premise acquisition, with forward and reverse missing-clause orders. Results
from later queries or the new union cannot assist any arm. Candidate discovery
is inherited from the earlier full-bank probe, whose roughly 32,000 restriction
literal visits per case are a separate cost; it is not a free selector.

| Case | Method | Expansion calls | New native rows | Added native bytes |
| --- | --- | ---: | ---: | ---: |
| 43 | Baseline | 10 | 10 | 9,798 |
| 43 | Conditioned, forward | 7 | 9 | 7,170 |
| 43 | Direct, forward | 8 | 8 | 6,932 |
| 43 | Conditioned, reverse | 6 | 8 | 9,035 |
| 43 | Direct, reverse | 7 | 7 | 8,797 |
| 172 | Baseline | 9 | 9 | 13,839 |
| 172 | Conditioned, forward | 13 | 14 | 20,797 |
| 172 | Direct, forward | 14 | 14 | 20,768 |
| 172 | Conditioned, reverse | 8 | 9 | 13,597 |
| 172 | Direct, reverse | 9 | 9 | 13,568 |
| 70 | Baseline | 4 | 4 | 5,978 |
| 70 | Conditioned, forward | 5 | 6 | 8,028 |
| 70 | Direct, forward | 6 | 6 | 8,002 |
| 70 | Conditioned, reverse | 5 | 6 | 7,833 |
| 70 | Direct, reverse | 6 | 6 | 7,807 |

All six conditioned/direct pairs have identical branch roots, branch proof
payloads and branch expansion counts. The conditioned route adds one row and
238 native bytes in case 43, and 29/26 bytes in cases 172/70, respectively.
Its smaller expansion counter reflects trace/subset publication instead of
ordinary expansion calls; this is still acquisition, checking and storage.

The case-43 partition offers a tradeoff: direct reverse minimizes rows among
the tested arms, while direct forward minimizes native payload. Case 172's
missing units are exactly the negation of an existing clause `[40,50]`: this
partition is an ordinary clause split. Forward order regresses sharply. Both
case-70 orders regress. Testing all twelve alternatives costs **94 expansion
calls and 102 row insertions**, compared with 23/23 across the three baselines.
Posthoc minima are neither a deployed policy nor an affordable discovery method.

Native bytes are not total memory. Case 43's reverse direct arm lowers native
payload, but serialized delta plus decision grows **29,688 -> 29,905 bytes**;
forward direct reduces it to 28,087. Case 172's reverse direct record grows
34,026 -> 35,266 bytes despite a small native reduction. No peak live-memory
measurement was made. Complete single samples range from 6.37 to 6.80 seconds,
including 5.20--5.49 seconds of cold replay and 0.76--0.99 seconds of preparation.
They establish no stable total-runtime improvement. Runtime sources were frozen
before production; tests and posthoc analysis ran afterward.

## A narrower next target: remove unnecessary assumptions

A read-only probe slices the direct unit proofs backward and separately repeats
unit propagation after removing each of the two candidate assumptions. The
unchanged native verifier checks both full and sliced conflict traces. SQL is
read-only, expansion/publication are blocked and each original prefix is
unchanged. Failure of a unit probe is inconclusive.

| Case | One assumption already refuted with target | Propagation literal visits | Forced value | Remaining native child at prefix |
| --- | --- | ---: | --- | --- |
| 43 | `[-230]` | 283 | `230=true` | Absent |
| 172 | `[-40]` | 642 | `40=true` | Absent |
| 70 | `[-40]` | 241 | `40=true` | Absent |

The other single assumption in each case does not yield a unit conflict. In
case 70, backward slicing alone drops `[-110,-50]` and retains just the two
target clauses `[40,50]`, `[40,-50]` plus `[-40]`. Those target clauses already
imply `40`. For 43 and 172, slicing the saved two-assumption trace keeps both
assumptions, but recomputing propagation with one removed finds a different
conflict. Causal slicing is therefore not assumption minimization.

If `T AND C` is refuted, every model of `T` falsifies `C`; for a unit assumption
this justifies one forced assignment and one remaining restricted target.
The new probe publishes none of these smaller premises or children. Their
acquisition, composition and net savings remain unmeasured. The immediate next
experiment should compare checked single-assumption guards against these saved
baselines and partitions, reusing the probe traces during publication. Then
test a bounded recognizer on excluded queries. Wider assumptions, minimum
supports, cheap discovery and arbitrary-SAT complexity remain open.

## Persistence and validation

Resume [the checkpoint](../experiments/results/cnf-conditioned-core-exposed/checkpoint.json).
It preserves all **21,482 old native payloads** and contains **21,525 keys**.
Six alternative certificates remain in their arm deltas; original payloads take
priority during union construction. All 2,957 ordinary decisions, 414 previous
composed records, 15 new composed records and six projection records pass cold
checking. Composed/projection schemas remain separate from the ordinary catalog.
The union is 67,989,504 database bytes / 4,980,892 compressed bytes, versus
67,891,200 / 4,970,840 previously; this includes all acquired alternatives' new
keys rather than a selected future policy.

All **1,057 tests**, including exhaustive partial assignments of unsatisfiable
two-variable CNFs, and 17 focused tests pass. The full suite retains 44 existing
SQLite ResourceWarnings; focused tests emit none. All **451 prior source files,
4,916 artifacts and 85 manifests** pass preservation. Four frontier ready/pending
counts remain 131/39, 138/69, 81/95 and 81/122; structural authorities are unchanged.
The 64 prior manuscript proof blocks remain unchanged. No new Lean theorem,
fresh-query coverage, global minimum-cost or unrestricted-SAT guarantee is claimed.
