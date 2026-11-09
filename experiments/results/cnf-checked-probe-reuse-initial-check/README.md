# Preserved harness failure

The first full run stopped on case 0 before producing measurements: direct Python
equality compared a live tuple-containing profile with its saved JSON list form.
This is a comparison-harness failure, not a solver or cache discrepancy. The
corrected runner compares exact canonical JSON encodings, matching the persistence
contract. The completed pilot and its original report are preserved; its runner
is copied byte-for-byte to `../cnf-checked-probe-reuse-pilot/runner-before-json-comparison.py`.
The old pilot runner fingerprint resolves to that snapshot. No partial full
measurements or failed proof checks are counted as successful results.

The restarted full run was intentionally interrupted during baseline cold replay
when code review found that a cached JSON key could identify a tuple of original
attempts with a valid list, bypassing the old checker's list requirement. The
implementation now delegates non-list attempts to the old checker before lookup;
a regression test first warms the cache, then requires rejection of the colliding
tuple input. The preliminary pilot implementation and tests are preserved beside
its runner snapshot; its numbers are not measurements of the final guarded code.
No completed full report was produced by either interrupted/failed run.
