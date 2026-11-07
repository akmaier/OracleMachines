# Persistent exact results

This service combines the Lean-verified SAT core with a local SQLite store.
Every completed SAT or UNSAT verdict is retained. SAT means that the valid
formula is satisfiable; UNSAT means it is unsatisfiable. A malformed encoding
is an error, never an UNSAT verdict. Neither name refers to a size restriction. SAT records also retain the
satisfying assignment. UNSAT records retain refutation trees. Up to four stored
witnesses and four stored refutations are checked against a new formula before
the lazy solver runs. The active witness is tried first; other distinct witnesses
and refutations are proposed in reverse acquisition order. Cache entries and learned
state survive closing the process and restarting it.

Build from the repository root, with the pinned Lean toolchain available:

```sh
cd formal
lake build OracleMachines oracleSolver
cd ..
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 0101010
python3 solver/persistent.py stats
python3 solver/persistent.py audit
python3 solver/persistent.py revalidate
```

`010` encodes variable 0. The first call solves it and retains witness `1`.
The second retrieves the exact cached result. `0101010` is its double negation;
the stored witness can certify that different input. `0100101011` is the
contradiction `x0 AND NOT x0` and has a retained UNSAT result after solving.
The input format is defined in [Encoding.lean](../formal/OracleMachines/Encoding.lean).

The default database is `solver/.cache/results.sqlite3`, which Git ignores.
Use `--cache /absolute/path/results.sqlite3` before the subcommand to choose a
durable location. Do not use a temporary directory for results you want to keep.
SQLite transactions and full synchronization commit a new result and its active
witness and negative certificate together. WAL mode permits concurrent readers and serialized writers.
There is no eviction or automatic deletion of earlier results. Storage therefore
grows with the number and size of distinct queries.

Results are keyed by the **complete binary input** and the SHA-256 fingerprint of
the compiled engine. A rebuilt engine gets its own namespace when its binary
changes; earlier records remain in the database. A checksum covers each record's engine identifier, input, answer, and witness
against accidental corruption. `revalidate` solves the inputs retained by older
engines with the current engine and commits each result. It never imports an old
answer as a current result, never removes the old records, and can resume after
interruption. An already-current result is reused normally. Errors, malformed
inputs, and interrupted calls
are never stored as UNSAT.

The cache is a trusted local store produced by this solver. Checksums do not
authenticate data against deliberate edits. `audit` re-solves every current
engine record with reuse disabled and checks retained SAT witnesses and
refutation certificates; this can be expensive. The
Lean cache proof assumes a loaded cache satisfies the invariant established by
prior writes. Python, SQLite, process communication, serialization, and disk
integrity are outside that proof. Copy the database with SQLite's backup tools
or after closing all connections; an active WAL database has auxiliary files.

`core_work` is the abstract operation ledger of the Lean evaluator and solver; `parse_work`
charges binary syntax parsing. `counted_work` is their sum. On an exact cache
hit both are zero because the native engine is not invoked; lookup and disk work
still appear in `wall_ns`. `setup_ns` separately reports connection and engine
fingerprinting time. JSON, ASCII conversion, database operations, and the native
runtime are not covered by these formal operation bounds.

`original_acquisition_core_work` and `original_acquisition_parse_work` retain
the first acquisition's measured costs on cache hits. Schema version 3 adds a
separate checksummed refutation archive, preserving version-1 and version-2 rows.
The version-1 migration also adds parser costs. Historical
unmeasured parser costs remain SQL `NULL` (JSON `null`), not zero; original
answers, witnesses, checksums, and engine namespaces remain intact. Missing
historical certificates are not invented; revalidation creates them in a new
engine namespace.


## Search and reuse

The fallback collects and deduplicates occurring variable indices. It explores
assignments depth first, evaluating the formula with three-valued logic at each
node. A partial true value supplies a satisfying extension; a partial false
value closes the branch. The solver never constructs the list of all assignments.
For example, `x100` needs three search nodes and returns a 101-bit witness, with
unused positions false. Original variable identities are preserved.

A negative result carries a tree whose leaves certify partial contradictions
and whose internal nodes check both values of a variable. Lean proves the
checker sound and proves that the fallback produces an accepted tree for every
UNSAT result. The same tree can be checked on a later formula, for example a
larger conjunction containing the original contradiction. A failed certificate
check falls back to search. Negating a contradiction does not preserve its
refutation. No negative answer is inferred from one failing full assignment.

The proposal limit does not evict archived results. Refutation proposals are
also limited to 65,536 serialized bytes each; larger certificates are retained
but excluded from the active portfolio. Candidate selection and serialization
are charged in elapsed time. The native checker charges its actual work.
Bounding candidate count does not give the earlier one-witness overhead constant.

For `d` distinct occurring variables, Lean proves at most `2^(d+1)-1` search
nodes. Sparse lookup, deduplication, formula traversal, and dense witness output
still cost work. A refutation tree and the durable archive can be exponential.
This is verified pruning and certificate reuse, without CNF conversion, unit
propagation, conflict-driven clause learning, or a polynomial general-SAT bound.
The earlier exhaustive implementation remains available as native JSON mode
`exhaustive`; `baseline` uses the new search without reuse, and `hybrid` enables
verified proposals. Earlier fixed-width cost constants describe that earlier
implementation and are not transferred to the new ledger.

Native JSON requests accept `bits`, `mode`, `candidates` (at most four bit
strings), and `proofs` (at most four trees). The legacy singular `candidate`
field is also accepted. A refutation is `"conflict"` or `[index, low, high]`.
Results include `certificate`, `nodes`, and `reuse_kind` (`none`, `witness`, or
`refutation`). The Python service reports `source` as `cache`, `fallback`,
`verified_witness`, or `verified_refutation`. Exact cache hits still trust the
local store; cross-formula proposals are independently checked.

Run integration tests against the real compiled engine:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
```

The tests cover SAT and UNSAT retention, restart without launching the solver,
witness transfer across restarts, preservation after learning a new witness,
empty witnesses, malformed inputs, corruption, semantic audit, engine
namespaces, concurrent writers, parser-cost retention, legacy-schema migration,
and recomputation of earlier engines' inputs. They also compare 400 generated
formulas with independent truth tables and the old exhaustive backend, exercise
sparse indices and early pruning, and check certificate transfer and rejection. The test databases use temporary directories;
they never replace the default persistent database.
