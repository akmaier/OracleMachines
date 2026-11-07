# Oracle Machines

A perspective on **resource accounting for learned reasoning**: how preprocessing,
stored knowledge, neural representations, and exact solvers redistribute computation
between acquiring an answer and using it later.

The project connects established ideas from complexity theory, knowledge
compilation, memoization, and amortized inference to the interaction between fast
and deliberative computation. Its contribution is an explanatory synthesis; the
finite-domain constructions do not establish a collapse of unrestricted complexity
classes.

## Paper

The current draft is **Bounded-Domain SAT, Compiled Knowledge, and Amortized
Reasoning: A perspective on resource accounting for learned reasoning**.

- [LaTeX source](paper/bounded_domain_sat_and_amortized_reasoning.tex)
- Status: working draft
- Format: self-contained LaTeX with embedded bibliography and TikZ figures

The paper distinguishes the costs of construction, storage, inference, training,
verification, and fallback solving. It examines exact finite-domain SAT tables,
finite restrictions of language classes, oracle simulation, explicit ReLU
representations, nonuniform advice, caching, and certified fallback. System 1 and
System 2 serve as a computational analogy, not as complexity classes.

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
README.md
LICENSE
```

## Literature review

The [annotated literature review](research/literature-review-2026-11-07.md) compares
the draft with work on neural advice, speedup learning, compilation, and failed
complexity proofs, including Deolalikar and Wen. It includes
[supplementary BibTeX](research/related-work.bib) and saved OpenAlex/SemOpenAlex
query evidence.

## License

This repository includes an [MIT license](LICENSE).
