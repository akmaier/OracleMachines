# Guard-guided probes inside ordinary search

24 November 2026. The live selector finds no additional completed inputs on the
eight exposed edits. Aggregate solve time increases 1.84%, with mixed per-case
results. Tracking alone costs 1.27% and preserves search exactly, so guard lookup
is no longer the main obstacle. The policy remains optional and experimental.

This policy uses saved conditional supports to select
a variable at an existing ordinary probe site. It removes the passive census's
event retention and duplicate canonicalization. A hint still gives no authority:
the unchanged native probe must establish a negative cofactor from a checked
cached proof, unit conflict or binary refutation. The opposite branch remains
an acquisition obligation.

## Implementation and controls

The source bank is copied at setup. Each query validates its templates and
checks exact support containment against the canonical target. A deleted source
clause makes the corresponding template ineligible. Eligible guards are compiled
once into immutable assignment pairs. At a probe site, the selector scans guards
until its query-wide check allowance is exhausted, stopping each guard scan on
an incompatible assignment or a second missing variable. Only a guard with one
remaining local variable can offer a probe. The first sorted variable/polarity
pair wins. This is a deterministic baseline, not an optimal ordering rule.

The coordinate tracker consumes the native canonicalization result, including
already prepared cofactor handoffs, instead of normalizing each visit again.
It records fixed source assignments when restriction is performed, carries
injections through canonical renaming, and accepts a component/subset transition
only when its clauses occur in the current parent. Unsupported transitions
disable hints. Pending bindings belong to their expansion and are released on
unwind, including native budget stops. There are no retained event graphs and
no repeated unit classification solely for tracking source assignments.

Full-source exclusion still does not imply exclusion of a selected clause
subset. The actual local probe and original proof checker therefore remain in
the authority path. On an inconclusive probe, the prepared handoff and ordinary
fallback continue unchanged. On a negative cofactor, the ordinary continuation
visits the opposite assignment and uses the existing split or model lift. No
new proof format or default solver change is introduced.

The fixed comparison uses all eight previously exposed origin/edit pairs and
four alternating serial repetitions of four arms:

| Arm | Coordinate tracking and bank checks | Probe variable | First polarity |
|---|---|---|---|
| Native | Existing solver | Ordinary frequency choice | False |
| Tracking | New tracker | Ordinary frequency choice | False |
| Variable | New tracker and guard matching | Guard offer when available | False |
| Guided | New tracker and guard matching | Guard offer when available | Guard's excluded polarity |

Variable is a polarity-order control. The initial selector is the same, but
different probe publication and later reuse may produce different subsequent
paths. Every worker restores the exact causal prefix immediately after its
origin. Neither the cumulative archive nor the separate census certificate bank
seeds search. All arms retain the 256-dispatch allowance and 2 MiB handoff cap.

Template loading/copying is charged to setup; validation, containment, matching,
coordinate maintenance, acquisition and publication are inside solve time.
Complete-worker time also includes restoration, retained-state accounting,
warm replay of newly retained native nodes, full native cold replay, result
serialization and compression. Imports, frozen-source hashing and case loading
are outside it. Earlier source acquisition/extraction and the final preservation
audit remain additional. Warm proof replay is not a second acquisition attempt
on an unfinished whole input.

## Result: cheaper tracking, no net selection benefit

All 128 trials stop at 256 native dispatches. The tracking control reproduces
ordinary counters and complete SQLite files exactly. Every native control also
reproduces the preceding census's native counters and six-table payload digest.
Each arm's four repetitions retain identical counters, certificates and archive
bytes. The following times average those four serial repetitions.

| Edit | Native solve, seconds | Guided solve, seconds | Change |
|---:|---:|---:|---:|
| 1 | 1.31444 | 1.29696 | -1.33% |
| 4 | 1.09665 | 1.08207 | -1.33% |
| 28 | 0.59299 | 0.65901 | +11.13% |
| 37 | 1.38101 | 1.38742 | +0.46% |
| 40 | 1.22554 | 1.22045 | -0.42% |
| 61 | 0.70069 | 0.72016 | +2.78% |
| 64 | 0.64732 | 0.67495 | +4.27% |
| 67 | 1.03399 | 1.09905 | +6.29% |

Across the eight workers, aggregate solve means are 7.99263 seconds native,
8.09408 tracking, 8.16963 variable-only and 8.14007 guided. Guided complete-worker
mean totals increase 0.77%, from 92.29653 to 93.00989 seconds. Full historical
cold replay and compression dominate worker timing; they are distinct from
ordinary append-only solver publication. These exposed comparisons establish
neither a representative general speedup nor a useful default change.

The guided arm chooses a guard offer at 148 of 676 probe sites, changing the
ordinary variable at 75 sites and trying True first at 76. It performs 33,379
guard checks and 94,683 pair inspections. These are events along the new path,
not distinct tractable SAT categories. In particular, the preceding census's
260 untried negative cofactors do not imply 260 useful steps on a changed path.

Guided native checked-cache bytes summed over the eight worker endpoints grow
1.68%, from 154,443,458 to 157,044,382. Banks add 248,919--402,579 charged bytes
per worker. Summed SQLite sizes grow 0.22%, from 719,503,360 to 721,055,744 bytes.
The bank measure excludes the retained canonical source snapshot and other
tracking fields; it is not total retained solver memory.
No event graphs are retained. Maximum pending tracking is 43,545 counted slots;
all pending bindings are released at return or budget stop. Neither tracking nor
matching reaches its cap, and no unbound-site misses are recorded. These facts
do not establish a whole-process memory reduction.

