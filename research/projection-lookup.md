# Discovering retained projection targets without a supplied match

2026-11-14. The previous projection bridge required two supplied endpoints. A new
experimental index finds that same connection from the source alone, by querying
all retained formulas under the current recognizer policy. It finds **no new
bridge among the 23 current unresolved frontier sources**. Coverage stays
**62/83**. This closes a target-discovery implementation gap while preserving the
negative result on the harder frontier.

The index is optional research infrastructure. It is not enabled in ordinary
expansion: its construction and storage cost are substantial, and this experiment
does not establish a total expansion saving from adopting it.

## Pattern and exact reuse condition

For a normalized CNF P, let M(P) contain its inclusion-minimal clauses: remove a
clause only when another retained clause is a proper subset of its literal set.
Use the existing anchored subset routine to construct this set. Keep the
projection's variable coordinates; do not renumber the remaining minimal clauses
again. Include support size and depth in the lookup signature, with the
recognizer policy shared by the whole index.

The known 28-variable target has **110 clauses**, but only **108** are minimal.
Looking up only the fully reduced formula would miss it. Both its minimal set
and the minimal set of the projected 29-variable source are identical. Indexing
those sets finds the actual retained, nonminimal target.

This filter matches the previous checker's deletion rule. For finite clause sets
T contained in P, every clause in P minus T has a proper subclause in T if and
only if M(P) equals M(T). In one direction, a minimal clause of P cannot have
been removed, and a clause minimal in T cannot have a smaller clause in P:
such a clause, if removed, would itself have a still smaller retained witness.
In the other direction, descend from any removed clause to a minimal clause of
P. Equality of the minimal sets puts that strict subclause in T. This is a
syntactic characterization of the existing rule, not a characterization of all
logically equivalent CNFs.

A signature hit is only a proposal. The checker reloads the actual acquired
endpoints, checks their policy, depth and variable map, reconstructs all opposing
clause pairs and checks a retained proper subclause for each deletion. It also
requires T to be a subset of P. Equal signatures caused by a hash collision,
changed index contents or broader equivalence do not replace those checks. The
positive proof still requires an independently justified target.

## Experiment and costs

The preserved authority has **41,912 patterns**. The new catalog scans every key
and indexes the **19,841** under the current policy, across its three depths.
They yield **17,801 distinct signatures**. It uses the existing SQLite search
index and compressed full keys; it does not scan stored proof payloads to build
its proposal catalog. Accepted endpoint payloads are checked normally.

The query batch contains the **23 unlabelled current frontier sources** from the
saved scheduler selection and the previous successful source as a control.
Neither target identifiers nor SAT/UNSAT answers are supplied to search. Each
source permits at most 64 variables, 64 opposing pairs per variable and 64 target
proposals. Three serial repetitions alternate mode order. The control scans the
same prepared signatures, uses the same order and limits, and invokes the same
proof checker. The scan reads SQLite rows; a compact in-memory scan is untested.
Only candidate lookup differs; this is not a comparison against a whole SAT
solver or against repeated construction of every candidate signature.

| Quantity | Scan prepared catalog | Indexed lookup |
|---|---:|---:|
| Mean 24-source batch time, seconds | 1.55276 | 0.87112 |
| Full catalog entries visited by the scan | 535,707 | 0 |
| Signature queries | 27 | 27 |
| Candidate targets passed to checking | 1 | 1 |
| Accepted bridges | 1 | 1 |
| Unresolved frontier sources with a bridge | 0 / 23 | 0 / 23 |

The **43.90% lower batch time** concerns warm target discovery. It includes
projection, minimal-set construction, lookup, decoding and exact bridge checks.
All six runs return identical records. Source payload checking is prepared once,
in **0.09162 s**, before the matched runs. The process and OS caches are shared;
three repetitions provide no confidence interval or holdout evidence.

Index construction and commit cost **14.42661 s**. The SQLite file is
**28,110,848 bytes**, or **23,149,996 bytes** in the preserved gzip archive.
The complete new result directory, including the catalog, all six query runs,
proofs, validation and manifest, is **25,107,665 bytes** across 21 manifested
artifacts plus the manifest. Those bytes are additional to the unchanged
**772,972,544-byte** authority.
They are not a measure of peak RAM or a reduction in historical solver storage.
Reopening the compressed catalog, repeating the indexed queries and recording
the selected-source diagnostic takes **0.96767 s** with the already checked
source inventory. A cold reconstruction is validated separately.

