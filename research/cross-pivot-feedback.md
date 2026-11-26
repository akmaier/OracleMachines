# Join failed branches across pivots and retain only required proofs

Date: 26 November 2026. Parent checkpoint: `6431db03` (conditioned saturation).
Evidence: `experiments/results/cnf-cross-pivot-feedback/`.

## Exact reusable pattern

No tested pivot in the three remaining cases has both branches refuted. However,
the previous run already checked several one-sided failures. Each refutation of
`B ∧ l` proves the unconditional implication `B ⇒ ¬l`. These implied units can be
joined even when they come from different pivots. A checked unit contradiction in
their union refutes `B`; source-only reconstruction then discharges all acquired
bank provenance. Both cold readers now accept the original snapshots `(61,0)`
and `(67,0)`, raising structural coverage **243/246 → 245/246**.

This joins consequences of branches of the **same seed**. It does not combine
arbitrary assumptions or treat an open sibling as unsatisfiable. Each retained
lemma has an exact assumption and a checked saturation refutation of that seed
plus the assumption. The collector validates both sides of each supplied old
partition, then retains only its failed sides. Independent cold replay needs only
those failed-side certificates, not the discarded siblings' search histories.
The full history remains available for future discovery.

Recognition binds the canonical seed, coordinates and ordering. It rejects
duplicate assumptions, open branch claims, changed signs, malformed bounds and
stale child traces. The summary's final proof is checked against the exact union
of the seed and negated assumptions. An unresolved summary must instead supply a
checked open unit closure. Unresolved is not SAT. A changed seed invalidates these
bindings; this implementation does not infer reuse merely from similar clauses.

## Proof-directed compression and native expansion

The full summary keeps all failed sides. For a refuted summary, backward causal
slicing of the joint unit trace identifies which implied units are actually used.
Keep only their branch certificates, remove unrelated trace steps, and remap clause
indices into the smaller augmented bank. Independently check the resulting proof.
This preserves the refutation, not every future inference that the discarded
lemmas might support. Unresolved summaries keep all their implied units. Both full
and compact summaries are retained alongside the original histories.

| Snapshot | Full failed sides | Required sides | Full joint trace | Compact joint trace | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| (61,0) | 9 | 7 | 36 | 18 | Source-only UNSAT certificate |
| (61,50) | 2 | 2 | — | — | Open closure, 334 → 314 residual clauses |
| (67,0) | 10 | 3 | 13 | 4 | Source-only UNSAT certificate |

Native conversion follows the joint trace from the original source. At an implied
unit's excluded branch, the context contains its original failed assumption;
conversion enters that branch's checked bank and expands its provenance. The
context is preserved through every recursive call. A condition-origin leaf is
rejected, preventing an assumption from proving itself. The root joint bank and
each failed-side bank have separate environment identifiers in slice memo keys;
identical clause indices across different banks cannot alias. All environments
share one 262,144 direct-unit work allowance per compilation. Warm root reuse
revalidates the supplied source, prefix, summary and underlying histories first.

Both summary forms produce **identical native graphs and compressed archives**
on each certified snapshot. Compact summaries reduce proof checking and setup;
they do not shrink these already sliced native graphs. The global direct-unit
allowance spends 137,505 work units at `(61,0)` and 257,570 at `(67,0)`, without
budget skips. The latter is close to the allowance; this result provides no bound
on native growth when direct closure fails or its allowance is exhausted.

## Acquisition, cold replay and memory

Six fresh-process permutations compare rebuilding the joint result from the old
history, checking the full failed-side summary, and checking the compact summary.
All three process the same three snapshots without fresh probing. Each timed run
includes input loading, checked seed reconstruction, summary reconstruction or
validation, and result serialization/reload. Prior branch discovery and the final
lineage audit are additional. The study uses the retained frontier, not held-out
cases or an estimate of arbitrary-CNF coverage.

