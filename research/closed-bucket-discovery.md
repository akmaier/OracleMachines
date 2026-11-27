# Unit closure and shared conditioned residuals

Date: 27 November 2026. Parent: `db843605`.
Evidence: `experiments/results/cnf-closed-buckets/`.

## Result and decision

Checked unit propagation after every conditioning assignment closes **6/20**
exposed acquisition gaps (five SAT, one UNSAT). On 24 frozen unique synthetic
inputs, direct coverage rises **12/24 to 17/24**; exact repeats remain **3/4**.
There are no coverage losses on this panel. The unchanged fallback already
supplies all 48 answers, so this expands a certified acquisition family rather
than the solver's answer coverage.

Sharing the simplified residual instead of duplicating its computation reduces
complete cost **4.22%** relative to a tree with the same per-cofactor units.
Together, closure and sharing reduce cost **9.17%** relative to the wrapped
root-only policy. Every paired order improves. The resulting pipeline still
costs **3.34 times as much as fresh solving**. It remains experimental; no
production default changes.

## Exact structure and transport

Each incoming cofactor is normalized, simplified by active units, and normalized
again. Its target identity is the **full normalized residual and remaining
conditioning depth**, under one fixed policy. Identical targets can share a
checked bucket/conditioning node. This is deterministic syntactic normalization,
not a general semantic-equivalence or graph-isomorphism oracle. Sharing is local
to a root program; exact complete root programs also share within the stream.

The incoming edge retains the original normalized cofactor, unit steps, residual
and target. A unit step is accepted only if its literal is an active unit. Replay
restricts all clauses independently of the discovery index. In the incoming
variable names, the invariant is

`cofactor = recorded forced literals AND inverse-renamed residual`.

Thus a shared residual witness lifts through **each edge's own** renaming and
forced assignments. Disappearing free variables can take arbitrary values. A
counterexample to putting forced values on the shared node is a guarded parity
core whose two branches force opposite guard values and then leave exactly the
same core. Both edges share the target but require different source witnesses;
swapping their recorded unit literals is rejected. The test preserves this case.

Every split is checked against both exact Shannon cofactors and decreasing depth.
A SAT child supplies a lifted parent witness; UNSAT requires both checked UNSAT
children. Unknown never supplies a refutation. All SAT edge transports are
checked, including those not chosen for the final witness. Reachability, node
identity, depth, bucket policy and the complete source witness are checked.
Discovery is disabled in cold-replay tests; replay does not call recognition.

Edits invalidate the affected incoming source and its unit evidence. Reuse is
allowed only after replay establishes the new edge's exact target; equality of
status, a digest alone, or equality before witness transport is insufficient.
Changing remaining depth or policy changes reuse identity. Every warm/cold load
checks the whole program. Native, equivalence, affine and Lean formats are
unchanged; `cnf-closed-buckets-v1` is a separate experimental JSON authority.

All modes retain root complementary folding. Thereafter `root` uses no per-edge
units and shares raw normalized cofactors; `tree` uses per-edge units without
memoizing nodes; `closed` uses per-edge units and shares their residuals. The
`closed`/`tree` pair isolates sharing. The `closed`/`root` pair includes both
closure and the changed sharing identity; `tree` is not a pure units-only
ablation of `root` because it also removes raw-cofactor memoization. The root
arm wraps the preceding policy in the new authority, not a timing rerun of an
old artifact.

Each newly visited incoming cofactor pays for preparation and normalization even
on a target hit. A hit skips bucket acquisition and descendants of the shared
node, but retains and verifies its incoming transport. There are at most
`2^(d+1)-1` incoming requests for depth `d` in this binary expansion; this is
exponential in depth. Each distinct residual/depth node is acquired at most once
within a shared program. The measured policy has depth two, bag width eight,
262,144 reserved table probes per node, and 512 preprocessing steps / 262,144
reserved index-maintenance units per invocation. A budget-limited transformation
is exact even if units remain; “closed” names the mode and does not promise a
fixed point on every input. Scans, candidate handling, normalization, checking,
serialization, elapsed time and RAM are not bounded by those local quotas.

## Matched costs and coverage

The frozen panel has 24 constructions (17 SAT, seven UNSAT), four repeats (two
SAT, two UNSAT), and twenty exposed sources (15 SAT, five UNSAT). New constructions
include random three-CNFs on 12/15/19/23 variables; guarded 10/14/18-variable
cores and deleted forcing clauses; even/odd parity prisms at sizes 5/7/9; and
conditioned planted 16/24-variable cores. Names, signs and input order are
scrambled. No new normalized source duplicates the preceding panel. Labels and
descriptions do not guide solving. These are designed synthetic controls, not
representative external SAT evidence or a global classification rate.

All workflows start empty with the same fallback. Four cyclic process orders
charge preparation, recognition, checking, JSON/SQLite persistence, warm reuse,
cold reconstruction and compression. Interpreter startup, report metadata,
panel generation, the post-hoc diagnostic and preservation audit are additional.
Both native cold readers audit fallback records. Two additional JSON replay
passes use the same checker, not independent implementations.

