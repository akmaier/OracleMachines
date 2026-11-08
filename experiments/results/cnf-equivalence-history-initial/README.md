# Initial equivalence comparison, preserved

This sequential 23-case run is valid evidence for the recorded inputs, but its
signed-equivalence additions already satisfied the acquired model. Merely
complementing the unsigned recipe did not complement the solver's chosen model.
The control therefore tests compatible signed additions, not signed repairs.
`runner.py` preserves the exact runner and `report.json` its other fingerprints.
All 46 archives and 82 earlier archives replayed without byte changes.

The main comparison in `../cnf-equivalence-history/` corrects this control to
force signed block changes and also measures the first update after a restart.
Keep this run to expose the control-design mistake and retain its measurements;
do not combine its timings with the corrected run.
