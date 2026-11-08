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
| Restricted core bound | `solveRun_bound`, `solveRun_fixed_width` | The same counted implementation has `T <= W^2 + 2^v (W+13) + 2`; fixing `v <= K` gives coefficient `14*2^K+3` and degree 2 in encoding length plus one. |
| Binary parsing and combined decision | [Parsing.lean](OracleMachines/Parsing.lean): `decodeRun_value`, `decodeRun_bound`, `decideRun_sat`, `decideRun_unsat`, `decideRun_fixed_width` | The counted parser agrees with the existing parser, costs at most `8L+7`, and composes with the solver. On `encode f` with width at most `K`, total counted decision work is at most `(14*2^K+12)(L+1)^2`. |
| Coverage of every accepted input | [Canonical.lean](OracleMachines/Canonical.lean): `encode_decode`, `parseProgram_decode`, `decideRun_valid_fixed_width`, `decideRun_valid_logarithmic_width`, `parsed_eval_steps`, `parsed_eval_space` | Successful decoding implies `encode f = bits`. The restricted decision bounds and evaluator transition/data-size bounds therefore apply to arbitrary accepted requests, measured against the original binary length. |
| Growing variable count | [Restricted.lean](OracleMachines/Restricted.lean): `decideRun_small_assignment_space`, `decideRun_logarithmic_width`, `small_assignment_space_requires_length` | If `2^v <= L+1` (in particular `v <= floor(log2(L+1))`), parser plus decision costs at most `24(L+1)^2`. Enforcing that premise by padding requires length at least `2^v-1`. |
| Certified adaptive policy | [Hybrid.lean](OracleMachines/Hybrid.lean): `hybridRun_correct`, `serve_correct`, `hybridRun_overhead`, `actual_savings_identity`, `repeated_hit_savings` | A previously acquired witness is checked on each new formula; fallback is exact. Costs include validation, fallback, copying the acquired witness, and stream control. The savings identity follows the actual changing state. |
| Lazy search and pruning | [Search.lean](OracleMachines/Search.lean): `partialRun_sound`, `solveSparse_correct`, `solveSparse_certificate`, `solveSparse_nodes`, `materialize_satisfies` | Branch only on distinct occurring variables; partial truth and falsity are sound; every UNSAT search returns a checked refutation; at most `2^(d+1)-1` nodes; dense witness conversion preserves satisfaction. |
| Reusable positive and negative certificates | [Knowledge.lean](OracleMachines/Knowledge.lean): `probeWitnesses_sound`, `probeRefutations_checked`, `solveSearch_verified`, `reuseSearch_verified`, `reuseSearch_correct` | Arbitrary proposed witnesses and refutations are checked against the current formula. The combined policy decides SAT correctly, without trusting proposal provenance. |
| Checked CDCL boundary | [CDCL.lean](OracleMachines/CDCL.lean): `compiledCircuit_correct`, `circuitFalse_sound`, `compiledCNF_unsat`, `checkLRAT_sound` | Shared AIG construction preserves formula evaluation. Standard-library CNF translation and LRAT checking compose to exclude a satisfying valuation whenever a proof is accepted. |
| Bounded preliminary attempt | [BoundedSearch.lean](OracleMachines/BoundedSearch.lean): `boundedSearch_remaining_le` | A finite node budget never increases. Exhaustion returns no proposal; the executable independently checks every proposed witness or tree before acceptance. |
| Accumulated exact results | [Cache.lean](OracleMachines/Cache.lean): `cache_lookup_sound`, `cacheStep_correct`, `cacheStep_exact`, `cacheStep_retains` | Every completed result remains available, including negative answers; lookup and insertion preserve exactness, assuming the loaded cache is intact. |
| Structural expansion | [Components.lean](OracleMachines/Components.lean): `componentSystem_sat_iff`, `surviving_exact`, `surviving_expand`, `repeated_component`, `equivalent_summaries` | Disjoint private witnesses compose through a shared feasible interface assignment; finite tables and incremental intersection are exact. |
| Component refutation transfer | `componentEmbedding_unsat`, `componentLRAT_sound` | Checked conjunct paths and renaming transfer a refutation, including after added constraints. |
| Structural resource budget | `summaryTable_size`, `structuralBudget_expand`, `structuralBudget_linear`, `summaryBits_reuse` | Exact relation-table size and arithmetic bounds for the declared shape-acquisition/intersection ledger, excluding runtime and matching costs. |
| Obligations for another representation | [Invariant.lean](OracleMachines/Invariant.lean): `expansion_invariant`, `answer_at_cover` | The base, preservation, and exact new-coverage hypotheses imply exactness at every finite stage and at a covering stage for each input. |
| Construction recurrence | [Resources.lean](OracleMachines/Resources.lean): `cumulative_eq` | Recursive construction cost equals base cost plus every expansion cost. |
| Arithmetic in Corollary 12.2 | `polynomial_stage_sum`, `full_polynomial_bound`, `bounded_expansion_cost` | Shared polynomial stage budgets yield a single polynomial bound including reading, base construction, expansion, and evaluation. |
| General coverage schedules | `polynomiallyBounded_comp` | Composing a polynomial cumulative-cost bound with a polynomial coverage-stage bound preserves polynomial boundedness. |
| Proposition 12.4: staged reuse | [Reuse.lean](OracleMachines/Reuse.lean): `totalWork_eq`, `totalWork_le`, `strict_savings_iff`, `savings_of_upper_bound` | All expansion and query work is charged. Avoided solver work must repay construction. An upper bound on retrieval gives only a sufficient savings condition. |
| Growing-domain amortization | `average_identity`, `amortization_iff`, `eventually_positive_queries` | The average-cost difference is exactly expansion cost divided by query count. Divergent counts are eventually positive. |
| Failure of the unrestricted inference | [Limits.lean](OracleMachines/Limits.lean): `exponential_not_polynomial`, `exponential_expansion_not_polynomial`, `explicit_table_not_polynomial` | The explicit answer count and the cumulative costs of stages costing `2^j` have no polynomial bound. |
| Contrasting workloads | `one_query_expansion_diverges`, `many_queries_amortize` | For expansion costs `2^j`, one query per stage gives divergent expansion cost per query; `4^j` queries per stage make it tend to zero, including any fixed base cost. |

All declaration names above are in the `OracleMachines` namespace. The root
module `OracleMachines.lean` imports the complete development and its audit.

## Conventions and boundary of the formalization

