# Persistent checked SAT service

Every completed SAT or UNSAT verdict is retained. SAT means that a valid formula
is satisfiable; UNSAT means it is unsatisfiable. A malformed encoding is an error,
never an UNSAT verdict. SAT records retain satisfying assignments. UNSAT records
retain checked refutation trees, LRAT proofs, or certificates that the compiled
circuit simplifies to false. Results and certificates survive restarts without
eviction.

## Build and use

With the pinned Lean toolchain available, run from the repository root:

```sh
./solver/build.sh
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 010
python3 solver/persistent.py solve 0101010
python3 solver/persistent.py stats
python3 solver/persistent.py audit
python3 solver/persistent.py revalidate
```

The build helper records the toolchain's bundled CaDiCaL path locally. The
measured version is 2.1.2 with ASCII LRAT output. The default `--backend auto`
uses verified simplification and a bounded local attempt before calling
CaDiCaL. `--backend cadical` skips that local search; `--backend lean` retains
the counted lazy solver. Set `ORACLE_CADICAL` or pass `--cadical /path/to/cadical`
to choose a compatible binary. Without CaDiCaL, `auto` uses the complete lazy
fallback. An external timeout (default 30 seconds, configurable with `--timeout`)
returns an error and stores no SAT/UNSAT verdict.

`010` encodes variable 0. The first call solves it and retains witness `1`.
The second retrieves the exact result. `0101010` is its double negation; the
stored witness can certify that different input. `0100101011` encodes
`x0 AND NOT x0`. The [encoding](../formal/OracleMachines/Encoding.lean) uses
binary postfix instructions and unary variable indices.

Keep the service warm for multiple queries:

```sh
python3 solver/persistent.py serve
```

Send one JSON object per line, for example `{"bits":"010"}` or
`{"bits":"0101010","learn":false}`. Each line gets a result or error; EOF closes
the service. One process keeps SQLite and the native checker open and amortizes
engine fingerprinting. Every newly acquired result still commits before its
response. `learn:false` disables cross-formula proposals and active-witness
updates, while exact results are still retained and reused.

## Checked acceleration

The automatic policy tries saved proposals, shared circuit simplification,
all-false/all-true witnesses, and up to 64 local search nodes. Exhausting this
node budget means no answer yet. Every successful local proposal is independently
checked. The policy then invokes CaDiCaL, which supplies mature unit propagation,
watched literals, clause learning, restart and phase heuristics, preprocessing,
and inprocessing. This integration uses its default techniques; it does not
implement every SAT algorithm or guarantee that one policy wins on all inputs.

[CDCL.lean](../formal/OracleMachines/CDCL.lean) proves that our cached AND/inverter
graph preserves the original formula's value. Lean's standard library provides
the CNF translation theorem and LRAT checker. A SAT model is checked directly on
the original formula. An UNSAT proof is checked against CNF reconstructed from
that formula. A CaDiCaL verdict, exit status, or temporary DIMACS file is never
sufficient for acceptance. Invalid certificates, failed subprocesses, and
timeouts store no answer. This is soundness of completed answers, not a
termination guarantee under finite service budgets. The standard-library
theorems compose directly, without a native-decision axiom; the axiom audit passes.

Identical gates share circuit nodes; constants and complementary terms simplify.
A proof can transfer across some syntactic changes, such as double negation,
but every transfer is checked on the current formula. An LRAT proof refers to
specific clause identifiers; arbitrary conjunction extensions need not preserve
it. SAT witnesses and tree proofs retain their respective reuse rules.

At most four stored witnesses and four stored proofs are proposed on each new
formula. An index of distinct proposals avoids scanning archived duplicates.
The active witness is tried first, followed by recent acquisitions. Proof
proposals are limited to 65,536 serialized bytes; larger proofs remain archived.
A bounded proposal count does not make certificate checking constant cost.
Exact hits avoid parsing and solving, and do not rewrite an unchanged active
witness. CaDiCaL starts a new process on each unresolved query, so its internal
learned clauses are not retained between queries. Persistent results, witnesses,
and certificates are retained. A proof-logging incremental CaDiCaL session would
require an additional checked integration.

## Persistence and trust

The default database is `solver/.cache/results.sqlite3`, which Git ignores.
Use `--cache /absolute/path/results.sqlite3` before the subcommand to choose a
durable location. SQLite transactions and full synchronization commit a new
result, certificate, and active witness together. WAL mode permits concurrent
readers and serialized writers. There is no automatic deletion of earlier
results; storage grows with the number and size of distinct queries.

