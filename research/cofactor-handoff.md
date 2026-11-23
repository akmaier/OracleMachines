# Pass prepared work to the selected cofactor

The [previous memo](prepared-cofactors.md) saved normalizations but paid for
101 misses as well as 13 hits on its new-edit stream. This experiment replaces
content-indexed lookup with a direct handoff from a cofactor probe to the child
that the unchanged two-polarity policy actually selects. It also reuses the
probe's nonconflicting propagation result when native search reaches that step.
The earlier failed memo, its timings and its proof archive remain unchanged.

## Binding and exactness

The policy probes the ordinary split variable's false cofactor first. If that
probe finds no contradiction, it can retain an immutable offer containing the
restricted raw CNF, its canonical CNF, original-name map, key and deterministic
unit-propagation result. If the following true probe yields a checked refutation,
the existing policy must acquire the false child. It passes that exact offer to
the ordinary visit. The producer has already performed restriction and
normalization, so the selected child can reuse both.

The offer is solver-owned and consumed once. A foreign, replaced or already
consumed object is rejected. Only the exact raw object can consume its canonical
triple. A context-local propagation dispatcher additionally binds the exact
canonical CNF object and counter object; it copies the immutable forced assignments
and trace into fresh return values. Equal-but-distinct formulas and other counters
follow ordinary propagation. This avoids raw-CNF hashing, equality matching and
miss scans at unrelated consumers.

Higher-priority structural recognition and existing cache reads retain their
order. The stored propagation is consumed only if ordinary native search actually
asks for it. A cached positive probe supplies normalization alone. A cached
negative still follows the existing negative-proof lookup even without initial
units. Nonconflicting propagation is not a satisfiability certificate: only a
fully checked model or refutation answers the query. Model lifting, publication
and independent child/certificate checks are unchanged.

If the false cofactor is refuted first, there is no prepared survivor. If both
probes miss, the offer is discarded before the existing binary-forced continuation.
This false-first asymmetry preserves the prior search; it makes no claim that
this polarity order is best. The query session clears preparation on normal
completion, budget stop or exception. Completed checked proofs retain the existing
persistence rules; incomplete preparation is never persisted.

## Resources

The cap is 256 KiB for the aggregate conservative charges of all retained offers,
including active ancestor visits. New offers that would exceed it are skipped,
and ordinary computation continues. There is no eviction or content index.
Charges include the immutable object, raw/canonical tuples, names, full key,
integers and frozen propagation data, deliberately overcounting sharing. The cap
excludes construction transients, dispatcher/control/accounting fields, allocator
overhead and the solver's existing state. It does not bound process RSS or search.

For a cofactor with `L` literal occurrences and `T` propagation-trace entries,
freezing and sizing add input/trace-dependent work. The actual propagation result
is produced by the existing repeated-scan procedure and remains charged to the
probe. A successful handoff removes a second restriction and normalization;
when propagation is reached, copying its result takes `O(T)` entries instead of
rerunning the scans. Integer widths, formula/key construction and checking retain
their own costs. Unselected offers still pay preparation costs. No uniform
saving follows for arbitrary CNFs, and this mechanism cannot reduce the unchanged
policy's expansion count or persistent proof graph.

## Comparison

The protocol is frozen after ten development tests and before timed solving.
Three arms run in separate serial workers in two opposite orders:
binary-frequency routing, two-polarity routing and two-polarity routing with the
direct handoff. Six previous novel edits become controls, the three saved sign
variants retain their exact cold prefixes, and six fixed-seed nearby edits have
roots absent from the preceding union. Donors and variable maps remain supplied.
The ordinary 256-expansion budget is unchanged; direct probes and publications
remain separately charged.

All session setup, freezing, sizing, dispatch and cleanup is included in handoff
query time. Complete worker time also includes restoration, proof checking,
warm reuse, persistence and cold reconstruction. Prior acquisition remains sunk.
The validator requires identical decisions, models, partitions, expansions and
complete native proof payloads between the two-polarity and handoff arms. Profiles
and independent object-graph walks run after comparative timing.

## Measured result

| Stream | Binary-frequency expansions | Two-polarity / handoff expansions | Two-polarity query seconds | Handoff query seconds |
| --- | ---: | ---: | ---: | ---: |
| Six controls | 53 | 61 / 61 | 0.273469 | 0.232464 |
| Original exposed sign | 30 | 4 / 4 | 0.014812 | 0.015834 |
| Variable-76 flip | 30 | 4 / 4 | 0.013932 | 0.013919 |
| Global complement | 30 | 4 / 4 | 0.014528 | 0.014317 |
| Six new edits | 53 | 55 / 55 | 0.218339 | 0.212530 |

These are sums across separate streams, averaged over two serial orders. On new
edits, handoff query time falls **2.66%**, with improvements of 2.26 and 9.36 ms in
the two orders. Complete worker time rises **0.15%**, with mixed order signs;
there is no demonstrated total-time gain. Cold replay and reconstruction dominate
that broader measurement. The control query mean falls 14.99%, but its paired
improvements are highly unequal: 79.18 and 2.83 ms. Treat that mean cautiously;
the deterministic work savings below are firmer evidence of what changed.

