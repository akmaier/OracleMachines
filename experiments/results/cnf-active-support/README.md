# Active support checks with complete cold lineage verification

Complete runtime falls 10.02% against eager extension and 6.85% against the
loaded-index control. Both extension modes have byte-identical proof archives
and identical search work. Every mode pays for the frozen complete proof/query
audit and all used-index provenance on one pinned cold snapshot. This is a
checking improvement: index growth 151 -> 170 gives no additional transfers or
saved expansions on this stream. See [analysis](../../../research/active-support.md).

Reproduce in a fresh directory, with timed workers running alone:

```sh
python3 experiments/compare_cnf_active_support.py /tmp/cnf-active-support
python3 experiments/validate_cnf_active_support.py /tmp/cnf-active-support
python3 experiments/analyze_cnf_active_support.py /tmp/cnf-active-support
```

`protocol.json` binds 368 runtime sources, the 17,161-key seed and saved 151-entry
index. Selection excludes 1,152 previous sidecar answers and cached complete roots.
Three balanced fresh-process triples visit 192 constructed neighbours twice;
no tests/builds/profiles overlap. The complete clock includes final digest/report
generation and full cold lineage checks. Imports, CLI reads and wrapper rewrite
are excluded; historical acquisition and selection remain separately charged.
This audit boundary is broader than earlier studies; percentages cannot be combined.

Saved descriptions are hints. A match checks its canonical core identity and
ordinary negative proof. A pending root requires checked derivation before subset
publication; current-query guard checks remain online. Complete historical lineage
is checked on the pinned cold snapshot, using the full auditor's checked proof
objects. The connection closes on success or failure. No persistent unchecked
validity flag is accepted. Private append-only live ownership is required.

Every mode answers 97 SAT / 95 UNSAT and makes 25 support transfers with 187
expansions. Guards include 44 negatives and two positives; the two SAT cases
account for 42 remaining expansions. Fifteen negatives account for the other 145.
Original template 12 contributes 169/187 expansions. Every measured transfer
shares its first origin's guard clause; broad cross-category coverage remains open.
The extended frontier has 170 entries, 106 available and 64 pending. Repeated
query visits add no rows. An active-loader-only comparison remains unperformed;
do not attribute the speedup to growing the bank.

`cost-attribution.json` keeps every query, paired comparisons, preparation counters
and pending-root counts. Preparation normalizes 517,355 literal occurrences
instead of 1,904,438 and makes 1,563 lookups instead of 6,625. Query time rises
27.91% versus eager, but complete time improves in every matched triple. Mean RSS
is 7.89% lower than eager, with mixed paired signs, and 5.06% lower than loaded.
Gzip plus sidecars grows versus loaded; no persistent-space improvement is claimed.

`checkpoint.json` preserves inherited fields and adds `active_support_study`,
`active_support_decisions` and `active_support_proposals`. Load the acquired
170-entry index rather than rebuilding it. Its six source catalogs remain in
order; future extension accepts only a new batch. The union retains 17,532 keys /
54,337,536 SQLite / 4,206,056 gzip bytes, adding 371 keys. Every earlier payload
remains; two alternative certificate occurrences are kept in trial archives.
New decisions have 146 direct roots and 46 guards, including the two SAT results.

All 461 tests, nine ordinary-solver archive checks / 3,456 replays, every union
node, 1,421 inherited decisions and all new decisions pass with fresh validation
search disabled. All 364 prior sources and 4,042 artifacts / 71 manifests remain
unchanged. The analyzer brings the source ledger to 369. Structural authority
stays 2,614 patterns / 259 pairs / 17 missing children, original 17/24 / 999 steps,
separate supplemental 24/24 / 208 and the original case 7 discovery pointer.
No new original structural closure, Lean result or uniform-polynomial SAT bound.

The manuscript builds to 197 pages without warnings; all 64 proof blocks are unchanged.
