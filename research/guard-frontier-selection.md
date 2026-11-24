# Spend the split budget on shared guard regions

The unfinished-origin census produced useful conditional proofs, but its
first-compatible tree closed only narrow assignment regions and made both
tested edits slower. This follow-up keeps all 395 templates and the existing
proof rules. It measures their guard structure, then changes which regions
receive the fixed tree budget. The result is mixed: one exposed edit improves
substantially against the preceding plan, the other regresses, and the ordinary
solver remains faster on both.

## Structure and selection rule

Within each origin bank, only ten captured guards have another captured guard
as a strict subset. There are five complementary pairs among the remaining
inclusion-minimal guards. These are syntactic relations within the saved banks,
not semantic minimality or an exhaustive account of possible simplifications.
A complementary pair here has identical other assumptions and opposite values
of one variable; the census does not construct merged certificates from it.
All 395 guards are distinct within their origin. Their 3,239 literal occurrences
give 2,512 edges in separate tries of sorted guards, revealing 727 repeated
prefix entries. This potential sharing is not a measured 22.45% reduction in
proof bytes: different guards still need their own source certificates, and
different origins cannot be merged merely because assignments look alike.

`experiments/cnf_guard_frontier.py` first checks every template and tests its
source clauses against the current target. Missing supports are excluded from
selection. All original templates remain persistent, including dominated guards
and alternative source supports: a later clause deletion may invalidate a
stronger exclusion while leaving a weaker one usable.

The builder begins with one open region. For every open region it considers
the compatible guards. A guard with no remaining assumptions closes that
region immediately. Otherwise, it offers the shortest remaining guard, breaking
ties by source-support literal volume and stable template index. Closing that
guard needs r additional splits. If the region already fixes d distinct
variables, the offer has uniform assignment mass `2^(-(d+r))`, and priority
`2^(-(d+r))/r`. Priorities use exact rational arithmetic.

The best fitting offer receives its whole chain of splits. Sibling regions
remain open and receive their own offers using compatible templates. Thus
already established decision prefixes serve later exclusions. The global
internal-node allowance is `floor((node_limit-1)/2)`, with `node_limit <= 129`.
Unfilled regions become explicit open leaves. The unchanged partial-plan
checker verifies every leaf assumption and the complete binary routing tree.
The unchanged native composer acquires unresolved regions and checks every
published proof. No new proof authority or database schema is introduced.

This policy is greedy, not an optimal tree or acquisition-cost model. Closing
an offer excludes only its certified guard cube inside an already open region;
the sibling regions account for every remaining assignment. The resulting
closed mass can be computed exactly from leaf depths. A larger measured mass
does not establish cheaper solving or coverage of more SAT instances.

## Census at the same output bound

| Origin | Previous closed assignment mass | New mass | Previous plan bytes | New plan bytes |
|---|---:|---:|---:|---:|
| 0 | 2.8473% | 14.9414% | 107,311 | 66,795 |
| 3 | 0.0254% | 12.0117% | 50,299 | 55,559 |
| 27 | 6.8146% | 45.7031% | 64,259 | 117,391 |
| 36 | 0.1208% | 7.2266% | 50,127 | 85,483 |
| 39 | 0.1081% | 1.6113% | 53,531 | 77,923 |
| 60 | 1.4587% | 32.1289% | 111,895 | 90,891 |
| 63 | 1.0178% | 27.3438% | 65,579 | 65,299 |
| 66 | 0.4873% | 23.7793% | 59,135 | 84,307 |

Every plan retains open regions. These are selected Python plan-graph sizes,
including chosen certificate data, not process peaks or all retained history.
The new plans have 125--129 nodes and use 8--22 distinct templates. Construction
checks all templates, including ones not selected; larger output mass need not
mean smaller plan memory. The complete banks and acquisition costs from the
preceding census remain in place.

## Four controls and total cost

The protocol retains all eight origins and the same two exposed target edits,
28 and 64. Four alternating serial repetitions compare ordinary native solving,
the previous supported tree, the new tree with all leaves open, and the new
supported tree. Every worker restores the same causal prefix from before the
edit. Neither a later repeat nor the cumulative union supplies answers. New
bank loading, containment, certificate checking, selection and tree construction
are inside solve timing. The open arm performs the same construction before
erasing its certificates.

The two new arms use the same composer, budget and finish-on-stop publication.
The ordinary solver has a different session handoff and abort-on-stop policy;
its comparison is an overall route diagnostic. The previous native and old-plan
controls reproduce their earlier counters and all six authority-table payloads
exactly. No tests or profiling run concurrently with the timed workers.

| Target | Ordinary solve, s | Previous plan, s | New tree, open leaves, s | New supported plan, s |
|---|---:|---:|---:|---:|
| 28 | 0.57628 | 1.01138 | 0.92879 | 1.05851 |
| 64 | 0.63441 | 1.00094 | 0.73161 | 0.72692 |

