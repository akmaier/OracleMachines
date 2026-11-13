# Parent lemmas across conditioning and elimination

2026-11-13. This is a checked reuse experiment on the remaining 19-variable,
84-clause leaf, not a new SAT class or an increase in structural coverage.

## Result and next target

The saved 22-variable parent has sixteen source-proved binary lemmas. Conditioning
its saved split to variable 4 = false satisfies eight of them. The other eight
survive two complete Davis–Putnam eliminations and the intervening checked binary
path reduction. One is explicit in the final leaf; seven can be added without
solving again. **All seven are also derivable from the leaf's already saved unit
traces.** The deterministic local batch finds eleven clauses in total, below its
sixteen-clause limit. Neither augmentation produces a forced literal, common
consequence or equivalence reduction in the implemented paired-probe pass.

Coverage remains **55/83**, including the parent's growth-exception ablation.
These are adaptively reused development inputs, not a holdout. The exact original
history is unchanged: **769,646,592 bytes**, 41,710 pattern nodes, six splits,
42 learned bases and 155 augmented blocks. The new augmentation proofs and failed
probe attempts are retained as sidecar evidence, not installed as successful
coverage routes. The reference archives remain unchanged too.

The next structural target is **another exact cofactor from the saved pairs on
the 19-variable leaf**, retaining both obligations and closed siblings. Do not
repeat either augmentation below. A further learning round on the newly augmented
traces remains a different, untested inference step; this result does not prove
saturation of all useful clauses. The alternative 18-base / 92-variable queue
remains available.

## Sound reuse conditions

`experiments/cnf_lemma_transport.py` checks a self-contained certificate:

1. The explicit source and conditional-unit reasons prove every initial lemma
   before any new clause is added. All references are used and duplicate reasons
   or clauses are rejected.
2. A conditioning step replays its unit closure and restricts the lemmas using
   every fixed value. Satisfied lemmas are discharged.
3. A projection step recomputes **all** opposing-clause resolvents under the
   recorded pair and additive growth bounds. Only lemmas whose entire remaining
   support survives are retained. A clause mentioning a removed variable is
   discarded whole; deleting only that literal would strengthen it unsoundly.
4. A binary-path step checks the retained reasons for each deleted source clause.
   Every step checks the exact normalized target and its variable-name map.
5. Augmentation requires an exact match to the actual final formula. The checker
   returns entailed clauses, not a satisfiability verdict or a coverage plan.

The underlying fact is elementary: if F entails C, then conditioning F by alpha
entails the restricted C unless alpha satisfies it. If G is exactly the
existential projection of F and C uses only G's variables, every G-model extends
to an F-model and therefore satisfies C. Equivalence and bijective renaming also
preserve entailment. Mere equisatisfiability is insufficient; unsupported path
kinds are rejected. The implementation supports only the three transformations
above. It is checked Python, not a new Lean refinement.

The checker replays the dependencies of one useful positive fact. It does not
restore unrelated inventory nodes, prove the inventory's ancestry, or validate
all structural routes. Step verification, normalization and clause transport
remain paid work; projection can still generate many resolvents outside the
stated budgets. There is no uniform polynomial bound for arbitrary SAT here.

## Matched augmentation trial

Both arms start at the same explicit 19/84 formula, use a 64-variable probe cap
(above its full support), and independently check the resulting traces. The
local alternative starts with the previously acquired leaf traces, whose costs
remain in the parent reports. This comparison does not give it free acquisition.

| Quantity | Transport from parent | Learn from saved leaf traces |
|---|---:|---:|
| New explicit clauses | 7 | 11 |
| Augmented clauses | 91 | 95 |
| Clear traces / binary variables | 32 / 16 | 34 / 17 |
| Other variables excluded by no-trigger lemma | 3 | 2 |
| Structural reduction | none | none |
| Portable positive proof, compressed bytes | 2,362 | 749 |
| Positive proof check, seconds | 0.001996 | 0.000655 |
| Probe discovery, seconds | 0.003767 | 0.003993 |
| Probe replay, seconds | 0.003055 | 0.003331 |

The four local-only clauses, in leaf coordinates, are `[-16,-5]`, `[2,14]`,
`[5,19]`, `[11,18]`. This containment is specific to this example. The experiment
stores both augmented-source exhaustion certificates, rather than inheriting
the old formula's negative certificate. No single-variable unit refutation works
on either exact augmentation; stronger reasoning is not excluded.

The transport certificate includes four source traces, sixteen lemmas, and four
path steps. It occupies **12,867 JSON bytes / 2,362 compressed bytes**, including
the explicit source and target keys. Export restores the old inventory in
**13.38857 s**, then packs and checks the proof in **0.01936 s**. Preparing the local
alternative from its saved exhaustion evidence takes **0.00291 s**. The complete
export-and-acquisition pipeline takes **14.05245 s**. All six compressed artifacts,
including the exploratory failed ordering, total **7,597 bytes**; report, test and
replay logs add separate uncompressed bytes. No old history is replaced.

Two fresh subprocesses per mode, in reversed order, check the same augmentation
and exhaustion conclusions. Compact replay takes **0.16158 / 0.11073 s**; adding
inventory reconstruction and a check of the retained path's ancestry takes
**14.43231 / 13.85120 s**. Process startup and teardown are included; OS caches are
not flushed. The history mode has an additional ancestry obligation, so these
are not interchangeable whole-solver validations or a general speedup ratio.
Single local acquisition samples and unmeasured peak RAM cannot support broader
runtime or memory claims.

## Validation and reproduction

**37 relevant tests pass**, including exhaustive two-clause formulas of width two
or three on three variables, every clear consequence-bearing assumption and
every projection variable. Truth-table evaluation checks surviving entailments.
Adversarial tests reject forged reasons, changed targets/name maps, invalid
projection and unsupported equisatisfiable rewrites. A separate conditioning
regression derives a new unit from a transported clause without dropping an
existentially eliminated literal. Both cold history reconstructions preserve the
database byte-for-byte with recognition discovery disabled.

```sh
python3 experiments/compare_cnf_lemma_transport.py run /tmp/cnf-lemma-transport-new
python3 experiments/compare_cnf_lemma_transport.py validate \
  experiments/results/cnf-lemma-transport/report.json --history
python3 experiments/measure_cnf_lemma_replay.py \
  experiments/results/cnf-lemma-transport/report.json /tmp/lemma-replay.json
python3 -m unittest solver.test_cnf_lemma_transport \
  solver.test_cnf_lemma_transport_conditioning solver.test_cnf_exhaustion_certificate \
  solver.test_cnf_trace_learning solver.test_cnf_trace_split \
  solver.test_cnf_variable_elimination solver.test_cnf_additive_elimination \
  solver.test_cnf_binary_paths
```

The report fingerprints the helper, extraction script and direct proof checkers;
the replay record binds fresh-process samples to that report. Continue inventory
work from `experiments/results/cnf-reuse-frontier/report.json` with
`continue_cnf_reuse_frontier.restore_checkpoint`; this experiment adds standalone
evidence, not a replacement inventory checkpoint. Read its `transport.json.gz`,
`local.json.gz` and both `*-acquisition.json.gz` files to reuse the new proofs.
The `pilot.json.gz` preserves the earlier exploratory clause ordering and its
same clear outcome; it is not the authoritative checked comparison.