| Workflow | Discovery (s) | Solve/check (s) | Warm (s) | Cold (s) | Complete (s) | Certificate bytes | Native-record bytes | Peak RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | 0 | 0.31347 | 0.03014 | 0.21080 | 0.70572 | 0 | 888,841 | 71,303,168 |
| root | 0.60205 | 0.57658 | 0.34085 | 0.83906 | 2.59562 | 4,989,744 | 819,454 | 77,873,152 |
| tree | 0.60359 | 0.49559 | 0.35289 | 0.80784 | 2.46123 | 4,307,744 | 586,142 | 73,154,560 |
| closed | 0.56785 | 0.47573 | 0.32413 | 0.79109 | 2.35748 | 4,147,444 | 586,142 | 72,433,664 |

Paired complete improvements are **7.30–10.63%** versus root and **2.55–5.22%**
versus tree. Cold verification is the largest phase, followed by discovery.
Certificate writes add 0.03119 / 0.02987 / 0.02582 seconds for root/tree/closed;
archive persistence adds 0.14301 / 0.19637 / 0.16306 / 0.16435 seconds in table
order. Timings are local observations, not asymptotic or cross-machine bounds.

Tree-to-closed bucket acquisitions fall **250 to 219**, and elimination steps
**456 to 414**. The shared mode makes 242 incoming requests with 23 memo hits;
19 targets have multiple incoming edges from distinct raw cofactors. Twelve of
those targets are constant residuals, seven nonconstant. Thus not all observed
sharing is reuse of a difficult core. Avoided descendants explain why the
31-node reduction is larger than the 23 direct hits. The root arm has 255 nodes
and seventeen raw-state hits. Root-fold steps stay 929 in all structural arms;
per-edge unit steps are 491 tree and 467 closed.

Nineteen queries have internal shared-target hits. Their discovery improves
12.92% versus tree; the other 29 (including four whole-program replays) regress
0.09% in discovery. Full per-case timings and these observed, post-hoc strata
are preserved, rather than selecting only successful examples.

Certificate bytes count pretty-printed files. Combined compressed SQLite/JSON
packages occupy **165,974 / 221,996 / 182,982 / 182,438 bytes** in table order.
Sharing saves only 544 compressed bytes against tree. Diagnostics add
0 / 67,587 / 64,736 / 60,219 bytes. Historical archives, trial copies and container
overhead are extra. Shared RSS is modestly lower than tree, but still above fresh;
raw certificate reduction is not a general peak-memory or storage guarantee.

## Remaining gaps and next investigation

Twenty-one unique roots and one repeat remain outside the acquisition family.
The count includes seven new unique misses; fourteen of the preceding twenty
remain. Their 45 unresolved depth-zero closed nodes exceed width eight:
32 have width nine, eleven width ten, and two width eleven. Eleven stop before
elimination; 34 do some bucket work first. Partial bucket programs remain saved.

A separately bound, post-hoc profile of these exact node CNFs finds **no units,
unit conflicts, disconnected components, Horn or dual-Horn leaves**. Further
unit scans at these nodes therefore cannot close this observed gap. Binary
subsets, however, give **three contradictions with checked implication paths**,
and **fifteen leaves have checked binary-equivalence blocks**, merging 23
variable occurrences in their selected largest blocks. These are node-local
counts, not 23 globally distinct variables or new root verdicts. The diagnostic
costs 0.02420 seconds, 6,917 propagation literal visits, 1,512 binary graph edges
and 3,024 equivalence SCC edge visits, separately from acquisition. Full counters,
source bindings and evidence are retained in `remaining-structure-profile.json`.

The next target is **checked binary implication and equivalence substitution
after unit closure**, before forming full buckets. Existing path and substitution
checkers provide a concrete starting point. Determine whether these relations
reduce the remaining interaction enough to certify roots, with separate witness
transport and exact quotient reuse. Three conflicting leaves do not necessarily
refute their roots, and equivalence blocks may leave a wide core. Preserve
novel/random/deleted-guard failures. Cold checking remains the main cost target;
reducing duplicated evidence must preserve exact source and transport validation.
No uniform deeper partition, compact arbitrary-SAT closure or polynomial-time
unrestricted SAT guarantee follows.

## Validation and preservation

All **2,266 full tests and 24 focused tests pass**. Eight new tests include all
512 two-variable clause sets, seeded random CNFs, opposite-forcing shared cores,
sparse model lifting, partial quotas, unknown verdicts, corrupt graphs and cold
replay with discovery disabled. The audit reconstructs all sixteen measured
program streams, rechecks each edge/node and audits each distinct native archive.
Existing SQLite ResourceWarnings are retained in raw logs.

All **227 prior manifests, 38,630 artifact entries, 1,248 scientific sources and
69 proof blocks** remain unchanged. Five new source/test files raise the ledger
to 1,253; one restricted transport/sharing proof is added. Resume
`experiments/results/cnf-closed-buckets/checkpoint.json`, key
`closed_buckets.remaining`; the new structural profile is bound alongside it.
