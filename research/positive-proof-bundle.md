# Reconstruct only the data needed by the selected positive proof

The existing 58-root positive proof can now replay without restoring its archive
lineage. A self-contained data bundle carries its source claims, configuration,
ordered proof, all five evidence lists and every SQL record read by the hybrid
checker. In two matched repetitions, mean cold process time falls from
**23.95282 to 3.03614 seconds (87.32%)**, including preparation and verification.
This saving applies when the bundle already exists; its production is accounted
for separately below. Coverage remains **58/83 reused development inputs**.

The subsequent [source-local expansion](source-local-expansion.md) adds a separate
ordinary-frontier path backed by full authoritative history. It does not repurpose
this positive-only bundle as a complete discovery store.

## Capture dependencies, then check them independently

`cnf_positive_bundle.py` wraps both inventory views' shared connection during a
fresh positive replay. It allows only the existing exact-key `SELECT payload`
queries on six fixed tables. Scans, writes, other tables and malformed parameters
are rejected. It records the exact returned key/payload pairs, rejects a changed
payload on a repeated read, and requires empty historical checking caches so
prevalidated nodes cannot hide dependencies. The connection is restored even if
checking fails. The producer saves a JSON value snapshot rather than retaining
mutable references to its inputs.

The consumer takes the intended source formulas and configuration separately.
It checks that claim against the bundle, imports records into a new temporary
database with a fixed schema, enables read-only SQL, and reruns the existing
hybrid positive checker. Its captured reads must match the supplied SQL records
exactly: a missing premise fails, and an unused SQL row is rejected. Duplicate
identities, extra tables, altered sources/configurations and a scope other than
`positive-proof-only` are rejected. A file digest is not a semantic premise.

This is an operational sufficiency check, not a proof of minimum bundle size.
Every SQL row is used, but the positive checker validates only the fields needed
by its selected semantic rules unless the original historical validator is
required. All five evidence lists are retained, including unused sidecar records;
their inclusion does not certify every unselected proposal. Historical-policy
validation still checks the same **471 nodes** across both configurations.

The API returns verification metrics and closes/deletes its temporary database.
It does not return a partial inventory for discovery. The serialized bundle also
contains no source-archive or lineage path. Consumer trials run in fresh Python
processes outside the repository's working directory, with lineage restoration
patched to fail. They use only the bundle, a separate requested-claim file and
the installed checker code. Thus the data is self-contained; the checker code
and Python runtime are still required.

## Included records and storage

| Table | Rows |
|---|---:|
| Pattern nodes | 2,797 |
| Probe windows | 42 |
| Probe continuations | 32 |
| Pivot trials | 4 |
| Coupled trials | 3 |
| Growth trials | 1 |
| **Total** | **2,879** |

The 2,797 pattern rows include the 2,748 graph steps and 49 further historical
dependencies. The **82 external-record rows** include direct trace references
as well as the selected route loader's cached records. Capturing only that
loader's maps would therefore be an insufficient dependency accounting method.
The sidecars retain **(1 rewrite, 42 learned bases, 156 augmented blocks,
11 splits, 1 affine family)** and occupy **932,621 logical JSON bytes**.

The entire bundle is **40,108,276 JSON bytes / 3,169,051 compressed bytes**.
It includes the proof and original requested formulas, so these sizes cannot be
compared with the earlier graph-only compressed size as if they represented the
same data. Its reconstructed SQLite database is **40,538,112 bytes**, versus
**770,338,816 bytes** for full history, a **94.74% reduction in temporary database
size**. This is not a peak-RAM measurement. Decoded JSON, the proof, sidecars and
checker caches still occupy memory.

The original **770,338,816-byte / 41,758-node** archive is byte-identical after
production and remains preserved with every old result. The new bundle adds
persistent storage; it does not delete or compact the historical archive.

## Matched cold costs and production cost

Both modes use fresh processes and the same sources, options, proof, semantic
checker and five evidence lists. Execution order is full/bundle, then
bundle/full. Both bundle trials retain the same 471 historical checks and all
2,748 positive steps. Operating-system caches are shared, and two repetitions
provide no confidence interval. No tests or builds ran alongside timing trials.