`Residuals.lean` adds exact single-variable conditioning and SAT/UNSAT branch
recomposition for arbitrary formulas. Its four main lemmas are `condition_eval`,
`satisfiable_condition`, `satisfiable_split`, and `unsatisfiable_split`. They
support the semantics of the research CNF residual candidate. The later
`no_injective_choice_of_card_lt` gives the finite-cardinality obstruction behind
a Hall certificate. These lemmas do not verify the Python recognizer, matching
algorithm, persistence or checker, or bound the residual count polynomially.
The positive-clause follow-up adds `positive_clause_subsumption`,
`positive_core_models`, and `positive_core_extension`: a retained subset implies
its positive superset, a covered retained core preserves every model, and a fresh
subset witness preserves coverage under an added clause. These use unsigned
clauses; they do not assert a refinement of the Python signed-literal encoding.
`positive_history_models` extends this invariant to a whole list of covered
additions to a fixed base. It supports the semantics of the separate Python
delta-history prototype without verifying its SQL representation or runtime.
The latest audit includes 4,067 declarations / 1,929 theorem declarations.

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
passes for 1,264 declarations, including 694 theorem declarations.

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
original adapter does not retain CaDiCaL's internal clause database between calls.

The rest of the paper's neural, oracle, and general expected-savings
arguments retain their conventional proofs and literature audit. This directory
provides machine-checked proofs for the claims mapped above, not for the entire
manuscript. The underlying results remain elementary consequences of established
theory; machine checking is not a novelty claim.

## Structural expansion and certified component transfer

`Components.lean` adds checked conjunct paths and renaming, with
`componentEmbedding_unsat` and `componentLRAT_sound` establishing transfer of a
negative result to a larger formula. Paths cannot descend through negation.
The executable accepts only one wrapper around an existing base certificate.

`componentSystem_sat_iff` proves exact composition of components with disjoint
private variables and a shared interface. `boundaryRelation_exact` and
`surviving_exact` connect finite interface truth tables to actual formula
satisfiability. `surviving_expand` gives incremental intersection;
`repeated_component` and `equivalent_summaries` justify summary reuse.
`shared_variable_counterexample` rules out composing bare SAT bits on an
overlapping variable. `summaryTable_size` gives exactly 2^b summary bits.

The `structuralBudget` ledger charges d distinct shapes of evaluation size s
and m occurrences: d * 2^(b+k) * s + m * 2^b. Its expansion and linear bounds
are arithmetic theorems for this declared budget, not a proof of Python/CDCL
instruction counts or of finding a small separator. `summaryBits` counts the
dictionary and current relation only; mappings, shape descriptions, witnesses,
parsing, proof checks and archived requests must be added. Fixed b and k allow
unbounded total private variables without a general-SAT consequence.

The structural milestone audits 1,264 declarations, including 694 theorem
declarations. All earlier modules remain included. The runtime component policy
currently implements the empty-interface case, with independent final checks.


## Local elimination, lazy rows, and incremental LRAT

- `Interfaces.lean`: exact bucket elimination (`eliminate_sat_iff`), leaf and
  projection semantics, unaffected-factor invariance and semantic replacement.
- `InterfaceProtocol.lean`: native definitions, memoized row calculation,
  original-constraint bindings and negative dependency-context checks. JSON/state
  bookkeeping is executable Lean, not an end-to-end kernel theorem.
- `InterfaceCosts.lean`: counted local evaluation, complete-table acquisition,
  short-circuit projection, and sound lower/upper interpretations of unknown rows.
- `IncrementalProof.lean`: a shared-graph definitional CNF with stable variables;
  `incrementalCNF_unsat` and `checkIncrementalLRAT_sound` connect a checked proof
  to the original formula for any previous AIG. Its state invariants come from
  the pinned Lean standard library; the local traversal adaptation is covered
  by [the third-party notice](THIRD_PARTY_NOTICES.md).

The Python planner, persisted proof hints and external solver remain untrusted
proposals. Formal local-operation bounds are separate from the elapsed ledger;
no complete CDCL, database, serializer or native machine instruction theorem is
claimed. The new interface path and optional `--incremental-proofs` extend the
historical milestone descriptions above.

The local-interface milestone audited 1,554 declarations, including 837 theorem declarations.


## Restricted scaling obligations

`Scaling.lean` adds symbolic-tree restriction, conjunction and existential
projection correctness; checked conjunct-refutation transfer; a depth/fanout
upper envelope for affected work; and conditional update/stream/archive bounds.
If affected summaries, row capacity, per-row work and all overhead each admit
one bound C*(N+1)^k, declared update work is at most (C+C^3)*(N+1)^(3*k).
Logarithmic local width suffices to bound complete-table row capacity by N+1.
Coverage, acquisition and the other resource premises are not inferred from
finite-stage correctness. The archive theorem also proves that retaining at
least one new unit per update cannot support unbounded updates under a fixed cap.

The symbolic reference is a tree, not a proof of Python's reduced-DAG optimizer.
The live LRAT check reuses the existing AIG and applies the established soundness
theorem for arbitrary previous graphs. Native verified-core state is replayed
from checked certificates after restart; JSON/state bookkeeping still needs an
end-to-end refinement theorem. No whole-service bit-machine bound is claimed.

The scaling milestone audited **1,650 declarations / 879 theorem declarations**.

The balanced-chain follow-up adds `BalancedChain.lean` and `ChainProtocol.lean`:
exact four-entry Boolean composition, associativity, identity padding, balanced
updates, preservation of all other leaves, and exactly height+1 copied nodes per
replacement. Native joins materialize four entries eagerly and carry the proved
summary invariant. `ProofFragments.lean` proves hinted RUP entailment, reuse under
added permanent premises, and UNSAT soundness through the existing circuit CNF
translation; `FragmentProtocol.lean` integrates the checker into native sessions.
The cost theorem is for tree operations, not all Python/SQLite/IPC work. The
fragment protocol's external session orchestration remains outside a complete
kernel-verified refinement. The transitive audit still rejects admits and custom
axioms.

The current full build audits **1,828 declarations / 941 theorem declarations**.

## Supplied finite-state layers

`Layered.lean` generalizes the Boolean chain to `q` states per boundary. It proves
existential composition, associativity/identity, summary exactness, preservation
under replacement, replacement at the selected position and invariance elsewhere.
The declared replacement ledger is `h+1+h*q^3` for capacity `2^h`; summaries need
`q^2` Boolean cells. For `b` Boolean variables per layer, `q=2^b`, so width remains
exponential. Materialization returns a vector before creating a lookup closure;
generated native code was inspected to ensure eager construction. This also
repairs delayed materialization in the original Boolean-chain join.

`LayeredProtocol.lean` carries valid trees across native checked definitions and
queries. The runtime accepts width 1–4. It checks every proposed join; witness
output is optional and independently checked by the Python caller. The abstract
work ledger excludes source conversion, decomposition discovery, bit arithmetic,
serialization, storage, full witnesses and restart. It is not a complete compiled
machine-cost theorem. The protocol/session/request binding also remains a
refinement obligation. These are established bounded-width dynamic-programming
and finite-monoid ideas, with a checked implementation and explicit accounting.

