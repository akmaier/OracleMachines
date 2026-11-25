# Probe strengthened B4 banks with fresh, resumable bindings

Checkpoint: 25 November 2026. The first 64 B4 assumptions expose **69 checked
failed probes in 13 of the 29 open events**, but no direct refutations. Coverage
therefore stays **217/246**. Probing only the 19 changed bank/closure pairs finds
the same failures on this sample and avoids **640 assumptions**. Measured
discovery time falls 4.63%; complete census time falls only 2.02%. Reconstruction
and provenance checks still dominate. These small timing differences are
descriptive, not a general speed guarantee.

## Exact discovery and reuse contract

The [previous feedback pass](cursor-feedback.md) turned checked B3 failures into
B4 exclusions. Nineteen open closures changed; ten did not. A candidate that
was open on B3 may fail on B4. The new experimental cursor starts a fresh order
on the actual B4 residual, and never uses the B3 completed list to skip a B4
candidate. The old cursor remains part of the checked provenance of B4.

The cursor binds exact source, B4 bank, closure including trace order, candidate
order, trace bound and policy version. It records completed assumptions and
clause-indexed failed unit proofs. Reload reconstructs the deterministic order,
checks every failure, and resumes the next untested assumption. A failed
assumption promotes its complement; an interrupted attempt is not completed and
is retried. A saved B3 cursor, changed closure, altered source, trace allowance
or policy invalidates reuse. Equality is checked on full content, not just a hash.

If unit propagation under literal `l` reaches a checked contradiction, B4 entails
`not l`. The transported trace first replays the checked unconditional B4
closure and then the residual trace with original clause identifiers. The earlier
layers remain separately checked; no B4 proof is flattened into B0. Two opposite
failed assumptions suffice to refute the bank. None occurred in these trials.
The 69 individual failures are useful consequences, not whole-root native
certificates. No native record or cumulative solver table was added.

The `changed` policy checks exact B3/B4 bank equality and closure assignment
equality, then skips matching pairs. It is a scheduling heuristic. A test retains
an unchanged-bank example that this policy skips while `all` refutes it. All
29 control runs stop at the 64-probe bound, not at exhaustive search. Even a
completed candidate order establishes neither SAT nor general exhaustion.
Claims of formerly open probes are trusted scheduling data: forging them can
lose coverage, but supplies no proof axiom or SAT certificate.

## Matched costs and persistence

Both methods run twice in opposite orders in isolated processes per target,
including all 29 cases. Source-prefix reconstruction, all earlier preparation,
recognition, search, JSON serialization/reload, semantic verification and report
writing are charged. Startup/input loading, historical acquisition, final audit
and any future general fallback are additional. This is an exposed corpus,
not a holdout. Each searched event permits 64 assumptions, 262,144 propagation
occurrence visits and 256 proof steps including the closure prefix.

| Summed per-target means | All 29 | Changed 19 |
| --- | ---: | ---: |
| Source-prefix reconstruction (s) | 0.58882 | 0.58238 |
| Discovery including preparation (s) | 0.21477 | 0.20481 |
| JSON persistence/reload (s) | 0.01024 | 0.00951 |
| Semantic cold verification (s) | 0.19212 | 0.19027 |
| Complete census (s) | 1.01278 | 0.99228 |
| Standalone cursor/result bytes | 391,534 | 272,483 |
| New assumptions | 1,856 | 1,216 |
| Per-probe initialization clause visits | 719,232 | 446,400 |
| Propagation occurrence visits | 85,842 | 66,479 |
| Checked new failures | 69 | 69 |
| Peak process RSS (bytes) | 96,387,072 | 96,468,992 |

Avoiding ten searches saves 34.48% of assumptions and 30.41% of standalone
cursor/result bytes. No peak-memory improvement is observed. Eight searched
events regress slightly in discovery timing; their measurements remain in
`analysis.json`. Both policies still construct exact bindings and validate the
old provenance on all cases. The combined discovery counters include inherited
B3 work: for example, reused-completed counts cannot be interpreted as only
new B4 cursor hits. A test initially assumed that and was corrected to compare
the additional resumed history against the initial preparation count.

The cumulative open-state export grows from **989,481 to 1,379,665 bytes**.
It preserves all old fields and the full measured control history for every
case, including the ten skipped by the selected policy. Those ten cursors were
acquired by the charged control arm, not for free by `changed`. A separate
273,467-byte selected-results export retains target/event envelopes. Historical
artifacts and repeated trial files remain preserved, so standalone cursor size
reduction is not a claim that total repository storage shrank.

For a residual with C clauses and L literal occurrences, occurrence-index
storage is O(C+L), plus assignments and trace. Q attempted probes still initialize
clause state, costing O(QC) in addition to at most W charged occurrence visits.
Preparation, exact binding and proof verification are extra. A cursor retains
O(Q+FT+L+H) word slots for Q completed assumptions, F failed proofs with at most
T steps, exact bank/source content and closure/history size H; byte costs also
depend on encoded identifiers. Bounded visits alone do not bound total work,
and repeated layers or arbitrary streams have no finite lifetime bound.

## Validation and next step

All **1,969 tests**, including **104 focused tests**, pass. The new tests check
cold split-versus-single equality, promoted complements, work/trace interruption,
old-bank invalidation, malformed proof/history rejection, the skip counterexample,
all subsets of the four non-tautological binary clauses on two variables, and
generated small formulas checked against complete truth tables. The audit
rechecks all 116 persisted results, 1,094 prior source fingerprints and all
26,679 artifact entries in 192 parent manifests. All 64 old manuscript proof
blocks remain byte-for-byte unchanged.

**Next coverage target:** compose the 69 new B4 failures in the 13 affected cases
as one checked feedback layer, with decreasing proof dependencies and the
[bounded direct-unit compiler](direct-unit-closure.md) retained as the measured
certificate baseline. The other 16 cases need later candidates or stronger
interaction; the preserved control cursors allow continuation beyond this prefix.
Repeated reconstruction/preparation is still the dominant avoidable runtime cost.
No improvement in unrestricted SAT complexity follows from these finite results.

Resume `experiments/results/cnf-b4-probe-cursor/checkpoint.json`, especially
`b4_probe_cursor.remaining`. Reproduction: run `prepare`, `run_census` with
`experiments/compare_cnf_b4_probe_cursor.py`, then `validate` and, after tests and
manuscript checks, `seal` with `experiments/validate_cnf_b4_probe_cursor.py` on a
fresh output directory containing the preserved pilot and source snapshot.
