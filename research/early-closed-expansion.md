# Early closed-cofactor reuse: a gain and a retained regression

## Result

Using a saved split with an already checked closed child reduces measured
expansion time on the current case **1445** from **8.08296 to 6.27974 seconds**
(22.31%). The two policies enter the same 32 state identities, store identical
pattern payloads and choose the same split records. Early reuse skips two clear
probe blocks: six advances replace eight, and 30 fresh external assumption
attempts replace 42. Both policies reach the state allowance with one pending
branch. Structural coverage remains **59/83**.

The historical forcing control **1189** exposes a loss. No early closed pair is
found. Both policies take the same eight advances, enter 21 states and close the
target through the same proof, but early searching takes **8.00118 seconds**
versus **7.87241 seconds** for probe-first (1.64% slower). Candidate checking rises
without improving the selected route. The implementation remains an experimental
policy; these two selected development cases do not establish a universal saving.

## Policy and exactness

`experiments/cnf_early_closed.py` adds `EarlyClosedExpansion`, preserving the
existing recognizers, proof checkers and 32-state admission contract. An unfinished
saved split resumes its exact two targets. An existing forced ordinary record
also takes precedence. Otherwise the policy ranks at most 64 retained pairs and
prefers a pair with an already checked closed child. If none qualifies, the old
ordinary-first policy runs. Failed searches and repeated ranking are charged.

The complete checked route catalog and immutable historical rows are prerequisites.
Both children remain mandatory for structural coverage; a closed child can be
SAT or UNSAT. No new propagation trace is required to reconstruct a saved split,
but reading and checking its evidence still costs time. The policy does not reset
the allowance, omit the second branch, treat a missing state as false, or change
the formula semantics.

Each case uses two independent copies of its bound parent checkpoint, with twelve
steps and 32 admissions per arm. Case 1445 starts from the current 29-variable /
103-clause / 307-literal leaf; case 1189 starts from the earlier 22 / 88 / 272
checkpoint, before its later solution became available. Policy order is reversed
between cases. There is one run per case and policy, without timing confidence
intervals. Initial authority reconstruction and final whole-corpus composition
are outside each worker and are reported separately.

## Matched costs

| Case and policy | Steps | New assumption attempts | Admissions | Acquisition including candidate checks, s | Route refresh, s | Expansion total, s | Complete worker, s |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1445, probe-first | 8 | 42 | 32 | 0.26291 | 7.81147 | 8.08296 | 20.70618 |
| 1445, early closed | 6 | 30 | 32 | 0.37896 | 5.89382 | 6.27974 | 17.90584 |
| 1189, probe-first | 8 | 51 | 21 | 0.13140 | 7.73711 | 7.87241 | 19.14551 |
| 1189, early closed | 8 | 51 | 21 | 0.31389 | 7.68331 | 8.00118 | 19.33329 |

Expansion includes selection, acquisition, complete route refresh, local coverage
composition and proof checking. Complete worker time also includes the authority
copy, initial route preparation, artifacts, delta export and cold new-row checking.
On case 1445, the complete-worker reduction is **13.52%**. On 1189 it is a
**0.98% regression**. Acquisition itself is slower under early search in both cases.

The current-case gain comes chiefly from avoiding two full route refreshes, not
from cheaper candidate recognition. Early search ranks **94 candidate pairs**
across its advances versus **41** for probe-first, recording one hit and five
misses. On the forcing control it ranks **94 versus 15**, with eight misses.
This identifies repeated unsuccessful ranking as a cost to address before broader
use. Newly saved traces and newly closed or admitted targets can change eligibility;
reusing a negative search result would require explicit invalidation conditions.

Current authority reconstruction costs **32.97981 s**, and reconstruction of the
earlier control authority **25.34922 s**. After merging all arms, complete route
preparation costs **7.44994 s**, and composition/checking of all 83 original
inputs costs **60.00692 s**. The complete comparison and persistence pipeline takes
**227.90943 s**. These costs remain even though one local scheduling choice improves.

## Structural progress and the state-budget boundary

On case 1445, early selection of local variable 12 on the 29-variable source reuses
the existing empty-CNF terminal for one child. The other child reduces to a
27-variable / 93-clause / 287-literal unresolved source after four admissions.
No saved pair there has an already closed child. Both policies eventually split
on its local variable **4**, with rank **[2, 2, 23, 407, 4]**: two unclosed,
missing cofactors, of **22 / 72 / 211** and **23 / 70 / 196**.

The false branch closes through **24 new states**: four probe reductions, seven
binary-path deletions, eleven eliminations, a polarity transformation and a Horn
terminal. The terminal has **6 variables / 9 clauses / 21 literals** and is not
2-CNF. Thus this sequence connects conditioning and elimination to a different
recognized family from the previous 2-CNF example. Clause and literal counts
increase at several elimination steps; shrinking support alone is not a bound
on all costs.

The true branch enters four additional states before the shared allowance is
exhausted. Those four unfinished states have no completed pattern rows. Their
identities, consumed admissions and pending split target are retained; completed
work is preserved. There are **32 admissions but 28 stored new patterns**. This
is an accounting boundary, not evidence that the remaining cofactor is hard or
that it requires another 32 states. The next run should resume this exact pending
target and measure which completed descendants it can reuse.

## Persistence and checks

Both policies' results, including the regression, are preserved. Their deltas are
conflict-checked and merged into the latest authoritative history; the historical
control's completed rows already exist there. The combined checkpoint is not one
32-state experiment: every comparison arm has its own allowance, and duplicated
experimental work remains charged.

The combined delta contains **28 patterns, one window and five continuations**:
**19,191 compressed bytes / 487,424 SQLite bytes**, plus two new split sidecars.
The early current-case arm alone uses **18,291 compressed bytes**, avoiding two
continuations, but the preserved union includes the control's additional evidence.
Full history grows by **417,792 bytes** to **771,342,336 bytes / 41,815 patterns**.
All previous rows survive and delta merge is idempotent. The reference archive
preserves all 2,075 earlier nodes and checks 2,115. The positive proof remains
2,828 steps. These are retained storage measurements, not peak RAM.

All **181 relevant tests** pass. A separate cold validation restores the combined
checkpoint, reconstructs each arm from its own parent, rechecks split records,
positive proofs and exact final local frontiers, and verifies admission accounting
and idempotent merges. New recognition is disabled throughout. All four arm
outcomes match; the complete validation takes **132.79116 s**. No new Lean
refinement or polynomial construction guarantee is claimed.

Resume **`experiments/results/cnf-early-closed/report.json`** using
`experiments.compare_cnf_early_closed.restore_checkpoint`, retaining all five
evidence lists **(1, 42, 156, 16, 1)**. Report SHA-256:
`8a526996c3c739f76c847d4f9f4d5a05d9530d14d7834930a40c5afab6d5245f`.
The one pending target is the true cofactor of the retained split on local
variable 4, at **23 / 70 / 196**, SHA-256
`69d0f3cad2b4d527495373e3fecf905d0c538d98adb833dbd0373598cfb0280e`.
Its split source SHA-256 is
`6be85c519f3e56d3096ab3e1ed2ad63597d70459193d435d885457fca290ca39`.

Reproduce the comparison with
`python3 experiments/compare_cnf_early_closed.py NEW_DIRECTORY` and validate it
with `python3 experiments/validate_cnf_early_closed.py DIRECTORY`.
Continue discovery from the merged checkpoint rather than rerunning the four
comparison arms. After the pending target, investigate reuse of candidate checks
and broader testing of when an early closed cofactor is worth pursuing.
