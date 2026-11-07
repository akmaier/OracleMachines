# Preserved development pilot

This is the first run of `run_priorities.py` at commit `b080a39`.
The direct-reference path mistakenly passed raw SATLIB text to CaDiCaL, while
the service normalized parsed clauses. SATLIB trailing delimiters caused 24
exit-1 errors in that reference. Those errors are a harness defect, not solver
performance. All original records and fingerprints are retained here.

The final study normalizes original CNF in the direct path, includes a regression
for this format, and reruns every mode with fresh databases. No solver parameters,
source selection, or algorithm were tuned in response to this pilot. Instances
were unused in earlier project studies, but the final run is a rerun of this
follow-up pilot, not a new blind development holdout.
