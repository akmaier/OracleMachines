# Learn complete conditional covers across edits

The 23 November experiment establishes three chronological reuse opportunities
beyond the existing negative-core pool. A checked negative cofactor supplies
conditional unit supports and a complete binary cover of its assignments. If
every support survives a later edit, the solver can recompose an ordinary native
refutation without fresh SAT search. This reduces search in the measured stream,
but discovery and reconstruction make the current policy slower overall.

## Exact recognition and recomposition

After a native negative result with at least three expansion dispatches, the
bank registers its native key, original variable-name map and supplied outer
guard. The origin is already checked. Extraction is deferred until a later
query misses static templates and the existing negative/witness pools. The same
outer guard selects candidates in oldest-first order. This filter assumes
explicit common source coordinates; it is not automatic variable correspondence
or an answer certificate.

Extraction uses the existing unit/split/component proof walk. A usable cover
contains checked unit-refutation templates and a complete binary tree. Each
root-to-leaf path must imply that leaf's assumptions. Both branches must exist,
split variables cannot repeat along a path, and unresolved endpoints are
rejected. Every support clause must occur in the new cofactor. A partial match
confers no answer authority.

Soundness follows directly: every assignment takes one complete tree path; that
path satisfies its leaf assumptions, under which a contained set of clauses is
unit-refutable. Hence no assignment satisfies the cofactor. The implementation
does not trust this reasoning alone: it constructs full conditioned children
and publishes ordinary native unit/empty/split certificates, checked by the
unchanged verifier. All children and the root share the existing publication
transaction and rollback rules. An absent split variable can use one branch
because restricting it leaves the current target unchanged.

This is a conditional result for the queried cofactor. It does not refute the
unconditioned source. Complete cover availability can itself require expensive
search or large proofs; this is no uniform efficient classification of SAT.

## Chronological experiment and costs

A discovery probe replays the previous nineteen-source stream, adding each
query's recorded native identities only after that query. It finds support
covers from case 4 that survive case 6/guard 3 and case 16/guards 3 and 4. The
main experiment then learns online from its own earlier native outcomes. No
target answer or final union is seeded. The probe informed this experiment, so
the cases are not a held-out benchmark.

Both arms retain shared template preparation, the same historical prefix,
nine-expansion donor acquisition and static hints. Four alternating serial pairs
give 912 attempts. Each worker answers the same 103 UNSAT and eleven SAT
cofactors. The nearby SAT case 7/guard 4 remains SAT: matching some conditional
supports does not promote it to a negative answer.

| Quantity per worker | Shared baseline | Learned covers |
|---|---:|---:|
| Query expansion dispatches | 43 | 33 |
| Preparation + query mean | 314.28 ms | 338.60 ms |
| Query mean | 301.90 ms | 326.22 ms |
| Complete-worker mean | 2.847 s | 2.836 s |
| Native payload bytes | 1,237,109 | 1,261,237 |
| Persisted hints | 11,505 bytes | 54,396 bytes |
| Compressed proof delta + hints | 126,657 bytes | 169,844 bytes |
| Selected retained Python containers | 6,847,167 bytes | 7,005,796 bytes |

There are three learned-cover hits. Case 6/guard 3 falls from one expansion to
zero; case 16/guards 3 and 4 fall from four and five to zero. This avoids ten
search dispatches (23.26%), but preparation plus query is **7.74% slower** and
query time is **8.06% slower**. All four paired repeats regress on preparation
plus query. Native payload grows 1.95% and the selected retained containers grow
2.32%. Later additional queries improve 3.16% in query time, while the earlier
controls regress 12.60%. The small complete-worker difference does not establish
a robust end-to-end improvement. Keep this route experimental.

The dominant regression is informative. Case 6/guard 3 was already refutable by
ordinary unit propagation. Discovering and reconstructing the learned split
cover changes its mean from **3.57 to 17.60 ms**. Failed first discoveries at the
SAT case 7/guard 4 and UNSAT case 9/guard 5 add about 6 ms each. Later reuse at
case 16/guards 3 and 4 saves about 1.43 and 2.37 ms respectively. These are useful
structural transfers with an acquisition cost that has not yet amortized.

At most sixteen descriptors and four same-guard candidates per query are used.
Extraction caps node occurrences at 64 and inspected node literals at 65,536;
repeated root/preimage scans are charged separately and are not that literal
budget. The bank caps compact encoded JSON at 262,144 bytes. This does not bound
total Python memory, serialization transients or full native proof storage.
The final bank has four descriptors, three extracted covers and one deferred
origin. Human-readable persisted JSON is larger than compact encoding. The
measured retained-container size includes the bank but excludes other state;
process RSS is also recorded and is not attributed to one structure.

All lookup, extraction, checking, failed matching and native reconstruction run
inside query timing. Persisted bank serialization is included in worker costs.
Cold answer replay and reconstruction use both readers; cold hint loading,
native-origin checks and cover checks are measured separately. Alternative
valid proofs are retained without replacing earlier authoritative payloads.

## Next gap

Before extracting or expanding a cover, recognize a full-target unit conflict
and retain its cheaper native proof. Price this gate on all misses, and reuse
the checked prefix in subsequent fallback where possible. Then measure whether
lazy extraction amortizes across more distinct supported edits. A cover hit is
not inherently cheaper than the solver it bypasses.

Ready covers are self-contained conditional proofs, but the current active bank
also retains full native origin keys and source-name maps. Separating archived
provenance from validated ready certificates is a secondary storage opportunity;
deferred origins still need exact reconstruction bindings. Neither change
removes automatic donor/guard discovery, variable correspondence, arbitrary-edit
closure or worst-case cover-size obligations.

## Reproduction and validation

Implementation: `experiments/cnf_learned_conditional.py`. The chronological probe,
paired comparison and validator are separate source-bound scripts. Resume from
`experiments/results/cnf-learned-conditional/checkpoint.json`.

Eleven targeted tests cover complete and partial trees, all 256 deletions of a
three-variable clause cube, sparse maps, guard mismatch, positive outcomes,
absent split variables, unsupported endpoints, capacity limits, stale origins,
commit rollback and both cold readers. The first discovery harness attempted
to append replay records through a read-only snapshot of an owned temporary
database. Its failure and source are retained; the corrected harness uses an
ordinary solver connection for that temporary chronological replay. No stored
source archive was modified.

Validation passes 1,550 full tests and 42 focused tests. All 912 comparative
queries are audited, including candidate availability before each transfer.
Both readers check 76,441 cumulative native records, the unchanged extension
tables and all 342 preceding partition records. The union adds twelve native
identities and preserves every older authoritative payload. All 12,751 prior
artifacts across 144 manifests are unchanged; the seal binds 822 source files.
The full suite retains 44 unclosed-SQLite warnings, with none in the focused
suite. The 247-page manuscript builds without LaTeX/layout warnings and retains
all 64 previous proof environments. `next-target.json` binds the costly unit
case, failed-discovery controls and successful later transfers.
