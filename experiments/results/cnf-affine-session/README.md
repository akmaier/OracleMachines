# Fresh queries with resumable negative affine reuse

See [the analysis](../../../research/affine-session-reuse.md) for the interface,
resource accounting, measurements and remaining gaps. The session performs an
exact-target extension lookup before discovery, publishes retained checked affine
negatives, and indexes guarded negative conclusions for warm reuse. Explicit
versioned replay uses the already-checked affine terminal; native search remains
unchanged and cannot acquire extension dependencies.

The fresh sixty-query stream excludes all inherited query and native roots.
Four serial workers compare affine/session and the reverse order. Both return
**37 SAT / 23 UNSAT**. Three negative targets replace 67 native nodes with three
certificates. Combined new additions fall **344 -> 280**, payload
**460,091 -> 384,362 bytes**, and mean query time **7.76%**. Both complete-worker
deltas are negative, but the mean saving is only **0.45%** and full cold replay
still takes about thirteen seconds. Sixty extension lookups produce zero hits;
all miss costs are included. Fresh acquisition savings do not come from cache hits.

All 120 paired discovery records and counter sets match. All twelve coupled
inputs avoid native expansion, through nine models and three negative proofs.
This is finite measured coverage; no general coupled-family or unrestricted-SAT
resource bound follows. Random-three acquisition and graph discovery remain the
largest measured unresolved work counters.

## Reproduce

Run from the repository root, using a new output directory:

```sh
python3 experiments/compare_cnf_affine_session.py prepare /tmp/new-affine-session
python3 experiments/compare_cnf_affine_session.py /tmp/new-affine-session
python3 experiments/validate_cnf_affine_session.py /tmp/new-affine-session
python3 experiments/analyze_cnf_affine_session.py /tmp/new-affine-session
python3 -m unittest solver.test_cnf_affine_session solver.test_cnf_affine_negative -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

Preflight completed forty prepared queries, warm reuse and full historical cold
replay across both modes before production began. Production ran serially without
concurrent tests, builds or profiles. Independent validation, exhaustive family
truth and attribution ran afterwards. `protocol.json` freezes the runtime/test
source ledger; the final ledger also binds the posthoc validator and analyzer.

## Resume

`checkpoint.json` retains the ordinary native metadata and adds explicit extension
catalogs and the `experiments.cnf_affine_session.TerminalStore` reader. Restore
`reference_union` with the existing archive utility. Use `TerminalStore(solver)`
and `NegativeChainBank` to check/reuse the negative catalog, or the module's
`evaluate` function for exact target lookup followed by checked publication or
native fallback. The supported discovery version fixes its limit at four.
For a brand-new database, create the versioned table with
`TerminalStore(solver, create=True)` before opening the session. Existing native
checkpoint readers see native proofs only; they do not silently trust extensions.

The union preserves all **26,743 prior native payloads and seven extension
payloads byte-for-byte**. It contains **27,087 native keys and ten extensions**,
with 117 new native and three new negative chain records alongside 4,990 inherited
composed records. It retains comparator results and occupies **83,312,640 SQLite
bytes / 6,318,187 compressed bytes**. Growth is 888,832 / 95,921 bytes over the
parent; this differs from the smaller matched session-trial storage.

Independent validation checks all 240 chronological queries, six publication
counter records, 48 exhaustive family truth tables, every warm answer and full
historical native/composed/projection replay for each archive and the union.
The ten extension chains replay with zero native-alternative reads. There are
no conflicting alternative native payloads in this comparison. Four new tests
cover terminal selection, cold exact lookup with discovery disabled, known native
fallback, and sixteen generated cross-family truth/warm comparisons.

The next recognition target is random-three case 56: 33 expanded nodes and 8,144
propagation visits with no extracted equations. Random-three totals 140 expanded
nodes / 27,761 acquisition visits. Graph discovery pays 25,375 visits; cases 47
and 35 still have no proposal. Hidden structure, large free dimension, complete
projection and extension-aware internal support scheduling remain open.

All **1,181 tests**, twelve focused tests, 240 chronological query audits and
six negative publication-counter audits pass. All **548 prior sources,
7,399 artifacts and 103 manifests** remain unchanged. The final source ledger
has 553 entries, including the posthoc validator and analyzer. Full
historical native/composed/projection replay passes for every worker and the
union. The 219-page manuscript builds with all 64 existing proof blocks unchanged
and a clean final compiler log. The full suite retains 44 existing unclosed-SQLite
warnings; focused tests have none. No new Lean theorem is claimed.

New manifest: **40 artifacts**. Next preservation audit: **7,439 artifacts / 104 manifests**. Final source ledger: **553**.
