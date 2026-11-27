# Conditioning before bounded Boolean buckets

Date: 27 November 2026. Parent: `448687f9`.
Evidence: `experiments/results/cnf-conditioned-buckets/`.

## Coverage gain and cost

Two conditioning levels resolve **6/10** exposed bucket-acquisition misses.
On a separately frozen panel, direct coverage rises **11/24 to 16/24** unique
synthetic constructions; four repeated queries improve **1/4 to 2/4** separately.
The unchanged fallback already decides all 38 queries. This expands a certified
acquisition family, not the set of SAT answers available to the whole solver.

Exact residual sharing reduces bucket discovery calls **158 to 149**, JSON
certificate-file bytes **1,437,097 to 1,373,023**, and mean complete cost
**1.59636 to 1.54155 seconds** (3.43%). Every matched order improves 2.16–5.18%.
However, fresh solving costs **0.33567 seconds**: the memo workflow is **4.59 times
as costly**. No production default changes. This panel supports a coverage gain
and a restricted reuse saving, not a general efficient SAT partition.

## Exact partition and reuse conditions

Each state first runs the preceding complete semantic-bucket method. If it
remains unresolved and has depth left, split on the most frequent variable,
breaking ties by canonical variable name. Restrict and normalize both cofactors,
then recurse. Two UNSAT cofactors prove UNSAT; either SAT cofactor provides a
model, lifted through the inverse normalization map and fixed branch value.
Unknown leaves give no verdict. The full source witness is checked again.

The memo key is the entire normalized residual plus remaining depth. All states
in one call use the same bucket policy; the memo is local to that root. It is not
valid to share arbitrary partial search results across different budgets,
policies or contexts. Normalization recognizes order-preserving renaming and
literal/clause ordering, not general variable/sign isomorphism. Each edge checks
its exact residual and strictly decreasing depth. Each leaf, including a partial
one, retains its full bucket program and witness dependencies. The verifier
checks each stored node once and checks every incoming edge. No cached discovery
status has authority on its own.

At conditioning depth `d`, a full tree has at most `2^(d+1)-1` bucket calls. The
DAG needs one call per distinct normalized residual-and-depth pair. This can be
much smaller when branches coincide, but it has the same exponential worst-case
bound. On the deliberately guarded full-cube test at depth two and bag width two,
seven states become three. That test is an invariant/control, not transfer
coverage evidence, and the explicit full-cube source is itself exponential.

The implementation explores both children even after a SAT child is found.
This keeps the matched partition comparison simple but may do avoidable work.
Certificates also retain partial bucket attempts at internal nodes. Shorter
SAT witness paths and smaller proof authorities are potential cost improvements,
not claims made by this experiment.

`cnf-conditioned-buckets-v1` is a separate experimental JSON format. Exact root
programs share within the stream under the same policy, including unresolved
roots; edits invalidate them. Every incoming warm or cold program is fully
checked. Both existing native readers audit fallback records, and two additional
cold passes use the same conditioned/bucket verifier, not independently developed
JSON verifiers. Native, equivalence, affine and Lean formats remain unchanged.

## Matched evaluation

The fixed policy is depth two, bag width eight and 262,144 reserved discovery
probes **per node**. Flat uses depth zero; tree and memo use the same larger
conditioning budget, and only memo shares residual states. At most seven bucket
calls are available per root. The probe allowance does not bound normalization,
pivot choice, planning, checking, runtime or memory. Flat wraps the previous
reduced-bucket method in the same new certificate/checking machinery; it is an
ablation, not a timing rerun of the preceding historical artifact.

The 24 frozen constructions contain 16 SAT and eight UNSAT inputs: random
three-CNFs at 10/13/17/21 variables, guarded duplicate cores and one-clause edits,
parity prisms and linked gates. Sparse names, signs and input ordering are
scrambled. Four repeated queries contain two SAT and two UNSAT cases. Ten exposed
development cases contain eight SAT and two UNSAT cases. None of the new sources
normalizes to a source in the preceding panel. These are designed synthetic
controls, not a representative external benchmark; descriptions and independent
DPLL truth labels never guide solving.

Four cyclic process orders run all four workflows from empty archives with a
common fallback. Complete times include acquisition, recognition, checking,
evidence and SQLite writes, warm replay, cold replay and compression. Interpreter
startup, report metadata, panel generation and the preservation audit are additional.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | Certificate-file bytes | Native-record bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0 | 0.15841 | 0.01403 | 0.09788 | 0.33567 | 0 | 369,216 | 60,473,344 |
| flat | 0.07161 | 0.14941 | 0.04750 | 0.15931 | 0.50191 | 474,405 | 326,806 | 59,195,392 |
| tree | 0.46431 | 0.29807 | 0.23290 | 0.52022 | 1.59636 | 1,437,097 | 235,256 | 58,474,496 |
| memo | 0.44674 | 0.29142 | 0.22426 | 0.49723 | 1.54155 | 1,373,023 | 235,256 | 58,703,872 |

Certificate-file bytes include pretty-printed JSON. Compressed combined
SQLite/JSON packages occupy **73,230 / 73,952 / 77,400 / 77,242 bytes** in table
order. The 4.46% tree-to-memo certificate-file saving becomes only a 158-byte
combined compressed saving. Diagnostic files additionally use 0 / 6,153 / 21,751 /
20,605 bytes. Reports, historical experiments and database/container overhead
are additional. Memo RSS is slightly above tree RSS; no peak-memory reduction
follows from state sharing.

Only **three complete guarded-twin constructions** (`c08`, `c10`, `c12`) have
internal memo hits, one each. Those three hits avoid nine total node acquisitions
because each skips an entire depth-one subtree. Discovery on those three cases
falls 43.68%; on the other 35 queries it regresses 0.65%. The edited twin controls
do not give those exact identities. No unobserved semantic-equivalence reuse is
assumed. Cold checking remains the largest measured phase (0.49723 s), followed
by discovery (0.44674 s); warm replay adds 0.22426 s.

## Remaining structural obstruction and next target

Four exposed inputs and eight new unique constructions remain outside the family;
two repeated queries add no new gap. The **12 unique remaining sources** contain
**41 unresolved depth-zero leaves**: 24 have width nine and 17 width ten. Nineteen
stop before any bucket work, while 22 make some progress before width grows past
the cap. Thus conditioning partly removes the initial obstruction, but does not
keep subsequent interactions small. All fallback answers remain available.

Next investigate inexpensive exact combinations of small factors **before further
branching**, starting with complementary clause pairs and their unit consequences.
The observed guarded-twin identity `(C or x) and (C or not x) = C` suggests that
some repeated branches can be recognized symbolically without constructing both
cofactors. Charge unsuccessful recognition on the remaining random cores and
preserve the one-clause edits as invalidation controls. This is the next hypothesis,
not an implementation or an unrestricted small-width guarantee. Simply increasing
depth spends exponentially more acquisition work.

Tests cover all 512 two-variable clause sets, seeded mixtures, sparse witness
lifting, edited guards, unknown leaves, corrupted edges/buckets, exact shared-depth
identities and cold checking with discovery disabled. Resume
`experiments/results/cnf-conditioned-buckets/checkpoint.json`, key
`conditioned_buckets.remaining`. All 225 prior manifests, 36,689 artifact entries,
1,238 sources and 67 existing proof blocks are preserved. Five new source/test
files raise the source ledger to 1,243, and one restricted proof is added.

Validation: **2,250 full tests and 24 focused tests pass**. All sixteen measured arms and their complete/partial DAG certificates replay exactly, with three unique SQLite archives checked by both native readers. Existing SQLite ResourceWarnings remain in the full test log.
