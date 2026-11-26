# External research watch

The daily `review-external-sat-research` automation checks
[pequalnp.com](https://pequalnp.com/) at 09:00 Europe/Berlin. The hourly
OracleMachines investigation remains guided by our own gap analysis. External
results are leads, not imported axioms or a replacement research agenda.

## 26 November 2026: finite circuit result and a relevant negative benchmark

Checked the live browser versions of [papers](https://pequalnp.com/papers),
[programs](https://pequalnp.com/programs) and the algorithm-search board. The paper
listing still shows Note 1. Static web extraction again returned loading shells;
the live browser was necessary to see the populated records.

The new highlighted [L-meta-18980](https://pequalnp.com/lemma#L-meta-18980), marked
checked on 26 November at 06:57 UTC, says the Hamiltonian-cycle function on the
six edge bits of a labelled four-vertex graph cannot be computed using at most
six AND/OR (fan-in two) and NOT gates, with inputs free and every gate counted.
Its [external PR](https://github.com/open-goat/pequalnp-proofs/pull/23793) is merged.
This is a finite restricted circuit claim. Locally, we checked the displayed
Boolean function against explicit Hamiltonian-cycle enumeration on all 64 graphs;
that verifies the function's interpretation, **not the circuit lower bound**.
The table and reviewed links are preserved in
`experiments/results/cnf-b10-probe-cursor/pequalnp-review.json`. We did not build
the external Lean code or independently audit its circuit definitions.

More relevant to our current gaps is the newly inspected, but **22 November**,
[L-alg-002 record](https://pequalnp.com/lemma#L-alg-002). It rejects a universal
fixed-width resolution-saturation algorithm for 3-SAT, citing Tseitin formulas
on degree-three split grids and reporting a Lean-checked width counterexample.
The supplied Lean artifact was inaccessible through the web tool; its full proof
and transitive definitions have not been independently checked here. Treat the
record as a concrete lead, not an imported axiom.

A useful follow-up is an adversarial evaluation family: encoded parity constraints
whose global inconsistency survives small local views. Measure affine recognition,
separator summaries and proof/reuse costs against bounded local saturation. This
is our proposed experiment, not a new result from the site. Resolution-width
limitations concern that proof system and do not establish limitations of all
SAT representations or of our affine route. Our checked B8/B9/B10 composition
work continues; no external claim changes proof authority or production policy.

## 25 November 2026: repeated neighborhoods and equivalent restrictions

Reviewed the live [papers page](https://pequalnp.com/papers),
[Note 1](https://pequalnp.com/papers/note-1), and the project's
[checking description](https://pequalnp.com/how). Static page extraction misses
the dynamically loaded research; an empty loading shell is not an empty feed.
Note 1 concerns circuit size of graph edge functions, not a general SAT solver.

The most relevant lead is its four-cycle example in section 6. For edges
01, 12, 23, 30, the disjunction of edge conjunctions factors as
`(x0 OR x2) AND (x1 OR x3)`. Opposite vertices have identical neighborhoods;
three assignments to `(x0,x2)` leave the same residual function. This suggests
looking for repeated neighborhoods or equal restrictions before expanding
separate branches. The elementary identity was independently checked over all
16 assignments locally. This checks that identity, not the paper's general
lower bounds or its Lean development.

A concrete future test is to identify small complete bipartite interaction
blocks or pairs with equal residuals, then compare shared representation against
separate expansions. Recognition, checking equivalence, maintaining boundary
meaning, and the effect on unit propagation must all be charged. Syntactic
equality gives a cheap sufficient test; arbitrary semantic equality is not a
free recognition step. Factoring can make representation smaller without making
an arbitrary SAT instance easy. Our existing checked residual/proof reuse
remains the starting point; the current B4 frontier experiment continues.

Treat the site's verification labels carefully. The listing displayed eight
checked claims and a human-review attribution, while the detailed paper dated
24 November described ten checked statements and explicitly said the prose had
not been read by a human mathematician. The page and embedded PDF also named
different GitHub owners. These inconsistencies do not refute the mathematics,
but a future adoption must pin the actual definitions, theorem, repository
revision, hypotheses and checker output. We did not run the external Lean code.
The paper itself separates formal statements from prose consequences and limits
several bounds to forests or graphs with long cycles and separated hubs.

Next daily check: look for changed papers/programs and concrete counterexamples;
follow the linked formal source only for a lead relevant to a current measured
gap. Do not repeat this unchanged overview or infer a P-versus-NP result.
