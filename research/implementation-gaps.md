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

The public/chronological benchmark and manuscript reconciliation follow in the
next milestone. The stronger claims in the final column remain open.

The public pilot exposed native stack exhaustion during counted length discovery.
A proved compiler replacement now preserves the exact value and ledger while
using stack-safe list length; ASCII decoding accumulates iteratively as well.
A regression test covers an encoding over 500,000 bits. The pilot is retained
in `experiments/results/expanded-pilot/`, including 32 failures (12 direct
DIMACS trailer errors, 20 checked-path stack overflows).
