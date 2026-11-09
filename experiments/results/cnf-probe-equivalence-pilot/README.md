# Selected-source signed-equivalence pilot

9 November 2026. These sixteen old sources were selected from the preceding
common-consequence archive because their chosen unresolved paths contain
indirect equivalences in saved probe traces. This is a diagnostic selection,
not a fresh holdout. The full source IDs are 799, 875, 879, 931, 933, 956, 962,
966, 970, 971, 978, 1021, 1042, 1048, 1052 and 1053; `original_case` preserves
the mapping in the report. All policies use depth two and both candidate caps
four. The independent solver still solves every original CNF.

| Mode | Closed / 16 | Total seconds | SQLite bytes | Pattern nodes | Logical node bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solving alone | -- | 0.33155 | 1,679,360 | -- | -- |
| Common baseline | 0 | 4.92437 | 16,863,232 | 1,698 | 8,754,887 |
| Signed equivalence | 7 | 4.86584 | 16,326,656 | 1,585 | 8,385,727 |

Gains are original cases 799, 879, 931, 933, 962, 1021 and 1048. Three are
variants of one source. Full cold checking and warm replay are retained in
`report.json`; all three archives replay byte-identically. The separate traced
allocation diagnostic uses the first three selected cases. Timings are single
sequential samples; no significance claim follows from the small difference.

The [larger comparison](../cnf-probe-equivalence/README.md) preserves all seven
gains but finds higher total time/storage, and no gain on 24 fresh random
sources. Keep both results; the optional policy is not a general optimization.