## Priority follow-up: executable counts and source binding

At that milestone the build audited **2,090 declarations / 1,047 theorem declarations**.
`LayeredCosts.lean` implements short-circuit `anyRun`, a materialized table of
values and test counts, `joinRun`, and `replaceRun`. Lean proves that their values
agree with the existing composition/join/replacement functions, that a join
performs at most `q^3` middle-state tests, and that replacement's test-plus-node
counter is at most `h+1+h*q^3`. These are counts produced by an executable
reference, rather than only a declared recurrence. They do not count vector
allocation bytes, integer bit operations, IPC, database work or native machine
instructions. The production join remains the uninstrumented equivalent.

`LayeredProtocol.lean` now proves that the executable rowwise relation comparison
is exact, that accepted witness extraction constructs a valid full-tree trace of
length `2^h+1`, and that splitting a valid tree yields prefix/suffix relations
whose composition is its summary. An identity suffix therefore preserves the
prefix decision. Native queries reject a shortened logical length when this
suffix condition fails. This check can add `O(q^3 log M)` work to a request;
the `q^2` endpoint-query bound presumes that the padding invariant is available.
Proposed join masks are decoded and compared rowwise, so acceptance no longer
depends on an unproved encode/decode round trip.

`LayeredSource.lean` compiles CNF under a supplied disjoint ordered partition of
positive variable IDs. Every clause must belong to one block or two adjacent
blocks; each block has at most four variables. The native checker rejects
missing/repeated variables and nonadjacent clauses. It recomputes compilation
and compares every source edge and padding leaf against the checked tree before
binding its answer to the source. Local clause semantics, sequence composition,
and the mathematical source-binding implication are proved. The follow-up below
also proves the original-variable mapping, local CNF translation and global clause
grouping. `SourceBinding.lean` now supplies complete-tree binding as described
below. Discovery of the partition, mutable node/patch invariants, JSON orchestration,
and a complete source-API refinement theorem remain open. This is a restricted tractable family,
not a compiler for unrestricted CNF with guaranteed bounded width.

For general factors, `factors_equal_matching` and `project_equal_conjunctions`
justify the semantic rule used by the new native rebind checker. Equal relations
can transfer row values while new nodes retain current parent/source identities.
The equivalence-class cache and row-cache implementation still lack a complete
state-invariant refinement proof. Deletion and restart tests complement, rather
than replace, that missing theorem.

## Source-bearing incremental decisions

At this milestone the build audited **2,279 declarations / 1,106 theorem declarations**.
[`SourceInvariant.lean`](OracleMachines/SourceInvariant.lean) represents local
CNF buckets and identity padding in a source tree. Its important connections are:

| Result | What it establishes |
| --- | --- |
| `compile_exact`, `decision_exact` | Cached composition represents satisfying paths through the local source. |
| `edit_at`, `edit_other` | A source edit changes its selected leaf and preserves every other leaf. |
| `edit_compile`, `checkedEditRun_correct` | Updating cached relations agrees with compiling the updated source. |
| `sourceTable_tests`, `checkedEditRun_budget` | Executable reference counts local clause/literal evaluation, joins and source nodes. |
| `CheckedSource`, `checkedLeaf`, `checkedJoin` | Constructors carry an alignment proof with the actual cached tree. |
| `checked_decide_exact`, `checked_unsat_exact` | The native decision's positive and negative answers have the current local-source meaning. |

For q=2^width, height h, and a replacement with c clauses and L literals, the
combined reference count is at most `q²(1+c+L) + h*q³ + 2(h+1)`. The source tree
alone has h+1 copied-node events. This starts from an aligned cached predecessor;
it does not include initial compilation or native transport/storage instructions.

[`SourceUpdates.lean`](OracleMachines/SourceUpdates.lean) initially constructed
these checked native values. The original-source nodes below now strengthen
their meaning. Registration validates partition-local clauses, proposed
masks, consecutive child ranges and unchanged subtree identities. Initial flat
CNF binding is linear. Later patches visit changed paths only. Decision-only
queries used `CheckedSource.decide` at this milestone; full witness requests additionally traverse
and check their output. Python keeps both roots until patch checking succeeds,
then native reference-count checks permit dependency-safe eviction.

The invariant concerns local CNF meaning. Original global IDs now have the local
translation and grouping proofs below. Composing these with JSON, the native
source-tree store, Python/SQLite, hashes and replay is still open. The reference
event bound is not a compiled bit-machine bound.
Neither native incoming-count maintenance nor Python live-reference tracking
has a complete state-invariant theorem here. Their pressure, branching, shared
children, failure and restart cases are covered by integration tests. General
factor equivalence/row-cache refinement is a separate remaining problem.

## Indexed negative-proof context

`InterfaceProtocol.lean` now uses `contextSubsetRun` in eager and lazy negative
checks. `contextSubsetRun_exact` proves it accepts exactly the previous condition
that every proof leaf occurs in the active list. `contextProbe_value` connects
the costed short-circuit loop to list `all`; `contextProbe_bound` bounds membership
probes by the number of proof leaves. `contextSubsetRun_budget` adds one index
insertion request per active entry. Hashing, equality, allocation and the full
evidence traversal are separate costs; this is no worst-case constant-time
hash-table assumption. Native responses and Python ledgers expose the two counts.

At this milestone the audit passed **2,290 declarations / 1,113 theorem declarations**.

## Original-variable mapping and local translation

[`SourceMapping.lean`](OracleMachines/SourceMapping.lean) strengthens the actual
source compiler. A dependent hash-map entry contains a `SourcePosition` proving
that its block/slot refers to its original variable ID and lies below the width.
An executable alignment pass gives `CheckedLayout.complete`: every coordinate
in the supplied block arrays maps back to itself. It includes unused variables,
short blocks, and empty blocks. The builder rejects zero IDs and duplicates.

| Result | What it establishes |
| --- | --- |
| `SourcePosition.agrees` | A mapped bit is the value of its original variable under array-based agreement. |
| `CheckedLayout.locate`, `blockWidth` | Every supplied coordinate is indexed correctly and each block fits the width. |
| `sourceWords_agree`, `CheckedLayout.sourceWords_bound` | Every global valuation yields agreeing states below `2^width`. |
| `CheckedLayout.sourceValuation_agrees` | Arbitrary block words define a consistent valuation of the original IDs. |
| `CheckedLiteral`, `CheckedClause`, `CheckedCNF` | Successful translations carry evaluation equality for the literal, clause, or bucket supplied as a type parameter. |
| `CheckedCNF.satisfiable_exact`, `unsatisfiable_exact` | A checked local bucket is satisfiable exactly when its compiled boundary relation has an accepting pair. |