The original sign variant regresses 6.90% on the mean, with mixed order signs.
The other sign variants change -0.09% and -1.45%, also with mixed signs. None of
these small exposed samples establishes a general runtime guarantee. We retain
all individual timings and leave the general solver default unchanged.

On new edits, six offers are admitted, four are consumed and two discarded.
Three consumed offers reach native propagation; the other child finishes earlier
in the unchanged priority order. Normalizer input-literal visits fall
**123,779 -> 120,730** (2.46%), native propagation visits fall
**71,723 -> 61,663** (14.03%), and restriction visits fall **83,351 -> 80,205**.
Probe propagation remains at 39,332 visits. Combining native and probe propagation
gives a **9.06%** visit reduction. Preparation sizes 4,687 raw literals, freezes
72 entries and copies 56 entries; these are distinct operations, not interchangeable
units of runtime. Controls consume six of eight offers and reuse four propagations.

Persistent native keys/payloads are identical between the two-polarity and handoff
arms: 628,482 bytes on new edits. Compressed deltas plus raw sidecars remain
162,328 bytes; summed endpoint checked objects remain 3,711,664 bytes. Those sums
are not simultaneous process-memory bounds. The largest live offer charge across
trials is 183,297 bytes. A separate audit of the selected new case stream checks
32 boundaries, sees at most two live offers, and finds at most 130,021 actual
object-graph bytes below the 182,613-byte conservative charge. Preparation is
released after each query, so it creates no archive growth of its own.

The comparison against binary-frequency routing still exposes a larger gap.
Handoff takes 55 rather than 53 new-edit expansions, has **17.39% higher query
time**, and retains **38.87% more native payload**. Reusing a probe's preparation
cannot undo the policy's choice of a more expensive continuation or proof graph.

## Next target: share the partition structure

The largest new handoff query is the case-31 deletion, at 108.98 ms versus
112.35 ms for two-polarity routing and 90.82 ms for binary-frequency routing.
`next-target.json` binds all three profiles, the raw source and exact pre-query
state. There are no additional prior-query rows for this selected position.
The handoff reduces native normalizations **130 -> 127** and propagation calls
**33 -> 31**, while publications stay at 39. Binary-frequency routing uses
108 normalizations, 24 propagations and 29 publications. Instrumented durations
are attribution aids, not comparative runtimes; cumulative times overlap.

A separate untimed audit finds **four calls producing the same six-branch
partition structure** for each query in the selected two-query stream. All four
complete input fingerprints and all four produced-structure fingerprints agree
within each query. The hashes are diagnostic, never proof authority. Construction
occurs in premise publication, branch acquisition, sidecar construction and
sidecar checking. The premise publisher builds branches that it does not consume.
The four construction calls also appear under binary-frequency routing, so this
opportunity is independent of the more costly two-polarity policy.

**Next primary experiment:** prepare the ordered missing-clause structure once
for acquisition and sidecar construction, and avoid materializing unused premise
branches. Bind immutable source, ordered missing clauses, guards and name maps;
charge preparation and retained space. Preserve the independent record checker,
its exact child bindings and fresh prerequisite lookups. Compare a descriptor
handoff with reconstruction, including malformed/modified sidecars and cold replay.
A shared prepared structure cannot authenticate an answer or let a residual
refutation discharge an unrelated source query. This should be tested against
binary-frequency routing as well as the optional probe policy.

Probe admission and continuation choice remain the next search-policy gap.
Full cold replay and sidecar representation remain larger total-worker costs.
The present experiment improves a narrow acquisition mechanism; it adds neither
whole-source coverage nor an efficient classification of unrestricted SAT.

## Verification and preserved state

All **1,428 tests** and **136 focused tests** pass. The ten new tests cover
immutable offers, original-name lifting, caller mutation, exact identity/counter
scope, single consumption, foreign/forged offers, capacity fallback, nested live
charges, retained budget stops, failure cleanup, cached cofactors and 512 small
formula/sign comparisons. Full tests retain the 44 previously observed unclosed
SQLite warnings; focused tests emit none.

The independent validator checks **90 attempts from 54 workers**, exact seeds,
chronological dependencies, repeated-order agreement and reproduction of earlier
controls. All 30 two-polarity/handoff query pairs have identical decisions, models,
expansions, native payloads and partition sidecars. Both readers recheck cumulative
authority, 24 current partition records and 170 previous partition records.
The union adds **74 unique native records**, reaching **75,416**. The 42
alternative-payload observations remain in trial deltas; older authoritative
payloads are preserved. All extension tables remain unchanged.

All 726 earlier source fingerprints and 10,493 artifacts in 132 manifests are
verified unchanged. The final source ledger contains 733 files. Older unrelated
composed/inventory audits remain bound by those manifests. The manuscript builds
to 239 pages without warnings, retaining all 64 earlier proof blocks. Resume
`experiments/results/cnf-cofactor-handoff/checkpoint.json`. No new external SAT
benchmark or Lean refinement theorem is claimed.
