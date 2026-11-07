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
| Concrete SAT solver | [SAT.lean](OracleMachines/SAT.lean): `solve_correct`, `solve_false_iff`, `witness_sound`, `no_witness_iff`, `extend_exact` | Exhaustive finite-assignment search decides ordinary propositional satisfiability and supplies checked witnesses. Appending a finite batch of its answers preserves exactness. |
| SAT/UNSAT and encoding errors | [Decision.lean](OracleMachines/Decision.lean): `decision_sat_iff`, `decision_unsat_iff`, `not_sat_iff_invalid_or_unsat` | A partial decision distinguishes satisfiable formulas, unsatisfiable formulas, and invalid strings. UNSAT is the complement only within valid encodings. |
| Binary SAT and bounded expansion | [Encoding.lean](OracleMachines/Encoding.lean): `decode_encode`, `encode_injective`, `solveEncoded_correct`, `satTable_correct`, `expandSAT_eq` | A concrete binary postfix encoding round-trips. The binary solver decides its defined SAT language, and incremental expansion produces the exact next bounded-domain table. |
| Executable cost semantics | [CostedSAT.lean](OracleMachines/CostedSAT.lean): `readRun_trace`, `evalRun_trace`, `solveRun_value`, `solveRun_bound`, `solveRun_fixed_width` | The instrumented evaluator realizes an explicit operational trace, the instrumented solver returns the verified solver's witness, and its counted work has a bound polynomial in encoding length for a fixed variable cap. |
| Explicit evaluator machine | [StackMachine.lean](OracleMachines/StackMachine.lean): `compile_machine_steps`, `evalMachine_correct`, `evalMachine_space` | One transition handles one instruction or one unary-index lookup step. Execution takes exactly the evaluator's reported count. Every reachable state has at most `2*A + L + S + 1` data units for assignment length `A`, encoded program length `L`, and initial stack length `S`. |
| Proposition 12.4: restricted core bound | `solveRun_bound`, `solveRun_fixed_width` | The same counted implementation has `T <= W^2 + 2^v (W+13) + 2`; fixing `v <= K` gives coefficient `14*2^K+3` and degree 2 in encoding length plus one. |
| Binary parsing and combined decision | [Parsing.lean](OracleMachines/Parsing.lean): `decodeRun_value`, `decodeRun_bound`, `decideRun_sat`, `decideRun_unsat`, `decideRun_fixed_width` | The counted parser agrees with the existing parser, costs at most `8L+7`, and composes with the solver. On `encode f` with width at most `K`, total counted decision work is at most `(14*2^K+12)(L+1)^2`. |
| Coverage of every accepted input | [Canonical.lean](OracleMachines/Canonical.lean): `encode_decode`, `parseProgram_decode`, `decideRun_valid_fixed_width`, `decideRun_valid_logarithmic_width`, `parsed_eval_steps`, `parsed_eval_space` | Successful decoding implies `encode f = bits`. The restricted decision bounds and evaluator transition/data-size bounds therefore apply to arbitrary accepted requests, measured against the original binary length. |
| Growing variable count | [Restricted.lean](OracleMachines/Restricted.lean): `decideRun_small_assignment_space`, `decideRun_logarithmic_width`, `small_assignment_space_requires_length` | If `2^v <= L+1` (in particular `v <= floor(log2(L+1))`), parser plus decision costs at most `24(L+1)^2`. Enforcing that premise by padding requires length at least `2^v-1`. |
| Certified adaptive policy | [Hybrid.lean](OracleMachines/Hybrid.lean): `hybridRun_correct`, `serve_correct`, `hybridRun_overhead`, `actual_savings_identity`, `repeated_hit_savings` | A previously acquired witness is checked on each new formula; fallback is exact. Costs include validation, fallback, copying the acquired witness, and stream control. The savings identity follows the actual changing state. |
| Lazy search and pruning | [Search.lean](OracleMachines/Search.lean): `partialRun_sound`, `solveSparse_correct`, `solveSparse_certificate`, `solveSparse_nodes`, `materialize_satisfies` | Branch only on distinct occurring variables; partial truth and falsity are sound; every UNSAT search returns a checked refutation; at most `2^(d+1)-1` nodes; dense witness conversion preserves satisfaction. |
| Reusable positive and negative certificates | [Knowledge.lean](OracleMachines/Knowledge.lean): `probeWitnesses_sound`, `probeRefutations_checked`, `solveSearch_verified`, `reuseSearch_verified`, `reuseSearch_correct` | Arbitrary proposed witnesses and refutations are checked against the current formula. The combined policy decides SAT correctly, without trusting proposal provenance. |
| Proposition 12.9: checked CDCL boundary | [CDCL.lean](OracleMachines/CDCL.lean): `compiledCircuit_correct`, `circuitFalse_sound`, `compiledCNF_unsat`, `checkLRAT_sound` | Shared AIG construction preserves formula evaluation. Standard-library CNF translation and LRAT checking compose to exclude a satisfying valuation whenever a proof is accepted. |
| Bounded preliminary attempt | [BoundedSearch.lean](OracleMachines/BoundedSearch.lean): `boundedSearch_remaining_le` | A finite node budget never increases. Exhaustion returns no proposal; the executable independently checks every proposed witness or tree before acceptance. |
| Accumulated exact results | [Cache.lean](OracleMachines/Cache.lean): `cache_lookup_sound`, `cacheStep_correct`, `cacheStep_exact`, `cacheStep_retains` | Every completed result remains available, including negative answers; lookup and insertion preserve exactness, assuming the loaded cache is intact. |
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

