# External research watch

The daily `review-external-sat-research` automation checks
[pequalnp.com](https://pequalnp.com/) at 09:00 Europe/Berlin. The hourly
OracleMachines investigation remains guided by our own gap analysis. External
results are leads, not imported axioms or a replacement research agenda.

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
