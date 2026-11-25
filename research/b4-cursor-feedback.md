# Compose B4 failures into a checked fifth bank

Checkpoint: 25 November 2026. Combining the 69 saved failed probes refutes
**four more events**, with no new assumed probes. All four distinct native
certificates pass both independent readers. Sampled structural coverage reaches
**221/246**, leaving **25 unresolved**. These four formulas already had UNSAT
answers in the inspected reference snapshot; the gain is a newly recognized
structural route with explicit native certificates, not four previously unknown
truth values or a new unrestricted tractability result.

The direct-unit shortcut remains useful on this new layer: complete positive
trial time falls **73.35%** and encoded bytes **81.40%** versus fresh bounded
solving. All four roots improve. These local trials charge compilation, warm
checking, both cold readers and persistence, but prior acquisition, discovery
and unresolved fallback are additional. The complete workload advantage remains
unestablished.

## Pattern and exact composition

The [previous B4 frontier](b4-probe-cursor.md) retained 69 checked contradictions
under individual assumptions in 13 open cases. Each proof on B4 under literal
`l` implies the exclusion `not l`. Append only those checked units, retaining
their proof origins, to obtain B5. A single unconditional propagation pass can
then expose interaction among exclusions that no individual probe found.
The base control constructs and validates the same provenance but propagates
B4 instead. All 29 base results remain open; B5 refutes `(1,44)`, `(1,45)`,
`(37,20)` and `(64,31)`. No assumed literal is newly searched in either arm.

A small test makes the interaction explicit: binary clause pairs force three
variables individually through failed assumptions, while a clause forbids all
three being true. Single-assumption propagation has no opposite failed pair;
combining the three exclusions gives an unconditional contradiction. The test
checks the full six-variable truth table and reconstructs native proofs.

Source clauses, conditional guards, previous failed probes, complete closures
and both cursor bindings are checked before discovery or a warm root lookup.
Open-history entries are not axioms. The new failure proof is checked on B4,
never on B5, so it cannot cite its own exclusion. Native reconstruction expands
each used exclusion through strictly decreasing banks B5/B4/B3/B2/B1/B0. Support
slicing remaps clause identifiers and variable coordinates, rechecks compacted
proofs, and falls back to full support if required coordinates are absent.
Only existing native empty, unit, split and component rules are published.

The inherited direct-unit shortcut tests the actual canonical source residual
before expanding a trace. Its query-local allowance charges gate clauses,
index clause/literal slots and occurrence visits; open or interrupted attempts
fall back. It introduces no unproved derived unit into the source. The new
compiler also has a disabled-shortcut control for the same B5 proofs. Production
defaults, old certificates and cumulative authority tables remain unchanged.

## Matched costs, including regressions and storage

Both discovery arms run twice in opposite order for every target, on the same
29 exposed cases. They charge source-prefix reconstruction, all provenance
checking, bank/index preparation and propagation. The base census totals
0.74783 seconds and feedback 0.75261 seconds: this is a small time increase,
not a discovery speedup. Feedback reconstruction takes 0.55531 seconds, about
74% of its census, and discovery 0.19336 seconds. Occurrence visits rise from
1,324 to 4,419 as more implications propagate. Input loading/startup, historical
acquisition, final audit and the separate closure diagnostic are additional.

Four distinct gained roots run twice in reverse orders for each of three
methods, producing 24 isolated positive trials:

| Summed per-root means | Fresh | B5, shortcut disabled | B5, direct units |
| --- | ---: | ---: | ---: |
| Solve/compile (s) | 0.91648 | 2.40178 | 0.27087 |
| Warm check (s) | 0.00837 | 0.04325 | 0.04406 |
| Both cold readers (s) | 0.95576 | 2.03686 | 0.22018 |
| Persistence (s) | 0.35997 | 0.67460 | 0.05643 |
| Complete local trial (s) | 2.25891 | 5.17953 | 0.60201 |
| Encoded key/payload bytes | 4,488,235 | 6,733,895 | 834,744 |
| Native records | 346 | 2,172 | 215 |
| Maximum process RSS (bytes) | 71,450,624 | 93,044,736 | 56,098,816 |

Direct closure reduces compile time 70.44% against fresh and 88.72% against the
disabled compiler; complete time falls 73.35% and 88.38%, respectively. Every
root improves in compile time, complete time and bytes against both controls.
The disabled compiler's complete cost is 2.29 times fresh and its bytes 50.03%
larger, so the expansion regression remains preserved. Warm checking with
derived provenance remains more expensive than fresh warm lookup. No claim of
an improvement on every future instance follows from four cases.

Support slicing reduces 5,192 source literal occurrences to 1,322 in both B5
compiler arms. Direct shortcuts make 185 attempts, of which 95 close a residual.
Native splits fall from 2,123 to 106 and frame constructions from 4,334 to 217.
All 12 unique archive/root pairs pass independent snapshot and canonical
verification. Separate archives may duplicate shared records; summed encoded
bytes are not the size of a merged lifetime database.

The 25 open B5 closures retain **151 assignments**. Nine cases gain **85**
assignments, including **49 beyond the 36 new exclusion variables** retained
in those cases. For example `(61,1)` gains 30 assignments from four exclusions.
The other 16 closures are unchanged. Complete open-state history plus closures
occupies 1,199,685 bytes, versus the previous 1,379,665-byte export for 29 cases.
The lower number includes removal of four closed cases from the open export;
it is not compression of an identical set. Older exports, all proof layers,
trial archives and gained-case provenance are preserved, so repository/lifetime
storage still grows. Closure reconstruction is a separately timed 0.18722-second
diagnostic outside bounded discovery.

## Bounds, checks and next target

Appending F checked exclusions needs a clause map and a canonical sort of the
new bank, in addition to validating the full input provenance and F proofs.
For C clauses and L occurrences, the live unit index has O(C+L) slots. One
propagation attempt uses the explicit occurrence and trace allowances, but
index construction, proof checking, source reconstruction, support processing
and serialization remain outside those allowances. Native expansion can still
create many distinct contexts. Direct closure bounds only its additional work;
neither a fixed number of layers nor small observed support proves polynomial
total construction, replay or lifetime storage for arbitrary CNF.

All **1,977 tests**, including **112 focused tests**, pass. New tests cover
joint failure interaction, selected/full support, direct/disabled shortcuts,
budget fallback, malformed and forward proof reasons, warm provenance checks,
open-history non-authority and generated small inputs against complete truth
tables. All 1,098 earlier source fingerprints, 26,882 artifact entries in 193
parent manifests and 64 original manuscript proof blocks remain unchanged.

**Next coverage target:** freshly bound probing on the nine stronger B5 closures,
especially the case with 30 new assignments. Old B4 completed lists cannot skip
candidates on changed B5 banks. For the sixteen unchanged cases, resume the
preserved B4 frontier beyond its first 64 candidates, or test stronger interaction;
do not reacquire the same prefix. Repeated reconstruction/provenance preparation
remains the dominant avoidable census cost. Retain direct-unit closure as the
measured native compilation baseline and keep acquisition costs explicit.

Resume `experiments/results/cnf-b4-cursor-feedback/checkpoint.json`, especially
`b4_cursor_feedback.remaining-closures`. Reproduction uses `prepare`,
`run_census`, `cases`, `run_trials` in `compare_cnf_b4_cursor_feedback.py`, then
`validate` and, after the test/manuscript checks, `seal` in
`validate_cnf_b4_cursor_feedback.py`, with a fresh output directory containing
the preserved pilot and source snapshot.
