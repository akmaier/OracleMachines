# Signed relations exposed by full-CNF probing

Date: 27 November 2026. Parent research: `7e4b47cb`; git parent: `1b2e7f63`.
Evidence: `experiments/results/cnf-probe-relations/`.

## Result and decision

One checked signed-equivalence substitution after probe consequences closes the
last exposed SAT root at bucket width eight. Its relevant leaf shrinks from 16
variables to 14; the other leaf remains unresolved. A lifted witness certifies
the complete root. Previous-panel coverage rises **47/48 to 48/48**. All 24 new
unique constructions and four repeats are already covered by both policies:
the new pipeline certifies **76/76** queries, versus **75/76** without the extra
substitution. This is one additional structural acquisition, not new answers
unavailable to the fallback or efficient coverage of arbitrary SAT.

Complete cost is **6.70% lower than a width-nine control**, with all four paired
comparisons favorable. Against unchanged width-eight probes, however, it is
**1.69% higher on average**, with mixed paired signs. It costs **1.66 times fresh
solving**. Keep the cost regression and leave production defaults unchanged.
Use the relation path as a coverage research baseline, retaining the probe-only
arm as its cheaper mean baseline on this panel.

## Pattern, recognition and exact recomposition

Failed assumptions can expose binary relations absent from the earlier binary
core. After the unchanged indexed probe preparation, inspect each nonconstant
incoming residual once using the existing source-checked binary-conflict and
signed-equivalence recognizers. The equivalence rule stores two implication
trees connecting a representative to every member and back. Every edge cites
an actual binary clause of this residual. This establishes a signed substitution
in all its models. Clean tautologies/duplicate literals, apply checked units,
normalize the quotient and retain inverse maps.

The additional nonconstant transformation must strictly reduce active variables.
There is at most one such preparation per incoming edge; it is not an iterated
fixed point. The unchanged prior engine still has its separate probe, binary,
unit and bucket allowances. Unsuccessful relation recognition is charged.
For a binary graph, graph construction and SCC discovery are linear in graph
size in the usual unit-cost model. Scanning the CNF, quotient construction,
sorting/normalization, repeated unit restriction, checking and transport are
additional. Unit/index quotas do not bound all wall time or memory.

Replay reconstructs the preceding residual and validates the cited relation
without rerunning recognition or probing. A quotient model lifts through its
signed map and post-substitution units before the older probe and binary maps.
Each incoming model is checked against its own source. An UNSAT quotient is
usable because substitution preserves satisfiability; split refutation still
needs both children. Unknown branches remain unknown, even when their sibling
provides a SAT witness for the parent.

Only exact normalized residual/depth pairs under the same policy share bucket
nodes. Each incoming edge retains its own history; there is no arbitrary semantic
canonicalization or cross-source reuse of omitted background. The proof format
is experimental and new; native, equivalence, affine and Lean formats are
unchanged. The disabled-tail control translates losslessly to the preceding
indexed-probe certificate. Width nine changes only the bucket limit.

## Frozen comparisons and full costs

The comparison retains the full preceding 48-query panel and adds 28 queries
frozen with seed `2711271112`: growing random three-CNFs, nonfolding five-variable
failure motifs, relations guarded by a subsequently forced literal, deleted
conflict/direction controls, parity prisms and four repeats. Names, signs and
clause/literal order are scrambled. Labels are audit-only. No new normalized
source duplicates the parent panel, but parity families recur structurally;
this is not a representative external benchmark. All 28 additions are covered
by the baseline, so they establish no extra coverage gain for the new rule.

Four cyclic orders run each arm in a fresh process. The panel has 48 SAT and
28 UNSAT queries. The same fallback is available in every arm.

| Measure | Fresh | Probes, width 8 | Post-probe relations | Probes, width 9 |
|---|---:|---:|---:|---:|
| Complete seconds | 1.29774 | 2.11690 | 2.15258 | 2.30724 |
| Discovery seconds | 0 | 0.66626 | 0.70425 | 0.73377 |
| Solve/check seconds | 0.58463 | 0.29929 | 0.29372 | 0.32755 |
| Warm seconds | 0.04204 | 0.33159 | 0.33433 | 0.35394 |
| Cold seconds | 0.38703 | 0.68767 | 0.68073 | 0.75289 |
| Evidence-write seconds | 0 | 0.03963 | 0.04463 | 0.03969 |
| Archive-persistence seconds | 0.27274 | 0.08363 | 0.08382 | 0.09067 |
| Raw certificate bytes | 0 | 3,756,582 | 3,746,502 | 3,686,213 |
| Native record bytes | 1,570,760 | 18,445 | 0 | 0 |
| Combined compressed SQLite/JSON bytes | 308,459 | 96,035 | 91,554 | 92,120 |
| Peak process RSS bytes | 86,179,840 | 65,880,064 | 60,817,408 | 60,850,176 |

