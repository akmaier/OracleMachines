# Combine B6 and B7 failures on their original proof banks

Checkpoint: 26 November 2026. Composing the retained failures refutes case
**`(37,40)`**, bringing sampled structural recognition from **228/246 to 229/246**,
with **17 open cases**. The formula was already UNSAT in the reference snapshot;
this adds a checked structural route to that result. Both independent native
readers accept the new source-only certificates.

The B7 failures alone already suffice. Combining the B6 comparison failures
improves certificate cost: **35 native records instead of 51** for B7-only direct
reconstruction, or **77** for fresh solving. On this one positive case, joint
reconstruction uses **49.16% fewer record bytes** and **39.93% less complete
measured certificate time** than fresh solving. Discovery, historical acquisition
and unresolved fallback are additional. This is not a uniform SAT speedup.

## Exact composition without changing the meaning of old proofs

The new composition accepts the original B6 input/result, the checked B7 closure
and result, and the separately continued B6 comparison result. It validates the
complete B7 history on the original bank, independently validates the comparison
history on B6, and explicitly checks that both preparations share the same B6
bank and provenance. Neither cursor is relabelled onto a modified input.

Each contradiction under an assumption `l` on either original bank justifies the
unit `(-l,)`. The joint bank extends B7 with the union of these units. Duplicate
clauses retain an earlier valid reason; the comparison-derived reason is chosen
before a B7 reason for a duplicate newly added unit. Open completed assumptions
supply no axiom. A consistent unit fixed point is an unresolved result, never SAT.

Correctness is inductive over the existing proof banks. Each B6 comparison
exclusion follows from B6; each B7 exclusion follows from B7, whose earlier
exclusions already follow from their own lower banks. Therefore all appended
units follow from the original guarded source. Unit propagation on their union
is sound. This argument needs validation against the original reason IDs and
banks; syntactically joining cursors or changing their bindings would not suffice.

The native compiler follows each used exclusion to its actual origin: B6
comparison proofs return to bank 6, B7 proofs to bank 7, and earlier origins to
their respective smaller indices. The top composition is bank 8. Every recursive
proof dependency strictly decreases that index. Native leaves use source clauses
or checked source-contained guard templates. The emitted records use the existing
empty, units and split rules, with the original source residual in each context.
All portable proof checks happen before warm-cache lookup. Bounded direct-unit
shortcuts inspect only canonical source residuals, with the inherited global
262,144 work allowance and 256-step trace bound.

The first compiler for this mixed provenance retains the full source; it does
not yet select a smaller source support. Decreasing bank indices establish
well-founded proof reconstruction, not a polynomial bound on the number or size
of its distinct contexts.

## Ablations and propagation diagnostics

Four arms validate both full histories and vary only the consequences used:

| Arm | Added consequences beyond B7 | New sampled refutations |
| --- | --- | ---: |
| Base | None | 0 |
| B6 only | Continued B6 failures | 0 |
| B7 only | Retained B7 failures | 1 |
| Joint | Both sets | 1 |

Thus the joint route must not be credited with a refutation missing from B7-only
composition. Its benefit here is cheaper native reconstruction. Every arm uses
zero new assumed probes and one bounded indexed unit-propagation call per case.

On `(37,40)`, the retained scan-based diagnostic takes 102 unit steps for B7 only
and 51 for the joint bank. The occurrence-indexed algorithm used in the census
instead produces **67 and 64 steps**, respectively, because its propagation order
differs. Both traces and their clause reasons are checked and preserved. These
counts must not be mixed when comparing algorithms or native certificate size.

Two isolated repetitions in opposite order give the following summed per-target
means over all eighteen exposed inputs:

| Census stage (s) | Base | B6 only | B7 only | Joint |
| --- | ---: | ---: | ---: | ---: |
| Source reconstruction | 0.37233 | 0.37018 | 0.37137 | 0.37090 |
| Discovery, preparation and propagation | 0.29308 | 0.29069 | 0.29122 | 0.29182 |
| Independent verification | 0.28676 | 0.28532 | 0.28463 | 0.28549 |
| Persistence/reload | 0.00542 | 0.00580 | 0.00540 | 0.00540 |
| Complete census | 0.96174 | 0.95626 | 0.95666 | 0.95761 |