Results are keyed by the complete binary input and SHA-256 fingerprint of the
compiled checker. When that binary changes, a new namespace is used and old
records remain. The process-local fingerprint cache is invalidated by a change
in file identity, size, or timestamps. `revalidate` solves older engines' inputs
with the current engine and commits each result. It never imports an old answer
as a current decision, removes old records, or invents historical proof provenance.
An interrupted replay can resume. Malformed or interrupted queries are never
stored as UNSAT.

The database is a trusted local store produced by this solver. Row checksums
detect accidental corruption; they do not authenticate against deliberate edits.
Exact hits trust that store. Cross-formula proposals are always checked afresh.
`audit` solves every current input with reuse disabled and independently checks
its saved witness or certificate. This can be expensive. Lean's functional
cache proof assumes a loaded cache satisfies the invariant established by prior
writes. Native compilation/runtime, Python, SQLite, JSON, process communication,
and disk integrity are outside the kernel proof. Copy an active database using
SQLite backup tools, or close all connections first to include its WAL contents.

Schema version 4 adds a distinct-proposal index and a measurement table. It
preserves the version-3 checksummed proof archive and all earlier result rows.
The version-1 migration adds parser costs; historical unmeasured parser costs
remain SQL `NULL`, never zero. Missing historical certificates are not invented.

## Accounting

With `--backend lean`, `core_work` is the abstract operation ledger of the
verified lazy evaluator and search; `parse_work` charges binary parsing, and
`counted_work` is their sum. Modern acquisitions instead return `core_work`,
`counted_work`, and `nodes` as JSON `null`, with `counted_complete:false`. CNF
construction, bounded preliminary search, CDCL, and LRAT checking have no complete
abstract ledger. Parser work alone is known, including both parses when an
external answer needs verification. It must not be interpreted as total work.

`wall_ns` includes query handling, IPC, verification, lookup, and committed
writes. `PersistentSolver.setup_ns` separately records connection and engine
fingerprinting time. External solves expose `external_ns`, `verification_ns`,
`cnf_clauses`, and `proof_bytes`; verification includes reparsing, proof/model
handling, and the native check. JSON, ASCII conversion, database operations, and
runtime costs are covered by elapsed time, not the old formal operation bound.

An exact hit has zero parser/core work because it runs no native query; lookup
and disk costs still appear in wall time. `original_acquisition_core_work`,
`original_acquisition_parse_work`, and `original_measurements` describe the
first acquisition, with unknown modern core cost exposed as `null`. The legacy
non-null SQL core-cost column uses a zero placeholder for modern acquisitions;
the measurement flag is authoritative. Consumers must use that flag or the public
interface, never interpret the raw placeholder as free acquisition.

## Counted lazy reference and native protocol

The lazy reference branches on distinct occurring variables, using three-valued
partial evaluation to close branches early. It never constructs a list of all
assignments. For example, `x100` needs three search nodes and returns a correctly
indexed 101-bit witness. A negative result carries a tree with checked partial
contradictions at leaves and both variable values checked at every split.
Lean proves the checker sound and the search complete, with at most
`2^(d+1)-1` nodes for `d` distinct occurring variables. A failing single assignment
is never evidence of UNSAT. Trees, search, and the durable archive can still be
exponential. Neither this reference nor the CDCL path proves a polynomial bound
for general SAT.

The old eager reference remains native mode `exhaustive`; `baseline` is lazy
search without proposals; `hybrid` enables checked proposals. Requests accept
`bits`, `mode`, `candidates` (at most four bit strings), and `proofs` (at most
four trees). The singular `candidate` field remains compatible. Tree proofs
are `"conflict"` or `[index, low, high]`. Earlier fixed-width coefficients and
single-witness overhead bounds describe their original implementations.

Modern requests use `prepare`, `verify_witness`, and `verify_certificate`.
LRAT certificates have `format:"lrat"` and a `text` field; constant-false
certificates have `format:"aig_false"`. The Python service handles CNF export,
external solving, and independent verification. Public `source` values are
`cache`, `fallback`, `verified_witness`, and `verified_refutation`; `fallback`
includes newly acquired results found by local preprocessing.

## Validation

```sh
python3 -m unittest discover -s solver -p 'test_*.py' -v
```

All 34 integration tests pass. The original tests cover retention, restart,
engine namespaces, concurrent writers, corruption, schema migration, witness and
tree transfer, sparse indices, and 400 formulas compared with independent truth
tables and the eager reference. Accelerated tests add 120 seeded CNFs checked
against truth tables, valid and forged external models/proofs, wrong-formula
and malformed LRAT, timeouts, unavailable-solver fallback, search-budget
exhaustion, gate sharing, indexed retrieval, and the warm JSON-lines interface.
Tests use temporary databases; they never replace the persistent store.

[Reproducible experiments](../experiments/README.md) include initialization,
verification, persistence, and shutdown costs and retain every historical dataset.
