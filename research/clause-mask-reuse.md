# Shared clauses across different residuals

The previous source-identity index rarely hits, even without eviction. This
follow-up measures the smaller immutable clauses shared across different CNFs.
It tests a bounded checker-owned mask without changing discovery policy,
certificate format or the default implementation. The preserved overlap observer
and three-source pilot are in
[cnf-clause-mask-pilot](../experiments/results/cnf-clause-mask-pilot/).

## What can be reused exactly

`ClauseMaskReconstruction` validates each admitted exact tuple of nonzero exact
integer literals independently. It holds that tuple alive and binds a 64-bit
variable mask to its identity. Bit `abs(literal) & 63` is set for every literal.
The current assignment has its own mask, constructed and checked on every call.
If the two masks have zero intersection, the clause contains no assigned variable:
an actual common variable would set the same bit in both masks. The converse is
false. A collision requires an ordinary scan of the actual literals; it never
licenses dropping a clause or literal. The optimization is therefore exact for
arbitrary positive integer variable identifiers, not just identifiers below 64.

The output still contains every unsatisfied clause, in source order. An untouched
clause is shared; a touched clause is reconstructed with lazy prefix copying.
When unit fixed-point checking is requested, an untouched empty or unit clause
is rejected, as is any touched unsatisfied residual of width at most one. Unit
reasons, conflicts and all other certificate obligations remain in the existing
checker. Neither discovery indexes nor old proof verdicts are used. Failures can
leave valid representation facts in the cache, never a successful proof verdict.

Exact immutable tuple identity is the reuse condition. Equal newly allocated
tuples need their own admission. An edited tuple has a different identity; mutable
clauses, subclasses and unusual values use the previous checker. Strong references
and an `is` comparison prevent object-id recycling from creating false hits. Both
prepared and new checker views share one FIFO cache. A hit does not update order.
Assignments, policy flags and reconstructed results are not retained.

## Account for the remaining work

For a reconstruction, let `a` be assignment size, `m` the clause count, `L_miss`
the literal occurrences inspected during admissions or oversize attempts, `L_scan`
the actual literal visits in possibly affected clauses, and `e` evicted entries.
Expected container work is O(a + m + L_miss + L_scan + e), with output copying
bounded by the visited prefixes and remaining literals. Across calls, evictions
are bounded by earlier admissions. The masks are fixed at 64 bits, but operations
on arbitrary-width integer identifiers and Python dictionaries are not a
constant-time worst-case model. First use still reads and validates every clause;
collisions can force all clauses to be scanned again. No universal improvement
over a linear source scan follows.

The 32,768 logical-slot limit charges identity, reference and mask (three slots)
plus each retained clause's literal slots. Python object/container overhead and
integer bit lengths are additional; this is not a byte or process-RSS cap. The
input, current output and current clause scan remain separate. Closing clears
the cache, so cold replay must prepare it again. Historical evidence storage is
unchanged and no previous result is removed.

The source-1194 observer finds 228,432 clause-identity hits in 324,855 positions
(70.32%), with 258,332 preparation literals. Source 1441 finds 172,963 hits in
245,241 positions (70.53%). These are actual clause-sharing opportunities, unlike
the much lower whole-source identity hit rate. Unbounded observer sets also
measure fixed-position blocks of 4, 8 and 16 clauses. Those block figures are
diagnostics, not bounded production-cache or memory results. Ordered block
matching loses hits as block size grows; arbitrary regrouping would also have
to preserve clause order and unit-reason positions.

The initial three-source pilot reduces literal work but does not establish a
runtime saving. Source 1194's old checker scans 864,479 literals; the mask path
prepares 258,332 and scans 111,571. Yet discovery is 1.13617 versus 1.12317 seconds.
Source 1441 is 0.90508 versus 0.90426, and the closed source 1471 is 0.14570 versus
0.14739. These are single fixed-order comparisons. The source observer's full
literal-position counts differ from scan visits because scanning can stop when
a satisfied literal is found. Lookup, mask construction, FIFO maintenance and
ordered output assembly must all be paid even when literal visits fall.

## Matched controls reject promotion

Two comparisons of the same 96 previously published control inputs use empty
history, with opposite execution orders. The ordinary solver uses transactional
accounting in both modes. Acquisition includes discovery, independent checking,
ordinary solving, source/model lifting and persistence. Opening, warm combined
replay, cold audit, compression and allocation diagnostics are recorded separately.

| Measurement | Scan then mask: scan / mask | Mask then scan: scan / mask |
| --- | ---: | ---: |
| Discovery seconds | 6.21594 / 6.38743 | 6.17950 / 6.38115 |
| Total query seconds | 7.37185 / 7.56226 | 7.31352 / 7.57542 |
| Cold audit seconds | 3.52632 / 3.54729 | 3.50472 / 3.54492 |
| Warm combined seconds | 0.04675 / 0.04791 | 0.04757 / 0.04953 |
| Four-case peak Python bytes | 615,971 / 871,147 | 615,819 / 871,299 |

All answers, roots, profiles, summaries and solver counters match. Every previous
row survives, the four final databases are byte-identical at 33,460,224 bytes, and
every cold audit leaves the database unchanged. Both modes close 88/96 sources.
There is no disk-storage reduction. Python tracing excludes native SQLite, RSS
and full-history peak; it measures the same four-query prefix in each mode.

Both orders produce 1,014,169 hits in 1,529,672 clause positions (66.30%). Preparing
515,503 clauses costs 1,402,257 literal visits, followed by 471,454 scan visits.
This is 55.10% less literal work than the old 4,173,407 visits, but total query
time rises 2.58% and 3.58%. The small-prefix Python peak rises about 41%.
The number of clause positions, copied literals, rebuilt clauses and dropped
clauses is unchanged. The cache therefore replaces many very short scans with
lookup/mask/maintenance work, without avoiding output assembly. These counters
explain why literal savings alone are insufficient; they are not a new profile
attribution of every elapsed second. Two ordered runs are not a statistical or
general speed-ratio claim. The candidate remains disabled and optional.

Preserved evidence: [forward](../experiments/results/cnf-clause-mask-empty/README.md),
[reverse](../experiments/results/cnf-clause-mask-empty-reverse/README.md), and the
[overlap/pilot](../experiments/results/cnf-clause-mask-pilot/README.md). All 496
Python tests pass, including exhaustive small reconstruction, collisions, huge
identifiers, mutations, malformed values, forged evidence and cold archive replay.
No new full prepared-corpus run is justified after these controls.

## Next target

Prioritize bounded, independently checked variable elimination on the remaining
unresolved frontier, then transport into shared equivalent cores. First measure
eligible variables and candidate transformation growth; require exact source
binding, complete checking and model lifting. The goal is to avoid residual
acquisition or expose a recognized family, rather than replace a short literal
scan with another per-clause operation. A coarser shared representation remains
possible, but needs a concrete way to avoid recognition and output work while
preserving order and proof-reason positions before another cache experiment.

The historical prepared result stays 902/985, with 83 open original sources / 99
selected leaves / 31,203 literals. These controls neither remeasure that full
corpus nor change its structural partition. No uniformly efficient expansion for
arbitrary SAT or Lean refinement is claimed.
