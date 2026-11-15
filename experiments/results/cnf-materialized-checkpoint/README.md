# Materialized checkpoint comparison

An optional local snapshot reduces reconstruction plus complete startup from
**220.33037 to 74.76157 seconds
(66.07%)** in two reversed-order comparisons.
All four outputs have identical database bytes, logical tables, evidence,
coverage certificates and next selections. Coverage remains **72/83**, with no
new discovery or reference nodes. See the [research account](../../../research/materialized-checkpoint-reuse.md).

The cache adds **87,337,082 bytes**. Materialization from a checked history
costs **7.88791 seconds**; its separate authoritative reconstruction
costs **150.88545 seconds**. Neither is free. Full pipeline time
also includes descriptor/report serialization, identity audits, orchestration and
cleanup beyond the named timing fields. All arms use one Python process with fresh inventory objects; process-global and
OS caches are not cleared. The complete historical source-ledger guard is measured
separately in `wrapper-replay.json`, after the frozen matched benchmark. Peak RAM and eviction over many versions remain open.

The compressed cache objects are optional and ignored by Git. The committed
`snapshot-descriptor.json` is bound by `report.json`; it is not an unauthenticated
trust bit. Source fingerprints, full database bytes (including schema), all table
digests, sidecar bytes, bridges and the positive proof are checked on reload.
Every measured arm also reconstructs the complete catalog and global frontier.
Two legacy controls independently use the unchanged authoritative restorer.
`wrapper-replay.json` separately verifies the continuation entry point with fresh
recognition and historical fallback forbidden. Missing cache objects use the
original restorer; corruption on the fast path is rejected.

Reproduce from the repository into a fresh output directory:

```sh
python3 experiments/compare_cnf_materialized_checkpoint.py /tmp/cnf-materialized-new /tmp/cnf-materialized-cache
python3 experiments/validate_cnf_materialized_checkpoint.py /tmp/cnf-materialized-new
```

Do not overwrite these frozen results. `comparison-summary.json` gives all samples,
means, disk costs and conditional amortization estimates. The 299-test suite passes,
including sixteen new snapshot and source-ledger tests. All **2,251 earlier artifacts /
39 manifests**, all **125 earlier implementation fingerprints**,
and the **5,488-node reference archive** remain unchanged. The manuscript builds
to **170 pages**, preserving all **64 existing proof blocks**.

Resume with `experiments.cnf_materialized_resume.restore_checkpoint`
and this `report.json`, or the existing acquisition restorer. Both return the
unchanged `cnf-retained-discovery` acquisition report and all five evidence groups.
Use **`next_selection` plus its pending split at 19/77/261**, within **case 1062 /
index 14**. The selector's original-index list stays empty; its checked ancestry
supplies the scope. Preserve **eight interrupted inputs**, evidence
**(1,42,156,69,1)** and **two bridges**. This experiment does not resolve any of the
eleven uncovered originals or establish a polynomial arbitrary-SAT bound.
