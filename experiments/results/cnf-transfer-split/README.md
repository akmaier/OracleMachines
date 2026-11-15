# Saved split completes the transfer stream

See [the analysis](../../../research/transfer-split-selection.md). The initial
size-based choice is preserved; the supplemental `pair-control` compares all four
saved pairs at the same allowance. Variable 14 closes both branches and the last
original. This completes 42/42 finite development inputs, not arbitrary SAT.

`checkpoint.json` binds all 477 retained patterns, four split alternatives, 42
original query sources and the selected positive proof. Restore it through
`experiments.validate_cnf_transfer_split.restore_checkpoint`; its `next_selection`
is null. Keep failed alternatives and prior histories. The source-only controls
are not complete resumable original-root checkpoints.

```sh
python3 -m unittest solver.test_cnf_transfer_split
python3 experiments/continue_cnf_transfer_split.py /tmp/transfer-split-new
python3 experiments/compare_cnf_transfer_pairs.py /tmp/transfer-split-new/pair-control /tmp/transfer-split-new
python3 experiments/validate_cnf_transfer_split.py /tmp/transfer-split-new
```

Use new destinations. Validation writes its derived files, so copy the stored
bundle before revalidating to preserve its original hashes.