Initial compilation uses `translateClause`; the local-update compiler returns
`CheckedCNF` from `translateCNF`. Both call the proved literal translator. The
iterative builders check that accumulated original arrays equal their supplied
inputs before returning. Thus their proofs are tied to the requested local
source, rather than an unrelated accumulated array. Zero, missing and nonlocal
literals are rejected. The next section proves global grouping; connecting the
result through native node identities to the whole source tree remains open.
Local exactness alone does not prove either obligation.

The layout validation adds one lookup per variable entry, plus block traversal.
Translation accumulates original arrays and checks their equality, adding linear
entry visits and temporary storage in clause/literal count. Initial grouping also
looks up literals before translation. Hashing and comparison of arbitrary-size
IDs, allocation and runtime instructions are separate costs. None of these is
included in the existing `q²(1+c+L)` relation-evaluation bound. Layout construction
is paid again on replay; warm edits translate their supplied buckets only.

At this milestone the build audited **2,477 declarations / 1,188 theorem declarations**,
with no admits or added axioms, and **148 integration tests passed**. Those checks compare
both compiler paths with 9,520 exhaustive boundary assignments across 112 CNFs,
including permuted slots and IDs larger than 64 bits. They also cover invalid
mappings, short/empty blocks, unused variables, restart, a 30,001-literal clause
and a 12,000-clause bucket. These are correctness checks, not a timing study or a
claim about efficient decomposition of unrestricted SAT.

## Complete CNF grouping and consistent paths

[`SourceGrouping.lean`](OracleMachines/SourceGrouping.lean) now carries the
grouping invariant in the executable compiler. `GroupedCNF` is indexed by the
entire supplied CNF. Its original buckets flatten to a permutation of that CNF,
preserving duplicate occurrences and empty clauses. Its local buckets carry the
evaluation equality for their corresponding original buckets at the given edge.
The arrays have the proved logical edge count. `GroupedCNF.push` preserves all
these properties when the native loop appends a checked clause at an in-range
edge. The final builder compares its accumulated flat input with the requested
CNF before returning a value indexed by that request.

| Result | What it establishes |
| --- | --- |
| `flatMap_modify_push`, `GroupedCNF.push` | Inserting at one bucket preserves the clause multiset and per-edge semantics. |
| `GroupedCNF.clause_occurrences` | Each original clause occurs equally often before and after grouping. |
| `GroupedCNF.original_exact` | The complete original CNF holds exactly when all original buckets hold. |
| `GroupedCNF.satisfiable_exact`, `unsatisfiable_exact` | The original CNF is satisfiable exactly when one shared sequence of bounded states satisfies every translated bucket. |
| `relationPath_iff`, `sequence_path`, `sequence_nonempty` | A sequence of relation compositions represents precisely consistent boundary paths. |
| `GroupedCNF.sequence_exact` | The complete original CNF agrees with nonemptiness of the composed relation. |
| `CompiledSource.bound_tree_exact`, `bound_tree_unsat` | The tree summary agrees with the original CNF, conditional on exact ordered leaf binding and identity padding. |

`compileSource` uses `groupClauses` and retains this proved grouping. It no longer
returns unrelated original and translated arrays. This establishes correctness
of successful typed compilation. A theorem that every valid promised input is
accepted is still separate. The final tree theorems **require** the binding
premise. The following checkpoint supplies it for complete-source checks;
preservation through the mutable node/patch protocol still needs a state theorem.

The flat builder adds an array of clause references and a final equality check.
Its additional entry visits are linear in clause/literal count, excluding the
cost of arbitrary-size integers, allocation and compiled execution. Proof terms
are erased. No whole-machine bound or timing improvement is claimed. Warm local
edits still use the existing checked bucket compiler and do not regroup the full
CNF; initial compilation, full binding and replay retain their separate costs.

At this milestone the build audited **2,562 declarations / 1,233 theorem declarations**
without admits or added axioms. **152 tests passed**, including 60 generated global
CNFs checked on all 11,680 complete assignments, exact bucket/multiplicity checks,
and service verdict/witness checks. A regression has nonempty local relations
but no consistent global path. Boundary tests compile 65,537 supplied blocks and
12,000 repeated clauses without stack failure. These complement the existing
local-translation, restart, patch, retention and persistence tests.

## Executable complete-source binding

[`SourceBinding.lean`](OracleMachines/SourceBinding.lean) discharges the ordered
leaf-binding premise for the actual stored `CheckedTree`. `bindCompilation`
checks its width, compares every logical leaf with the corresponding compiled
bucket or individual identity padding, and returns a `BoundCompilation` carrying
that equality and the tree's validity proof. `BoundCompilation.decide_exact`
and `unsat_exact` connect its executed Boolean decision to the original CNF.
Both `layered_source_query` and initial `source_bind` use this constructor and
decision. The latter retains its original-clause/provenance checks as well.

`Tree.leavesInto_exact` proves the accumulator traversal preserves leaf order.
It visits expanded tree occurrences, not just distinct shared native nodes.
`bindingScan_exact` proves acceptance exactly when the leaf lists agree;
`bindingScan_bound` bounds relation-comparison calls, and
`bindingScan_complete` proves one comparison per logical leaf on success.
The scan is tail recursive and the tree traversal uses a list accumulator.

For N padded leaves and q=2^width, both Python interfaces expose
`binding_leaves` and the proved `binding_relation_comparisons=N` count.
`binding_cell_bound=N*q²` and
`binding_source_test_bound=(N+c+L)*q²` are diagnostic reference bounds, with
c source clauses and L literal occurrences. Only the comparison-call count has
a new executable counting theorem. The other fields apply the existing
row/clause/literal ledger and do not establish a total native cost theorem.
Actual-mask reads, bit operations, indexing, list/array allocation, endpoint
queries, witness output, JSON and storage remain separate costs.

Initial source-version binding now evaluates the source relations again during
this scan. Full-source layered queries already performed an unproved comparison
pass. Warm local edits and current-source queries do not run the new full scan;
their four binding counters are zero. No new timing or memory reduction is claimed.

At this milestone **156 tests passed**. Lean audited **2,615 declarations / 1,259 theorem declarations**
without admits or added axioms. Regressions reject wrong leaf order even when the
SAT/UNSAT answer agrees, and reject nonidentity padding whose composition is
identity. They check width/capacity mismatches, valid witness output, counts at
widths 1, 2 and 4, and 65,536 logical leaves represented by 17 shared native nodes.

This closes initial complete-source binding. The following checkpoint retains
original-source meaning through typed node construction and consecutive joins.
Mutable identity lookup and requested-patch preservation are still separate.

