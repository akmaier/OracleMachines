# Validation of the retained-clause subsumption experiments

Runtime checkpoint `14ae642` contains the optional checker, discovery policy,
model lifting, regression tests and Lean proof. The comparisons cover the saved
59-leaf frontier in both execution orders and the 83 original prior misses.
Neither produces additional structural closures; the feature is not promoted.

`validation.json` binds the three reports, all six complete archives, runtime
fingerprints, subsequent growth diagnostic and manuscript to exact hashes.
The validator confirms:

- All 506 Python tests pass; the Lean build and axiom audit pass at 4,173
  declarations / 2,009 theorem declarations. The actual logs are retained.
- All archives decompress to their reported hashes/sizes, pass SQLite integrity
  checks and have identical ordinary-solver residual evidence between modes.
  The original-input baseline matches the previous bounded archive exactly.
- Each mode's leaf database is identical in the two execution orders. Source
  outcomes, profiles and ordinary solver counters agree; gained/lost closure
  sets are empty in all comparisons.
- New-edge counts match the additional endpoint/model diagnostics: ten subsumed
  edges in each leaf comparison and 324 in the original-input candidate. The
  retained witnesses contain 12 and 404 omission references respectively.
  Existing-rule edges receive complete cold proof checks; their additional
  endpoint diagnostic is not repeated in these runs.
- The growth diagnostic is bound to its reports, script and helper, including
  the exact earlier script snapshot. It finds zero candidates under the current
  joint non-growth rule, 48 leaves with a plain non-growing-clause candidate and
  49 with a subsumption-assisted candidate. It implements no new growth policy.
- All 63 previous manuscript proof blocks remain unchanged and all 226 labels
  are unique. LaTeX builds without warnings, overfull or underfull boxes.

`visual-review.json` binds inspection of pages 129--131 to the final PDF. The
new section and following transition are legible without clipping or overlaps.
Visual review is separate from proof and runtime validation.

The three comparison reports retain complete cold audits, old-row preservation,
source/model checks, memory samples and separate preparation/persistence costs.
Cold audits leave bytes unchanged. New subsumed-edge endpoint/model diagnostics
take 33.47933 seconds on the original inputs, outside acquisition. The ordinary
decision solver still searches the original CNFs.

The measurements are selected prior failures and repeated controls, not a new
holdout or full-corpus rerun. Semantic Lean results do not refine the Python
implementation. The per-intermediate-CNF size argument does not guarantee an
admissible pivot or bound the entire retained branching history. See
[the mechanism and next gap](../../../research/subsumed-elimination.md).
