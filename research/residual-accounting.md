# Residual archive accounting

The optional `AccountedResidualSolver` preserves the existing search, certificate
checker and stored residual rows. Its superclass remains the census control.
The change targets the full `count/sum(length(...))` performed after every query,
including cache hits. This is metadata work, not a new SAT algorithm.

One private SQLite row holds the residual count, the historical SQL payload-length
total and a dirty flag. Five triggers maintain it in the same transaction as
ordinary insertions, updates and deletions. Other connections and the old solver
also fire these triggers. Writes to unrelated pattern tables do not invalidate
the totals. Every open independently reconstructs the counters under a write
lock; old residuals are never rewritten. An unchanged cold open leaves the
archive bytes unchanged after this one census.

SQLite replacement can delete a conflicting row without firing delete triggers
when recursive triggers are disabled. Before a possible key or rowid conflict,
we therefore mark the totals dirty. The next metadata read reconstructs them
under a write lock. Ignored duplicates and upserts can cause conservative extra
censuses. Rollbacks restore both data and counters, including reconstruction in
a caller-owned transaction. Direct modification of the private accounting schema
during an open connection is outside the contract. Counters do not certify SAT
answers; the original proof checker still does that.

Let B be the residual key/payload length and R the number of residuals. Opening
costs O(B+R); a clean metadata read accesses one row. An ordinary insertion adds
one indexed conflict check and length accounting for its key/payload, plus a
constant number of metadata updates in the existing transaction. Logical retained
accounting state is one row and five fixed trigger definitions. Conflicting
writes can still incur O(B+R) reconstruction at the next read. Disk-page overhead,
commit latency, initial scanning, locking and cold verification remain charged.
The old `archive_payload_bytes` field retains SQLite TEXT length semantics;
generated JSON is ASCII, but arbitrary Unicode or NUL-containing SQL values must
not be described as UTF-8 byte counts.

Initial validation: 476 Python tests pass, including exhaustive two-variable
answer/proof/metadata equivalence, independent legacy writers, rollbacks,
replacement under both recursive-trigger modes, cold preservation and resource
budget failure. A first budget-test fixture unexpectedly reused two identical
canonical children; disabling reuse for that test exercises partial persistence.
Matched full, fresh and empty-history measurements are the next step before any
default change. Structural coverage and unrestricted-SAT obligations are unchanged.
