# Targeted split-variable implication discovery

The optional solver adds at most one targeted implication search after the
unchanged eight-root whole-cover phase. It reuses cached positive/negative
reachability results and the existing direct excluded-branch compiler. All
fourteen saved recognition misses, including six split nodes, now yield checked
paths. Existing native proof formats and defaults remain unchanged.

Four serial workers compare frequency-only and targeted reuse in opposite orders
on sixty fresh queries. All return 44 SAT / 16 UNSAT with identical preceding
discovery evidence. Targeted selections rise two -> twelve, expansions fall
169 -> 163, and compiled excluded children rise one -> five. Actual native
additions fall **252 -> 250**, payload **2,599 bytes**, and propagation visits
**29,008 -> 27,154 (6.39%)**. The extra 56 searches, 8,756 ranking-literal visits,
source checks, serialization and full history replay are included.

Timing is unstable: query deltas are -0.00495 / -0.25149 seconds, while complete
worker deltas are +0.08083 / -4.92162 seconds. Unchanged preparation and cold
replay also vary sharply. The raw mean query improvement of 28.21% is not a
stable speedup. Trial SQLite size is unchanged, gzip falls 114 bytes, and sidecars
grow about 5.4 KB. Both policies remain optional.
See [the full analysis](../../../research/targeted-backbone-discovery.md).

## Reproduce

From the repository root, use a new destination:

```sh
python3 experiments/compare_cnf_targeted_backbone.py prepare /tmp/cnf-targeted-new
python3 experiments/compare_cnf_targeted_backbone.py /tmp/cnf-targeted-new
python3 experiments/validate_cnf_targeted_backbone.py /tmp/cnf-targeted-new
python3 experiments/analyze_cnf_targeted_backbone.py /tmp/cnf-targeted-new
python3 experiments/diagnose_cnf_targeted_backbone.py /tmp/cnf-targeted-new
python3 -m unittest solver.test_cnf_targeted_backbone solver.test_cnf_binary_backbone solver.test_cnf_binary_clause_cover solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

Workers run serially, without concurrent study tests/audits/profiling.
`protocol.json` binds runtime sources and unchanged workload-selection rules.
Complete-worker costs include preparation, recognition, checking, persistence,
compression, warm reuse and full cold replay. Posthoc analysis, final report
rewrites, validation, tests and manuscript compilation are outside worker timing.
The saved-source mechanism study uses separate empty archives and reports no
timing; its six-node saving is not a historical-prefix replay saving.

## Preserve and resume

`checkpoint.json` preserves all **27,888 prior native payloads / twenty-two
extensions** byte-for-byte, reaching **28,145 native keys / twenty-six extensions**.
It adds 112 native and eight negative composed records to 5,530 inherited records.
Union growth is 647,168 SQLite / 71,842 compressed bytes, including comparator
history. Four alternative native roots remain in trial archives; the union keeps
its first payloads. The targeted solver is explicitly optional, and affine
negatives still use the `TerminalStore` reader.

All **1,212 tests**, **43 focused tests**, 240 chronological query audits, sixteen
publication counter audits, 48 exhaustive family truth tables, warm answers and
full historical replay pass. Eight new tests check small-formula truth and
binary-forcing detection over 4,096 sources, cover priority, search-cache reuse,
independent budgets, direct compilation, signed lifting, cold readers and edits.
Full tests retain 44 pre-existing SQLite warnings; focused tests have none.
All 574 prior sources, 7,568 artifacts and 107 manifests are unchanged.

`attribution.json` records twenty sources with binary-implied equivalences and no
forced literal, including eleven ordinary split nodes. Mutual reachability is
cross-checked by 242 two-CNF disagreement refutations over all diagnosed blocks.
Exact full-source substitution with native certificates is the next experiment;
these diagnosed opportunities are not yet measured savings. The census includes
model/subsumption records, and arbitrary CNF still has unresolved wide-clause
interactions. No new Lean theorem or unrestricted-SAT resource bound is claimed.

The **222-page manuscript** builds with a clean final log and all **64 prior
proof blocks unchanged**. Final source ledger: **581**. New manifest: **40
artifacts**. Next preservation audit: **7,608 artifacts / 108 manifests**.
