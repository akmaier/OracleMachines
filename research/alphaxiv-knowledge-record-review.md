# alphaXiv connection and review of the K-record paper

Reviewed 26 November 2026 at the user's request. Source: Darren Hall,
[P(K>p) = NP: Knowledge Makes Solving as Easy as Checking](https://www.alphaxiv.org/abs/2611.knowledge-solving-complexity-checking),
version 3 displayed by alphaXiv. The nine-page PDF is dated 25 November. Its DOI
is [10.5281/zenodo.24555932](https://doi.org/10.5281/zenodo.24555932).
The original PDF was downloaded and read; the formal sketch on page 8 was also
visually inspected. The platform's generated overview and discussion were leads,
not proof authority. No external theorem was adopted and no comment was posted.

## Connection to our work

The useful common idea is paying once for a result, retaining it and testing
reuse before searching again. Positive witnesses can also be tried after a small
edit. Our cost identity separates acquisition, representation size, lookup,
recognition, verification, updates and fallback. The experiment in the source
concerns exact repeats and one-clause neighbors of small satisfiable formulas;
it does not establish efficient structural coverage of arbitrary CNFs.

The natural baseline for the neighbor experiment is a saved satisfying assignment
without the additional record metadata. Its absence prevents attributing a gain
to the record's method fields. A random non-tautological three-literal clause is
satisfied by any fixed assignment with probability 7/8 when its three signs are
independent and uniform. Replacing one clause leaves the other old clauses
satisfied, so a high survival rate is expected even without learned structure.
This calculation assumes that sampling model; the paper does not provide enough
code to establish its exact generator or possible selection bias.

## Specific gaps and errors

1. **Complexity-class claim.** Polynomial online access to already acquired
   information does not bound its construction or encoded size. Defining a domain
   after observing successful application also supplies neither an advance
   recognizer nor a uniform running-time guarantee. An individual fixed instance
   is not the asymptotic object to which P and NP apply.
2. **UNSAT is not a knowledge deficit.** No amount of stored knowledge creates a
   satisfying assignment for an unsatisfiable formula. A negative result can be
   accompanied by a refutation, which can be checked without rerunning the search.
   Its length and checking cost must be charged; polynomial-size refutations for
   every UNSAT formula are not established. Our source-only certificate archives
   provide concrete examples of the distinction.
3. **The implemented solver in the sketch never invokes the verifier.** A record
   lookup unconditionally returns a positive answer when an entry exists. The
   hypotheses require only verifier soundness and an entry's existence; they
   never require that its witness passes verification. Take an identically false
   language and identically rejecting verifier, and supply any record entry:
   the soundness hypothesis holds vacuously, but the displayed solver returns a
   positive answer. This is a counterexample to interpreting that function as a
   certified solver under the listed hypotheses.
4. **The record type is not a finite-map specification.** An unrestricted function
   from natural numbers to optional entries imposes no finite support, encoded
   size, computability or access-cost bound. A concrete finite representation and
   access model are needed for the accompanying finite-storage interpretation.
5. **The cost statement is not an asymptotic bound.** Its existential multiplier
   is chosen after the input and record. If checker cost is positive, choosing
   a sufficiently large input-dependent multiplier makes the inequality trivial.
   Without positivity, the unconstrained costs can instead give solver cost one
   and checker cost zero, making the inequality impossible. Runtime is attached
   to returned values rather than operational computations; a Boolean output
   alone cannot distinguish arbitrarily different checking work. Witness-length,
   polynomial-time and verifier-completeness premises are absent too.
6. **The formal and experimental claims remain unverified.** The Lean-style
   theorem contains an admitted proof. The paper also reports that the experiment
   script had not reached its author and the results had not been independently
   reproduced. We have not compiled that sketch or reproduced its experiments.

These observations do not refute memoization or practical warm starts. They
identify the additional obligations a complexity claim would require. Our own
restricted-family theorems, empirical gains and open arbitrary-SAT obligations
must remain equally distinct.

## Connection and publication

The [official alphaXiv MCP service](https://www.alphaxiv.org/docs/mcp) is accessible
at `https://api.alphaxiv.org/mcp/v1`. A native plugin was not returned by the
available plugin directory, so we connected through its documented MCP protocol
using the operator-supplied local credential. The client is
`scripts/alphaxiv_mcp.py`; `alphaxiv.org` is ignored by git and its content must
never appear in commands, logs, publications or commits.

The user authorized publication, daily updates, and the byline Andreas Maier plus
GPT Astra, explicitly identified as an OpenAI AI research collaborator. The AI
Track submission discloses AI execution and drafting and mixed human/AI direction
and analysis. Exact historical model versions are not asserted. See
`publications/alphaxiv/publication.json` for the published URL, approved metadata,
verified research checkpoint and daily update automation.

The daily updater should publish revisions of the same paper when verified
research changes, never create a duplicate paper each day or publish unfinished
experiments. Publication screening is not mathematical peer review. The original
hourly research direction remains unchanged.
