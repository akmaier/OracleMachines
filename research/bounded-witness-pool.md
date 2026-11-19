# Bounded automatic witness retrieval

The previous study supplied a donor model for one stopped source. This checkpoint
implements candidate retrieval without donor relationships or generator labels.
The optional `WitnessPoolSolver` remembers at most 64 distinct packed assignments
from checked native SAT publications. Before fresh residual search, it tries at
most four newest vectors with the same compact variable count. Every proposed
assignment must satisfy the complete target CNF and pass the existing native
witness verifier before publication. Misses leave the original search available.

## Correctness and scope

The vector coordinates are compact variable ranks. Equal variable count does not
establish a relation between two formulas, and the method claims no such relation.
It simply proposes an assignment. A complete satisfying assignment certifies SAT
for the target, regardless of where the vector came from. Failed candidates
establish neither UNSAT nor the absence of a useful older vector. UNSAT still
requires the existing independently checked proof. Malformed input is still
validated before the hook; empty formulas and empty clauses use the base path.

Candidates are disposable hints, not proof authority. A vector can remain after
a publication batch rolls back: using it on a later target still requires a full
check and native verification. Checked proof aliases retain the original rollback
invalidation. Reopening seeds hints from at most the newest 64 native payloads;
malformed hint records are ignored where decodable and cannot certify a target.
Archive validity is checked independently, including every retained UNSAT proof.

This mechanism supports valid CNFs generally but discovers no new tractable class.
It can shorten successful acquisition and subsequent proof storage. A hit still
counts one native expansion because that counter is incremented before the hook.
It does not perform the later descendant search that the witness avoids.

## Frozen comparison

Eight serial workers compare the existing 32-record publication policy with the
pool in opposite orders. Each split starts from an empty archive:

- Exposed: the preceding 108-query stream, scales 24/48/72.
- Holdout: 108 queries at separately frozen scales 30/54/78, using the same six
  generator designs and two samples, with base/edit/repeat variants.

The policy, limits, generators and tests were hashed before either split ran.
No outcome filtering or holdout tuning occurred. Each attempt permits 256 native
expansions, with budget exhaustion recorded as unresolved. This is a designed
size holdout, not evidence of performance on arbitrary or industrial SAT.

| Measurement | Exposed baseline | Exposed pool | Holdout baseline | Holdout pool |
|---|---:|---:|---:|---:|
| Mean query seconds | 2.66956 | 2.59017 | 4.16415 | 3.81977 |
| Mean complete worker seconds | 5.84894 | 5.59388 | 9.10327 | 8.27884 |
| Native expansions | 2,166 | 1,961 | 3,028 | 2,641 |
| Native proof records | 2,259 | 2,044 | 3,292 | 2,873 |
| Key/payload bytes | 12,128,848 | 11,569,416 | 18,942,841 | 17,050,525 |
| SQLite bytes | 22,851,584 | 21,524,480 | 34,770,944 | 30,937,088 |
| Checked cache graph plus pool bytes | 53,930,463 | 50,843,676 | 83,155,305 | 74,284,351 |

Mean query reductions are **2.97% exposed / 8.27% holdout**, with improvements in
both orders. Complete worker reductions are **4.36% / 9.06%**. Complete timing
includes setup, solving, candidate work, checking, persistence, append metadata,
retained-object measurement, warm replay, cold proof replay, cold solver
reconstruction, sidecars and compression. Preparation and posthoc audits are
separate. Two orders do not provide a statistical generalization guarantee.

Both arms return 70 SAT / 36 UNSAT / 2 unresolved attempts on the exposed stream,
and 64 SAT / 42 UNSAT / 2 unresolved on the holdout. The same case IDs stop within
each split. Original budget-stop observations remain unchanged. No new discovery
closure or recognition coverage is inferred from the lower acquisition cost.

The pool makes 32 / 30 successful residual checks from 2,369 / 2,388 candidates,
scanning 117,662 / 157,747 pool entries. Its conservative retained charge peaks
at **14,181 / 14,163 bytes**, with 64 vectors. Peak counts in the aggregate counters
are sums of per-query snapshots; the dedicated report fields are the actual maxima.
Checked graph size excludes SQLite, allocator and transient state. Process RSS
includes benchmark metadata and replays, so it is not an isolated solver bound.

