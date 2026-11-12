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
The matched experiment compares prepared original inputs, the previously
published fresh controls and empty history. No coverage gain or general SAT
bound is claimed. The aim is to avoid repeating already-certified analysis
when an earlier overall attempt did not close the formula.

For a matched source, let P be fresh probe acquisition, V admission checking of
the saved trace, and C/C' the later checks under the respective bounded-cache
states. The relevant comparison is P+C against V+C', in addition to common
recognition and lookup. There is no general inequality V<=P. Long traces, cache
eviction, no matching preparation or cheap fresh propagation can erase the gain.
`prepared_probe_attempts_reused` counts the original-pass attempts in the saved
trace; it is not a count of all continuation operations avoided. Certificate
read/parse work was already present in the baseline's exact old-plan lookup.

The implementation checkpoint passes all 481 Python tests. Tests cover failed
admission, source/settings changes, empty history, 512 exhaustive two-variable
CNFs, seeded larger inputs and byte-preserving cold replay. Full stored probe
evidence is still checked: selective validation of only successful OR-plan
dependencies remains a separate open problem.


## Matched results

Both modes use the accounted residual solver. On the 1,497 original inputs,
2,437 traces are reused, of which 2,414 occur inside the 83 still-open input
expansions. Original-pass reused attempts number 15,454; including continuation
work, total fresh probe attempts fall 77,804 -> 60,972 (21.63%). Verified attempts
remain 77,498. New check-cache admissions rise 11,339 -> 11,340, while lookups
rise 22,492 -> 24,929 and hits 11,153 -> 13,589. This explains why less acquisition
does not eliminate the independent checking cost.

Discovery time is 79.80360 -> 78.51427 seconds (1.62%) and total query time
85.97296 -> 84.07622 seconds. Open inputs account for 66.09933 -> 64.72515 discovery
seconds; closed inputs 13.70427 -> 13.78912. The unchanged ordinary solver also
varies in timing, so not all total variation is an acquisition saving. These
single ordered comparisons establish no stable small speedup. Cold audits cost
77.21884 -> 76.58480 seconds; warm combined replay 0.59213 -> 0.58386 seconds.

Both final databases are byte-identical, at 629,280,768 bytes, and retain all old
rows. Six-case peak Python allocation is 24,164,349 -> 24,199,805 bytes, excluding
native SQLite, RSS and full-history peak. No storage or memory reduction follows.
The 96 published fresh-input controls reuse zero traces: discovery worsens
6.44922 -> 7.07650 seconds and total 7.70214 -> 8.61204. Empty history also has
zero reuse, with total 7.59890 -> 7.43109. Both controls retain 88 closures and
identical discovery/search counters; their variation cannot support the mechanism.
They are not independent holdout data. The option remains experimental.

The [full report](../experiments/results/cnf-prepared-probes-full/README.md),
[fresh control](../experiments/results/cnf-prepared-probes-fresh/README.md) and
[empty control](../experiments/results/cnf-prepared-probes-empty/README.md) retain
all inputs, results, hashes and six complete archives. The unchanged Lean audit
passes (4,148 declarations / 1,988 theorems), and the manuscript's 63 earlier proof
blocks remain unchanged. This is tested Python evidence reuse, not a new Lean
refinement. The next gap is shared checked intermediate work and transport beyond
exact sources: 83 original sources / 99 selected leaves / 31,203 literals remain
unresolved under the optional prepared policy.