## Original-source nodes with indexed intervals

[`SourceNodes.lean`](OracleMachines/SourceNodes.lean) retains the original clauses
and their `CheckedCNF` translation in each logical leaf. `OriginalTree` is indexed
by the exact layout array, width, start and height. A logical leaf has a proved
in-range edge; an identity-padding leaf has a proved out-of-range edge. A branch
requires children at starts s and s+2^h with the same height h.

`CheckedNode` couples that original tree to the actual cached relation tree by
an alignment proof. Checked leaf, padding and join constructors preserve it.
`checkedJoin_clauses` and `checkedJoin_occurrences` prove that a join concatenates
the original clause lists and preserves every occurrence, including duplicates
and empty clauses. The clauses are retained even when their relation is unchanged.

The decision theorem now concerns those **original clauses**, not just the local
bit representation. `OriginalTree.path_exact` connects relation paths to states
at the indexed global edges. A satisfying valuation gives agreeing block states;
the final block state repeats through identity padding. Conversely, any accepting
path yields a global valuation using the complete layout map. Thus
`CheckedNode.decide_exact` and `unsat_exact` prove exact SAT/UNSAT semantics for
the original clauses stored in the node. Flattening is a specification operation;
the executed decision reads only the cached summary.

The native `Context` contains a model map whose value type depends on its layout.
This fixes width and layout for every node without comparing the whole layout at
each join. Registration uses the new constructors, checks consecutive **typed**
starts, and stores their cached trees in the existing relation store. Warm queries
use `CheckedNode.decide`; restart reconstructs nodes using the same constructors.
Changing context resets both maps. Failed definition batches return no new state.

Original integer-clause arrays now remain reachable from native source leaves in
addition to JSON evidence and local translations. New metrics
`original_source_nodes`, `original_clause_entries` and `original_literal_entries`
count newly registered source nodes and their logical original payload entries.
They include replay, exclude duplicate registrations, and are zero on warm
unchanged queries. These counters are runtime diagnostics, not a new formal
allocation/byte bound. Joins retain child references and do not flatten the source;
reference management, actual object sizes and allocator/bit costs remain separate.
No new speedup, smaller memory footprint or total-resource bound is claimed.

All **159 tests pass**, including 20 source-update tests. Lean audits **2,751
declarations / 1,320 theorem declarations** without admits or added axioms. New
regressions exercise rejected intervals, layout changes, definition-batch rollback,
duplicate registration, incompatible shared boundaries, payload counters, sparse
IDs above 64 bits, empty/short blocks, local edits, old branches and restart.

The named-map part is extended by the following checkpoint. The theorem that a
patch selects the requested successor remains open; typed node semantics alone
does not establish it.

## Paired native maps and decoded source metadata

[`SourceStore.lean`](OracleMachines/SourceStore.lean) makes pointwise agreement a
field of the native store. Both maps have the same keys, and the relation tree
stored at each key is exactly the associated model's checked tree. `BodyMatches`
also binds successful JSON getters for identity, layout, width, start and height
to that model. At a logical or padding leaf it retains exact original clauses,
including their order and repeated or empty entries. Branch payloads are not
flattened or reparsed.

| Declaration | Guarantee |
| --- | --- |
| `corresponds_empty`, `corresponds_insert`, `corresponds_erase` | Pointwise agreement survives initialization and paired updates. |
| `Store.lookup_exact`, `Store.missing_exact` | A named relation lookup retrieves its matching original-source model; absence agrees. |
| `Store.lookup_semantics` | A retrieved tree's decision is equivalent to satisfiability of its model's original clauses; a negative decision is equivalent to unsatisfiability. |

Native registration retains equations from the actual field getters and uses
these paired constructors. Source deletion erases both entries together. These
proofs do not require a full-store scan. Parsed/header wrappers may allocate
temporary values; proof fields erase, while decoding and comparisons remain
runtime work. The existing reference-count loops are shared by the generic and
source stores, with their previous underflow/reference checks. Their arithmetic
is not covered by the new map invariant.

The next checkpoint below adds serialized-summary correspondence and proves
named child lookups at registration. Dependency lifetime, exact requested-patch
semantics, complete serialized replay, Python/SQLite refinement, general factor
row/equivalence caches, acceptance completeness and complete resource costs
remain separate obligations. The guarantee is for the supplied adjacent-block
representation; it gives no unrestricted-SAT structural or coverage bound.

At this checkpoint, **162 tests pass**, including 23 source-update tests. Lean
audits **2,858 declarations / 1,367 theorem declarations** without admits or added
axioms. New regressions cover atomic deletion failure, reference checks after
rollback, shared descendants, safe name reuse, distinct original clauses with
equal relations, and missing-field rollback.

## Named child registration and serialized summaries

[`SourceLinks.lean`](OracleMachines/SourceLinks.lean) defines `JoinLinks` against
the exact model-map snapshot used at registration. `readJoin` returns a node
with equations for its decoded left/right names, their successful lookups and
the checked consecutive join of those two retrieved models. The native source
registration path now executes this constructor. Its subtype proof erases;
it does not retain the registration map or copy/scan a store.

`JoinLinks.original_clauses` attributes every original clause occurrence to the
retrieved children. `decision_exact` requires one valuation satisfying **both**
child sources. It does not conjoin independently chosen SAT answers.
`distinct_children` follows from consecutive starts and positive subtree span;
this fact is specific to indexed source nodes, not the generic relation DAG.

`insert_fresh` preserves a join's links under a fresh-key model insertion.
`erase_unreferenced` preserves them when the removed key is neither decoded child.
These are conditional map-transition theorems. The next checkpoint discharges
their lifetime premise for the native source store and connects registration
snapshots to current lookups.

`BodyMatches.summary` now also retains the decoded mask and its exact relation
equality to the model's cached summary. This field is part of the existing paired
store invariant and survives paired insertion/erasure. Leaves and padding use
their checked relation directly; branches retain the successful comparison proof.
The decoder still enforces the bounded mask range. This adds no relation scan
beyond the existing comparison, and no new runtime counter or speedup claim.
Parsing wrappers, comparisons, allocation, transport and archive access remain
outside a complete native cost theorem.

All **165 tests pass**, including 26 source-update tests. Lean audits **2,874
declarations / 1,380 theorem declarations** without admits or added axioms.
New cases cover equal relations with distinct named sources, malformed/missing
children, live-identity rebinding, wrong masks with unchanged SAT answers, and
12 parents deleted in shuffled order while preserving their shared children.

## Exact incoming counts and live source dependencies

