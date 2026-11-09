# Independent reconstruction with shared untouched clauses

The preceding source-index optimization left simplification checking as the
largest named own-time cost on source 1194. This experiment changes only the
checker's residual reconstruction. The ordinary SAT decision solver, unit-reason
replay, conflict checks, pure rounds and recognition policy keep their semantics.

## Measured reuse and a rejected implementation

The [twelve-source observer](../experiments/results/cnf-simplification-reuse-diagnostic/report.json)
records 12,209 checks, 2,758,965 input literal occurrences and 1,003,961 clause
positions. Complete semantic checks repeat 2,649 times (21.70%); clause objects
repeat at 669,809 positions (66.72%). On source 1194, only 82 of 2,303 calls reuse
the whole source object. A simulated 256 KiB full-key/result cache hits 392 times
there, while all lookups serialize 3,321,249 key bytes. The observer retains
objects and serializes inputs, so it is not a timing or allocation measurement.

An independent clause-support cache seemed more promising. It validates immutable
clauses, retains their variable sets and uses disjointness from the current
assignment to share untouched tuples. It stores no proof verdict. However, its
first eight-source pilot increases discovery 2.42915 -> 2.77177 seconds. Batching
counters and using set-to-set intersection still gives 2.39739 -> 2.64530 seconds.
These are separate sequential pilot comparisons, not controlled significance
claims. Both reconstruct the same archived proofs and preserve database bytes.
They expose preparation and bookkeeping overhead on short clauses. The code,
snapshots and failed results remain available, but this cache is not selected.

## Selected method and correctness

`SinglePassCheckInventory` optionally scopes `reconstruct_single_pass` into the
existing independent checker. The default reconstruction remains available.
There is no new retained index, checked-result cache, persistent format or policy
identity. This helper does not call discovery's `restrict` or use its indexes.

Let alpha be the already checked Boolean unit assignment. For each clause C,
inspect literals in order. A true assigned literal drops C immediately. A false
assigned literal is omitted; the first such occurrence allocates a buffer holding
the preceding unassigned prefix. Later unassigned literals append to that buffer.
If no occurrence is removed or satisfies C, share C when it is an exact tuple,
or convert an exact list to a new tuple. Check the unchanged unit-fixed-point
obligation on every surviving clause. Other clause containers, nonstandard
literals or assignments fall back to the reference scan. Mutable lists are
never retained or returned as mutable residual clauses.

The prefix invariant proves correctness. Before finding a true occurrence, every
visited assigned literal is false. While the buffer is absent, no visited literal
has been removed, so the visited prefix is already the exact residual prefix.
Once allocated, the buffer contains exactly the unassigned occurrences of the
visited prefix, in order and with multiplicity. The first false occurrence and
each subsequent iteration preserve that invariant. A true occurrence makes the
whole clause satisfied. Otherwise the final tuple is precisely restriction of C
by alpha. Original clause order and empty clauses are preserved. The same length
test accepts or rejects exactly the same unit fixed point.

Unit reasons and conflicts are checked before this helper. Pure-round checks
consume the same ordered residual afterwards. Thus the complete checker returns
the same residual and lifted assignment, or rejects the same certificate, on
valid CNFs. Sharing an immutable tuple changes no literal or clause order. There
is no identity shortcut, lifetime invalidation requirement or cross-call trust
assumption. Edits are scanned afresh. This is an algorithm-level argument and
differential test result, not a Lean refinement of Python.

## Resource account and limits

For m clauses, L literal occurrences and A assignment entries, let V <= L be the
occurrences visited before satisfaction/end, and K <= L the logical entries copied
into pending buffers or untouched mutable-clause outputs. Under constant-time
dictionary access and word operations, eligible reconstruction takes
O(1+A+m+V+K), hence O(1+A+m+L) worst-case time. Prefix slicing, temporary-list
construction and final tuple conversion add constant multiples of copied lengths;
the `single_check_copied_literals` counter counts logical buffer/output entries,
not every physical reference copy. It includes a partial buffer later discarded
because a later literal satisfies the clause.

The outer result still has O(m) references. Changed clause tuples require their
residual literal storage, and the current pending buffer adds O(maximum clause
width) temporary space; intact immutable clauses share existing storage. There
is no retained cross-call state from this helper. Mutable clauses still require
tuple copies. This bounds additional reconstruction storage, not the separately
retained source, proof graph, existing caches, archive or whole process.

The worst-case asymptotic scan bound is unchanged. The potential gains are fewer
Python generator scans and copies, independent of having previously seen a CNF.
All assigned-variable lookups, type guards, prefix copies, tuple conversion and
fixed-point checks remain charged. Early satisfaction, small inputs, many changed
clauses and unusual fallbacks need measurement and can regress. Long integer
labels and dictionary collisions add costs beyond the conditional word account.

No new tractable family or efficient unrestricted acquisition result follows.
The same 116 source misses still require certified relations or exact interaction
decompositions. Cheaper existing checks support that investigation.
