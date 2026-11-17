# Checked composition on exact historical prefixes

One additional missing-clause guard reduces fresh expansions and new native
proof rows **68 -> 29** across eight historical unresolved cases. Added native
identifier-plus-JSON payload falls **124,143 -> 52,493 bytes (57.72%)**. Serialized
proof deltas plus chain sidecars fall **251,022 -> 217,209 bytes (13.47%)**. The SAT
control remains SAT. All six strengthened premises already exist; no premise
row is published. Cases 41 and 179 fall back unchanged.

These are post-hoc historical cases, one cold-cache sample per arm, with the exact
persistent pre-query state restored. Baseline proof payloads match the preceding
stream exactly. Recognition and premise checking outweigh child-solve time saved
in the samples: the query-phase sum rises **0.088170 -> 0.160206 seconds**. That sum
excludes separately reported preparation, cold replay, serialization, warm-bank
construction and prefix reconstruction. Full-row export/report overhead remains
in aggregate study time. No peak RSS, fresh coverage, stable total runtime gain,
or downstream stream-sharing effect is claimed. Tests/builds/profiling did not
overlap timed production.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_guard_chain.py /tmp/new-guard-chain
python3 experiments/validate_cnf_guard_chain.py /tmp/new-guard-chain
python3 experiments/analyze_cnf_guard_chain.py /tmp/new-guard-chain
python3 experiments/profile_cnf_guard_premises.py /tmp/new-guard-chain
```

`protocol.json` binds the historical initial archive, query stream, prior full
trial and diagnosis. Each arm saves only its `delta.json`, `chains.json` and
phase/count report. Reconstruct its database by restoring the bound historical
initial archive, applying the strict prior-query append prefix from the bound
full trial, and adding the delta. The validator does this independently and
checks every native node and both index lineages, then replays the chain with
fresh solving disabled. It also checks selection order and pre-query readiness.
Old certificates remain in place; no alternate native certificate occurs here.

`union-chains.json` retains eight conclusions in `checked-guard-chain-v1` format.
Load them through `GuardChainBank` against the checked reference union to reuse
composed answers. The native root table need not contain the composed source;
these sidecars and their checker are required. Every guard premise and final
child remains an ordinary native proof. The bank checks on load, transports
models for identities admitted by the existing normalizer, and assumes an
exclusively owned immutable or append-only proof session. It does not recognize
arbitrary formula equivalence.

`reconstruction.json` records independent replay of all 16 arms, 2,957 inherited
decisions and eight chain conclusions. The union has **20,666 native keys**,
preserving all 20,649 previous payloads and adding 17. It occupies 64,909,312
SQLite / 4,784,034 gzip bytes. The union retains old results; per-arm savings do
not shrink the historical archive. Original structural authority stays 2,614
patterns / 259 pairs / 17 missing children, with original 17/24 / 999 steps and
separate supplemental 24/24 / 208 steps. No discovery pointer is replaced.

`frontier-check.json` verifies all four complete retained lineages with no fresh
search: ready/pending counts remain **129/41 original, 136/71 legacy, 74/102 causal,
and 74/129 optional expanded causal**. No support origins are acquired.
`preservation.json` and `parent-manifests.json` verify 416 prior sources and 4,579
artifacts in 80 manifests unchanged. The runtime protocol binds 420 sources;
the post-hoc analyzer and checking-cost probe bring `validation.json` to 422.

The full **1,022-test** solver suite passes against the bound implementation.
Nine focused chain/condition tests passed earlier; two subsequent assertions
that composed source roots are absent from the native table were exercised by
the full suite. The full log retains 44 older unclosed-SQLite ResourceWarnings;
focused tests emit none. Test commands and logs are retained. The paper builds
to **203 pages** with all **64 prior proof blocks unchanged** and no overfull,
undefined-reference or LaTeX warnings. No new Lean theorem is claimed.

The separate read-only `premise-profile.json` probe uses the six selected
historical candidates. Checking the stored strengthened premise directly,
without first checking the separate core, reduces verified nodes **148 -> 57**,
verification literal payload **13,299 -> 8,073**, and read bytes **122,683 ->
68,141**. It changes neither discovery nor the deployed selector. A negative
strengthened premise is sufficient for the guard; unchecked metadata can only
suggest candidates. Missing premises still require checked derivation.

Next, integrate this check order, reuse prepared core clause membership, and
compare fresh excluded inputs with preparation and cold replay charged. Cases
176/41/179 retain ten/eight/four expansions. More guards are not automatically
cheaper, and arbitrary-SAT polynomial or optimal-expansion bounds remain open.

New manifest: **70 artifacts**. Next preservation audit: **4649 artifacts / 81 manifests**.
