# Balanced short-clause conditioning: more coverage, less reuse

The previous study identified expensive unresolved random 3-CNFs. A separate
[profile and pilot](../cnf-conditioning-pilot/README.md) showed that repeated
normalization, recognition and checking dominate unit propagation. The present
experiment changes conditioning order while retaining depth two and the exact
two-branch checker. It is optional; the default frequency policy is unchanged.

## Policy, semantics and prior work

For each variable v, count positive and negative occurrences p_v and n_v in
clauses of minimum current width, and total occurrences f_v. Rank by descending
lexicographic `(p_v*n_v, p_v+n_v, f_v)`, then ascending variable ID. Only the first
k candidates are explored. Each attempt still includes both restrictions, and
search stops at the first fully closed decomposition. Otherwise the old rule
selects the least unresolved literal/leaf total. All alternatives remain stored.

This is a MOMS-inspired heuristic. Short-clause occurrence and unit-propagation
heuristics are established in [Li and Anbulagan (IJCAI 1997)](https://ijcai.org/proceedings/1997/54).
The exact ranking above is our tested variant, not a claimed reproduction of
Satz. We perform no speculative propagation in the ranking. The inference is
that variables with occurrences in both polarities in short clauses may expose
useful implications in both branches; this is not an optimality theorem.

The score changes no family test or semantic composition rule. Exact source and
child bindings remain checked, and the checker recomputes the deterministic
candidate order. A versioned policy field prevents reuse of an incompatible
old trace. Edits create new exact source identities; changed occurrences require
ranking again. Variable IDs break ties, so arbitrary renaming need not preserve
the selected decomposition. Counting costs O(L), sorting O(v log v), and the
count maps use O(v) words per ranking on a node with L literals and v variables.
Count products need O(log m) bits for m clauses, up to constant factors; machine
word assumptions and encoding costs remain explicit. Cold checking also ranks.
This bounds ranking work, not the number or total size of acquired residuals.

## Frozen policy and matched sources

The corpus retains all 841 previous sources and adds 108: 48 fresh random 3-CNFs
(16 each at 12, 20 and 32 variables, density 4.25), 24 fresh mixed-width CNFs
(eight each at those sizes, widths 2--4), and 36 renaming/sign-flip/unit-edit
controls of previous random sources. The rule was frozen before generating the
72 fresh sources. The 36 transfer controls are not independent holdout data.
No labels enter the policy. Every mode uses the same ordinary decision solver.

Coverage below excludes the 512 exhaustive tiny sources, all closed in every
inventory mode. A closed decomposition can describe SAT or UNSAT. Times include
analysis, checks, original solving, successful root lifting and persistence.

| Policy | Closed / 437 | Total s | Discovery s | SQLite bytes | Cold audit s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solver only | n/a | 4.63270 | 0 | 16,404,480 | 0.90616 |
| Frequency, units, k=4 | 322 | 17.20315 | 12.47667 | 79,118,336 | 6.26480 |
| Short-balanced, units, k=4 | 330 | 20.24553 | 15.57125 | 96,911,360 | 7.64375 |
| Frequency, units+pure, k=4 | 329 | 17.94629 | 13.19441 | 78,061,568 | 6.73012 |
| Frequency, units, k=8 | 332 | 42.11042 | 37.09149 | 194,686,976 | 17.89568 |

The new rule gains eight closures and loses none relative to frequency/unit-only
at cap four. Three gains are in the old 48 random 3-CNFs (10 -> 13 closures),
two are in fresh inputs, and three are transfer controls. On fresh 3-CNFs it
improves 7/48 -> 8/48, and on mixed widths 13/24 -> 14/24. No policy closes any
of the 32 fresh 3-CNFs on 20 or 32 variables at this depth, even with eight
frequency candidates. This does not prove that no small backdoor exists.

Compared with the previous combined unit/pure policy, the new rule gains six
cases but loses five, including original case 631. It is not a replacement for
that policy. Eight frequency candidates also solve a different set: a larger
candidate budget is much costlier and does not dominate the new rule on every
input. The selected unresolved-literal sum falls from 33,281 to 26,784 with the
new rule, yet elapsed time and storage increase. This proxy is not total work.

The exact eight gains are retained in `mechanisms.json`, along with all 107
remaining non-tiny misses. On the seven gains whose root is an OR node, the
winning root variable was already attempted by frequency ordering. The gain
therefore comes from subsequent conditioned choices, where binary clauses and
unit consequences matter. Selected leaf certificates mainly expose small
contradictions, constants and existing tractable families, not a new family.
Case 941 first undergoes checked unit simplification and then conditioning.

## Why cost rises, and the next opportunity

Despite fewer attempted conditioning candidates (4,300 -> 3,956), acquired nodes
increase from 9,162 to 11,224. Repeated child references fall from 3,344/11,839 to
2,469/13,026. These are graph sharing counts, not cache time estimates. Different
branches create more distinct residuals and propagation intermediates.

Logical node payload grows from 35,730,036 to 44,967,792 bytes. `simplify` nodes
alone grow from 10,312,149 to 18,717,650 bytes, accounting for about 91% of that
increase. Their count grows from 3,085 to 4,968. Full unsimplified residuals,
profiles, unit traces and simplified children are all retained. Source payload
also grows from 2,052,640 to 2,184,551 bytes because policy metadata is included
in exact identities. All modes still retain the same 4,034 solver residuals.

**Next concrete target:** represent a conditioning step followed by forced-unit
closure as one checked edge to the final residual. Retain the assumption, unit
reason references, exact parent source and variable transport, so cold replay
can reconstruct and verify the intermediate restriction. Compare against the
current explicit intermediate-node representation. The intended saving is fewer
duplicated full residuals, profiles and acquisitions, while preserving all
choices, proofs and historical source records. Recognition before propagation
and terminal-family behavior must be kept comparable. No such fusion is yet
implemented, and the avoidable fraction must be measured rather than equating
all simplification bytes with savings. A cheaper checked closure could then
support informative lookahead on the still-unresolved 20/32-variable cases.

Warm reinspection is 107.98 versus 103.65 ms for the two cap-four unit policies.
A separate six-case traced Python diagnostic gives peaks of 152,392 versus
153,174 bytes; it excludes native memory and does not measure full-corpus peak
memory. All times are single sequential samples, not significance estimates.
Initialization, corpus generation, truth tables, summary walks and gzip are
outside operation timing. Full cold audit includes all attempted alternatives,
all sources and all ordinary solver certificates. Five new and seven previous
archives replay without byte changes or fresh solver expansion.

## Validation and reproduction

All 306 Python tests pass, including exhaustive two-variable sources, all-branch
truth-table/fiber checks on unlabelled mixtures, renamings and edits, corrupted
candidate order, policy coexistence and cold replay. The existing Lean build and
audit pass (4,087 declarations / 1,946 theorems); no new Lean theorem or Python
refinement is claimed. Earlier experiment results remain unchanged.

```sh
python3 experiments/compare_cnf_conditioning.py --output /tmp/cnf-conditioning-new
python3 experiments/analyze_cnf_conditioning.py /tmp/cnf-conditioning-new
python3 -m unittest discover -s solver -p 'test_*.py' -q
```

Use a new output directory. Exact inputs, fingerprints, all counters, summaries
and compressed SQLite archives are retained. The development pilot preserves
the larger-cost cap-eight short-clause trial as well. This experiment expands
bounded discovery coverage; it proves no uniformly polynomial arbitrary-SAT
solution, compact closure or optimal conditioning policy.
