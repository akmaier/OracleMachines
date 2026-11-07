# Persistent exact results

This service combines the Lean-verified SAT core with a local SQLite store.
Every completed SAT or UNSAT decision is retained. SAT records also retain the
satisfying assignment. The active witness can solve a different formula after
verification; otherwise, the exhaustive solver runs. Cache entries and learned
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
witness together. WAL mode permits concurrent readers and serialized writers.
There is no eviction or automatic deletion of earlier results. Storage therefore
grows with the number and size of distinct queries.

Results are keyed by the **complete binary input** and the SHA-256 fingerprint of
the compiled engine. A rebuilt engine gets its own namespace when its binary
changes; earlier records remain in the database. A checksum covers each record's engine identifier, input, answer, and witness
against accidental corruption. Errors, malformed inputs, and interrupted calls
are never stored as UNSAT.

The cache is a trusted local store produced by this solver. Checksums do not
authenticate data against deliberate edits. `audit` re-solves every current
engine record and checks retained SAT witnesses; this can be expensive. The
Lean cache proof assumes a loaded cache satisfies the invariant established by
prior writes. Python, SQLite, process communication, serialization, and disk
integrity are outside that proof. Copy the database with SQLite's backup tools
or after closing all connections; an active WAL database has auxiliary files.

`core_work` is the verified abstract evaluator's operation count. On an exact
cache hit no Lean core runs, so this field is zero; lookup and disk work are
still charged by `wall_ns`. `setup_ns` separately reports connection and engine
fingerprinting time. These quantities must not be conflated with a formal
end-to-end machine-step bound. `original_acquisition_core_work` preserves the
initial solve's cost on cache hits.

Run integration tests against the real compiled engine:

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
```

The tests cover SAT and UNSAT retention, restart without launching the solver,
witness transfer across restarts, preservation after learning a new witness,
empty witnesses, malformed inputs, corruption, semantic audit, engine
namespaces, and concurrent writers. The test databases use temporary directories;
they never replace the default persistent database.
