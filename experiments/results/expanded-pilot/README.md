# Development pilot, retained before fixes

This one-repetition run is diagnostic evidence, not the final comparison.
It used a two-second query budget: 54 runs, 420 planned queries, 388 completed
correct answers and 32 errors. Twelve direct CaDiCaL calls rejected SATLIB's
historical `%` trailers; twenty checked circuit queries hit native stack overflow.

The final runner normalizes DIMACS syntax without changing the CNF. Native ASCII
conversion and counted length discovery now avoid one stack frame per input bit;
the latter replacement has a Lean equality proof. The pilot's raw records,
source fingerprints, selection, timings, and errors remain unchanged. No SATLIB
source files are redistributed here. See the source URLs and hashes in the
manifest; dataset provenance is separate from this repository's code license.
