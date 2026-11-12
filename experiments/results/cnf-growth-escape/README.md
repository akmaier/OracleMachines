# Controlled growth-three escape

Frozen acquisition code: `6134c54`. Reproduce from the repository root:

```sh
python3 experiments/compare_cnf_growth_escape.py experiments/results/NEW-DIRECTORY
python3 experiments/validate_cnf_growth_escape.py experiments/results/NEW-DIRECTORY
```

Validation expects the separately recorded 538-test log at
`/tmp/oraclemachines-growth-tests.log`; its preserved copy is `full-validation.txt`.
The full source/policy/fingerprint record is `report.json`.

The unique minimum-growth-three pivot (15) closes the saved 35-variable core.
It first produces 34 variables / 153 clauses / 506 literals, then acquires four
checked probing nodes under the unchanged recognizer policy. The matched
growth-two control admits no pivot. Both keep pair/candidate limits 64 and a
32-new-state admission cap. No cap is reached.

| Phase or retained size | Measured value |
|---|---:|
| Resident growth-two control | 0.0026375 s |
| Growth-three expansion/check/persist | 0.0227487 s |
| Warm search and saved-trial check | 0.0032055 s |
| Paid-history preparation | 65.69362 s |
| Complete cold inventory audit | 114.36987 s |
| Separate trial replay | 67.67913 s |
| New pattern nodes / trials | 4 / 1 |
| Working database increase | 69,632 bytes |
| Delta SQLite / compressed | 122,880 / 7,870 bytes |

This is one selected development core, not a general speedup. Old composition
still reports 31/83 source coverage; the successful leaf lies on a saved
alternative route. Whole-source propagation is studied separately in
`cnf-growth-routes`. Stored bytes are not peak process memory.

All 538 tests pass. Independent enumeration confirms that pivot 15 is the sole
minimum-growth-three choice. Delta reconstruction, all-old-row preservation,
idempotence, exact bindings, admission accounting and cold replay pass. The suite
retains 20 existing SQLite `ResourceWarning`s. An initial validator assertion
counted 563 first trials but omitted the 25 additional first-trial checks inside
coupled replay; it was corrected to expect 588 checks. That failure log is
preserved separately and was not a solver or certificate failure.

The reusable history has 41,335 pattern nodes, 563 first-pivot trials, 25 coupled
trials and one growth trial, with all 1,548 source bindings and 21,838 ordinary
solver proof rows intact. To restore it, use `restore_latest` from
`compare_cnf_growth_escape.py`, then hash-check/unpack `proof-delta.sqlite3.gz`
and apply the **six-table** `apply_delta` from that module. Compare the resulting
logical table digests with the report and recheck all trial types before reuse.
