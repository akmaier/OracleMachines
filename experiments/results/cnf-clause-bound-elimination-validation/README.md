# Clause-count elimination: validation checkpoint

`validation.json` binds four matched comparisons (eight complete archives) to
their runtime fingerprints, exact case lists, prepared-prefix provenance,
compressed and restored hashes, SQLite integrity, exact ordinary residual-table
equality and source/profile/search-counter agreement. Every new elimination
edge has independently solved endpoints and SAT model restoration; every archive
node passes cold proof checking without changing bytes. All old rows survive.
The original-input baseline reproduces the earlier bounded-elimination database.
Opposite-order leaf runs reproduce both per-mode databases exactly.

- **511 Python tests** pass, including exhaustive tiny-CNF projection and lifting,
  random edits, signed large identifiers, positive literal growth, rejected
  clause growth, SQL persistence and corrupted-certificate checks.
- Lean builds successfully and its transitive axiom audit passes at **4,195
  declarations / 2,018 theorem declarations**, with no admits or new axioms.
  The new module proves conditional formula/chain size bounds, not an available
  pivot or a verified Python implementation. Formal source hashes are retained.
- All **63 prior manuscript proof environments** remain unchanged from
  `e5225f4`, with **227 unique labels** after adding Section 12.77.
- The rebuilt 139-page PDF has no LaTeX, overfull or underfull warnings. Pages
  129--132 were rendered and manually checked; `visual-review.json` binds the
  reviewed images to the final manuscript and PDF hashes.
- The exact final-frontier diagnostic records all pivot margins, runtime-capped
  versus uncapped opportunities and retained-clause subsumption. These are not
  additional integrated-policy results.

The 83-input original-source comparison improves structural closure from 29 to
31, at increased acquisition and storage cost. The repeated 96-input control
retains exactly 88 closures, with higher query time. The original-source endpoint
diagnostic separately costs 961.43125 seconds using the historical reference
solver, which retains its per-solve SQL census. Its cost split is not profiled.
No full-corpus rerun, untouched holdout, default promotion, full Python refinement
or efficient arbitrary-SAT partition is claimed.

Runtime implementation checkpoint: `2c422ff`. Raw logs are retained here. The
validator expects the named reports and logs and writes a fresh validation
folder; preserve this folder before rerunning. See the [mechanism and next
step](../../../research/clause-bound-elimination.md) and [ranked gap
record](../../../research/structural-reuse-priorities.md).
