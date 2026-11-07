# Lean proofs

This project checks the finite-expansion induction and resource-accounting
arguments in Section 12 of the paper. It also proves why correctness alone does
not provide a polynomial cost bound. It does **not** prove P = NP or P != NP.

## Build

Install [Lean's version manager, elan](https://lean-lang.org/install/), then run
from the repository root:

```sh
cd formal
lake exe cache get
lake build
```

`lean-toolchain` pins Lean **4.24.0**. `lakefile.toml` requests mathlib
**v4.24.0**, and the committed `lake-manifest.json` pins mathlib and all transitive
dependencies by commit. The first build downloads dependencies; later builds can
use the local cache. `.lake/` contains downloaded dependencies and generated
files and is intentionally excluded from Git.

The default build includes `OracleMachines/Audit.lean`. It checks the transitive
axiom dependencies of every declaration in the `OracleMachines` namespace and
rejects anything except `propext`, `Classical.choice`, and `Quot.sound`, Lean's
standard logical axioms. In particular, admitted proofs, additional axioms, and
native-decision axioms fail the audit. Warnings are treated as errors.

## From the paper to the code

| Paper claim | Lean file and main declarations | What is checked |
| --- | --- | --- |
| Proposition 12.1: exact expansion | [Expansion.lean](OracleMachines/Expansion.lean): `table_lookup`, `table_append`, `preserves_answers`, `eventually_covered`, `exact_on_domain` | All binary words up to each length receive the supplied solver's answer; old entries remain; requests outside coverage return `none`. |
| Explicit table size | `length_words`, `length_domain`, `table_answer_count` | There are `2^n` words at length `n` and `2^(n+1)-1` answer entries through stage `n`, including the empty word. |
| Obligations for another representation | [Invariant.lean](OracleMachines/Invariant.lean): `expansion_invariant`, `answer_at_cover` | The base, preservation, and exact new-coverage hypotheses imply exactness at every finite stage and at a covering stage for each input. |
| Construction recurrence | [Resources.lean](OracleMachines/Resources.lean): `cumulative_eq` | Recursive construction cost equals base cost plus every expansion cost. |
| Arithmetic in Corollary 12.2 | `polynomial_stage_sum`, `full_polynomial_bound`, `bounded_expansion_cost` | Shared polynomial stage budgets yield a single polynomial bound including reading, base construction, expansion, and evaluation. |
| General coverage schedules | `polynomiallyBounded_comp` | Composing a polynomial cumulative-cost bound with a polynomial coverage-stage bound preserves polynomial boundedness. |
| Proposition 12.3: staged reuse | [Reuse.lean](OracleMachines/Reuse.lean): `totalWork_eq`, `totalWork_le`, `strict_savings_iff`, `savings_of_upper_bound` | All expansion and query work is charged. Avoided solver work must repay construction. An upper bound on retrieval gives only a sufficient savings condition. |
| Growing-domain amortization | `average_identity`, `amortization_iff`, `eventually_positive_queries` | The average-cost difference is exactly expansion cost divided by query count. Divergent counts are eventually positive. |
| Failure of the unrestricted inference | [Limits.lean](OracleMachines/Limits.lean): `exponential_not_polynomial`, `exponential_expansion_not_polynomial`, `explicit_table_not_polynomial` | The explicit answer count and the cumulative costs of stages costing `2^j` have no polynomial bound. |
| Contrasting workloads | `one_query_expansion_diverges`, `many_queries_amortize` | For expansion costs `2^j`, one query per stage gives divergent expansion cost per query; `4^j` queries per stage make it tend to zero, including any fixed base cost. |

All declaration names above are in the `OracleMachines` namespace. The root
module `OracleMachines.lean` imports the complete development and its audit.

## Conventions and boundary of the formalization

Stages are numbered 1 through `n`; the base stage is charged separately. Queries
inside each stage use zero-based indices. A stage may have no queries, but its
expansion cost is still included. Natural-number costs express step budgets;
real-valued ledgers support subtraction and limits. The accounting identities
hold even for arbitrary real ledgers. Interpreting them as work requires
nonnegative actual costs measured in the same model.

Lean's division by zero is defined. Consequently, the algebraic average identity
holds even with zero queries, but that case has no average-cost interpretation.
`eventually_positive_queries` establishes the required eventual positivity when
the query count tends to infinity. The examples use this growing-query regime.

The table implementation is an actual finite list of `(binary word, answer)`
pairs. It uses sequential lookup and includes explicit keys. The answer-entry
count matches the paper's answer-bit count; keys and list structure add overhead.
This is not a verification of the packed address function or constant-time
random access, and the number of entries is not a measure of Lean heap bytes.

The solver is a parameter `List Bool → Bool`. `exact_on_domain` explicitly assumes
that it decides the chosen language. A function in Lean's logic is not, by
itself, a verified algorithm with a runtime bound: it may have been specified
noncomputably. The executable definitions operate when given executable solver,
state, and update functions. No computability equivalence or SAT parser/solver
has been formalized here.

`PolynomiallyBounded` is a predicate on numerical functions. It is **not** a
formal definition of the class P. The project does not model Turing-machine or
RAM execution, verify the charged costs of a learned implementation, or
formalize NP-completeness, advice classes, or the time hierarchy. In particular,
the formal conditional bound does not discharge the missing uniform SAT
construction and evaluation budgets.

The rest of the paper's neural, oracle, certification, and expected-savings
arguments retain their conventional proofs and literature audit. This directory
provides machine-checked proofs for the claims mapped above, not for the entire
manuscript. The underlying results remain elementary consequences of established
theory; machine checking is not a novelty claim.
