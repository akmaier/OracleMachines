# Retained rejection by the raw two-CNF acquisition gate

The initial run binds 455 sources and completes the case-43 baseline. Its next
arm is rejected before acquisition because the absent projected cofactor has
ternary clauses. The gate behaves as specified; the failed attempt and log are
preserved. The cofactor actually has a unit-propagation refutation requiring
23 literal visits. The extended gate in `../cnf-conditioned-core-exposed/` reuses
that checked trace, completes all fifteen arms and independently validates exact
baseline parity with this run. No completed conditioned result is claimed here.

The manifest in the complete result directory covers this directory as well.