All controls pay the same full dual-history validation. Base is consequently an
ablation, not an optimized old-search timing baseline. The small census timing
differences show no material total-cost saving from composition. Source
reconstruction and final checking alone account for **68.54%** of the joint census;
discovery also repeats preparation. Census peak RSS is about 98 MB in every arm.
Startup/input loading, historical acquisition, scan diagnostics and the final
archive audit are additional. Earlier fused-expansion timings use a different
workflow and must not be multiplied into these results.

## Native cost on the newly recognized root

The comparison covers the same complete root, including its prefix, in isolated
processes with two opposite-order repetitions. The joint-disabled control expands
the proof with direct-unit shortcuts disabled. The two direct controls use the
same bounded source-unit shortcut. All four produce the same UNSAT answer and
include warm checking, persistence, and both independent cold readers.

| Positive certificate measurement | Fresh solve | Joint, shortcut off | B7 direct | Joint direct |
| --- | ---: | ---: | ---: | ---: |
| Initial solve/compile (s) | 0.25764 | 4.21363 | 0.21329 | 0.15992 |
| Warm check (s) | 0.00263 | 0.02833 | 0.02804 | 0.02714 |
| Both cold readers (s) | 0.27646 | 4.63248 | 0.20248 | 0.14019 |
| Persistence (s) | 0.10656 | 1.43870 | 0.08939 | 0.05885 |
| Complete certificate trial (s) | 0.64844 | 10.33664 | 0.53655 | 0.38950 |
| Native records | 77 | 1,164 | 51 | 35 |
| Record bytes | 1,339,495 | 16,812,163 | 1,006,246 | 680,946 |
| Peak process RSS (bytes) | 72,679,424 | 261,423,104 | 66,830,336 | 62,259,200 |

Joint direct reconstruction improves complete measured time **27.41%** and record
bytes **32.33%** versus B7 direct reconstruction. Against fresh solving the
reductions are **39.93%** and **49.16%**. Warm checking regresses substantially
against a fresh native cache hit because the compiler still checks the full
portable provenance first. The disabled baseline's much larger costs are retained;
its reduction is not the headline comparison. These positive-case measurements
exclude acquisition, discovery, unresolved fallback and the final independent
archive audit.

## Remaining frontier, storage and next work

The seventeen remaining cases retain both histories, containing **19 B6 comparison
failures** and **7 B7 failures**. Four joint closures gain **eight assignments**:

* `(28,18)`: one;
* `(28,19)`: four, including one beyond explicit exclusions;
* `(40,0)`: one;
* `(67,63)`: two.

Fresh bounded probing on these four changed residuals is the next coverage
candidate. The other thirteen joint banks are unchanged and may reuse previous
search only after exact bank, closure-trace and trace-bound checks. Old cursors
must not simply be retagged onto the changed banks. Repeated preparation across
the two checked histories and repeated source-prefix reconstruction remain the
largest avoidable census costs. Smaller source support is a remaining native
certificate opportunity.

The retained open rows are **1,944,017 bytes**, or **1,973,910 bytes** with the new
checked joint closures, compared with the previous **2,122,938-byte** export. This
decrease reflects removing the newly recognized case, not a general compression
or lifetime-storage bound. The gained case and four distinct native archive/root
combinations are preserved separately; previous files and cumulative tables are
unchanged. Total experiment storage continues to grow.

All **2,048 full tests** and **183 focused tests** pass. Tests cover both origin
banks, malformed old/current/comparison histories before warm lookup, forward
reason rejection, native direct/off paths, both cold readers, prefix publication,
budget fallback, empty-history outcomes, all sixteen subsets of the four signed
binary clauses on two variables, and generated small truth tables. The audit
reconstructs all census outcomes and scan diagnostics, verifies every retained
closure, and cold-replays four unique native archives. All **1,133 prior source
fingerprints**, **28,609 artifact entries in 201 parent manifests**, and **64
original manuscript proof blocks** remain unchanged.

Resume `experiments/results/cnf-joint-cursor-feedback/checkpoint.json`, especially
`joint_cursor_feedback.remaining-closures` and the supplemental archive bindings.
Reproduce `pilot`, `prepare`, `run_census`, `cases`, `run_trials`, `validate` and
`seal` with the corresponding compare/validate scripts in a fresh directory.
Full arbitrary-CNF structural coverage, uniformly polynomial preprocessing and
expansion, and bounded lifetime storage remain open.