[`ReferenceCounts.lean`](OracleMachines/ReferenceCounts.lean) defines exact incoming
counts as the sum of decoded child-reference multiplicities across every live
parent. A finite parent set witnesses the map domain **inside a proposition**;
neither that set nor the aggregate sum is constructed or scanned at runtime.
The specification counts occurrences, including a repeated child in a reference
list. Native source branches separately prove their two child names are distinct.

`increment_exact` proves the fold's pointwise addition law. Successful `decrement`
returns its subtraction equation, retaining underflow rejection. `exact_insert`
and `exact_erase` prove the aggregate invariant for fresh insertion and zero-count
deletion. `Exact.zero_no_child` proves that a zero count excludes the deleted key
from every live parent's decoded child list.

[`SourceLifetime.lean`](OracleMachines/SourceLifetime.lean) wraps the paired store
with this count invariant and `Linked`, which requires every live branch to name
its exact current child models. `linked_insert` uses fresh-key preservation.
`linked_erase` combines metadata, decoded children and zero-count exclusion to
discharge the earlier deletion premise. `Store.lookup_branch` recovers these
current child links from a named relation-tree lookup.

The executed source context now uses this wrapper. Initialization creates the
empty invariants. Fresh registration supplies its actual missing-key equation
and either a leaf proof or the checked join links. Duplicate registration changes
no state. Source deletion uses the counted decrement and constructs both updated
invariants; a failed functional batch returns no replacement state. Thus surviving
parents retain their exact named dependencies after successful source operations.
Deleting a parent may make children eligible for a later parent-before-child
deletion. An unreferenced name can be reused without rebinding a live parent.

Each inserted/deleted body decodes at most two children and updates those counts.
Proofs and the parent-domain witness erase. The runtime still pays for hashing,
map updates, wrappers, integer operations, source retention and transport; this
is not a bit-machine, allocation or RSS theorem. The generic relation-store loops
and Python active-reference policy remain outside this new wrapper's state proof.
Exact requested-patch semantics, complete serialized replay, acceptance
completeness, general factor caches and full resource costs remain open. No
unrestricted-SAT coverage or speedup claim follows.

All **166 tests pass**, including 27 source-update tests. Lean audits **2,944
declarations / 1,416 theorem declarations** without admits or added axioms.
The new regression compares native eviction against a separate full recount of
a 44-node graph with 16 roots, shared descendants, randomized deletions and
duplicate definitions, then rebuilds and reclaims all names. Existing tests
cover rollback, reuse, tight caps, historical branches and restart.


### Executed source-patch certificate (2026-11-08)

[`SourcePatch.lean`](OracleMachines/SourcePatch.lean) proves the requested bucket
transition for the checker now used by `SourceUpdates.patchQuery`. `Patched`
records equal start/height, exact replacement arrays at every requested edge,
and equality of all unedited buckets. Its leaf and join lemmas preserve original
clause order and repeated/empty entries, independently of relation equivalence.

`LiveNode` connects actual native map lookups to the indexed source model.
`readParts` recovers the current decoded child names and models using the global
live-link invariant. Its checked-join equality erases; it does not recompute a
summary. `checkNodes` returns a visit count with the transition proof. Empty edit
lists require identical names, leaves compare original arrays, and branches
combine the two filtered requests. `check` connects this proof to live root names.

`checkRequest` records the actual JSON base/root/edits getters, batch-size bound,
entry-by-entry decoding and logical-edge bounds. The duplicate guard remains
executed; soundness does not assume uniqueness. The source service calls this
checker before querying the same store/request. The new comparison uses decoded
clause arrays; malformed clauses fail decoding.

Bucket specifications and proofs erase. The implementation still performs map
lookups, child-name decoding, list filtering, array comparison and temporary
wrapper allocation along the visited paths. It neither flattens original clauses
nor rebuilds relation summaries. The visit count is not a complete cost theorem.
A changed unedited identity is rejected even if its source is equivalent.

Full initial-binding/root-coverage/verdict composition, flattened-CNF transition
correspondence, Python retention, complete replay/SQLite refinement, generic
relation/factor stores, acceptance completeness and full resource costs remain
open. This establishes a restricted native transition, not unrestricted coverage.

All **169 tests pass**, including **30 source-update tests**. Lean audits **3,043
declarations / 1,461 theorem declarations** with no admits or added axioms. New
checks include split-path edits with padding, exact arrays under equal relations,
request order, unedited aliases, invalid roots/partitions, malformed and duplicate
entries, and the decoder's full 4,096-entry limit plus over-cap rejection.


### Complete successor formula and returned decision (2026-11-08)

[`SourceFormula.lean`](OracleMachines/SourceFormula.lean) proves that flattening
an indexed source's complete interval gives exactly its original clause list.
Bucket presence is equivalent to interval membership, and padding has an empty
array. An accepted `Patched` certificate yields equality with the predecessor's
bucket function after the requested replacements, then equality with its entire
flattened successor CNF. `patched_decide` and `patched_unsat` give both Boolean
outcomes for that formula. All flattening is specification work.

[`SourceVerdict.lean`](OracleMachines/SourceVerdict.lean) certifies the executed
root-origin, coverage and minimal-height checks and the actual returned answer
getter. It proves every logical edge is represented. `compose_patch` connects
the actual request fields, live root identities, both roots' coverage, exact
successor formula and returned SAT/UNSAT decision. The nested `verdict` getter
is certified too. `SourceUpdates.query_success` and `patchQuery_success` transfer
the certificates to the exposed JSON-returning functions. Warm calls do not
flatten clauses or recompute relation summaries; proofs erase.

The decision-only response getter proof is definitional. Witness-mode calls use
the existing decoded-answer equality check. Serialized witness contents remain
outside this new theorem, as do byte transport, complete initial raw-CNF binding,
history composition, Python retention and replay/SQLite refinement. Source
lookups, root checks, parsing, array comparisons, filters and temporary wrappers
remain runtime costs; no timing or unrestricted-SAT claim follows.

All **171 tests pass**, including **32 source-update tests**. Lean audits **3,107
declarations / 1,506 theorem declarations**, with no admits or added axioms.
New tests reject incomplete, shifted and oversized roots in query and patch modes,
then compare actual nested/direct verdicts against exhaustive truth tables for
54 transitions across 1, 3 and 5 logical edges, including padding, historical
branches, empty clauses, deletion and repeated clauses. Positive witnesses are
checked independently. Existing unknown-root diagnostics remain unchanged.


### Initial raw-CNF binding and returned verdict (2026-11-08)

[`SourceInitial.lean`](OracleMachines/SourceInitial.lean) closes the initial
source-provenance gap. `compileSource_fields` extracts the actual request getter
equations from success of the existing compiler. `readCompilation` carries them
without duplicate compilation or reparsing.

