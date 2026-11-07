# Implementation follow-up: seven remaining gaps

This record tracks the work requested on 7 November 2026. A completed
implementation is distinguished from a stronger theorem that it does not prove.
Earlier experiments and persisted results must remain intact.

| Item | Concrete work | Stronger claim that must not be inferred |
| --- | --- | --- |
| 1. Uniform expansion | Executable compact coverage states for the logarithmic-width SAT family, with preservation, coverage, construction-size and query-cost theorems. | Uniform polynomial-time SAT for unrestricted inputs. |
| 2. Accounting | Disjoint elapsed phases, child resource measurements, certificate and storage sizes, explicit unknown formal costs. | A complete machine-level cost proof for external CDCL or SQLite. |
| 3. Machine/memory | Extend operational semantics and storage bounds beyond one evaluation; expose remaining bit-machine obligations. | Verified compilation/runtime or constant-memory search. |
| 4. Internal reuse | Long-lived CaDiCaL over shared circuit definitions and root assumptions; independently check answers. | An incremental UNSAT proof checker if negative answers still require a fresh LRAT run. |
| 5. Service guarantees | Deadlines covering native work and certificate checks, bounded message/proof sizes, recovery, checked-cache option, and rollback tests. | Kernel verification of Python, the OS, and SQLite. |
| 6. Learned proposals | Persist a compact online predictor, charge updates, check every proposal, and test chronological held-out transfer. | Efficient exact learning of unrestricted SAT. |
| 7. Evidence | Public SATLIB instances and structural/shift streams; direct and checked baselines; retained failures/timeouts; memory and acquisition costs. | Universal speedup or a representative SAT-competition result. |

First implementation milestone:

- `CompactExpansion.lean` proves preservation, eventual coverage, construction
  cells/steps, SAT/UNSAT soundness, and the restricted reference-query bound.
- `SearchMachine.lean` proves operational search composition and reachable-state
  payload bounds. Parsed programs and assignment generation remain supplied.
- Live CaDiCaL clause reuse, a checksummed bounded predictor, disjoint elapsed
  phases, deadline-aware I/O, monitored external files, and strict cache checking
  are implemented. Internal clauses remain live-session state; saved results,
  certificates and models survive restart.
- Lean's transitive axiom audit: 1,197 declarations / 651 theorem declarations.
  All 57 integration tests pass, including truth-table comparisons, timeout
  recovery, forged proposals/cache entries, concurrent model updates, and DIMACS
  conversion. No proof admits or new axioms were introduced.

The final public/chronological benchmark and manuscript now include this work.
The stronger claims in the final column remain open.

The public pilot exposed native stack exhaustion during counted length discovery.
A proved compiler replacement now preserves the exact value and ledger while
using stack-safe list length; ASCII decoding accumulates iteratively as well.
A regression test covers an encoding over 500,000 bits. The pilot is retained
in `experiments/results/expanded-pilot/`, including 32 failures (12 direct
DIMACS trailer errors, 20 checked-path stack overflows).

Final evidence and disposition:

| Item | Implemented and checked | Remaining boundary |
| --- | --- | --- |
| 1 | Compact coverage, exactness/preservation, unary construction, restricted decision ledger; native demonstration. | No unrestricted polynomial constructor. Coverage/promise checks are outside that ledger. |
| 2 | Disjoint wall-time phases, service/reaped-child CPU, process RSS, proof/model/database bytes, explicit unknown formal totals. | No full CDCL/SQLite instruction proof, simultaneous process-tree peak, energy or hard physical memory cap. |
| 3 | Complete assignment-search traces, reachable-state payload bound, restricted quadratic space, proved stack-safe length replacement. | Parsing/generation are supplied to the trace; no full bit-machine/compiled-runtime proof or production-CDCL memory proof. |
| 4 | Shared live circuit clauses, retained learned clauses and root assumptions; every proposed result checked independently. | Internal clauses do not survive restart; negative proposals still use a fresh LRAT run. |
| 5 | Query deadlines, size limits, bounded child I/O, reaping/recovery, SQLite rollback, strict-cache rechecking and adversarial tests. | Cooperative timing, outer transport and OS/runtime trust remain; budgeted service can return an error. |
| 6 | Bounded persistent predictor, charged training from checked answers, transactional concurrent updates, chronological new-witness transfer. | Simple tractable family; no exact general-SAT learning guarantee or universal savings under shift. |
| 7 | 28 public SATLIB instances, four chronological/structural streams, six modes, three repetitions; all 1,260 answers correct. | Older small suites, local host noise, no current competition baseline or equal-total-memory study. |

The benchmark and manuscript report regressions as well as gains. Internal
retention does not isolate the causal contribution of learned clauses. The
combined predictor policy includes other mechanisms; incremental alone performs
similarly on signed units. Initial benchmark execution overlapped the test suite
briefly; small timing differences should not be interpreted as significant.

The live store preserves all 1,420 previous rows and 258 proofs, adds 355 checked
current-engine results and 129 proofs, and retains a bounded current model.
`experiments/results/expanded/persistence.json` records the replay, semantic audit,
and hashes confirming preservation. Four historical experiment datasets are
unchanged. `expanded-pilot/` preserves the development failures; `expanded/`
contains the final data and source/binary fingerprints.
