# Resume deeper probe blocks from verified checkpoints

The [first continuation pass](probe-continuation.md) left 42 clear streams with
later ranked candidates. This experiment resumes the complete eight-table
history and applies the same search policy once more. Each visited source may
acquire one new block of at most four candidates; each original still has limits
of four distinct source visits and 32 newly entered recognition states. No
recognizer, ranking, prefix-checking or recomposition rule changes.

`continue_cnf_probes.py` makes the parent report explicit. Its ordered lineage
terminates at the first prefix-continuation checkpoint. Each generation checks
the parent hash, implementation fingerprints, seed logical digests, baseline
coverage, delta hash and resulting table digests before adding the next delta.
Conflicting rows cannot replace old data. The base restoration also retains all
earlier solver proofs, failed attempts, source bindings and alternative routes.
The runner can resume its own output on a later pass, avoiding another bespoke
reconstruction script or accidentally restarting from an obsolete seed.

The experiment processes the same 83 selected development originals in their
saved order, skipping those already structurally covered. An earlier clear
prefix avoids repeated probe discovery. A forced record resumes its exact
residual. Results remain structural-coverage witnesses; complete reference
solving separately checks the answers of newly covered originals. Reused cases
whose historical group names contain `holdout` are not independent evaluations.

The saved opportunity analysis now distinguishes all retained streams from
ones exposed on selected paths of still-open originals. It follows existing
forced rewrites, skips subplans already closed by finite composition, and marks
unstarted leaves separately. This analysis does not acquire a new target or
probe an assumption, and it does not apply admission/source caps. Other saved
alternatives can offer different paths. Pool exhaustion refers only to the
bounded binary-frequency ranking; variables outside that pool are explicit.
Neither exhaustion nor a clear unit-propagation trace establishes SAT or UNSAT.

Preparation, acquisition, persistence, cold inventory checks, route replay,
serialization, restoration and reference solving remain charged. Previously
checked local continuation endpoints are included again in this run's reference
archive, with their cost included. This is additional bounded discovery, not a
claim of faster whole-SAT solving or a new general tractability result.