`checkBinding` follows actual live children using the proved named-child invariant.
Each original leaf array must equal its compiled original bucket, including
literal order and repeated/empty clauses; padding must have an empty array.
`matches_complete` connects all compared buckets to the whole live clause list.
`matched_partition` uses the grouping theorem to prove a permutation of the raw
input clauses, with multiplicities. Global input order need not equal tree order.
`partition_eval` then proves equal evaluation under every original valuation.

`InitialResponse` combines actual width/layers/clauses/root getters, live identity,
coverage, exact original buckets, the clause permutation and returned SAT/UNSAT
semantics. The nested `verdict` and `binding_visits` getters hold definitionally.
`SourceUpdates.bindSource_success` transfers the certificate to every successful
native `source_bind` call. The existing relation-binding scan and decision
comparison remain executed; the already checked verdict is returned unchanged.

The scan proves `visits + 1 = 2^(height + 1)` and `height < fuel`; the API supplies
fuel 17. This covers logical node visits, including padding, at permitted heights
through 16. It does not cover parsing, map operations, array comparisons, allocation,
the separate relation scan or witness work. Full initial binding remains distinct
from warm paths. Flattening and proof composition erase.

All **174 tests pass**, including **35 source-update tests**. Lean audits **3,154
declarations / 1,539 theorem declarations** without admits or added axioms. New
checks cover grouping permutations, multiplicity/literal-order forgeries with equal
answers, repeated empty clauses, both response modes, complete padded scan counts,
malformed input and root failures with continued live-root usability.

Operation-history composition is next. Serialized witnesses, byte transport,
Python retention, persistent replay/SQLite refinement, generic stores, acceptance
completeness and total costs remain separate. These are successful-call guarantees
for the supplied adjacent-block family, with no new timing or unrestricted claim.

## Affine growth

Four modules certify a separate growing parity-constraint interface:

- `Affine.lean`: `eliminate_exact`, `project_exact`, `basis_exact`, `basis_size`,
  `project_left_exact` and `extend_exact` operate on `Vector (ZMod 2) n` rows.
  They prove full valuation equivalence and existential projection, including
  inconsistent systems, without assignment tables.
- `AffineGrowth.lean`: `State` stores the original `History`, an exact boundary
  summary and its `b+1` row bound. Appends add a fresh width-`b` block; equations
  mention only the old and fresh boundaries. `answer_exact`, `answer_false`,
  `summary_cells`, `replay_exact` and `history_source_bound` distinguish exact
  decisions, bounded current summary and growing source history.
- `AffineCosts.lean`: `basisRun` and `projectRun` execute coefficient elimination
  with reference charges. Their value theorems connect them to the semantic
  operations. `extendRun_bound` bounds actual append/decision charges by
  `appendBudget b c`; `replayRun_bound` composes them across original histories.
  Full-list pivot scans, produced coefficient/rhs cells and constant checks are
  upper charges. They are not primitive instructions, allocation or byte counts.
- `AffineProtocol.lean`: the native append executes `State.appendRun` and
  `decideRun`. `report_semantics` proves actual returned Boolean semantics for a
  typed node; `report_charge_bound` connects its returned charge to the bound.
  Immutable native identities and malformed JSON are tested. Raw decoding,
  named-store operation histories, Python and SQLite refinement are not proved
  by these typed-node theorems.

For `b>=1` and `c` new equations, the charge is `O(b^3+b^2*c)`, independent of
history length when the parent is resident. The current summary has at most
`(b+1)^2` logical cells. Keeping all summaries and original batches grows with
history; replay repeats the cumulative charge. There is no full-history witness
output, automatic general-CNF conversion or arbitrary older-block update.
The general source-CNF operation-history proof remains a different obligation.

The current complete build audits **3,485 declarations / 1,708 theorem
declarations**, without admits or added axioms. **184 tests pass**, including
10 affine-growth tests. The mathematical histories have no fixed cap; the native
interface currently limits width to 128, equations per batch to 4,096 and resident
versions to 4,096. Exceeding a cap is an error, never an UNSAT result.

## Native source histories and erased affine provenance

`SourceHistory.lean` centralizes the source dispatcher actually executed by the
JSON-lines worker. `handle_valid` proves exact dispatch and rollback on errors.
`execute_valid` composes these contracts over arbitrary finite interleavings of
initialization, compilation, definitions, deletion, initial binding, queries and
patches. `trace_meaning` retains the entire `InitialResponse`/`PatchResponse`
contract; `trace_query_semantics` connects query verdicts to the complete original
CNF in the actual predecessor store. `earlier_event_retained` proves that adding
requests preserves earlier observations and their certificates. Administrative
functions return the existing invariant-carrying store types. No accepted-operation
assumption is silently applied to failures.

This closes native eventwise protocol composition. The worker uses `handle`,
not the mathematical `execute` trace list, so it does not store past snapshots for
proofs. A name reused after eviction or layout reset can have a different meaning;
its event snapshot determines its interpretation. Cross-process content-addressed
lineage, raw byte transport, serialized witnesses, Python and SQLite remain outside
this theorem. It does not prove a journal of database operations.

`AffineResident.lean` replaces the literal-history native `State` with `Resident`.
Its exact history uses Mathlib `Erased`, retaining the original semantic witness
in proofs while the compiled resident value contains only the coefficient summary.
`Resident.appendRun_history`, `answer_exact`, `answer_false`, `appendRun_bound`
and `summary_cells` preserve the earlier algebra and reference charges. Generated
C inspection confirms the single runtime field and absence of ancestor-history
construction. The ordinary reference `State` remains available unchanged.
`AffineProtocol.dropNames_preserves` proves exact lookup preservation for names
not removed. An already computed child needs no live ancestor name.

The current complete build audits **3,625 declarations / 1,766 theorem
declarations**, without admits or added axioms. **190 tests pass**, including 15
affine tests and 36 source-update tests. A 4,101-append history and its restart
fit a two-version native policy; all original equations remain durable. The native
4,096-version cap bounds simultaneous residency, not history length. This is not
a physical-memory or Python-policy refinement theorem.

## Affine decoded inputs and chronological origin

`AffineProtocol` now supplies `DecodedRow`, `DecodedRows`, `Created`,
`DefinitionResponse`, `QueryResponse` and `DropResponse`. Successful row parsing
preserves exact Boolean fields, dimensions, order and multiplicity. Fresh appends
use the actual predecessor-store parent. Existing-definition retries preserve
the prior node and check typed source agreement in addition to JSON equality;
the proof does not assume a theorem about the partial JSON equality routine.