Edits account for almost all saved expansions: **1,013 to 809** on exposed inputs
and **1,342 to 955** on holdout inputs. Base expansion counts are nearly unchanged.
Parity mixtures have zero hits and unchanged expansion counts; their first-order
query time rises from 0.5672 to 0.5919 seconds and 1.3061 to 1.3233 seconds.
Holdout graph-colouring also regresses in that order. Mean holdout warm time rises
from 0.04222 to 0.04286 seconds. All these measurements remain in the record.

## Cost bounds and cold reconstruction

Let L be the residual's literal count, C the entry cap, K the candidate cap and
V the admitted variable cap. In a word-cost model, a miss adds O(L + C + KL) work;
short-circuit checks can use less. A hit additionally materializes n Boolean
values, then incurs the unchanged full native check, encoding and publication.
Admission validates and packs a model in O(n) work; dictionary lookup, hashing,
eviction and resizing are additionally charged. Retained vector data is
O(C ceil(V/8)) bytes plus O(C) container/metadata words. Here C=64, K=4, V=4096.
Integer and encoding bit costs must be charged separately when varying limits.

These caps bound candidate state and per-residual proposal work, not the number
of residuals. Search, proof size, cumulative acquisition and total storage can
remain exponential. No uniform efficient construction covering arbitrary SAT is
established. Since the pool can alter later cache contents, saved work must be
measured over the complete matched stream, not summed from isolated opportunities.

Cold seeding reads 64 payloads: **278,521 bytes exposed / 191,476 bytes holdout**,
with roughly 1.8 / 1.7 ms seed time. The exposed tail contains no SAT candidates,
so its reconstructed pool is empty; the holdout reconstructs 33 distinct vectors.
Warm exact-root replay uses saved certificates and does not require these hints.
The current seed policy therefore does not preserve candidate availability across
restart. Its row bound also does not bound decoded payload bytes or transient RAM.

## Remaining priorities

1. **Reuse negative search across clause edits.** First-order pool runtime remains
   dominated by random 3-CNF and parity: 82.7% exposed and 83.6% holdout combined.
   The parity work receives no witness benefit. Investigate retained UNSAT cores
   with explicit clause dependencies: a core survives an edit only when its
   required clauses remain, or a new checked implication supplies them. Restrict
   discovery and dependency checks before claiming a total saving. Deletion must
   invalidate unsupported refutations; adding constraints preserves an existing
   refutation but can invalidate SAT witnesses.
2. **Persist useful candidates selectively.** The newest-row policy can lose all
   models after an UNSAT tail. A bounded SAT-only index could retain root vectors
   without an unbounded archive scan. Charge maintenance, durability, payload bytes
   and restart cost; compare against the frozen policy on another fresh split.
3. **Reduce failed probes and improve coordinate transport.** Same-count compact
   ranks are cheap but restrictive. Size buckets can avoid unrelated vector scans;
   checked variable correspondences or source bindings may recover more edits.
   Recognition cost, misses and verification must remain explicit. Blind probing
   already regresses on some families.
4. **Broaden structural discovery and evaluation.** Successful model reuse is not a
   semantic partition or compact interface construction. Mixed/shared interactions,
   scalable negative proofs and representative external workloads remain open.

The [checkpoint](../experiments/results/cnf-witness-pool/checkpoint.json) retains
all previous archives and appends new checked proof keys. When a trial produces a
different valid witness for an existing key, the authoritative old payload stays;
the alternative is preserved in its full trial archive. All 512 two-variable
clause-set CNFs are checked against truth tables and replayed independently.


## Verification and preservation

Both readers validate the union of 34,426 native records and every prior affine,
equivalence and discovery record. All 647 prior source fingerprints and 8,088
artifacts across 119 manifests remain unchanged. The union adds 3,285 native keys;
130 differing valid-payload observations retain their original trial archives.
Earlier 5,650 composed / 444 pilot decisions, 108 larger-stream observations,
624 inventory nodes and supplied-witness recovery are rechecked. The 864 timed
query observations retain exact committed deltas and original budget stops.

All 1,319 full / 150 focused tests pass; the exhaustive 512-formula audit yields
95 SAT and 417 UNSAT with independent cold replay. The full suite retains 44
SQLite ResourceWarnings at unchanged files; focused tests emit none. The
229-page manuscript builds without warnings and preserves all 64 proof blocks.
The initial audit used an incorrect nested key for the preceding recovery result.
Its source and failure log remain in `failed-audit/`; the corrected audit passes.
No timed worker was repeated or changed because of that validation error.
