# Oracle Machines

A perspective on **resource accounting for learned reasoning**: how preprocessing,
stored knowledge, neural representations, and exact solvers redistribute computation
between acquiring an answer and using it later.

**Terminology:** SAT with no fixed size cap remains the satisfiability problem.
UNSAT denotes unsatisfiable valid formulas and is coNP-complete. An invalid
encoding is neither a satisfiable nor an unsatisfiable formula.

The central architectural conclusion is that **the efficiency rationale for
combining System 1 and System 2 survives either resolution of P versus NP**.
Either way, the relevant comparison is avoided computation versus acquisition,
retrieval, verification, and control costs. Actual savings depend on the workload
and implementation.

The exact reuse identity applies to **every decidable language**, including
problems in PSPACE, EXPTIME, and EXPSPACE. This generality concerns the cost
comparison. Cheap certification, compact storage, and efficient acquisition need
their own justification, and finite tables for an undecidable language do not
provide a uniform computable way to construct them.

The project connects established ideas from complexity theory, knowledge
compilation, memoization, and amortized inference to the interaction between fast
and deliberative computation. Its contribution is an explanatory synthesis; the
finite-domain constructions do not establish a collapse of unrestricted complexity
classes.

## Paper

The current draft is **Bounded-Domain SAT, Compiled Knowledge, and Amortized
Reasoning: A perspective on resource accounting for learned reasoning**.

- [LaTeX source](paper/bounded_domain_sat_and_amortized_reasoning.tex)
- Author: Andreas Maier
- Status: working draft
- Format: self-contained LaTeX with embedded bibliography and TikZ figures

The paper distinguishes the costs of construction, storage, inference, training,
verification, and fallback solving. It examines exact finite-domain SAT tables,
finite restrictions of language classes, oracle simulation, explicit ReLU
representations, nonuniform advice, caching, and certified fallback. System 1 and
System 2 serve as a computational analogy, not as complexity classes.

The expanded draft compares these ideas with neural-advice and speedup-learning
literature, discusses the failed Deolalikar argument and Wen's learned-oracle
claims, and proves conditional expected-savings and bounded-overhead results.
An exact reuse identity states when avoiding repeated solves repays cache costs.
These savings conditions apply whether P = NP or P != NP, and a scaling example
shows how reuse can help even when solving has polynomial cost.
The detailed argument audit makes setup costs explicit in every cache bound,
states the finite-expectation assumptions for unbounded query domains, and proves
that uniform computable construction of exact finite tables is equivalent to
decidability. It also explains why optimal metareasoning can remain hard.
The literature comparison attributes the utility criterion to Minton, discusses
self-improving algorithms for polynomial-time tasks, and relates fast/slow
arbitration to Milli et al. and SOFAI. These are established precedents for the
paper's explanatory cost bounds.
The follow-up search adds Goré and Nguyen's published global-caching solver for
an EXPTIME-complete problem and Ferrara et al.'s model-checking preprocessing
work. The finite-table construction criterion is explicitly attributed to
standard computability, and the EXPTIME obstruction to the time hierarchy.
These connections strengthen the perspective without establishing theorem novelty.
An explicit induction now constructs exact answers on successively larger finite
domains. Separate results state the uniform expansion bounds that would imply
polynomial-time decision and the workload conditions that amortize costly
expansion. The correctness induction supplies neither bound by itself and does
not prove P = NP.
The executable development now supplies an exact SAT solver, a restricted
polynomial bound for a fixed variable cap, and a certified witness-reuse policy.
The [persistent solver](solver/README.md) retains every completed result across
restarts. The [reproducible study](experiments/README.md) compares reuse with repeated
exhaustive solving;
they do not establish a competitive SAT solver or efficient exact learning on
unrestricted instances.

The central question is when the expense of acquiring reusable knowledge is repaid
by reduced future computation. Exact representability alone establishes neither
compactness nor efficient learning, and a correct hybrid need not be faster overall.

## Build

Install a LaTeX distribution with `latexmk` and the packages used by the source
(including `newtx`, TikZ, and `natbib`). From the repository root:

```sh
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error bounded_domain_sat_and_amortized_reasoning.tex
```

Alternatively, run `pdflatex` twice:

```sh
cd paper
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
pdflatex bounded_domain_sat_and_amortized_reasoning.tex
```

The PDF is generated alongside the source. To remove auxiliary build files while
keeping the PDF, run `latexmk -c` from `paper/`.

## Repository layout

```text
paper/
  bounded_domain_sat_and_amortized_reasoning.tex
formal/
  OracleMachines.lean
  OracleMachines/
  lean-toolchain
  lakefile.toml
  lake-manifest.json
  README.md
solver/
  persistent.py
  test_persistent.py
  README.md
experiments/
  run_workloads.py
  results/
research/
README.md
LICENSE
```

## Lean verification

The [Lean project](formal/README.md) checks the expansion invariant, explicit
table size, conditional polynomial cost bound, staged savings criterion, and
amortization limits. It also proves that the explicit table and exponential
expansion costs are not polynomially bounded. A theorem map identifies the exact
coverage and remaining obligations.

With Lean's version manager installed, run:

```sh
cd formal
lake exe cache get
lake build
```

The toolchain and dependencies are pinned. The default build audits all declarations in the formal library
namespace for admitted proofs and additional axioms. The formalization treats
general runtime costs as explicit numerical ledgers and connects a concrete
SAT core to an operational cost model. Its cost bound is polynomial in formula
length only for a **fixed** variable cap, with exponential dependence on that
cap. It does not formalize P versus NP or prove an unrestricted polynomial bound.

## Persistent solver

Build the executable with `cd formal && lake build oracleSolver`. Then, from
the repository root, run `python3 solver/persistent.py solve 010`. Subsequent
calls reuse the result from `solver/.cache/results.sqlite3`; new formulas can
also reuse a retained satisfying assignment after checking it. SAT and UNSAT
results accumulate without eviction. The [service documentation](solver/README.md)
covers encoding, storage, restart behavior, integrity checks, and testing.
The database is local and ignored by Git; source code and reproducible experiment
results are versioned.

## Literature review

The [annotated literature review](research/literature-review-2026-11-07.md) compares
the draft with work on neural advice, speedup learning, compilation, and failed
complexity proofs, including Deolalikar and Wen. It includes
[supplementary BibTeX](research/related-work.bib) and saved OpenAlex/SemOpenAlex
query evidence. The closest precedents and relevant historical cautions are now
integrated into the manuscript's self-contained bibliography.

The review also contains a [detailed proof audit](research/literature-review-2026-11-07.md#detailed-argument-audit-and-scope-beyond-np)
covering every formal argument, the repaired accounting omission, and the limits
of extending the result beyond NP.
The [publication-status reassessment](research/literature-review-2026-11-07.md#publication-status-of-the-generalized-observations)
maps the generalized claims to prior work and distinguishes checked publications,
an MSc thesis, and sources whose full text could not be verified.
The [induction audit](research/literature-review-2026-11-07.md#inductive-expansion-proof-and-limitations)
checks the expanding-domain proof, its cost conditions, and counterexamples to
an unconditional polynomial-time conclusion.

## License

This repository includes an [MIT license](LICENSE).
