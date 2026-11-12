# Exact-source reuse trace

`trace_cnf_subset_reuse.py` runs original corpus source 1444 (48 variables,
204 clauses) alone from the paid prefix with additive allowance two, depth two,
probe and learn limits four. `calls.json.gz` retains every ordered source,
phase and returned certificate. `report.json` binds the script, prior experiment,
profile and identical output database. The existing profile archive is reused.

There are 1,694 calls, 851 unique ordered CNFs, 843 proposal calls and 851 check
calls. Neither independent role repeats a source. Separate-role LRU simulations
at 64, 256 and 1,024 slots therefore have zero hits. This rules out that cache
for this trace; it does not rule out caching on other inputs or structural
filtering within a call. Sharing unchecked proposals would not supply an
independent checker. Trace timings include instrumentation and are not benchmark
speedups. Full matching certificate tests and source bindings are retained in
`test_cnf_anchored_subsets.py` and the following anchored-index validation.
