# Required-literal subset kernel replay

Command: `python3 experiments/benchmark_cnf_anchor_kernel.py experiments/results/cnf-anchor-kernel`

Five alternating-order repetitions replay all 1,694 retained calls, with counters
and exact-certificate equality assertions timed. Trace median: 1.116163 seconds
for the previous width index, 0.556901 for required-literal postings. Subset tests
fall from 4,904,264 to 150,503; postings visit 409,454 entries. Peak traced Python
allocation over the replay and controls rises from 84,047 to 88,045 bytes.

Control median seconds (baseline / anchored):

| Control | Baseline | Anchored |
|---|---:|---:|
| Uniform width | 0.0001247 | 0.0001283 |
| Mixed widths sharing literals | 0.0002990 | 0.0003839 |
| Units plus wider clauses | 0.0003997 | 0.0002272 |
| Repeated literals | 0.0000064 | 0.0000071 |
| Empty clause | 0.0000043 | 0.0000051 |

These tiny controls retain regressions but do not provide robust latency ratios.
`report.json` includes exact formulas, all runs, operation counters, allocations
and source/trace hashes. This is one previously costly source, not a corpus
speedup. Full acquisition and independent cold checking are measured separately
in the `cnf-anchored-subsets-*` experiments. No stored state or coverage changes.
