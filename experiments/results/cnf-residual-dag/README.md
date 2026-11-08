# Residual CNF candidate: first acquisition and reuse checkpoint

8 November 2026. This is a research implementation, not a production trusted
solver path or a uniformly polynomial SAT result. The candidate source and
benchmark hashes are in `report.json`; this evidence must not be overwritten
when the candidate changes.

The candidate applies unit propagation, explicit Horn/dual-Horn/2-CNF leaves,
independent component splitting, and variable branching to arbitrary CNF. It
retains exact normalized residuals. Normalization removes tautologies and
duplicates and compacts sorted variable IDs. It recognizes order-preserving
renamings, not arbitrary semantic equivalence. Full serialized CNFs are keys,
so correctness does not require collision-free hashes.

SAT answers have full witnesses. UNSAT certificates contain forced-unit traces,
contradictory implication paths, a contradictory conjunct, or two contradictory
conditioned children. A separate Python checker validates these certificates,
including every needed dependency on cold loading. Lean's `Residuals.lean`
proves the semantics of conditioning and variable splitting, but does **not**
verify this Python checker or its parser, persistence, or runtime. Existing
production solver code and its archive remain untouched.

## Matched results

There are 26 inputs, four acquisition modes, and warm/cold replays for the full
candidate: **156 decisions**, all agreeing with expected answers. The nine
seeded 3-CNF cases are checked by exhaustive assignment enumeration; component
cases have planted models, odd inequality cycles and pigeonholes are UNSAT.

| Input | Full expanded nodes | Without search reuse | Without class leaves | Without component splitting |
|---|---:|---:|---:|---:|
| 32 copies of a six-variable component | 6 | 161 | 8 | 129 |
| 32 novel six-variable components | 107 | 119 | 117 | 113 |
| Odd inequality cycle, 201 variables | 1 | 1 | 3 | 1 |
| Pigeonhole, 7 pigeons / 6 holes | 416 | 1,235 | 468 | 416 |

Acquisition starts with a fresh archive for every input/mode. Repeated components
at sizes 4/8/16/32 require six expanded nodes in each case, while input reading,
normalization and the retained root still grow. Full logical archive payload
grows from 2,612 to 14,724 bytes, so constant expansion count is not constant
time or memory. Novel components require 17/31/55/107 expanded nodes. Splitting
is not uniformly beneficial: four novel components need 17 expansions with it
and 14 without it.

Pigeonhole sizes 2/3/4/5/6 holes need 1/8/34/122/416 expanded nodes. Finite
measurements do not prove an asymptotic lower bound. They expose a missing
global constraint representation: these instances are polynomially decidable
matching problems, despite stressing this particular portfolio. This motivates
recognizing matching structure and checking Hall witnesses in the next revision.

Warm and cold replays create **zero new nodes**, and every saved row is unchanged.
Cold SAT replays check one source witness. Cold pigeonhole replay at six holes
checks **all 416** certificate nodes; zero new search does not mean constant
verification. Its logical archive payload is 741,698 bytes. Full process peak
RSS is not measured. Named counters are literal payload/visit counts, not an
instruction-level cost semantics.

Timing includes normalization, solving, checking, full-key construction,
serialization, SQLite operations, and a final archive-size SQL scan. Database
initialization is separate. Integrity checks, snapshots and report generation
are offline. These pilot timings were collected while other verification jobs
were active and are not evidence of a wall-clock speedup. Mechanism counts are
the primary comparison; no competitive CDCL baseline is claimed.

## Persistence and reproduction

The 104 gzip-compressed SQLite snapshots retain all completed residual results
and certificates from every acquisition mode. Together they occupy 684,429
compressed bytes. `report.json` records the uncompressed hash, row digest,
logical size and physical database size. Every database passed `integrity_check`.
Decompress a snapshot to a new path before opening it with `ResidualSolver`.
The compression is for evidence storage, not an online solver optimization.

```sh
python3 experiments/compare_cnf_residuals.py --output /tmp/cnf-residual-new
python3 -m unittest solver.test_cnf_residuals -v
```

The seven added tests include all **512** CNFs formed from the nine normalized
two-variable clauses (including the empty clause), under four ablations; 400
seeded formulas up to seven variables; cold positive/negative reuse; renamed
components; source edits; invalid literals; corrupted certificates; and budget
exhaustion without a guessed verdict. All **217** repository Python tests pass.
The Lean audit passes **4,061 declarations / 1,924 theorem declarations** with
only the existing allowed axioms. Logs accompany the evidence.