The follow-up adds two independently scoped modules. `CompactExpansion.lean`
stores a unary coverage cap of `n` cells, constructs it in `n` allocation steps,
preserves answers at each extension, and eventually covers every valid
logarithmic-width input. It uses the established `24(L+1)^2` reference decision
bound; building coverage to `L` plus that decision costs at most `25(L+1)^2`
in those ledgers. Coverage tests, promise tests, and compiled execution are not
charged by that bound. It is a compact algorithm plus a cap, not a precomputed
answer table or a solution to unrestricted SAT.

`SearchMachine.lean` composes the evaluator into explicit assignment-selection
and completion transitions. `search_machine_complete` bounds a complete search
trace by `1 + 2^v(W+2)` steps. `search_machine_space` bounds every reachable state's
payload by `(v+1)2^v + v + 2L + 2`; `search_machine_restricted_space` bounds it by
`5(L+1)^2` when `2^v <= L+1`. Candidate assignments and parsed code are supplied
to this machine. The proof does not yet compose candidate generation and parsing
into the same transition system or measure physical heap bytes. It describes
the eager reference, not the production lazy/CDCL path. The complete audit now
passes for 1,197 declarations, including 651 theorem declarations.

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
state, and update functions. The separate `SAT.lean` module now supplies a
concrete solver on a typed propositional syntax and proves its correctness;
that result requires no exact-solver hypothesis. `Encoding.lean` supplies a
binary postfix parser, proves encoding round trips, and connects the solver to
exact expansion on all binary words up to each length. Malformed encodings are
rejected. `CostedSAT.lean` now connects an executable solver core to explicit
operation counts and proves its correctness and cost bounds together.

`PolynomiallyBounded` is a predicate on numerical functions. It is **not** a
formal definition of the class P. The project does not yet prove a simulation
from its abstract cost semantics to Turing-machine or compiled Lean execution,
or formalize NP-completeness, advice classes, or the time hierarchy. In
particular, uniform polynomial SAT budgets with no fixed size cap remain
unproved. This refers to general satisfiability, not UNSAT (unsatisfiability).
The conventional NP-completeness of SAT and coNP-completeness of UNSAT are
not formalized as complexity-class claims here.

## Reference implementation and its concrete cost model

`CostedSAT.lean` operates on an already parsed formula. It charges formula-node
dispatch, Boolean operations, sequential list-cell access, and cell allocation.
`ReadTrace` and `EvalTrace` are inductive execution judgments; the executable
functions' returned answers and counts realize those judgments. Both operands
of a conjunction are evaluated. Variable indices are treated as unary data;
lookup walks the assignment, and width discovery charges unary comparisons.
Assignment generation charges prefix allocation, list copying, and control.
The counters are instrumentation; their own integer arithmetic is not included.
No conversion of these units to elapsed machine instructions is claimed.

For evaluation weight `W`, variable width `v`, and binary encoding length `L`,
the checked solver bound is