Against the previous plan, the new plan saves **27.38%** solve time on target 64
but adds **4.66%** on target 28. All four target-64 solve pairs improve; three
target-28 pairs regress. Complete-worker means change from 17.20067 to 16.56778
seconds on 64 (-3.68%) and from 7.55523 to 7.60639 seconds on 28 (+0.68%).
Worker time includes restoration, setup, solving, complete cold replay,
serialization and archive compression. Imports, source hashing and initial
case loading remain outside the timer. Earlier source capture and extraction
remain additional acquisition costs.

The new-tree ablation matters. Supports alone save only 0.64% solve mean on 64,
with mixed pair signs, and add 13.97% on 28. Relative to ordinary solving, the
new supported route costs 14.58% more on 64 and 83.68% more on 28. The useful
target-64 improvement is mainly associated with a changed branch order; it is
not evidence of a general certificate-reuse speedup. No default changes.

All four routes stop on both targets at 256 native dispatches. The new plan
uses 19 support leaves on 28 and four on 64, compared with 31 and 15 in the
old plan. Larger global closed mass therefore does not even imply more support
leaves reached before the stop. On 64, two open-region acquisitions consume
122 and 69 dispatches. The first completes a negative cofactor; the second
remains unresolved. They contain 152/151 variables and 613/600 clauses before
their local search. These counts identify unresolved work; they are not a
wall-time decomposition.

The final database for 64 falls from 143,507,456 to 140,926,976 bytes (-1.80%),
while 28 falls from 59,670,528 to 59,437,056 bytes (-0.39%). The same new trees
without supports retain 140,906,496 and 58,511,360 bytes. Thus support publication
still increases storage relative to that ablation. Raw archives preserve every
alternative checked acquisition.

## Bounds and next target

For C templates, maximum guard length g, maximum support clause count M and
output-node bound K, at most O(K) open-region offers are formed. Each can scan
C guards, sort their remaining assignments and evaluate support sizes, giving
O(K C (g log(g+1) + M)) word work for these scans. Copying contexts adds
O(K D), where D is the largest constructed path depth, at most K/2. Input
copying, source membership and certificate verification are additional. Heap maintenance adds
O(K log(K+1)) comparisons of rational scores whose bit lengths grow with guard
length. Literal encoding and integer arithmetic costs remain explicit
qualifications to the word account.

The copied bank, heap candidate lists, contexts and construction transients
remain outside the output-tree bound. They can require the full certificate
bank plus O(K(C+g+D)) bookkeeping words. Plan retention and native proof history
are separate costs. Most importantly, open-region acquisition still has no
uniform polynomial bound for arbitrary SAT.

The next target is to use these checked exclusions where ordinary search
already reaches an applicable context, instead of imposing a separate tree.
Existing `cnf_trace_learning.py` and `cnf_probe_learning.py` already support
checked source implications in bounded learning. Their binary implications do
not by themselves implement clauses excluding arbitrary multi-assumption
guards. Audit and extend the existing source-checking and lifting machinery
before adding such clauses; reject circular justifications and invalidate
deleted supports. Keep this tree and its ablation as controls. A fresh,
unlabelled evaluation and automatic origin recognition remain necessary.

A narrower first candidate can reuse `cnf_whole_lookahead.py`: when an ordinary
context already implies every guard assumption except one, that last assumption
offers a failed-literal probe. First census such opportunities before changing
search. Bind source variables to the actual residual, verify the excluded child
with existing native unit certificates, and keep the existing split/model lift.
The remaining branch still requires acquisition. Price guard matching and
coordinate maintenance, and exclude proposals already tried by ordinary probing.
This opportunity has not yet been measured or implemented.

Shared source restriction and unit-extraction prefixes remain the second cost
opportunity. Simple guard subsumption alone has limited headroom in this bank.
The two failed developmental inspections are preserved: a test supplied an
unsorted clause to a canonical-source helper, and an initial display tried to
parse a version-prefixed native key as raw JSON. Corrected checks use normalized
sources and reconstruct cofactors from their source and context.

Artifacts and the resumable checkpoint are in
`experiments/results/cnf-guard-frontier/`; restore with
`experiments.cnf_archive_parts.restore_archive`. Both native readers audit every
distinct trial archive and every new cumulative node with its dependencies.
Every earlier authority payload remains unchanged; previous full-history and
partition audits remain bound by verified manifests rather than being rerun.

The cumulative union adds 787 native records, reaching 157,898; the other five
authority tables are unchanged. The database grows by 13,303,808 bytes to
2,061,574,144 bytes, and compressed history grows by 949,398 bytes to
149,633,893 bytes. This combines both new comparison policies and is not the
memory cost of a single expansion. Every earlier payload is retained exactly.

All 1,715 full-suite tests and 71 focused tests pass. The full suite retains the
preceding 44 SQLite resource warnings; the focused suite has none. The 257-page
manuscript builds without warnings and all 64 earlier proof environments are
unchanged. No Lean definition or proof changed in this step.

To reproduce, use a new output directory with `prepare`, `census` and `run`
in `experiments/compare_cnf_guard_frontier.py`, followed by
`experiments/validate_cnf_guard_frontier.py`. Preserve the saved directory.
