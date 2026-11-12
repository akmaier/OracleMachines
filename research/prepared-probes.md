# Reusing analysis from unresolved prepared plans

After removing per-query residual censuses, the accounted 1,497-input run spends
81.41598 seconds in discovery. The 83 unresolved inputs consume 67.35991 seconds
(82.74%); all 1,414 closed inputs consume 14.05607 seconds. The 1,410 roots that
directly reference old closed plans consume 13.74019 seconds. A selected-proof
checker for closed plans therefore has a smaller immediate saving ceiling than
work that also addresses unsuccessful expansion. The source report is
`experiments/results/cnf-accounting-full/report.json`.

The optional `PreparedProbeInventory` uses information already read by exact
retained-plan lookup. If the old source-and-depth record is unclosed, its saved
probe trace can replace a new probe acquisition. The existing independent probe
checker validates it against the complete current normalized CNF and matching
settings. It checks source reasons, fixed points, learned implications and
continuations. Only then can the saved trace enter the ordinary new profile.
No old classification, closure summary or descendant graph is trusted from this
hint. Other recognizers, reductions and the current planning policy still run.

The pending hint lasts for one discovery call and is cleared on exceptions.
The existing bounded checked-probe cache can serve later local checks; this
extension adds no unbounded profile cache. The source and policy bind the reuse;
an edited source or incompatible settings require fresh work. Corrupted probe
evidence must fail checking. An old unresolved plan is never treated as UNSAT.

This is an acquisition optimization within the existing certificate contract,
like the existing checked-probe cache. It introduces no persistent node format
or configuration change. Old archives remain readable by the ordinary checker,
and matched tests require byte-identical key/payload records. Recognition,
decoding, checking, serialization, persistence and cold replay remain charged.
The initial experiment will compare prepared original inputs, the previously
published fresh controls and empty history. No coverage gain or general SAT
bound is claimed. The aim is to avoid repeating already-certified analysis
when an earlier overall attempt did not close the formula.
