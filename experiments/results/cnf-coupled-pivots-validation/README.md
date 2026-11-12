# Coupled search validation

All **535 Python tests** pass. They include exhaustive admissible two-variable
projection/model lifting, a descendant-budget interruption with a completed child,
restart and zero-budget reuse, exact coupled replay, and rejection of corrupted
summaries, pivots and maps. A separate five-table smoke check passed roundtrip,
idempotence and conflicting-payload rejection. The full suite log retains 20
SQLite `ResourceWarning`s during garbage collection. The four new tests, run
alone with forced collection, emitted zero such warnings; the full suite passed.

The artifact validator restores the exact five-table seed, binds all source and
input hashes, checks old-row counts and emitted deltas, rebuilds identical logical
tables and checks byte-preserving idempotence. Every new pattern-node identity
occurs in the recorded admission fingerprints; each input stays below 32 admitted
states and eight new trials. No experimental input reaches the state limit.

Both histories previously passed full graph/source/solver cold verification and
separate exact old/coupled trial replay without changed bytes. No replacement
closes, and endpoint stores contain no solved evidence. Source bindings, old
one-pivot trials and ordinary solver proofs are unchanged. The original history
has 41,331 pattern nodes / 25 coupled trials; the repeated one has 24,999 / 15.

Continuation analyses are bound by report/script hashes. The core diagnostic's
growth counts are independently reconstructed, and a separate variable-occurrence
enumeration confirms the full 30 first-pivot / 662 ordered-pair set under the pair
cap. All 35 variables fit below the candidate cap. These are projection-admission
facts, not endpoint recognitions or SAT lower bounds.

`validation.json` is the final record, including post-run analyses.
`pre-analysis-validation.json` preserves the earlier intermediate check record.
Timed experiments finished before archive analysis. Formal sources and manuscript
are unchanged from `fc16148`; no new Lean build is claimed.
