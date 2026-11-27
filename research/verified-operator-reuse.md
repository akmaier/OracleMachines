# Reusing independently verified local projection operators

Checkpoint: 27 November 2026. A bounded, empty-at-start bank of checked local
operators reduces complete cost **10.37% versus the unchanged checker**, across
all five matched process orders. Reuse within a query alone saves **6.91%**;
sharing across a pass saves another **3.72%**. All certificates, verdicts and
stored evidence remain identical, with **180/182** structurally certified queries.
The pipeline is still **38.78% more costly than fresh solving** on this synthetic
panel. Production defaults remain unchanged.

This closes the measured repeated-operator verification gap from
[selective width expansion](selective-width-discovery.md). It does not enlarge
structural coverage or establish efficient arbitrary SAT. The two remaining roots
and their three coupled active-factor frontiers remain the coverage target.

## What is reused and what is checked

The new experimental checker in `cnf_verified_operators.py` retains every source,
policy, incident-factor, encoding, output-scope, terminal-verdict and root-witness
check. Its only shortcut is the exhaustive local row loop for an operator whose
complete immutable description has already passed that independent loop.

The key includes the support-reduction flag, pivot rank in the sorted local bag,
the sorted multiset of input scopes and complete truth tables, output-scope ranks,
output bits and the complete reconstruction-choice table. Input multiplicity is
retained. Exact tuple equality, not a hash digest alone, determines a match.
Different output representations have different keys and must be checked afresh.
Each coordinate map is rebuilt from the current occurrence; every active incident
factor must still be present and every factor comes from a checked earlier step
or a source clause.

A first occurrence is inserted only after all projection and choice rows pass.
For a hit, equality of this full description gives the same Boolean relation and
false-before-true witness choices in corresponding coordinates. Induction over
locally checked factors preserves the old checker’s soundness. A failed root may
have yielded valid local operators before its failure; those operators establish
no root verdict. The final source witness and all outer recomposition checks
remain mandatory.

Banks start empty, accept no persisted contents and are discarded between phases.
They retain at most **4,096 entries** and **4 MiB of conservatively counted key and
value objects**, evicting oldest entries when necessary. Dictionary infrastructure,
inputs, certificates and the interpreter are additional memory. The bound is not
a total-RAM bound. Tests exercise zero and small capacities; eviction changes
reuse opportunity, not the verdict.

A temporary adapter installs this checker only inside an isolated single-threaded
experimental call, restores the legacy function on exit and rejects nested or
concurrent/background use. It is not a production integration. Direct checker
calls use a trusted in-process bank created by this implementation; arbitrary
Python code capable of mutating its private state is outside the certificate-input
threat model. Certificates themselves cannot seed or mutate entries.

## Matched comparison

The experiment reuses the preceding **182-query frozen panel**, including 158
distinct normalized sources and 24 repeats. Acquisition, pair rounds, selective
width, structural certificates and fallback are unchanged. There is no new-panel
coverage claim. Labels never enter recognition.

Five cyclic process orders compare fresh solving; the unchanged checker
(`legacy`); the new checker with reuse disabled (`off`); a bank shared across
one query’s discovery/internal/explicit checking (`query`); and a bank shared
across all queries in a single phase (`pass`). Warm replay starts empty. Each of
two cold passes also starts empty, so neither reuses acquisition or warm state.

| Policy | Complete seconds | Discovery with internal checks | Explicit checking / fallback | Warm replay | Cold replay |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fresh | 8.90555 | — | 4.00181 | 0.15139 | 3.25626 |
| Legacy | 13.78908 | 5.07198 | 1.94878 | 2.03201 | 4.09000 |
| Off | 13.87626 | 5.06981 | 1.94635 | 2.06959 | 4.14608 |
| Query | 12.83622 | 4.56616 | 1.54549 | 2.00275 | 4.07964 |
| Pass | 12.35870 | 4.50848 | 1.50094 | 1.88609 | 3.81622 |

Pass-versus-legacy reductions are **9.94–10.85%** across the five pairs. The
uncached new implementation is **0.63% slower on average**, with mixed signs;
retain this overhead control. The much larger repeated-probe fraction does not
translate into the same fraction of runtime: source preparation, mapping,
recognition, table construction, other checks and persistence remain.

Complete time charges input, discovery with internal checks, explicit checks,
cache construction/lookup/insertion/size accounting/eviction, evidence/database
writes, warm/cold replay and compression. Startup, final report metadata, labels,
historical acquisition and independent audits are additional. Two independent
native readers audit fallback archives; JSON cold replay uses two passes of one
checker. The experiment does not measure a concurrent or persistent cache.

