# Materializing a checked acquisition checkpoint

2026-11-15. The latest discovery sequence spends roughly 145 seconds reconstructing
its parent before about one second of local expansion. We now retain an optional
compressed copy of the independently reconstructed **current** checkpoint. This
removes repeated historical delta reconstruction while preserving the original
archives and the complete startup query. It acquires no additional SAT structure.

## What is reusable

The authority remains `cnf-retained-discovery/report.json`, SHA-256
`0d59f8bb3018c78b5da947a31d1a0d492103c15968df7d706b7ad1910b038f84`.
Its history contains **42,543 patterns / 781,606,912 bytes**, with evidence groups
**(1,42,156,69,1)**, two bridges and structural coverage **72/83**. Publication
first runs the unchanged authoritative restoration chain. It then binds the
entire closed SQLite file and a consolidated evidence sidecar to a descriptor.
The new experiment report authenticates that descriptor; a mutable cache manifest
alone is not an authority and a checksum alone does not prove a mathematical claim.

The cache contains two immutable, content-addressed gzip objects. Database bytes
include schema and triggers, so matching only the known row tables is insufficient.
A restored file is not opened by SQLite until its full byte hash matches. The
loader also checks parent identity, source fingerprints, options, every ordered
table digest, complete sidecar bytes and counts, bridges and the expanded positive
proof. Verification runs with zero admission budget. The destination is published
only after checking and may not overwrite an existing file. No Python verifier
cache is persisted. Exclusive ownership and a closed database without outstanding
WAL/journal data are preconditions; these APIs do not defend against a concurrent
raw-file attacker or make an untrusted descriptor authoritative.

Positive evidence establishes its claimed covered roots. It does not establish
the completeness of the unresolved frontier. Each measured arm therefore starts
a fresh canonical inventory, constructs the complete route catalog and queries
all 83 originals. Its flags, exact positive certificate and pending selection must
match the authoritative acquisition report. Both legacy controls reconstruct
independently with the frozen historical code, without using the seed or snapshot.

## Matched runtime and storage

Two repetitions reverse order: legacy/materialized, then materialized/legacy.
Fresh inventory objects are used for every arm in one Python process; process-global
and OS filesystem caches are not cleared. Tests finish before the producer.
Means in seconds:

| Cost | Historical reconstruction | Materialized checkpoint |
| --- | ---: | ---: |
| Reconstruction, identity and positive checking | 155.45916 | 9.94660 |
| Complete catalog, global query and serialization | 64.74772 | 64.49429 |
| Complete timed sequence | 220.33037 | 74.76157 |
| Separate post-timing byte/table identity audit | 0.75944 | 0.75742 |

Reconstruction decreases **93.60%**; the complete sequence
falls **66.07%**. Individual sequence samples are
**215.19881/225.46193**
versus **75.13042/74.39272**.
This is an observed saving on one retained development history, not an arbitrary-SAT
runtime bound or a held-out solver comparison. Intermediate historical checkpoints
are no longer reaudited on every fast load: equality to the independently checked
materialization replaces that repeated work. Both authoritative controls and all
four complete global queries pass with new discovery disabled.

The one-time authoritative reconstruction costs **150.88545 seconds**;
subsequent materialization and its extra checks cost **7.88791 seconds**.
Using observed complete-sequence savings, materialization from an already checked
history pays back after **one future reload**.
Charging an additional reconstruction solely to create the cache instead gives
**two future reloads**.
These are conditional amortization estimates, not guarantees about future machines
or workloads. The experiment's full pipeline, including preparation and four arms,
takes **752.89795 seconds**.
This full pipeline also includes descriptor/report serialization, post-timing
identity audits, orchestration and cleanup beyond the separately named phases.

The database cache occupies **87,129,428 bytes** and the
evidence cache **207,654 bytes**, a total of **87,337,082 additional
bytes**. The decoded evidence is **1,694,324 bytes**. A working database
still requires **781,606,912 bytes**. This does not reduce logical history size or
replace the original proof archives. Streaming compression and hashes use bounded
blocks, but sidecar parsing, catalog construction and retained proof objects still
consume memory. Peak RAM is unmeasured. All four arms retain the same current and
prepared checked-node counts: **20,472 and 2,916**, respectively.

## Resume and failure behavior

The final resume entry point also binds the historical validation ledger and checks
**all 125 historical implementation fingerprints**, including indirect helpers
absent from the immediate acquisition report. This guard costs **0.01286 seconds**
in a separate audit, in addition to the frozen matched table above. Its guarded
restore takes **8.43016 seconds** in that audit; this later observation does not
replace the matched reconstruction samples. Four extra regression tests cover
indirect source changes, ledger identity, parent binding and failure before loading.
The complete **299-test suite** passes.

The optional objects live under the ignored directory
`solver/.cache/materialized-checkpoints/<parent-sha256>/`. The small descriptor
and experiment results are committed; the full duplicate database is not. To
reproduce, use a fresh result directory and optional separate cache directory:

```sh
python3 experiments/compare_cnf_materialized_checkpoint.py /tmp/cnf-materialized-new /tmp/cnf-materialized-cache
python3 experiments/validate_cnf_materialized_checkpoint.py /tmp/cnf-materialized-new
```

For continuation, call
`experiments.cnf_materialized_resume.restore_checkpoint` on the new
experiment report. It returns the original acquisition report and its five
evidence groups, matching the previous restorer interface. Missing local objects
invoke the unchanged authoritative restorer; corrupt objects used by the fast
path are rejected. Cache loss therefore affects performance, not retained results.
An arbitrary descriptor may not be substituted for the report-bound one.

The unchanged next source is **19/77/261**, inside **case 1062 / retained index 14**.
Resume **`next_selection` and its pending split**, not the report's initial source
from completed case 1406. The selector's original-index list is empty; actual
scope comes from the already checked dependency path. Keep the eight interrupted
identities, whose re-entry is still charged. Reference evidence remains **5,488
nodes**, unchanged. Classification coverage and SAT decision remain different.

## Remaining costs

Complete startup checking still costs about **64.49 seconds**.
The immediate discovery choice is to retain that checked session across further
batches, then inspect whether case 1062's mixed reduction chains expose useful
shared nonterminal or exact boundary descriptions. No shared intermediate records
across the three previously touched scopes have yet been shown; only their
contradiction terminal was shared.

For a checkpoint with B database bytes, S serialized sidecar bytes and C compressed
bytes, snapshot I/O and hashing scan O(B+S+C) bytes, plus ordered table traversal,
positive verification and complete startup costs. Full decoding retains a B-byte
working database and the C-byte cache. Keeping a full snapshot at every expansion
would sum these costs over versions; eviction and cross-version compression are
open. This experiment keeps one checkpoint. The optimization does not bound the
number of discovery states, guarantee small separators or supply polynomial
construction for arbitrary CNFs.
