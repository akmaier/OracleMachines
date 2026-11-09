# Closure reuse with compact policy metadata

9 November 2026. The same checked closure references now use a replacement
local-learning version tag, rather than an extra field in every full key.
Policy namespaces remain distinct. The [first trial](../cnf-probe-closure-reuse/README.md),
its storage regression, proofs and archives are preserved unchanged.

## Comparison and interpretation

This supplement measures only the compact mode on the same 1,209 inputs. The
three reference modes, including their timings and byte-identical archives, are
inherited verbatim from the first study. Their fingerprints and archive hashes
are verified before this run. This is one additional sample, not a repeated or
interleaved significance study. A checkpoint staging/commit overlapped part of
compact acquisition; no tests, Lean builds or profiles overlapped its timings.
The small runtime differences should therefore remain exploratory.

| Mode | Total seconds | Discovery seconds | SQLite bytes | Cold seconds | Six-case Python peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full second pass | 62.75908 | 48.01501 | 197,103,616 | 26.78483 | 20,377,769 |
| References, verbose identity | 61.35989 | 46.25967 | 200,323,072 | 26.49960 | 20,080,017 |
| References, compact identity | 61.68668 | 46.53708 | 196,096,000 | 25.09448 | 20,021,725 |

Against the full pass, compact total time is 1.71% lower, discovery 3.08% lower,
SQLite 0.51% lower and cold replay 6.31% lower. It is slightly slower than the
verbose sample despite identical propagation; do not infer a timing effect from
the tag alone. Warm replay is 0.17067 s. The allocation subset is unchanged
(cases 858, 875, 907, 970, 1042, 1061) and excludes native SQLite, RSS and
full-corpus peak. Ordinary solving alone remains the inherited 14.72990 s sample.
No production decision-solver optimization or competitive SAT performance is claimed.

All three inventory modes close **634/697** non-tiny sources and **15/24** new
random sources. They retain exactly **13,066** CNF/depth nodes, **1,201** exact
source records and **10,856** ordinary solver residuals. Every semantic node,
all alternatives and selected source plans match the full-pass baseline.
Compact and verbose modes also have byte-equal profile objects, including the
same proof references. Earlier structural gains are preserved; no new closure
is claimed. Sixty-three sources remain unresolved, including nine new holdouts.

The 17,548 continuations contain **14,705** reused closures, **672** active repeated
assumptions and **2,171** fresh assumptions. Reference bytes are unchanged from
the verbose trial: 968,853 bytes of repeated certificates become 161,755 bytes
of references. Compact logical node bytes are **78,532,589**, versus 79,561,439
in the full pass and 80,448,229 in the verbose trial. Exact-source bytes are
4,253,476, versus 4,282,300 and 4,503,284. The distinct replacement tag removes
the metadata regression while preserving exact full-key collision checks.

The matched discovery counters retain the reductions in restriction, propagation
and fixed-point checking recorded in the first study. The separate compact profile
again selects source **1194**, at 4.32714 s under instrumentation. Restriction,
unit checking/propagation and literal helpers remain dominant. Original probes
account for 55,553 of the 73,101 logical attempts; optimizing the remaining 672
active continuation restarts alone is unlikely to be the largest opportunity.

## Next discovery target

`learning-frontier.json` inspects the 94 selected unresolved nodes, using their
already checked original traces. Sixty nodes have an unsuccessful learned batch;
34 have no eligible batch. Twenty reach the current four-clause cap. Extending
only candidate enumeration to sixteen finds **61 additional eligible clauses on
16 leaves affecting 13 unresolved source paths**, including fresh cases 1189,
1194 and 1196. One leaf reaches that diagnostic cap; the search is not exhaustive.
Thirty-eight existing nonempty batches draw all their clauses from one assumption.

This suggests selecting a more useful four-clause batch from saved evidence,
rather than increasing every probe budget. A concrete next test is to rank
candidates by which checked closures they make active and by coverage of distinct
assumptions, comparing with the current first-four order at the same retained
batch/probe caps. Keep the cost of candidate generation, ranking and changed
probe choices; compare a fixed-choice control to separate propagation strength
from candidate selection. Inconclusive and regressing alternatives must remain.
The 61 candidates are opportunities, not measured new closures.

The diagnostic visits 1,805 saved unit candidates and 14,871 source literals;
998 candidates are explicit duplicates and 603 are binary-path redundant.
It charges 6,203 graph vertices and 5,971 graph edges. Candidate generation takes
0.00378 s separately, excluding archive loading and selected-path traversal.
The current ordering/filtering is preserved, so this does not enumerate every
possible alternative batch. All original proofs and source dependencies remain
in the archive; no unbounded prepared oracle or efficient arbitrary-SAT result
follows from these counts.

## Validation and reproduction

All **348 Python tests** pass. Both closure-reference formats coexist with earlier
archives and reject wrong assumptions, active deltas, corrupted original reasons,
changed batches, invalid references and cold corruption. Expanded references
also pass the original full checker and exhaustive small model-fiber tests.
The compact cold replay checks every node, source and ordinary solver certificate
without changing the database. The first study's three new and three older cold
checks remain preserved. No inference or proof is deleted to obtain the savings.

Lean's full build and axiom audit pass at **4,121 declarations / 1,964 theorem
declarations**. `Residuals.lean` formalizes source-local unit reasons and complete
unit derivations, their append-only preservation, and the necessary/sufficient
added-clause fixed-point criterion. The final closure theorem composes them.
It does not verify Python, clause-index serialization, persistence or costs.

`report.json` includes inherited and new records with explicit provenance;
`summary.json` compares all modes. `mechanisms.json` checks all matched plans and
retains the separate profile. `learning-frontier.json` preserves every selected
leaf's candidate list, source paths, counters and unresolved outcome. Source
fingerprints and archive hashes make the continuation reproducible. Use new
output directories and preserve the frozen reference study:

```sh
python3 experiments/compare_cnf_probe_closure_compact.py --output /tmp/new-closure-compact
python3 experiments/analyze_cnf_probe_closure_compact.py /tmp/new-closure-compact
python3 experiments/analyze_cnf_learning_frontier.py /tmp/new-closure-compact
python3 -m unittest discover -s solver -p 'test_*.py' -q
```
