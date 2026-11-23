# Direct reuse of the canonical joint prefix

See [the invariant and interpretation](../../../research/joint-prefix-reuse.md),
`protocol.json`, `analysis.json`, `next-target.json` and the final
`checks.json`/`manifest.json`.

The optional serial implementation reuses the first surviving cofactor's
canonical triple while assembling a two-consequence refutation. That triple is
already live from the forward lookup. No extra CNF cache or name-map lookup is
introduced. Cached-prefix priority, single consequences and all native proof
checks remain unchanged. The existing two-consequence bound is essential.

The main comparison has 15 targets, 36 workers and 60 attempts, using opposite
serial mode orders. Each six-edit group avoids two reconstructions; each isolated
branch avoids one. Native proof bytes, partitions, expansion counts and storage
are identical. Control/new-edit query means fall 2.98%/1.42%, but no-hit queries
also vary and one isolated branch order regresses. These small two-order timing
differences do not establish a robust runtime speedup. Every sample is retained.

Reproduce in a fresh directory:

```sh
mkdir experiments/results/cnf-joint-prefix-reproduction
python3 experiments/probe_cnf_joint_prefix.py experiments/results/cnf-joint-prefix-reproduction
python3 experiments/compare_cnf_joint_prefix.py prepare experiments/results/cnf-joint-prefix-reproduction
python3 experiments/compare_cnf_joint_prefix.py experiments/results/cnf-joint-prefix-reproduction
python3 experiments/analyze_cnf_joint_prefix.py experiments/results/cnf-joint-prefix-reproduction
python3 experiments/profile_cnf_joint_prefix.py experiments/results/cnf-joint-prefix-reproduction
python3 experiments/validate_cnf_joint_prefix.py experiments/results/cnf-joint-prefix-reproduction
```

Finish serial timing before running profiles, tests or cumulative audits. Profiles
are diagnostic and instrumented, not comparative timings. Prior acquisition and
supplied donor/maps remain sunk. The exposed census creates no additional proofs.
Four of ten observed frames have no stored answer after the stopped probe; their
local construction identities and path evidence do not turn them into answers.

Both readers recheck 76,182 native records, all retained extensions and 342
partition records. All earlier payloads are preserved; 80 new native records are
retained. All 1,496 full and 204 focused tests pass. The full suite emits 44 unclosed
SQLite warnings, the focused suite none. The 244-page manuscript builds without
warnings and preserves all 64 earlier proof environments. The final source ledger
contains 788 entries. No new Lean refinement theorem or SAT coverage cell is
claimed.

The next primary target is conditional mixed-width reason reuse. In
`next-target.json`, the `novel` observation at query position 0, acquisition index
2, binds 125 variables, 258 ternary/56 binary clauses, 886 literal occurrences,
budget 247 and three earlier native IDs. Restore that exact prefix plus those IDs
from the bound trial delta; replay the preceding probe/branch for warm pools.
Never seed comparison queries from the final union.

Its `proof_census` rechecks a 14-node DAG: five splits, nine unit nodes. Six unit
nodes end in conflicts; three require child proofs. Their stored CNFs have 6,495
literal occurrences, but their explicit local reasons reference 148, including
12 ternary reason clauses. These are not one unconditional core or an achieved
compression ratio. Test whether conditions, original-variable maps and child
obligations can be retained while matching against the existing causal core bank
before full reconstruction. Charge recognition, mapping, checking and replay.
