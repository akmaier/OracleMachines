# Indexed proof context and upgrade preservation

Runtime checkpoint: `580e331`. The earlier source-update timing study is unchanged.
This follow-up is a correctness and operation-count diagnostic, not a new timing
comparison or a claim that the general factor solver now has local provenance.

## What changed

The negative checker builds a hash-set index of active source identities, then
probes it for the proof leaves. `contextSubsetRun_exact` proves exact equality
with the previous list-membership condition, including duplicates and ordering.
`contextProbe_value`, `contextProbe_bound`, and `contextSubsetRun_budget` connect
the actual costed reference to that check and bound its membership probes by the
leaf count. The native reply and Python ledger expose index entries and probes.

For A active entries and D proof leaves, this requests A insertions and at most
D membership probes. It does not bound hashing, string comparisons, collisions,
allocation, or the full evidence traversal by a machine-level constant.

| Chain edges | Proof leaves | Index entries | Probes | Tripled-list entries | Tripled-list probes |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 34 | 34 | 34 | 102 | 34 |
| 64 | 130 | 130 | 130 | 390 | 130 |
| 128 | 258 | 258 | 258 | 774 | 258 |

All nine context checks have their expected acceptance result. Deleting one proof
assumption rejects the previous negative proof. Removing the end constraint from
the formula produces SAT in each case; selecting the old branch remains UNSAT.
The diagnostic's old-list comparison count is calculated for a complete unique
context, not measured from an old executable. No timing speedup is inferred.

Saved source versions can now cross checker namespaces. The new engine checks
archived source nodes and computes its own answer before adding a current row.
A regression deliberately flips older verdict bits and confirms they are ignored.
A source-ID index supports older-namespace lookup; warm current-engine lookups
continue using the existing composite primary key. Replay and index space are
charged separately; an upgrade is not a warm local edit.

Initialization cleanup now covers database configuration, migration, and later
service setup failures. Failure-injection tests verify closed handles and retained
history. Two test-owned SQLite connections now explicitly close as well.

## Evidence and reproduction

The full suite passes **144 tests**, without resource warnings. The Lean audit
passes **2,290 declarations / 1,113 theorem declarations**, without admits or added
axioms. Exact logs are in `tests.log` and `lean-build.log`.

```sh
python3 -m unittest discover -s solver -p 'test_*.py'
python3 experiments/check_context_index.py --output /tmp/oracle-context-new.json
```

`diagnostic.json` preserves all counts, phase metrics, labels, source fingerprints
and the compiled-engine hash. `preservation.json` records an ignored local SQLite
backup, verification of 355 older generic inputs, and checked adoption of all five
older source versions. Every old row in all 21 existing tables remains present;
there are now 4,970 generic results and 1,548 refutations. All 135 previously tracked
experiment files retain their hashes. Historical source rows remain intact under
their old checker namespace; the current engine has additional checked rows.

Remaining priorities are global variable-ID/source-compilation refinement,
reference-count and eviction invariants, general row/equivalence-store invariants,
compact general input encoding, and full resource/accounting guarantees. The
source update family still assumes a supplied adjacent-block partition. Learning
and unrestricted SAT performance claims are not established by these checks.

`source-study-recheck.json` revalidates the frozen earlier inputs, all 1,824
answers, counts, lifecycle arithmetic, and 73 tracked source fingerprints from
`f29aef0`. The current binary differs, as expected after this follow-up. This
historical-data check does not claim to have rerun the old executable. Run it with:

```sh
python3 experiments/validate_source_updates.py experiments/results/source-updates --source-ref f29aef0
```
