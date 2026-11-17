# Bounded single-assumption guards at exact historical prefixes

Nine arms compare baseline solving, direct premise acquisition and retained
unit-trace publication on cases 43/172/70. Both candidate methods pay the same
bounded probes and produce identical proof payloads, composed records and child
metrics. See [the analysis](../../../research/assumption-guard.md).

Native rows fall 23 -> 20 and bytes 29,615 -> 24,582, but case 70 regresses 4 -> 5
rows. Retained traces avoid 1,166 repeated propagation visits versus direct
premise solving. Total propagation still exceeds baseline (4,501 -> 5,907), and
serialized deltas plus records grow 88,960 -> 98,668 bytes. Lower native storage
does not establish lower total storage or runtime. The supplied candidates come
from a separately charged earlier core-bank diagnostic.

`discovery-probe.json` checks target-local binary-incidence ranking with a four
variable budget. It finds different forced guards after one/one/two probes,
without scanning the core bank at that stage. All their remaining child roots
are absent at the historical prefixes. This diagnostic publishes nothing; those
choices still need acquisition measurements and excluded-query tests. Original
and unit-residual scoring select the same first conflict on these three cases;
later candidate orders differ in 43 and 70.

`checkpoint.json` preserves all 21,525 previous native payloads and has 21,528
keys. Only three premise roots are new to combined history; the remaining
children already occur in the earlier partition arms but were excluded from
the measured pre-query states. There are no alternative native payloads. Cold
replay checks 2,957 ordinary decisions, 429 prior composed records, nine new
chains and six retained projections. Four frontier lineages and structural
authorities remain unchanged.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_assumption_guard.py /tmp/cnf-assumption-reproduction
python3 experiments/validate_cnf_assumption_guard.py /tmp/cnf-assumption-reproduction
python3 experiments/analyze_cnf_assumption_guard.py /tmp/cnf-assumption-reproduction
python3 experiments/probe_cnf_assumption_discovery.py /tmp/cnf-assumption-reproduction
python3 experiments/finalize_cnf_assumption_guard.py /tmp/cnf-assumption-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_assumption_guard solver.test_cnf_guard_chain solver.test_cnf_partition_screen
```

All 1,064 full-suite and 21 focused tests pass, including exhaustive 512
two-variable CNFs, SAT witness lifting, tampering, persistence and bounded
rejection. The full suite retains 44 existing SQLite ResourceWarnings; focused
tests emit none. Production binds 466 sources, including four new runtime/test
files. The final ledger adds three posthoc tools for 469 sources. Prior 462
sources, 5,008 artifacts and 86 manifests are unchanged. Timed sources were
frozen before production; tests and analysis ran afterward. All 64 previous
manuscript proof blocks are unchanged; the rebuilt paper has 206 pages and no
overfull or undefined warnings. No new Lean, fresh structural coverage, stable
runtime, peak-memory or unrestricted-SAT result is claimed.

New manifest: **49 artifacts**. Next preservation audit: **5057 artifacts / 87 manifests**.
