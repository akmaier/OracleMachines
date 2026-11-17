# Fresh premise-first guard-chain comparison

Three policies share the same 20,666-key starting union and ordinary recognition
pipeline: `plain` adds no extra guard, `core-first` uses the previous scan/check
order, and `premise-first` uses copied clause postings and checks a stored negative
strengthened premise before the separate support proof. All policies persist
checked chains and use a checked conclusion bank on repeat visits. Core metadata
can only suggest a clause; a checked negative strengthened premise or checked
core/subset derivation must justify it. No premise search is allowed.

The next 192 neighbouring queries exclude prior ordinary/chain answers and native
roots, with 64 per template. Two reversed-order triplets run in fresh processes
without concurrent tests, builds or profiles. Both chain policies reduce expansions
**139 -> 67**, splits **46 -> 19**, new native rows **436 -> 364** and added native
payload **706,491 -> 579,076 bytes** versus plain. Seven cases improve without
per-case expansion/publication regressions. Eight extra guards all use existing
premises; answers are 97 SAT / 95 UNSAT. Native chain-policy payloads are identical.

Premise-first reduces extra verified nodes **247 -> 102**, read bytes **198,609 ->
109,646**, and additional guard literal visits including its index setup **208,132
-> 36,985** versus core-first. The copied index stores 11,953 memberships and 484
clause keys. Its 42,548 posting visits are not directly comparable units to the old
2,504 core inspections. Case 45 uses a pending-core hint with the same checked
premise as the ready core chosen later by the old selector.

Mean complete times are **20.14800 / 18.48525 / 19.60037 seconds** for plain /
core-first / premise-first. Paired premise-first changes are **-8.51%, +1.10%**
versus plain and **-31.67%, +58.09%** versus core-first. No stable total speedup.
Mean query time improves, but full cold replay and compression consume about
61.9% / 20.2% of premise-first complete time. Peak RSS means are lower with limited
replication; no general memory bound follows. Larger chain sidecars increase one
compressed-archive-plus-trial size **0.414%** versus plain, despite fewer native
proof bytes. All repeated trials and historical acquisition/state cost extra.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_premise_guard.py /tmp/new-premise-guard
python3 experiments/validate_cnf_premise_guard.py /tmp/new-premise-guard
python3 experiments/analyze_cnf_premise_guard.py /tmp/new-premise-guard
python3 experiments/check_cnf_premise_parity.py /tmp/new-premise-guard
python3 experiments/probe_cnf_premise_gaps.py /tmp/new-premise-guard
```

`protocol.json` binds input authority, ordinary/support banks and 426 runtime
sources. `previous-decisions.json` preserves 2,688 ordinary and eight chain records
for exclusion (the eight historical chain sources already have older ordinary
records). Input selection excludes their normalized identities and cached native
roots. Three post-hoc source files bring the final ledger to 429.

Each trial retains a complete compressed native archive, query chains, ordinary
recognition traces, per-query added keys, count/time attribution, and warm replies.
Complete time includes restore, setup, queries/chain checks, warm-bank construction
and replay, serialization, complete cold native/chain/lineage audit, compression
and report generation. Module imports, initial CLI reads and final timing rewrite
are excluded. Input selection, original acquisition and independent validation
are separate charges. `cost-attribution.json` preserves all paired changes,
regressions and remaining targets rather than selecting only improvements.

`reconstruction.json` verifies every native proof, all first/warm queries and both
measured index lineages in six trials, fresh exclusions, and pre-query selection
order using a direct core scan rather than the prepared index. The untimed
`frozen-control/` reproduces the old ordinary worker: guards, cofactors, witnesses,
answers, children, expansion counts, new keys and final native payloads match the
adapted plain arm exactly. The timing interfaces differ and are not compared.
All 2,957 inherited ordinary decisions and eight inherited chains replay.

Resume `checkpoint.json`: **21,128 native keys**, adding 462 while preserving every
one of the prior 20,666 payloads. `union-chains.json` supplies **192 new conclusions**;
the eight prior chain records remain bound separately. Load/check these sidecars
with `GuardChainBank` for composed reuse. The native root table alone need not
contain their source conclusions. Native proof formats stay unchanged, and the
bank assumes an exclusively owned immutable or append-only proof session.

The union occupies **66,498,560 SQLite / 4,889,065 gzip bytes** and contains no
alternate native certificates. `frontier-check.json` checks all four complete
lineages: ready/pending counts **130/40 original, 137/70 legacy, 79/97 causal,
79/124 optional expanded causal**. No new support origins are acquired. Original
structural coverage remains 17/24 with 999 steps and 2,614 patterns / 259 pairs /
17 missing children; supplemental coverage remains 24/24 with 208 steps.

All **1,028 full-suite tests** and thirteen focused tests pass. The initial focused
failure was an unsorted test expectation; its log is retained. The implementation
was unchanged by that correction. Full-suite logs retain 44 older unclosed-SQLite
ResourceWarnings, with none in the focused tests. The paper builds to 203 pages
with 64 prior proof blocks unchanged and no overfull/undefined/LaTeX warnings.
All 422 prior sources and **4,649 artifacts / 81 manifests** pass preservation.

The remaining-gap probe is read-only, masks availability to each pre-query prefix,
and checks actual negative ready cores. Case **68 costs 27/67 expansions** and
needs three missing clauses; cases **6/135 cost seven each** and need three/two.
A negative conjunction of several missing clauses forces some clause false, not
all of them. Exact multiple-clause alternatives, branch composition and their
cost are the next structural target; no such inference is implemented here.
No unrestricted-SAT polynomial or optimal-expansion claim is made.

New manifest: **57 artifacts**. Next preservation audit: **4706 artifacts / 82 manifests**.
