# KD-trees and candidate search for expansion reuse

Assessment: **8 November 2026**. No KD-tree is currently implemented or
benchmarked in this repository. The literature collection contains nearest-neighbor
language-model work, but that is not an evaluation of indexing our solver states.
This note records the candidate and its prerequisites, not a measured speedup.

## Current search and the possible role

The affine preparation and transition caches use hashes followed by full typed
equality checks. Each computes one direct-mapped slot; a collision replaces a
candidate rather than starting a scan of every archived transition. Key hashing
and comparison still traverse coefficients. Content-addressed archive lookups
use SQLite indexes. The current repeated-stream cost therefore is not a linear
scan of all past states. See [AffineKernel](../formal/OracleMachines/AffineKernel.lean)
and [the resource audit](resource-bounds.md).

A KD-tree addresses a different operation: retrieving nearby numerical feature
vectors. It could select a few old states for a **checked small-change repair**
after an exact-cache miss. This would be useful if proximity predicts a cheap
valid repair. The present affine kernel can reuse an equal transition, but does
not yet repair a merely similar one. An index alone cannot create that ability.

| Required match | Candidate mechanism | Evidence needed before reuse |
|---|---|---|
| Same ordered normalized batch and boundary | Existing hash and equality check | Existing native kernel contract |
| Row permutations or equivalent row spaces | Canonical keys, when affordable | Exact semantic transport, including the boundary |
| Overlapping equation/support sets | Inverted indexes or bitset filters | Exact overlap/change validation and repair |
| Nearby cheap structural descriptors | KD-tree shortlist | Exact candidate validation and certified repair |

These alternatives are hypotheses for comparison. Canonical row-space discovery
may itself require elimination; it must be charged. Rank is not a free feature
when it has not already been computed.

## Why distance cannot authorize an answer

Over GF(2), the batch `[x=0, x=0]` is satisfiable, while `[x=0, x=1]` is
unsatisfiable. Only one right-hand-side bit changes. Even the closest nonidentical
coefficient representation can therefore have the opposite answer. Conversely,
invertible row operations can change many coefficients while preserving every
solution. Raw coefficient distance is not semantic equivalence or a guarantee
of low repair cost. Variable order and basis representation further affect it.

A safe pipeline is:

    exact cache -> on miss, feature-index shortlist
                -> validate source/interface and check repair
                -> if no repair succeeds, ordinary checked compilation

False positives must be rejected by the checker. A missed candidate loses reuse,
not correctness, because fallback remains available. The index is proposal state;
neither approximate neighbors nor distances certify SAT or UNSAT.

## Cost and maintenance conditions

For M indexed states and d features, the coordinate payload alone is O(M*d),
plus IDs, tree nodes and the reusable state. Building or rebuilding a balanced
index costs work; there is no unconditional logarithmic nearest-neighbor bound.
SciPy explicitly cautions that even around 20 dimensions its KD-tree may offer
little advantage over exhaustive comparison. Flattening our width-32 summary
envelope already gives up to 1,089 coefficient cells, before including a batch.
This makes raw-coefficient indexing a poor default hypothesis. A small descriptor
vector could behave differently and requires measurement.
[SciPy KDTree documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html).

The full expected expansion cost must include

    feature extraction + index query + maintenance + amortized rebuild
      + all candidate validation/repair work
      + probability(no accepted repair) * ordinary compilation.

To improve on ordinary compilation, the added overhead and unsuccessful attempts
must be smaller than the expected compilation work avoided. Budget the candidate
count and search effort so misses cannot trigger an unbounded sequence of repairs.
Measure hit probability against the candidates that actually pass checking,
not just the geometrical nearest-neighbor recall.

Partition by compatible width/interface and interpretation before searching.
Bind an index entry to immutable source IDs and the checked worker generation;
drop or mark entries when their underlying reusable state is evicted. A durable
feature entry is not evidence of native residency after restart. Rebuild from
validated sources, or independently revalidate retained entries. Source changes,
failed transactions and feature-schema changes must invalidate affected entries.
Never mutate coordinate storage behind a built index without its supported
update protocol; SciPy documents that this can invalidate search results.
[SciPy data ownership contract](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html).

## Experiment to run once checked repair exists

Keep exact hashing as the first stage. On misses, compare bounded linear scans,
simple feature buckets, support indexes and a KD-tree on the same candidates.
Start with cheap descriptors computed during existing decoding, such as row
count and support-density statistics; do not count precomputed elimination as
free preprocessing. Include colliding descriptors with different answers,
row permutations, valid small changes, incompatible boundaries, repeated and
fully novel structures, changing index size, eviction and cold reconstruction.
Vary d and report feature cost, index construction/update, candidate count,
verification, repair, fallback, total time, live memory and persistent bytes.

For the present 64-slot native cache, searching similar entries has no established
advantage. First implement and check a reusable repair operation, then evaluate
the indexing choice. This recommendation is an inference from our implementation,
not a KD-tree benchmark. It changes neither affine worst-case elimination bounds
nor the status of unrestricted SAT or P versus NP.

Foundational literature: Jon Louis Bentley, *Multidimensional Binary Search Trees
Used for Associative Searching*, CACM 18(9), 509–517 (1975),
[DOI](https://doi.org/10.1145/361002.361007). For nearest-neighbor performance under
clustering assumptions, see S. Maneewongvatana and D. M. Mount,
[*Analysis of Approximate Nearest Neighbor Searching with Clustered Point Sets*](https://arxiv.org/abs/cs/9901013)
(1999). Those geometric assumptions have not been established for our solver
states or for descriptors that predict repair cost.
