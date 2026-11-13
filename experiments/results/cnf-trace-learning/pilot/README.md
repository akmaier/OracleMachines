# Exploratory observations

The preliminary graph scan found no forced values and only the previously saved
equivalence. Bounded augmented-CNF probes returned two equivalences and one
forced value; same-variable controls showed a genuine propagation difference on
cases 31 and 32. The final parent-bound experiment independently reproduces and
checks these results. These pilot runs were untimed, used temporary reconstructed
histories and did not add persistent recognition nodes.

`explore.py` records the initial read-only exploratory procedure. The controls
were evaluated interactively with the augmented binary-frequency choices and
are retained in `same-order-controls.json.gz`; the final driver contains the
reproducible control procedure. `initial-test-failure.txt` preserves an indexing
error in a corruption test: the first clear trace had no unit to corrupt. The
corrected test selects a unit-bearing trace. This was a test-fixture error, not
a rejected proof or solver answer.
