# Checked cofactor support reuse

Sixteen new restricted targets reuse checked supports. Fresh expansions fall
30.77% and query time 34.06%, but complete time rises 23.01% and peak RSS 9.23%
after charging bank construction. This remains an optional experiment. See the
[analysis](../../../research/cofactor-support.md) for proof obligations and costs.

Reproduce into a fresh directory, running the timed producer alone:

```sh
python3 experiments/compare_cnf_cofactor_support.py /tmp/cnf-cofactor-support
python3 experiments/validate_cnf_cofactor_support.py /tmp/cnf-cofactor-support
python3 experiments/analyze_cnf_cofactor_support.py /tmp/cnf-cofactor-support
```

`protocol.json` binds 352 runtime sources, the 14,630-key seed, old banks,
selection rule and alternating four-pair order. `previous-decisions.json` binds
all 576 earlier double-deletion answers excluded before selection, including
guarded answers without complete roots. Both modes use incremental accounting,
a target-cache lookup and the complete snapshot cold audit. The candidate pays
for support preparation; historical acquisition and selection are separate.
No tests, builds or profiles overlap timed workers.

There are 145 negative inherited cofactors and three positive guarded cases.
Only checked negatives supply supports. Extraction yields 112 raw supports and
a 104-core containment antichain, publishing 1,310 proof nodes. Every origin and
dominance witness is retained in `cofactor-0/cofactor-bank.json`; all trials keep
their own copy. Fourteen cores match sixteen novel targets, saving 72 expansions.
All measured hits share their first origin's guard clause; only a unit test
demonstrates cross-guard transfer. The arbitrary-SAT coverage gap remains open.

Both modes return 84 SAT / 108 UNSAT with 63 old core hits, 83 witness answers,
46 guards and six cached targets. The candidate still uses 151 negative and
11 positive expansions. New-catalog case 7 is the guarded SAT counterexample;
it is unrelated to original structural case 7. Repeated visits add no rows.

`cost-attribution.json` retains per-query savings, regressions, used-core counts
and proof dependencies. The whole bank needs 1,272 preparation nodes, whereas
the current query proofs need only 118. Only 38 nodes are unused by the complete
bank and queries. Constructing proofs only on a match is the next untested
policy; selecting only the fourteen observed cores would use future knowledge.
Do not re-extract this already materialized bank for later warm comparisons.

`checkpoint.json` preserves all inherited fields and adds `cofactor_support_study`,
`cofactor_support_decisions` and `cofactor_support_bank`. Load the bank's `cores`
field from the latest union. The union holds 16,320 keys / 49,610,752 SQLite /
3,953,721 gzip bytes. Earlier payloads win overlaps; sixteen alternatives remain
in the trial archives. The 192 new decisions have 146 direct roots and 46 guarded
records. A cofactor hit still needs its source and checked guard for a complete
query answer.

All 434 tests, 3,072 ordinary-solver trial replays, every union node, 845 inherited
decisions and all new decisions pass with fresh validation search disabled.
Structural closure remains original 17/24 and separate supplemental 24/24. Prior
348 sources, 3,873 artifacts / 68 manifests and all 64 proof blocks are unchanged.
The manuscript builds to 194 pages without warnings. The final source ledger
contains 353 sources including the post-hoc analyzer.