`AffineHistory.handle` is executed by the worker. `Origin` tracks chronological
original inputs, `empty_execute_sourced` proves every resident node has such an
origin after any finite trace from the empty store, and
`executed_query_semantics` connects the actual query verdict to that full history.
Errors are atomic. A retained child survives parent deletion/reuse; a fresh child
binds the current parent. These trace proofs introduce no runtime history list.

The current audit covers **3,794 declarations / 1,836 theorem declarations**,
without admits or added axioms; **192 tests** pass. Byte transport, Python/SQLite,
serialized witnesses and total resource costs remain separate obligations.

## Exact affine transition reuse

`AffineKernel.lean` separates a certified algebraic `Kernel previous equations`
from the source history to which it is applied. It certifies the exact output
summary, decision and uncached coefficient charge. `Kernel.attach` constructs the
new erased original history from the current parent; `Kernel.attach_history`
and `Kernel.bound` preserve provenance and the earlier polynomial ledger.

`KernelCache.obtain` hashes into a configured slot, then checks the width and
both complete typed input lists with decidable equality. Dependent proof
transport supplies a result only for those exact inputs. Misses compute and
replace the selected entry. Zero slots bypass cache work. `kernelInputCells_bound`
bounds hashed coefficient payload by `(b+1)^2+c*(2*b+1)`. This is not a theorem
about map time, allocation, byte memory or a complete instruction count.

The executed affine protocol now carries separate node and kernel maps.
Configuration preserves existing nodes, reset preserves the configured slot
count, and both clear the kernel map. `AffineHistory` covers configuration too;
`executed_query_semantics` still proves verdicts against chronological original
inputs. The generated C hit branch returns the existing kernel without calling
`extendRun` or `decideRun`; history attachment retains only its summary at runtime.
Kernel slots are distinct from the resident-version cap. Entries carry no
source ancestors; source batches remain durable in the Python archive.

This checkpoint passes **197 tests**, including 22 affine tests, and audits
**3,938 declarations / 1,875 theorem declarations** without admits or added axioms.
The cache's executable slot policy is checked with forced collisions and bounded
residency; no new whole-process memory or Python persistence theorem is claimed.

## Certified duplicate-free affine calculations

`AffineNormalize.lean` uses a hash set with lawful structural row equality.
`uniqueRowsAux_mem`, `uniqueRowsAux_length`, `uniqueRowsAux_nodup` and
`uniqueRows_exact` prove that the executable procedure removes duplicate
occurrences without losing or adding any boundary solution. `PreparedRows`
retains this semantic equivalence and the original-row count bound.

`Kernel` now carries semantic exactness and compactness. `compileKernel_summary`
and `compileKernel_charge` still identify the unnormalized constructor's exact
executed values. `Kernel.restoreOriginal` transports a normalized kernel back to
the original batch's semantics and budget; `restoreOriginal_charge` confirms that
this introduces no second coefficient calculation. `Kernel.attach_history`
therefore still appends the actual original rows, with their order and multiplicity.

The preparation cache checks complete typed original batches and reuses their
certified normalized lists independently of parent summaries. The transition
cache checks the parent summary and reduced batch. Configuration preserves source
nodes, clears both caches and selects normalization; the chronological source
proof continues through the executed handler. Preparation and normalization
payload counters are partial ledgers; hash-set collision/resize costs and actual
allocation are not yet given a complete machine bound. Native request JSON remains
resident per version. The Python archive codec and admission policy remain tested
boundaries, not new Lean persistence theorems.

This checkpoint passes **207 tests** (26 affine growth, six affine archive, 36
source updates). The axiom audit checks **4,043 declarations / 1,911 theorem
declarations** without admits or added axioms. The matched four-mode experiment
and generated-code inspection are retained in
[the batch reuse record](../experiments/results/affine-batch-reuse/README.md).


## Refutation and fixed-model clause histories

`Residuals.lean` now proves `unsatisfiable_conj_extension` and
`unsatisfiable_history`: a refuted base remains refuted after arbitrary
conjunctive additions. `fixed_model_history` and
`satisfiable_fixed_model_history` show that a single assignment satisfying the
base and every addition satisfies the entire folded conjunction. This preserves
one witness, not the complete model set. Failed model checks prove no negative
answer. These semantic results support the separate Python history experiment;
they do not verify its signed parser, database, implementation or resource costs.

The current audit passes **4,071 declarations / 1,933 theorem declarations**.
The matched comparison and limitations are retained in the
[decision-history record](../experiments/results/cnf-decision-history/README.md).


## Checked pure-literal model repair

`Residuals.lean` defines signed clauses using variable/polarity pairs.
`signed_occurs_append` gives the exact support update law.
`pure_repair_preserves` proves that setting a literal true preserves every old
clause when its opposite is absent from the full parent source;
`pure_repair_extension` includes the new clause containing that literal. This
covers fresh variables and existing pure variables, not arbitrary repairs when
both signs occur. The Python integer encoding, immutable trie and archive
protocol remain outside these semantic proofs.

The current audit passes **4,079 declarations / 1,939 theorem declarations**.
All 242 Python tests pass. The resource measurements and preserved limitations
are in the [repair-history study](../experiments/results/cnf-repair-history/README.md).

## Checked affected-clause model repair

`affected_repair_preserves` and `affected_repair_extension` in `Residuals.lean`
weaken purity: an old clause containing the opposite literal may contain the
new literal or an unchanged true literal that protects it. Changing the variable
then preserves all old clauses and satisfies a new clause containing the repair
literal. The rule handles nonpure variables and tautologies. It does not find
repairs or bound the size of the affected set.

The audit passes **4,081 declarations / 1,941 theorem declarations**. All 249
Python tests pass. The new Python experiment uses persistent occurrence and
true-literal-count indexes, reconstructed during cold checking. The count maps,
integer encoding, archive protocol and resource costs remain outside these Lean
semantic proofs. See the
[affected-repair comparison](../experiments/results/cnf-affected-history/README.md)
for gains, index overhead and cases still requiring fallback.

## Checked simultaneous model repair

`joint_repair_preserves` and `joint_repair_extension` in `Residuals.lean` allow
an arbitrary set of variables to change together. The updated assignment must
agree with the parent outside that set, satisfy every old clause touching it,
and satisfy the added clause. The proof retains an old satisfying literal for
unaffected clauses. Intermediate scalar assignments need not be models.

The audit now passes **4,083 declarations / 1,943 theorem declarations**, and all
255 Python tests pass. The separate Python implementation aggregates exact
count differences over affected postings before checking positivity, proposing
changes from complementary binary pairs in the base. The generic protection
theorems do not verify that discovery, the count formula's implementation,
persistent indexes, parsing, SQL or runtime bounds. The
[joint-repair comparison](../experiments/results/cnf-equivalence-history/README.md)
retains signed/coupled controls, old versions, failed discovery and budget limits.
