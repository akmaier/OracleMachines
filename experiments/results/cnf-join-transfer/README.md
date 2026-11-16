# Cross-input transfer of saved nonterminal joins

On 24 distinct constructed CNFs, preloading 39 exact proof nodes and four split
certificates avoids 35 acquisitions and 154 probes. Both histories cover all 24
inputs with identical proofs. Mean whole runtime falls only 0.99%; final storage
and peak RSS increase slightly. Twelve edited controls gain no acquisition saving.
See [analysis](../../../research/join-transfer.md).

Reproduce from the repository root into a fresh directory:

```sh
python3 experiments/compare_cnf_join_transfer.py /tmp/cnf-join-transfer-reproduction
python3 experiments/validate_cnf_join_transfer.py /tmp/cnf-join-transfer-reproduction
python3 experiments/analyze_cnf_join_transfer.py /tmp/cnf-join-transfer-reproduction
python3 experiments/check_cnf_supplemental_queries.py /tmp/cnf-join-transfer-reproduction/checkpoint.json /tmp/cnf-join-transfer-reproduction/supplemental-check.json
```

The frozen protocol fixes histories, construction, limits and order. `seeds.json`
binds both audited initial histories; `cases.json` preserves every CNF and its
validation-only construction witness. The four trial directories contain all
query proofs, counters and complete compressed databases. `analysis.json` traces
the exact 35 avoided acquisitions and four unused retained nodes.

Resume the complete current authority with `checkpoint.json`, using
`experiments.validate_cnf_bootstrap.restore_checkpoint`. It retains the latest
parent and every trial addition: 2,614 patterns, 259 pairs, 17 inherited missing
children, and a 999-step proof covering 17/24 original queries. The separate
`transfer-queries.json` and 208-step `transfer-proof.json` cover the constructed
24-input set and are bound through the checkpoint's supplemental fields. Do not
merge those denominators or discard the supplemental evidence on continuation.
The study validator checks these proofs; the supplemental checker additionally
replays the combined proof against a fresh read-only archive. `next-discovery.json` retains original case 7.

Preparation (16.014 seconds), historical acquisition and retrospective audit
(98.033 seconds) are separate from stream timings. Retain these costs and the
negative controls. All 376 relevant tests pass. Default solver policy is unchanged;
this is synthetic structural coverage, not an unrestricted SAT guarantee.