Complete time includes input, recognition, internal and explicit checking,
evidence writes, warm use, cold replay and compression. Process startup, protocol
construction, oracle labels, historical acquisition, post-hoc diagnostics and
lineage audit are additional. Diagnostic bytes are separately 0/217,031/232,434/
209,115. RSS is a measured process peak, not a worst-case memory bound.
Cold checking uses both native readers for fallback archives and two JSON passes
through one implementation. It does not claim two independent JSON checkers.

Relations versus probes have paired differences +4.92%, -4.88%, +8.62%, -1.02%.
Relations versus width nine save 6.08%, 4.70%, 9.09%, 6.77%. Extra recognition runs
111 times and retains sixteen equivalence transforms, removing 27 variable
occurrences and storing 2,449 compact tail bytes across unique programs.
Bucket steps fall 587 to 567, but nodes remain 161 and splits remain 54.
Fifteen shared targets and ten distinct-raw merges remain; all those merges are
constant. There is no demonstrated new nonconstant quotient sharing. Two unknown
leaves remain below SAT parents even though every root has a certified answer.
Most combined compressed savings come from removing fallback records: compressed
JSON alone falls only 90,700 to 90,559 bytes.

## Fresh frontier and next bottleneck

A separate **post-hoc** census freezes six larger random three-CNFs at 32, 40
and 48 variables, density 4.26, seed `2711271114`. It does not enter the 76-query
comparison or justify its speedups. Only **2/6** have structural verdicts. Four
roots remain unresolved (`h32-1`, `h40-1`, `h48-0`, `h48-1`), with oracle labels
three SAT and one UNSAT. Eight unknown leaves occur overall at widths 9–11;
one is beneath a SAT parent. Their complete sources, proofs, diagnostics and
separate oracle results are retained in `frontier.json` and its bound files.

A further source-checked census probes every sign in each of these eight leaves.
Four contain thirteen failed assumptions; all four came from incoming preparation
that stopped at the 128-probe allowance, with no subsequent relation tail.
None contains an additional equivalence block. These diagnostic consequences
are not new whole-root authority. They distinguish a bounded acquisition gap
from a claim that the remaining formulas lack useful consequences.

**Next coverage target:** selective continuation of capped probe work, with an
explicit global allowance and reused indexes only while the CNF is unchanged.
Compare against simply increasing the allowance, and retain the four leaves
without failed assumptions as controls. Avoid repeating completed probes where
their exact source is unchanged; restrictions require valid rebinding. More
unconditional SCC passes have weak evidence here. The larger-input census remains
a small synthetic sample; an external workload is still required.

**Next cost target:** discovery (0.70425 s, including internal checking) and cold
replay (0.68073 s) dominate. Retain the earlier profile-supported plan to reuse
validated normalization and intermediate residuals within one check, with exact
source/context bindings and charged lookup/invalidation. The extra relation
stage has not established an overall speedup over probes. Complete coverage of
one finite panel does not close general discovery, preprocessing, worst-case
expansion or compact representation obligations.

## Verification and preservation

All **2,323 full and 47 focused tests pass**. Eleven new tests include exhaustive
two-variable formulas, 100 seeded wider cases, nonfolding probes exposing an alias,
signed/sparse witness transport, deleted relation directions, malformed evidence,
strict progress, discovery-disabled cold checking, exact baseline translation,
and a whole-root regression for the last exposed source. Every matched certificate
is regenerated and replayed, every SAT witness checked, and fallback archives
audited. Prior 232 manifests, 44,871 artifact entries, 1,273 scientific sources
and 74 manuscript proof blocks remain unchanged. Five new scientific files and
one restricted composition proposition are added. Existing SQLite ResourceWarnings
are retained. Resume `experiments/results/cnf-probe-relations/checkpoint.json`.