The complete study takes **145.00455 s**, including **53.92432 s** restoring the
authority and **63.29684 s** preparing and checking complete original coverage.
These costs are outside the warm query means. The first build costs much more
than the **0.68164 s** saved by indexed lookup on one batch. Construction would
need amortization, narrower demand-driven indexing, or a substantially higher
reuse rate to justify adoption. Factoring the shared policy out of each stored
full key is also an obvious remaining space opportunity.

The total **967 variable proposals** leave **95** over the opposing-pair cap.
Of the remaining 872 projections, **845** still exceed the final two-clause
growth allowance even after subsumption. Only 27 reach lookup, and only the
known control matches. The present obstacle is mostly the restricted projection
shape and lack of acquired matching targets, rather than lookup speed alone.
A missed match does not establish hardness or absence of another decomposition.

## Concrete next expansion

The selected **37-variable / 151-clause / 455-literal** residual has one eligible
minimal projection: eliminate **variable 13**, then remove a redundant clause.
The raw projection has **154 clauses**; the minimal target has **153 clauses**
and **36 variables**, satisfying the final additive allowance of two. The ten
opposing pairs leave **470 literal occurrences**, up from 455; lower support
does not reduce every representation cost. No matching
retained target is found. Its exact normalized key is preserved in
`selected-diagnostics.json.gz`, SHA-256
`2689db3a9f1f850442aacef39eb4e6acd62bc431404592a129dc81b9695d94cf`.
This describes a candidate to acquire and classify, not an acquired proof or a
closed source.

The highest-priority next test is bounded acquisition of that target, with a
checked projection/subsumption edge and comparison against ordinary continuation
from the same seed. Determine whether it exposes useful structure or merely
moves unresolved work. Preserve the remaining ordinary probe options
**15, 18, 19, 20** and the existing split candidates. Avoid deploying the global
index by default on the strength of one previously known match.

## Persistence, bounds and validation

`cnf_projection_lookup.KernelIndex` stores compressed exact keys, not SQLite
rowids. It can reopen against a reconstructed authority. New acquired keys can
be added incrementally; duplicates are checked and do not overwrite earlier
entries. A different policy is rejected. Missing endpoint entries cannot close a
source. Omissions from a stale index only produce inconclusive misses, so current
coverage of the catalog must be audited separately when claiming search coverage.
The experiment's cold validator compares its key set with the entire current
policy snapshot and recomputes every minimal set using an independent subset
scan, without anchor postings.

For R indexed targets, construction includes normalization, subsumption,
compression and R SQLite insertions. Subsumption can require quadratically many
clause comparisons in the worst case. Indexed queries avoid an unconditional
R-entry scan, but a large equal-signature bucket can still require many visits,
including candidates rejected by the final clause-count filter. Projection,
normalization, failed matches and proof replay remain charged. The local search
caps do not bound how many expansion steps or retained formulas arbitrary SAT
will require. The index does not give a minimum-cost expansion theorem.

Resume the unchanged solver authority at
`experiments/results/cnf-projection-bridge/report.json` with its existing
restorer, five evidence lists **(1, 42, 156, 24, 1)** and separate bridge archive.
The new study is `experiments/results/cnf-projection-lookup/report.json`; its
`index` descriptor binds the optional catalog and its uncompressed hash. Its
`bridges` archive preserves the previous bridge, rediscovered without a supplied
target. No new pattern, reference proof or solver answer is added or removed.


All **194 regression tests pass**, including seven new tests for minimal-set
construction, automatic discovery, scan/index agreement, budgets, depth and
policy binding, restart, incremental insertion, stale or corrupted entries and
adversarial edits. Minimal-set construction is compared with the direct subset
definition on every formula with at most three distinct clauses over three
variables; the existing bridge tests retain their exhaustive semantic checks.

Independent cold validation takes **141.78499 s**: **57.57172 s** restoring the
authority, **15.99245 s** validating the entire index, **0.97903 s** repeating all
queries, and **64.08563 s** preparing/checking global coverage, plus other replay
and artifact checks. New recognition is forbidden throughout. It confirms all
six result sets, all 19,841 indexed keys, unchanged authority and zero admissions.
All **439 artifacts across fifteen earlier manifests** retain their hashes.

The manuscript builds to **156 pages**, without overfull boxes or undefined
references. All **64 prior proof blocks** remain unchanged. The new study's
report SHA-256 is
`9f13df361c5e9efd6308c71d3b157f6f43df396c883e7d8c3c259b2cb863d4af`.
Detailed validation, source fingerprints and artifact hashes are stored alongside
its report. The minimal-set argument is not a new Lean formalization.
