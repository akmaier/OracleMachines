# Reusing checked canonical source order

2026-11-15. The investigation targets cold verification, which dominated the
previous retained-session sequence. It also resumes the saved conditional
frontier of case 1190. The normalizer, source keys and proof policy remain
mathematically identical; the candidate avoids sorting and renaming when a
complete input scan establishes that these operations would be identities.

## Why this target

The [cold global profile](../experiments/results/cnf-cold-global-profile/report.json)
separates route construction from the full global query on the unchanged
checkpoint. Instrumented construction takes **22.82681 seconds**, including
**3.90452 seconds / 8,828 calls** in normalization (17.10%). The query takes
**168.88106 seconds**, including **33.16367 seconds / 62,020 calls** in
normalization (19.64%). These are instrumented diagnostic times, not comparison
timings. Cumulative times overlap and must not be added.

Unit fixed-point reconstruction is the larger individual primitive: its own
instrumented query time is **25.797 seconds**, and its cumulative time is
**37.422 seconds**. Previous reconstruction and clause-mask experiments remain
relevant. Here, canonical-source reuse is a smaller, independently checkable
change that requires no retained cache or new proof representation.

## Recognition and correctness

The fast path accepts only built-in list/tuple CNFs and clauses. It scans the
complete accepted source and checks all of the following:

- Literals are nonzero built-in integers, strictly increasing within each clause.
- No clause repeats a variable, so neither duplicates nor complementary literals occur.
- Clauses are strictly increasing lexicographically, so no clause repeats.
- An empty clause appears only as the sole clause.
- The variable support is empty or has size equal to its maximum identifier.

Every support member is a positive integer. Therefore the last condition makes
the support exactly `{1, ..., n}`. The old sorted renaming is then the identity.
There are no tautologies or duplicates to remove, and both sorting operations
leave the source unchanged. The empty conjunction and sole empty clause agree
with their original normal forms. Thus the returned formula and variable-name
map equal the existing normalizer's results on every accepted source. Any
failed condition invokes the original normalizer on the complete original
input, preserving its normalization and rejection behavior.

Both the current inventory and the prepared-policy verifier use this operation.
Key serialization still binds the same complete policy, remaining depth and
normal form. Certificate checking still runs. There is no acceptance based on
object identity, a hash, or a cached SAT answer, and there is no archive migration.
Canonical ordering does not imply membership in a tractable SAT family.

The accepted path uses a linear number of literal visits, set operations and
adjacent-clause comparison positions. That is an operation count, not a
worst-case Python or bit-cost bound: hashing, integer operations, allocations
and serialization still cost work. A failed precheck adds work before fallback.
Transient clause tuples and support sets require space proportional to the
input; this experiment does not measure peak RAM. No normalization cache or
additional persistent index is retained.

Eight new tests cover all 512 two-variable clause sets and reorderings or
renamings, 1,000 seeded mixtures, duplicate/tautological clauses, large variable
identifiers, malformed literals even after an empty clause, iterator fallbacks,
mutable input changes, exact keys in both verifier policies, identical fresh
records and cold replay, and rejection of forged coverage. These finite tests
support the implementation; the argument above establishes why the checked
fast-path conditions suffice for arbitrary accepted sources.

## Measured costs and discovery

The [matched comparison](../experiments/results/cnf-canonical-source/report.json)
uses two reversed-order repetitions with fresh inventories. Both methods build
the complete maintained catalog, query all 83 originals, resume the same saved
split with a 32-state/12-advance budget, and query all originals again. Both copy
the batch seed, hash every historical table and check/export the append. Full
catalog audits follow each timed sequence. The
[timing summary](../experiments/results/cnf-canonical-source/timing-summary.json)
retains individual samples and operation counts.

| Mean time in seconds | Original normalizer | Checked canonical source |
| --- | ---: | ---: |
| Initial construction, global query and serialization | 69.51709 | 65.98742 |
| Route/session construction | 8.59657 | 7.92333 |
| Initial complete global query | 60.58666 | 57.72311 |
| Worker including preparation, checks and export | 1.29386 | 1.23793 |
| Local expansion | 0.15800 | 0.15350 |
| Updated global query | 0.34235 | 0.23702 |
| Updated query serialization | 0.34996 | 0.33667 |
| Complete measured sequence | 71.96107 | 68.45498 |

The complete sequence improves **4.87%**; initial construction and query improve
**5.08%**. Sequence samples are **71.23496 / 72.68719 seconds** for the original
normalizer and **68.31649 / 68.59346 seconds** for the candidate. These are two
development-case observations with shared OS caches, not a statistical or
held-out performance claim. Fallback-heavy inputs may have different costs.
The earlier batch-copy regression remains preserved; this experiment retains
the copied-seed behavior in both methods.