## Profile the largest regression before another optimization

After the fixed comparisons, an explicit adaptive rule selects edit 28, the
largest guided/native mean solve-time ratio. Separate query-only profiles repeat
both arms with identical native counters and archive bytes. Profile timings are
diagnostic and excluded from the comparisons above.

| Profiled operation | Native cumulative seconds | Guided cumulative seconds |
|---|---:|---:|
| Complete query | 1.61705 | 1.68949 |
| General normalization | 0.48695 | 0.50635 |
| Native certificate verification | 0.48482 | 0.49224 |
| Negative-child checking | 0.30940 | 0.31392 |
| Scanning restriction | 0.37384 | 0.37720 |
| Unit propagation | 0.18690 | 0.20618 |
| Guard choice | -- | 0.00188 |

These cumulative rows overlap and must not be added. General normalization and
restriction each also have substantially larger exclusive time than matching.
The guided run makes fewer general normalizer calls (679 versus 682) and fewer
unit-propagation calls (268 versus 271), yet both cost more in the profile.
Its native normalization literal visits rise 5.18%, native propagation visits
25.25%, and attempted proof-insertion bytes 4.83%, despite 358 rather than 363
insertion attempts. After the stop rolls back pending writes, retained new
native nodes instead increase from 347 to 357. Attempt counters and durable
growth must remain distinct. Larger/different residuals offset the selected exclusions. The
propagation visit comparison refers to the native counter; separately prefixed
probe counters remain in the raw results.

The next useful reuse experiment should preserve a fixed selection path and
test whether a surviving conditional certificate can be transported directly
to the actual local cofactor, avoiding fresh propagation over the full cofactor.
Start with `cnf_conditional_unit_support.materialize`; exact local support
containment, fixed assignments, source/name maps and unchanged native checking
are mandatory. Missing component clauses require fallback. This is a candidate,
not an established saving, and it leaves normalization/verification costs open.

Do not repeat the earlier broad memo experiment without new evidence:
[proof-normalization reuse](proof-normalization-reuse.md) gave modest mixed
benefits, [prepared cofactors](prepared-cofactors.md) regressed despite fewer
normalizations, and [ordered normalization](ordered-residual-normalization.md)
already implements a checked clause-order path. The live stack also already
uses direct canonical-certificate checking. A new proposal must identify its
additional reuse boundary and charge recognition and retention.

For broader coverage, investigate interactions among guards with more than one
unfixed assumption only after establishing useful local composition. Such a
census must distinguish a full-source exclusion from a valid component-local
one and leave all unresolved interaction explicit. Merely adding more offers or
an index for the now-small matching loop does not address the measured cost.

## Resource limits and remaining obligations

The query-wide allowance is 100,000 guard checks. At most one guard variable is
selected at each existing probe site; the original two-polarity probe mechanism
then applies. If the largest guard has length `g`, guard-pair inspections are
at most `g` times the number of admitted guard checks. Root support validation,
map construction, copying fixed assignments and the local proof work are
additional. These operation limits are not a bound on all computation.

Pending tracking is limited to 4,096 bindings and 1,000,000 counted slots.
Slots count literals, map entries and fixed-assignment entries, not bytes.
The caps exclude active frames, ownership lists, copied banks, verification and
construction transients. Retained checked-cache and bank sizes are measured
separately; process peak RSS includes preparation and cold replay. Sums of
per-case database sizes represent separate worker histories, not a simultaneous
memory requirement or the deduplicated cumulative archive.

All inputs are exposed and the origin banks are provisioned. Automatic origin
recognition, general variable transport, fresh unlabelled evaluation and a
uniformly efficient classification of arbitrary CNF remain open. Selecting more
locally provable exclusions need not find a whole witness or refutation sooner.
The independently checked proof boundary preserves correctness even when a hint
is unhelpful; it does not establish a runtime or storage improvement.

The first preservation-audit attempt compared an absolute profiler-source path
with its relative spelling and stopped before checking any trial archive.
Its source and failure log remain saved. The final audit resolves the paths and
still checks the exact source hash; this changes no benchmark or solver result.

The final audit checks both proof readers for every target/arm, verifies all
repeat and profile hashes, and preserves every previous six-table payload
byte-for-byte. The cumulative archive adds 812 native records, reaching 158,942;
the other five tables are unchanged. SQLite grows by 15,892,480 bytes to
2,081,153,024 bytes; compressed storage grows by 1,201,935 bytes to 151,177,096.
Validation takes 623.78731 wall-clock seconds, including 110.63378 seconds of
cumulative gzip creation; other correctness checks run during this audit, so
this is maintenance accounting, not an isolated timing comparison.

All 1,731 full tests and 87 focused tests pass. The full suite retains its 44
existing SQLite `ResourceWarning` reports; focused tests have none. The 258-page
manuscript builds without warnings and preserves all 64 previous proof blocks.
The sealed checkpoint binds 949 source files and 421 new artifact entries,
retaining 163 prior manifests covering 14,882 artifact entries. Resume
`experiments/results/cnf-guard-probe-selection/checkpoint.json` with
`experiments.cnf_archive_parts.restore_archive`.