| Mean measure | Full-history path | Bundle path |
|---|---:|---:|
| History restoration and verifier preparation, seconds | 21.00323 | 0.07054 |
| Bundle file loading/decompression/JSON parsing, seconds | Included in full preparation | 0.07221 |
| Semantic replay, seconds | 2.71937 | 2.70359 |
| Worker operation including accounting and cleanup, seconds | 23.80923 | 2.91658 |
| **Complete process wall time, seconds** | **23.95282** | **3.03614** |

The bundle preparation figure excludes its separately listed file loading.
Process wall time includes Python startup and all worker work, and is the main
comparison. Its two full samples are **23.93237 / 23.97327 seconds**; its bundle
samples are **3.10332 / 2.96896 seconds**. Replay time itself is essentially
unchanged. This addresses repeated cold preparation rather than a new semantic
checking optimization or the earlier warm-replay regression.

Producing the first bundle still requires **20.82422 seconds** to restore history,
**2.78123 seconds** to replay/capture/copy its dependencies, and **1.53465 seconds**
to serialize, compress and write the bundle. Integrity checks and diagnostics
also remain in the complete study's **80.64054 seconds**, which includes the
producer and all four consumer/control processes. Do not attribute the 87.32%
consumer saving to the first production or to an entire SAT expansion pipeline.

## Validation and remaining gap

New tests cover independent retained-plan replay, value snapshots, deletion of
every required small-fixture row, missing branch occurrences, corrupted source
and retained references, missing external evidence, duplicate identities, changed
claims, invalid scope/schema, unused SQL rows, changed repeated reads, denied
scans/writes and connection restoration on failure. The experiment also confirms
identical source-archive bytes and table digests and checks all selected roots
with fresh discovery disabled.

All **139 relevant tests** pass. Seven additional checks mutate the full real
bundle: deleting a consumed row from each of its six tables, and deleting a
selected learned antecedent. Each fails semantic verification without using a
file-hash mismatch as the rejection mechanism. The manuscript builds to 150
pages with no overfull boxes or undefined references; all 64 existing proof
blocks are byte-identical, and all four preceding artifact manifests match.

The next integration needs the **actual open-frontier dependencies**. This bundle
proves only the selected covered roots. It cannot answer which other routes were
tried, whether a probe stream is exhausted, or whether a missing recognition
state is novel. Treating absence as negative evidence would be incorrect. Extend
a separate partial working state only with explicit completeness/admission
contracts and preserve its deltas against full history. Until then, discovery
continues from the full checkpoint, and warm replay retains its earlier tradeoff.

The unchanged **23-variable / 93-clause** leaf remains the coverage target:
ordinary candidates **7, 9, 16, 17** versus saved pairs **5, 6, 11, 13**, under a
shared admission allowance. No new tractable family, SAT answer, Lean refinement
or bound on constructing compact proofs for arbitrary CNFs follows from this
data packaging improvement.

## Reproduce and resume

Produce and compare with:

```sh
python3 experiments/compare_cnf_positive_bundle.py OUTPUT_DIRECTORY
```

To independently replay existing data, pass absolute paths to the saved bundle
and the separately reviewable claims file:

```sh
python3 /Users/maier/Documents/code/OracleMachines/experiments/compare_cnf_positive_bundle.py \
  --worker bundle \
  --input /Users/maier/Documents/code/OracleMachines/experiments/results/cnf-positive-bundle/positive-bundle.json.gz \
  --claims /Users/maier/Documents/code/OracleMachines/experiments/results/cnf-positive-bundle/claims.json
```

Results are under `experiments/results/cnf-positive-bundle/`. This is a positive
verification artifact, not a discovery checkpoint. Resume discovery from
`experiments/results/cnf-reused-branch/report.json` using
`continue_cnf_reused_branch.restore_checkpoint`, preserving the five full
evidence lists and all earlier sidecars.