The candidate accepts **28,169 of 48,182 canonicalization calls** across the
current and prepared views, falling back **20,013 times**. Original-normalizer
input-literal charges fall from **29,076,849 to 18,045,239**, while the candidate
adds **16,666,740 precheck literal visits**. These counters do not establish a
reduction in total literal inspections: the old charge counts input payload,
not every internal sorting, set-building and renaming operation. Exact counter
identities account for the **11,031,610** input literals whose ordinary
normalization was replaced. Serialized-key bytes and verified-node counts agree.
The saving is in the operations performed on these inputs, not a free lookup.

Each run stores exactly **25 new records** in one resumed split: twelve
eliminations, seven binary-path reductions, four probes, one polarity change
and one family terminal. The new terminal is **8/10/27**, recognized as Horn
and zero-valid. All **twelve previously entered but unstored states** now have
stored records; the batch enters and stores 25 states, with none interrupted.
These completed reductions close the remaining structural obligations of
**case 1190**, raising original coverage **68/83 -> 69/83**. Classification
coverage is distinct from the SAT truth value of an original input.

The complete sequence also charges the initial arm copy, union-delta merge and
checks, and output serialization. Each arm has an independent history; the
diagnostic union is shared, so later identical merges are idempotent. Shared
parent restoration is **134.48837 seconds**, final cold route/coverage checking
is **71.80313 seconds**, and the full producer is **523.23332 seconds**. The
final full-history delta comparison takes **6.26852 seconds** outside the
individual sequences. Reference acquisition and cold checks are separately
recorded in the report. Instrumented profiling finished before this comparison;
tests and cold replay started after its timed producer completed.

## Space, resume state and next priorities

Both methods retain the same **20,404 current / 2,916 prepared checked objects**.
History grows by **319,488 bytes**, from **780,357,632 to 780,677,120 bytes**, and
from **42,450 to 42,475 patterns**. The union delta is **380,928 SQLite bytes /
14,120 compressed bytes**. Reference evidence grows **4,750 -> 4,802 nodes**;
the reference archive is **31,289,344 SQLite bytes / 2,194,628 compressed bytes**.
Coverage certificates contain **1,002 compact / 3,731 expanded steps**. Persistent state is identical between the two methods; peak RAM remains
unmeasured.

Resume **`experiments/results/cnf-canonical-source/report.json`**, SHA-256
`50c57ea9172332c0bca659299311680db68097e45343f8ef91d71bce9225ed3f`, using
**`experiments.compare_cnf_canonical_source.restore_checkpoint`**. Use its
**`next_selection`**, not the completed `source`: **40/165/494**, original
**case 1227**, retained index **38**, **no pending split**. Next source SHA-256 is
`dd908b0c5efb9e89a0936f123445c33fc5e96692454607748994d96583bd3b3b`.
Preserve evidence **(1, 42, 156, 63, 1)** and **two bridges**. The restorer and
independent replay continue to use the original normalizer; the new inventory
is an optional implementation with identical source and certificate identities.

1. Continue discovery on case 1227 with the checked inventory and complete
   catalog retained. Compare complete sequences when adopting the canonical
   path; include sources that fail its precheck and broader workloads.
2. The larger cold-checking gap is unit fixed-point reconstruction and repeated
   checking of source-bound proof traces. Investigate exact shared structure
   before adding a larger cache. The existing probe cache has many evictions;
   that does not prove the evicted keys are reused. Preserve earlier clause-mask
   regressions and charge preparation and invalidation.
3. Cold restoration remains more expensive than one initial global query.
   Investigate retaining already checked immutable authority across restoration
   and startup without treating unverified historical alternatives as absent.
   Positive coverage certificates alone do not establish a complete frontier.

All **274 tests** pass. Cold replay uses the original implementation with fresh
discovery disabled to check the eight saved global queries, every acquisition
prefix, counter identities, exact stored operations and logical results, and
reference evidence. No new tractable family, minimum-expansion guarantee or
uniform polynomial solution of arbitrary SAT follows from this result.


## Final validation and preservation

Independent cold replay passes in **637.39273 seconds**, checking **eight saved
queries**, every acquisition prefix, identical operations and final logical
state, and all **4,802 reference nodes** with fresh search disabled. The retained
reference certificate reports the original **48/204/612** case 1190 as SAT, and
its model is checked against that original CNF. This truth-value check is
separate from the structural-coverage result.

All **1,973 artifacts from 34 earlier manifests** and **six new profiling
artifacts** retain their recorded hashes. All **4,750 earlier reference payloads**
remain byte-for-byte present. The comparison manifest binds **79 artifacts /
9,042,977 bytes**, excluding the manifest itself; validation checks **115 source
fingerprints**. The manuscript builds to **167 pages**, preserving all **64
existing proof blocks**, with no new proof blocks, undefined references or
overfull boxes. The build, test and cold-replay logs are retained alongside the
experiment. Validation jobs overlap, so their elapsed times are not comparative
runtime measurements.
