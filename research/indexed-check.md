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


## Negative measured result and the next pattern

The 96-input empty-history comparison keeps 88 structural closures and exactly
matching evidence-table digests and final database bytes (33,460,224). Discovery
is 6.36510 -> 6.63704 seconds, total 7.54255 -> 7.89263, and full cold audit
3.62441 -> 3.76949. Four-case peak Python allocation is 615,971 -> 738,163 bytes.
All prior seed rows and cold replay bytes are preserved. The candidate remains
optional; this control provides no performance or space benefit.

Only 658 of 15,071 reconstruction calls hit the source index. Admissions number
14,413, with 4,054,848 source literal visits, followed by 471,454 affected-literal
inspections. The original one-pass reconstruction visits 4,173,407 literals.
Indexing therefore does more literal work in this run, despite sharing most
unchanged clauses during output assembly. Its new source objects are usually not
reused enough to amortize preparation.

On the costly source 1194, a 32-fold larger budget (32,768 -> 1,048,576 logical
slots) leaves both checker views together at 80 hits / 2,617 calls, 2,537 admissions
and 858,647 preparation literals. Time is 1.20417 / 1.20699 seconds. Eviction drops
and retained entries grow from 23 to 1,002, but useful reuse does not increase in
this diagnostic. Do not infer a benefit from a bigger cache on this source.

`SharedReconstructionInventory` additionally memoizes restrictions by retained
immutable source identity and a sorted exact assignment. It admits a result only
after `IndexedRestriction` validates that source. Cache hits return the immutable
original result; mutable or unusual inputs and oversize entries use the old path.
The source, assignment and result are charged to a separate 32,768-slot LRU; old
and new views share this restriction engine while the checker index stays separate.
Every proof reason and fixed point is still checked. This is another optional
prototype, not a replacement for the current solver.

The isolated three-way source-1194 pilot keeps identical roots/profiles/summaries.
Timing is 1.12695 seconds for the current path, 1.17052 for the checker index and
1.19950 for indexing plus restriction memoization. The combined prototype gets
498 / 3,231 restriction hits, but only 141 / 2,617 checker-index hits. Its source
preparation still visits 838,245 literals. This attempt also fails to demonstrate
a saving. The source-identity barrier remains; preparation across independently
allocated equivalent CNFs is the next target. A bounded structural interner must
charge exact hashing/equality, source verification and retained state. No such
interner is implemented or measured here.

These negative controls stop this candidate before a full prepared-corpus run.
The existing 902/985 full-corpus result is historical, not newly measured for these
candidates. The preserved profile, both diagnostics and complete matched control
prevent later runs from repeating the same capacity-only idea without new evidence.


A further no-eviction observer retains all 2,537 indexed source objects and finds
only 2,167 distinct exact CNF values: 1,797 occur under one identity, and 370 under
two. There are 2,617 checks and 80 identity hits, with zero evictions. The actual
index occupies 2,215,640 logical slots (the observer uses extra unbounded analysis
sets). Thus whole-source interning can eliminate at most 370 duplicate admissions
in this case, before paying for recognition. This is a limited opportunity, not
an explanation for all the remaining work. The larger next question is reuse of
unchanged clause blocks and checked small deltas across the 2,167 different CNFs.
The earlier per-clause support cache's negative result remains relevant; a new
representation must reduce total recognition and checking work, not just literal
counts. The observer is a diagnostic, not a production cache or timing comparison.
