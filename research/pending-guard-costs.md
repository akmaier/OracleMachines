# Price pending proofs before expanding through another guard

The six pending matches from the previous guard experiment have very different
costs. Only current **case 85** has a smaller publication footprint than fresh
solving. Its checked unit-conflict proof yields a support without visiting any
child proof. This gives a useful next recognition target: **terminal conflict
proofs**, rather than all pending supports or all proofs labelled `units`.

## Controlled historical probes

Each arm restores the exact persistent payloads immediately before its first
query in `cnf-alternative-guard/alternative-0`. Later query results are excluded.
The baseline replays the ordinary first-target miss and bounded guard selector;
candidate arms then derive one of the six previously diagnosed alternatives.
Every arm opens a cold live checker. This reproduces the persistent prefix, not
the original stream's warm proof cache or extractor memo tables.

| Case / pending support | Fresh expansions / rows | Derived rows, including target | Origin nodes visited | Added payload: fresh / derived |
| --- | ---: | ---: | ---: | ---: |
| 23 / causal 162 | 11 / 11 | 35 | 21 | 21,057 / 23,045 |
| 85 / causal 4 | 6 / 6 | 2 | 1 | 11,350 / 1,805 |
| 103 / legacy 116 | 1 / 1 | 12 | 7 | 2,012 / 10,937 |
| 103 / legacy 117 | 1 / 1 | 12 | 7 | 2,012 / 10,978 |
| 103 / causal 87 | 1 / 1 | 12 | 7 | 2,012 / 7,547 |
| 103 / causal 98 | 1 / 1 | 12 | 7 | 2,012 / 7,956 |

All six derivations use **zero fresh SAT expansions**. They still traverse,
normalize, check and publish proofs. Case 23 publishes 34 derivation rows and
one target row; case 85 publishes one of each. Every case-103 alternative
publishes 11 derivation rows and one target row. The smaller causal supports for
103 reduce payload relative to the legacy supports, but require the same seven
origin visits and twelve publications. Clause count alone does not price reuse.

Case 85's added payload is **84.10% smaller**. Case 23's is **9.44% larger**, even
though its row count more than triples: rows have different sizes. The four
case-103 alternatives add **275.10–445.63% more payload** than fresh solving.
Payload here is the sum of identifier and ASCII JSON lengths. It excludes
SQLite page overhead, indices, checker state, Python objects and other retained
artifacts; it is not a peak-memory measurement.

One timing sample per arm is diagnostic only. For case 85, derivation,
publication and child lookup together take about 0.00173 seconds versus 0.00755
seconds for baseline child solving. Preparation takes about 0.72–0.90 seconds,
and full cold proof/query and lineage replay about 4.91 seconds in both arms.
These different phases, cold caches and unpaired samples establish no total
speedup. All phase measurements remain in the reports. Input selection, earlier
acquisition, experiment reconstruction and independent validation are separate
costs. The probe does not measure peak RSS or downstream stream interactions.

## A restricted publication bound

For a checked negative origin whose certificate has kind `units` and a non-null
`conflict`, the current causal extractor makes no recursive extraction call.
It slices the checked trace, constructs the required clause subset, and either
uses its existing certificate or publishes one core row. The ordinary checked
subset rule adds at most one target row. Thus **one selected terminal origin
requires at most two new proof rows**, without fresh SAT search.

This is a bound on publications, not constant time or bytes. Reading and checking
the origin, slicing its trace, canonicalizing the core, matching candidates,
serializing certificates and checking the target still cost work. An arbitrarily
long trace or large formula is not bounded by the two-row claim. A `units` proof
that delegates to a child is not terminal: all six origins here have kind
`units`, but only case 85 has a conflict at that origin. The others enter larger
proof graphs. Sixteen synthetic chain/irrelevant-unit combinations exercise the
two-row bound and independent cold replay; they supplement the code argument.
There is no new Lean theorem or unrestricted SAT bound.

## Preservation and validation

All nine arms retain exact proof deltas and query records. The deltas total
**101,284 bytes**, avoiding nine duplicate complete databases. Reconstruct an arm
from the bound initial archive, the historical append prefix and its delta.
All three baseline deltas match the original stream's proof payloads exactly.
Every candidate checks its original guard, a genuinely absent support root,
containment, the derived certificate and the resulting query answer.

Independent replay checks every reconstructed proof, all nine queries and both
full eight-catalog support lineages. The durable union preserves all **20,270**
earlier payloads and adds **70** keys, reaching **20,340**. It occupies
**63,578,112 SQLite / 4,714,800 gzip bytes**. Three alternative certificate
occurrences for one case-103 target remain in their individual deltas; the union
keeps its first certificate. All **2,765** inherited decisions pass replay.
These are already-known source queries, so the probe claims **no fresh coverage**.

The first validator stopped on a reused temporary filename. Its source and
failure log are preserved. `check_cnf_pending_guard_deltas.py` corrects that
reconstruction-path bug; no measured worker or measurements changed. The new
checker, attribution tool and cost-bound test are post-hoc validation sources.
The 32 relevant tests pass with ResourceWarnings enabled and no warnings.

Resume `experiments/results/cnf-pending-guards/checkpoint.json`. All prior
semantic fields remain unchanged; `pending_guard_probe` records this diagnostic.
The separate historical case-121 archive remains preserved through its previous
bindings. Structural authority remains 2,614 patterns / 259 pairs, original
17/24 coverage with 999 steps, and separate supplemental 24/24 with 208 steps.

## Next investigation

Evaluate a terminal-origin filter for pending alternative guards on fresh inputs
excluded from the retained union and earlier decisions. Recognize the actual
checked conflict form; do not accept an index label as a proof. Charge candidate
enumeration, origin checking, repeated guard selection, derivation and full
persistence/replay. Keep case 23 and the one-expansion case 103 as regression
controls against indiscriminate materialization. Their now-retained derived
proofs are available to future queries, but their historical acquisition costs
must remain in amortized accounting.

For recursive origins, the remaining question is how to estimate and share the
affected derivation graph before publishing it. A smaller clause core does not
by itself imply a cheaper derivation. Full cold replay also remains a dominant
complete cost. Neither this terminal rule nor the larger accumulated archive
establishes a minimum-cost decomposition or polynomial solution for arbitrary SAT.


Prior preservation checks confirm **403 sources / 4,467 artifacts / 78 manifests**
unchanged. The new validation ledger binds 408 sources. Retained ready/pending
counts are **128/42 original, 134/73 legacy, 71/105 causal and 71/132 optional
expanded causal**, with all four complete lineage checks passing and no new
origin acquisition. The manuscript builds to 202 pages with all 64 existing
proof blocks unchanged.

New manifest: **46 artifacts**. Next preservation audit: **4513 artifacts / 79 manifests**.