```text
work <= W^2 + 2^v (W + 13) + 2,     W <= L.
```

For any **fixed** variable cap `K` with `v <= K`, Lean proves

```text
work <= (14 * 2^K + 3) * (L + 1)^2.
```

This is a restricted result with an explicit exponential dependence on `K`.
It does not by itself give a polynomial bound as `K` grows without restriction.
The full table still has exponentially many entries. The separate `Parsing.lean` development
now charges binary syntax parsing: length discovery, unary index scanning,
instruction allocation, and formula-stack assembly. Its result equals `decode`
and costs at most `8L+7`, including malformed-input rejection. Formula subtrees
are shared rather than copied. The parser uses already materialized Boolean-list
input; JSON and ASCII-to-bit conversion remain outside this model.

`decideRun` returns `none` for malformed encodings, `some true` for SAT, and
`some false` for UNSAT. For an input `encode f` with width at most `K`, parsing
plus exact decision costs at most `(14*2^K+12)(L+1)^2`. Malformed encodings are
rejected within `8L+8`. These are numerical bounds in the explicit abstract
model. `Restricted.lean` also proves a bound with growing variable width:
`v <= Nat.log 2 (L+1)` gives at most `24(L+1)^2` counted operations. This is
a promised-family result. Padding that retains the variable range and enforces
the premise requires `L >= 2^v-1`; it can therefore require exponential length
and does not give a polynomial reduction from all SAT inputs.

`Canonical.lean` checks the converse round trip: `decode bits = some f` implies
`encode f = bits`. The index parser consumes precisely its unary prefix, the
instruction parser accounts for every input bit, and assembly reconstructs
exactly the consumed program. Thus the bounds on `encode f` cover **every**
successfully decoded request, using the request's own length. Malformed input
retains its separate rejection bound.

Counter arithmetic, garbage collection, physical memory traffic, and
compilation to a bit-machine still require a separate simulation argument.

`StackMachine.lean` makes one part of that connection explicit. `evalStep`
executes supplied postfix code without calling the recursive evaluator. Loading
a variable enters a read state; each subsequent transition inspects one
assignment cell and decrements the unary index. The checked execution takes
exactly `(evalRun f a).2` transitions and halts with the correct Boolean. The
existing bound therefore gives at most `W(f) <= L(f)` transitions.

The machine also has an invariant on every reachable state, including prefixes
of an execution. Remaining code bits, stack bits, and a unary read index have
nonincreasing total size. The read suffix never exceeds the original assignment.
Counting that suffix separately gives `2*A + L + S + 1` data units, including
the read-only assignment and one control tag. This is a data-size bound, not
physical heap usage: addresses, list headers, serialization delimiters, and
garbage collection remain outside it. The code must already be supplied; it can
come directly from the parser, without recompiling the formula. Parser execution,
assignment enumeration, and the full solver do not yet have a combined
transition-machine simulation. The native service uses `evalRun` when checking complete witness proposals; its
evaluator count is realized exactly by this separately proved machine. The new
partial evaluator has no corresponding transition-machine proof yet.
`parsed_eval_steps` and `parsed_eval_space` apply these conclusions directly to
the program produced by parsing a valid request. This machine evaluates **one
assignment**; a false result is not an UNSAT verdict. The reference solver
searches all assignments for a negative answer; the new solver instead supplies
a tree of sound partial contradictions covering both branches at each split.

The next proof obligations are concrete:

1. Give parser, width discovery, assignment generation, and search explicit
   transition semantics, and compose them with this evaluator. Charge all
   control, copying, and construction work in that combined machine.
2. Specify a finite-alphabet configuration encoding and prove a simulation
   with charged access, copying, and index operations. The current data-size
   potential is useful for this, but is not itself that simulation.
3. Bound the full solver's live data, rather than just one evaluation. The
   reference engine materializes all assignments. The new engine avoids that
   list but may construct an exponential refutation tree. Its search-stack and
   certificate allocation need their own bound.

A general polynomial SAT algorithm is a separate algorithmic requirement.
Completing these verification steps for the reference exhaustive solver will not
remove its exponential assignment dependence.

## Current lazy search and certificate portfolios

