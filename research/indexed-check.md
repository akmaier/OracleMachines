# Reuse source structure inside independent reconstruction

The cold-cache profile of prepared source 1194 identifies `reconstruct_single_pass`
as the largest individual Python own-time entry: 2,617 calls, 0.33136 own seconds
and 0.48292 cumulative seconds in a 3.08000-second instrumented query. Normalization
is second by own time (0.20585 seconds). Profiling overhead is charged and cumulative
times overlap. This diagnostic starts from the old seed, not the full benchmark's
preceding-query cache state. It motivates a reconstruction experiment, not a speedup
claim. The exact profile is retained in `cnf-indexed-check-profile`.

## Independent source index

The optional `IndexedCheckInventory` uses `CheckedReconstruction` in both new and
prepared checker views. The views share one bounded source index, separate from
the discovery restriction index. The persistent policy and certificate format are
unchanged. Unit reasons, conflicts, pure rounds, probe traces and final source-bound
results continue through their existing independent checks.

Admission reads the actual CNF. Only exact built-in tuples of exact tuple clauses
containing nonzero exact integers qualify for identity reuse. An entry holds the
source alive, maps each variable to all clause positions where it occurs, and
records every source clause of width at most one. Mutable inputs, subclasses,
unusual assignments, disabled indexing and over-budget sources use the prior
single-pass implementation. Failed certificate checks may leave valid source
representation facts cached, never a successful proof verdict.

For assignment A, let T be the union of clause positions in the postings of its
variables. If a clause position is outside T, none of its literals is assigned;
its residual is therefore exactly the original clause. It may be shared unchanged.
For positions in T the checker inspects the actual literals, drops a satisfied
clause, and removes falsified literals from every other clause. It preserves
source order, duplicates and empty clauses. With unit fixed-point checking enabled,
an untouched clause already of width zero or one is rejected; every touched,
unsatisfied reconstructed clause must also have width at least two. These two
checks cover all clauses. The occurrence index is derived locally and is neither
read from a certificate nor borrowed from discovery.

The index never caches an assignment, policy verdict or reconstructed result.
Changing assignments or the `units` flag therefore requires a fresh reconstruction.
An edited immutable source has a different identity and must be admitted again.
Retaining the source and checking `is` prevents object-id recycling from producing
a false match. No source comparison is bypassed for mutable or unusual containers.

## Cost and scope

Let m be the number of clauses, L their literal occurrences, a the number of assigned
variables, o the visited posting entries, and L_T the literals inspected in affected
clauses. Successful admission costs O(m+L) representation work, followed on each use
by O(a+o+m+L_T) work, including ordered output assembly. The previous reconstruction
visits the source literals on each call. Dictionary/set operations use the Python
implementation's expected-cost model; integer bit lengths and collision behavior
are not constant-cost guarantees. Oversize and low-reuse sources can lose time to
attempted admission before fallback. No universal speedup or sublinear-in-input
first use follows.

The shared LRU budget is 32,768 logical retained slots: one source reference, clause
references, source literal occurrences, posting positions, two slots per distinct
variable, and short-clause positions. Python object/container overhead and integer
bit sizes are additional. Preparation holds a bounded partial index plus the input;
reconstruction/output space is still charged separately. This budget is not a byte
or process-RSS limit. Clearing or closing releases indexed source references; cold
replay starts without them. Neither persisted evidence nor historical storage is
removed. Broader SAT coverage and transport to different equivalent cores remain
separate questions.
