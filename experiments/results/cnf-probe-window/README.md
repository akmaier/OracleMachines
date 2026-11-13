# Bounded continuation of saved probe windows

Frozen implementation: `a11cddf`. Reproduce from the repository root:

```sh
python3 experiments/compare_cnf_probe_window.py experiments/results/NEW-DIRECTORY
python3 experiments/validate_cnf_probe_window.py experiments/results/NEW-DIRECTORY
```

The validator expects `/tmp/oraclemachines-window-tests.log`; its preserved copy
is `full-validation.txt`. `report.json` binds input archives, source fingerprints,
budgets, individual attempts, phase costs and table digests.

The mechanism diagnostic explains the previous growth success: pivot 15 removes
two binary clauses without adding a binary resolvent. The first four probe
candidates change from [17,4,8,13] to [17,8,13,14]. Assumption 14=true was already
refutable on the original source. Full checked single-assumption traces show
source conflicts {14=true,15=true,32=true} and projected conflicts
{14=true,32=true}, in source coordinates. This identifies a selection-window
effect on that core, not a general statement about elimination strength.

The continuation tries the next four untried binary-frequency candidates, with
at most four distinct unresolved sources and 32 new recognition admissions per
original. It preserves all old policy identities. Forced, inconclusive and
interrupted-acquisition results have explicit persistence semantics.

Coverage improves **32/83 -> 36/83**. Independent reference solving confirms:

| Selected case | Historical group | Original case | Variables | Result |
|---|---|---:|---:|---|
| 41 | selection_holdout3 | 1231 | 48 | SAT |
| 49 | core_holdout3 | 1300 | 48 | SAT |
| 62 | order_holdout3 | 1374 | 48 | SAT |
| 78 | implied_holdout3 | 1478 | 48 | UNSAT |

These are reused development inputs despite their historical group names.
Removing the older growth-exception route retains all **36** closures. The known
positive-control core also closes via two continued windows, adding five states.
Its acquisition is charged before the remaining originals; it is not a fresh gain.

The run adds **70 window records** (52 clear, 18 forced), **475 assumption attempts**
and **81 pattern nodes**. No state cap binds (maximum 24), and there are no pending
targets. Resident search/check/persist/compose is 0.84607 s, including 0.04175 s
for the positive control. Eligibility and final recomposition add 0.04547 and
0.05027 s. Preparation takes 65.30144 s; full cold audit 106.59552 s; separate
route replay 63.01694 s. The whole reported pipeline takes 252.05013 s.

The working database grows by **2,142,208 bytes** over a seed with the empty
seventh table. The delta is **2,220,032 SQLite / 129,619 compressed bytes**.
`coverage.json.gz` is 71,810 bytes. The separate reference archive retains
409 proof nodes in a 3,502,080-byte database. These are storage measurements,
not peak RAM, and this experiment claims coverage rather than a speedup.

All **543 tests**, seven-table reconstruction, unchanged old rows, exact source
bindings, admission accounting, cold finite-plan replay, growth-edge ablation
and reference proof replay pass. The full suite retains 20 existing SQLite
resource warnings. Earlier archives, including all failed trials, remain intact.

Resume from `restore` in `compare_cnf_probe_window.py`, hash-check and unpack the
delta, then apply its **seven-table** `apply_delta`. Compare logical table digests
and construct `WindowRoutes` to verify every retained record before composition.
The new complete history has **41,416 pattern nodes, 563 one-pivot trials,
25 coupled trials, one growth trial and 70 probe windows**, plus the unchanged
1,548 source bindings and 21,838 ordinary solver proof rows. Separate reference
archives remain additional paid evidence. The [study](../../../research/probe-window.md)
records the next gaps, including advancing a window without repeating its prefix.