`Search.lean` provides the counted lazy fallback. `occursRun` and `distinctRun` collect
the distinct indices without renaming them. A sparse assignment stores only
chosen variables. `partialRun` returns true, false, or unknown; a known value
holds for every extending total valuation. `searchSparse` branches only while
unknown, with false tried first. It produces a satisfying sparse assignment or
a refutation tree. `materialize_satisfies` justifies the dense compatibility
witness returned by the service. The search bound is `nodes + 1 <= 2^(d+1)` for
`d` distinct indices. It bounds nodes, not elapsed time or heap allocation.

`checkRefutation_sound` proves that accepting a tree excludes every satisfying
valuation. A conflict leaf must evaluate to false under the current partial
assignment. A split must validate both children. `Knowledge.lean` composes this
checker with complete-witness checking and the fallback, proving correctness
for arbitrary proposal lists. The Python/native interface limits each portfolio
to four entries; correctness does not rely on this limit. A previous refutation
may prove a related query, including a conjunction extension, only after checking
it against that query. No input-shape heuristic or cached negative bit suffices.

These definitions charge variable collection, deduplication, sparse lookup,
partial evaluation, search, witness materialization, and proposal checking in a
new abstract ledger. The fixed-width coefficients and one-witness overhead bound
above still refer to the earlier eager solver and policy. They are not claimed
for the new ledger. No composed transition-machine, physical memory, or general
polynomial resource bound has been added for this fallback. The default service
uses the checked CDCL boundary below; structural-width algorithms remain future work.

The default audit now checks 1035 declarations, including 563 theorem declarations
(with generated helpers), and accepts only the standard logical axioms.

The native executable and [persistent service](../solver/README.md) retain the lazy
core and verified portfolios. SQLite retains complete SAT/UNSAT
results, witnesses, and refutations across process restarts. The functional cache invariant is checked in Lean;
database transactions, serialization, engine fingerprinting, and the Python
adapter are integration-tested, not kernel-verified. Build the executable with
`lake build oracleSolver`. [Workload experiments](../experiments/README.md)
compare actual operation counts and elapsed service costs.

## Default checked CDCL service

`CDCL.lean` recursively compiles formulas into cached AND/inverter graphs,
preserving the value under every valuation. The graph shares duplicate gates
and simplifies constants. `compiledCNF_unsat` composes that theorem with
`Std.Sat.AIG.toCNF_equisat`. `checkLRAT_sound` then composes the standard
library's `LRAT.check_sound` with the formula-to-CNF theorem. This uses the
pinned Lean 4.24.0 implementation directly, without invoking `bv_decide` or
introducing a native-decision axiom. The build's transitive axiom audit passes.

The Python adapter runs the bundled CaDiCaL 2.1.2 and returns an answer only
after a checked witness or proof. SAT models are evaluated on the original
formula. For UNSAT, the checker reconstructs CNF from that formula before
checking the LRAT actions; the external DIMACS file and clause identifiers are
not a trusted shortcut. Constant-false AIGs use `circuitFalse_sound` instead.

The automatic policy first tries saved proposals, constant simplification,
all-false/all-true witnesses, and a 64-node local attempt. `BoundedSearch.lean`
is a proposal generator: a returned witness or refutation is checked again.
Budget exhaustion means no proposal, never UNSAT. Its node budget does not
bound the work of an individual partial evaluation. External timeouts and
rejected certificates return errors without persisting a decision; thus this
bounded service is sound on completed answers, not an unconditional total
decider. If CaDiCaL is unavailable, the complete lazy fallback remains available.

The new connection proves semantics, not a complete cost model for CNF
construction, CDCL, or LRAT. Modern results therefore use `null` for total
abstract work and search nodes, with `counted_complete=false`. Parser work
alone is measured, including both parses when an external result is checked.
The earlier coefficients continue to describe their original definitions.
Native compilation/runtime, JSON, the Python adapter, and SQLite remain outside
the kernel proof. Cross-query witnesses and certificates persist, but the
current adapter does not retain CaDiCaL's internal clause database between calls.

The rest of the paper's neural, oracle, and general expected-savings
arguments retain their conventional proofs and literature audit. This directory
provides machine-checked proofs for the claims mapped above, not for the entire
manuscript. The underlying results remain elementary consequences of established
theory; machine checking is not a novelty claim.
