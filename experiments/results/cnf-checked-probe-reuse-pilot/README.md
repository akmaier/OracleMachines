# Bounded exact probe-check reuse pilot

Eight fixed prior sources (858, 875, 907, 970, 1042, 1194, 1185, 1467) compare
unchanged checking with 32 KiB, 256 KiB, 1 MiB and 8 MiB logical cache budgets.
All modes produce the **same database bytes**, source identities, structural
profiles and summaries, SAT answers and cold-replayed certificates. No new
structural coverage is claimed. The shared archive is retained once.

| Cache budget | Total seconds | Cold replay seconds | Hits / lookups | Retained peak bytes |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 3.59508 | 1.73302 | none | none |
| 32 KiB | 3.16483 | 1.42529 | 1,317 / 2,252 | 32,768 |
| 256 KiB | 3.07915 | 1.42505 | 1,385 / 2,252 | 262,142 |
| 1 MiB | 3.20282 | 1.45756 | 1,387 / 2,252 | 1,048,569 |
| 8 MiB | 3.18566 | 1.44617 | 1,387 / 2,252 | 2,603,844 |

These are sequential single samples on selected sources; they establish neither
an optimal budget nor a general runtime benefit. The 1 MiB budget was fixed for
the full comparison, rather than selecting the fastest noisy pilot time. The
256 KiB case gets almost all observed hits and motivates a later memory/capacity
comparison. Cache bytes count retained ASCII source/proof/config keys and result
strings, excluding Python overhead, transient serialization and original state.

Only successful independent checks enter the ephemeral LRU cache. Exact input
serialization and full-key equality are paid on every lookup. Source, proof or
policy edits miss the cache, and hits return newly decoded results. Eviction
causes rechecking; cold replay starts empty. Persistent evidence and namespace
are unchanged. All 409 tests pass, including malicious edits and cold corruption.

The original report remains unmodified. Its runner fingerprint resolves to the
byte-identical `runner-before-json-comparison.py` snapshot: the later full-run
harness correction compares canonical JSON profile encodings because saved JSON
uses lists where some live tiny profiles use tuples. The preserved initial failure
is in `../cnf-checked-probe-reuse-initial-check/`; no failed measurements count.
The later implementation/test snapshots described below preserve the other changed fingerprints.

**Superseded pilot:** subsequent review found a tuple/list cache-key alias for
malformed direct inputs. The guarded implementation is tested and measured in
`../cnf-checked-probe-reuse-guarded-pilot/`. The original module/test fingerprints
resolve to `implementation-before-type-guard.py` and `tests-before-type-guard.py`;
the earlier pilot numbers must not be presented as final guarded measurements.