All structural modes retain the same **607,765 combined compressed SQLite/JSON
bytes**, including 577,137 JSON bytes, 61 fallback records and 1,068,073 diagnostic
bytes. Fresh uses 2,193,009 compressed bytes. Maximum observed RSS is 285,556,736
fresh, 130,744,320 legacy, 126,451,712 off, 127,336,448 query and 127,582,208 pass.
These are process observations, not evidence that adding a cache lowers memory.

## Verified work and the narrow transfer result

One cold pass checks 3,279 operator occurrences. The pass bank retains **1,325
keys**, conservatively accounting for **1,797,404 key/value bytes**, without
reaching either cap. A within-query bank peaks at 72 entries and 94,620
key/value bytes; sharing across a pass trades more retained state for reuse.
The pass bank avoids **288,484 of 730,144 table probes (39.51%)** and
**32,930 of 87,474 rows**. The query bank avoids 107,408 probes per cold pass
(14.71%). All other checker counters match the unchanged checker; skipped rows
and probes exactly reconcile the differences. Discovery and explicit checking
together avoid another **1,679,408 probes and 197,026 rows** with the pass bank.
This is now measured execution reuse, rather than the preceding opportunity census.

A separate audit excludes repeated source queries and counts only first local
occurrences against the first owner of each key. It confirms 100,948 matching
probes across distinct sources, but only **six nonconstant operator occurrences,
36 rows and 144 probes** match an owner with a different stored family label.
Another 1,232 probes cross labels through constant operators. The labels include
inherited generator/frontier descriptions; they are not disjoint semantic SAT
classes. This is a small local transfer result, not new nonconstant sharing of
whole residuals or evidence of broad transfer across SAT categories. Most savings
come from repeated checking within the existing programs and panel.

## Remaining gaps and the next experiment

1. **Coupled factor coverage.** `d-d-d-j06` and `d-d-k09` remain structurally
   unresolved. Their three previously checked active-factor frontiers still stop
   at width ten, and the saved width-ten diagnostic still certifies none before
   widths eleven/twelve. These widths describe one factorization/order, not an
   optimal-width lower bound. Next investigate exact factor descriptions,
   separators or conditioning with explicit recomposition. Wider tables alone
   have a demonstrated miss and an exponential cost.
2. **Repeated source preparation in checking.** Discovery/internal checking
   (4.50848 s) and cold replay (3.81622 s) remain the largest phases. An instrumented
   JSON cold pass calls normalization **5,449 times** and restriction **6,127 times**.
   Their cumulative profiled times are 2.1435 s and 1.0870 s in a 5.4325 s profiled
   run; cumulative costs overlap and instrumentation changes time. This identifies
   exact validated source/intermediate contexts as the next cost experiment,
   not a quantified runtime saving. Charge context construction, bindings and
   invalidation; cached results cannot justify their own inputs.
3. **General structural recognition.** These keys recognize exact locally ordered
   operators, not arbitrary signed permutations or semantic equivalence. Broader
   nonconstant reuse, external workloads and efficient unrestricted expansion
   remain open. A complete classification with an unresolved cell is not an
   efficient solution of every class.

## Validation and retained negatives

Sixteen new tests cover all 512 two-variable CNFs, seeded small cases, warmed-bank
mutations, exact local embeddings, memory bounds, cold starts, hook isolation and
full root replay with discovery disabled. All **33 focused and 2,401 full tests pass**. Existing unclosed-SQLite
ResourceWarnings remain in the full-suite log; no test deadline or assertion was
relaxed.
An independent truth-table audit checks **1,303 valid partial projection programs
on 692 CNFs**, repeats every valid program and rejects **6,515 mutations** of
relation bits, reconstruction choices, incident factors, coordinates and source
bindings with both old and new checkers. Full boundary scopes also exercise valid
nonminimal supports.

The first nonconstant-transfer test fixture used greedy discovery, which removed
degree-one leaves into constants. Its stricter assertion failed as it should.
The corrected fixture supplies explicit independently checked nonconstant partial
projections at different variable ranks. The algorithm was unchanged. The failed
log, test snapshot and earlier protocol are retained under `preflight/`, with
source mappings; this correction preceded every measured run.

All prior **237 manifests, 73,288 artifact entries, 1,300 scientific sources and
79 proof blocks** are preserved. Four scientific sources and one restricted
correctness proof are added. Resume
`experiments/results/cnf-verified-operators/checkpoint.json`, key
`verified_operators`. `analysis.json` records all controls and timing signs;
`transfer-audit.json` and `remaining-check-profile.json` record the narrow transfer
and remaining cost. Final checks are recorded in `checks.json`.
