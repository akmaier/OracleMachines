# Validation and interpretation

- All 481 Python tests passed before timing. The benchmark runtime remains byte-identical to implementation checkpoint `836fb96`; the final validator checks this.
- Full, fresh and empty comparisons passed paired-answer, root/profile/summary, archive total and search-counter comparisons. All evidence digests and complete raw database hashes match within each pair. Fresh and empty discovery counters also match and have zero new trace reuse.
- All six compressed archives passed compressed/raw SHA-256 and size validation. Timed cold audits verified every stored node/source/residual, SQLite integrity and byte-preserving replay. Every seed row was checked unchanged.
- The unchanged Lean build passed 3,151 jobs; axiom audit: 4,148 declarations / 1,988 theorems. No new Python/SQLite refinement is claimed.
- The manuscript keeps all 63 previous proof blocks, with 223 unique labels. It builds without warnings; pages 126–127 were rendered and visually checked. The added empirical discussion is section 12.73.
- The new benchmark has no failed acquisition or audit to recover. The published fresh/empty controls are not independent holdouts, timings are single ordered comparisons, and sampled Python allocation is not RSS or full-history peak.
- Positive scope: exact prepared sources avoid fresh probe acquisition. Limitation: checking remains, the runtime difference is small, the fresh control regresses with zero reuse, and no storage or structural-coverage improvement follows.