| Input representation | Load (s) | Seed (s) | Check/join (s) | Persist (s) | Complete (s) | Input bytes | Peak RSS (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Original histories | 0.02933 | 0.04827 | 0.47371 | 0.00133 | 0.55279 | 3,654,264 | 73,515,008 |
| Full failed-side summaries | 0.01070 | 0.04816 | 0.16079 | 0.00127 | 0.22109 | 1,328,981 | 60,080,128 |
| Compact proof summaries | 0.00753 | 0.04812 | 0.09796 | 0.00100 | 0.15478 | 827,782 | 55,820,288 |

Compact replay is **72.00% faster** than rebuilding from histories, with **77.35%**
fewer input bytes and **24.07%** lower peak RSS. Against full summaries it is
**29.99% faster**, with **37.71%** fewer bytes. Seed reconstruction now costs about
31% and checking about 63% of compact replay. These are smaller replay payloads;
the archive retains all older representations, so total historical disk use grows.

Building the full summaries costs 0.54168 s; checked compaction adds 0.25996 s.
These costs include their input work and serialization and are not subtracted
from the replay timings. Using the observed means, full summaries repay their
construction after two replays versus histories; compact summaries repay their
entire 0.80164 s preparation after three. If full summaries already exist, the
extra compaction pays back after four replays. These are workload-specific measured
break-even counts, excluding sunk historical discovery, not worst-case guarantees.

## Native conversion against fresh solving

Six mode permutations compare full-summary reconstruction, compact-summary
reconstruction and the existing fresh solver at its 256-node limit. Full and
compact share the same global shortcut budget. Fresh uses a different algorithm
and its node limit is not an equivalent work budget. Both fresh solves succeed.

| Snapshot | Mode | Construct (s) | Warm (s) | Cold readers (s) | Persist (s) | Complete (s) | Records | Record bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| (61,0) | Fresh | 0.36350 | 0.00153 | 0.36726 | 0.13099 | 0.86989 | 204 | 1,644,718 |
| (61,0) | Full | 0.33698 | 0.08790 | 0.19686 | 0.05403 | 0.68329 | 91 | 857,487 |
| (61,0) | Compact | 0.30220 | 0.07288 | 0.19112 | 0.05322 | 0.62752 | 91 | 857,487 |
| (67,0) | Fresh | 0.45438 | 0.00217 | 0.48753 | 0.17164 | 1.12335 | 175 | 2,443,583 |
| (67,0) | Full | 0.53324 | 0.11456 | 0.39201 | 0.12868 | 1.17863 | 123 | 1,953,396 |
| (67,0) | Compact | 0.44289 | 0.06364 | 0.39602 | 0.12726 | 1.03889 | 123 | 1,953,396 |

Complete time also includes input loading and database handling. Earlier summary
construction and branch discovery are additional. Compact native workflows total
**1.66642 s**, versus **1.86192 s** full and **1.99324 s** fresh: savings of **10.50%**
and **16.40%**. Their 214 records occupy 2,810,883 raw bytes, versus 379 records and
4,088,301 bytes fresh (**31.25% less**). Full reconstruction at `(67,0)` is slower
than fresh despite its smaller native graph; preserve that regression. No
end-to-end one-shot advantage is claimed after charging summary construction.

| Snapshot | Mode | Peak RSS (bytes) | Compressed native archive (bytes) |
| --- | --- | ---: | ---: |
| (61,0) | Fresh | 82,640,896 | 181,299 |
| (61,0) | Full | 71,335,936 | 75,655 |
| (61,0) | Compact | 70,074,368 | 75,655 |
| (67,0) | Fresh | 92,897,280 | 251,310 |
| (67,0) | Full | 90,292,224 | 192,327 |
| (67,0) | Compact | 87,490,560 | 192,327 |

All modes and samples remain. The overlay selects the least measured complete
native workflow per certified case, without changing production defaults or
charging away acquisition. Process RSS does not bound lifetime retained state.

## Validation and next gap

The new checker and compiler pass 2,200 full tests and 25 focused tests, including
all 256 subsets of the eight two-variable unit/binary clauses, 80 seeded five-variable
formulas, sparse coordinates, independent seed contradictions, proof remapping,
summary ownership, both real native certificates and corrupted warm bindings.
Both archive readers independently verify the original source roots. The audit
reconstructs the old seeds independently and checks every saved sample and digest.
All 1,208 old source fingerprints and 33,298 artifact entries in 219 manifests are
unchanged, as are previous native archives and all 64 manuscript proof blocks.
Five new science/test files bring the source ledger to 1,213.

Resume `experiments/results/cnf-cross-pivot-feedback/checkpoint.json`, key
`cross_pivot_feedback.remaining`, using the new comparison module's loader. The
single remaining row `(61,50)` is preserved exactly. Its checked full/compact
summary retains implications `60=false` and `73=false`, which shrink the residual
from 334 to 314 clauses. The next coverage step is saturation or conditioning of
this strengthened bank, with source provenance maintained for those two units.
Do not repeat the old sixteen-pivot search on an unchanged seed. The larger
unresolved obligation is discovery and economical recomposition on novel CNFs;
even complete coverage of this finite benchmark would not solve arbitrary SAT.
