# Pilot: occurrence indexes for immutable source restrictions

Eight fixed inputs compare ordered propagation alone with a bounded restriction
index on top of that inventory. Both keep the same 1 MiB successful-check cache,
proof order, discovery policy and ordinary SAT solver. Every answer, profile,
root and database byte agrees. Both cold audits check every retained node,
source binding and solver certificate without changing bytes.

Single-sample total time is 2.78393 -> 2.48218 s and discovery 2.63831 -> 2.33911 s.
This is a selected synthetic pilot, not a full-corpus speedup estimate. The full
study includes memory, repeated timing, preparation and locality regressions.

The index retains exact immutable source objects and their signed occurrence
lists. A cache hit must be the same strongly held tuple/tuple/nonzero-int source
validated on admission. Mutable or unusual inputs use the old scan. Changed or
separately allocated equal sources prepare independently; no assignment or proof
result is cached. Unaffected clause tuples are shared in the returned residual.

The 32,768-unit cap counts one source plus clause and literal-occurrence slots,
not physical bytes or RSS. The independent simplification checker still scans
its input branch directly; indexed branch construction remains trusted Python.
There is no new structural category or unrestricted SAT bound. Full data and the
shared pilot archive are retained here, with implementation fingerprints.
