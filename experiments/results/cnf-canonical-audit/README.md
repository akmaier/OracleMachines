# Checked canonical form in complete cold audits

Case 19 closes in one batch with 35 new patterns, five pairs, ten source
assumptions and 135 probes. Coverage grows 11/24 -> 12/24. Four paired,
alternating-order fresh-process runs compare original normalization against the
existing checked canonical-source fast path inside every verifier view of the
complete independent cold auditor. Acquisition and scheduling stay identical.

Mean full-audit time is 6.75146 -> 6.46583 seconds (4.23%); whole-stream time is
8.20199 -> 7.88948 seconds (3.81%). All corresponding acquisitions, proofs,
SQLite and gzip hashes match. Mean peak RSS rises 386,387,968 -> 386,977,792 bytes
(0.153%). This is no memory or persistence saving, and no universal speed claim.

The auditor checks every pattern, split, original binding and positive proof;
there is no trusted parent-validity flag or warm verifier. The fast path scans
actual ordering and dense names, with original normalization as fallback. Each
query proof is also independently cold-checked. Full historical acquisition is
preserved in the parent experiments. The timed streams include restoration,
local work, bookkeeping, snapshots, query checks and full audits, but exclude
interpreter imports and final summary writing; RSS includes all phases.

The 42-step target proof has six conditional nodes, 35 unary reductions and one
contradiction terminal. It reuses seven retained steps and one split. Only the
contradiction is shared within the proof (seven occurrences; 48 unfolded steps).
Depth three uses changing local coordinates; it does not identify a fixed
backdoor or prove efficient arbitrary SAT.

The union contains 1,981 patterns, 199 pairs, seventeen inherited missing
children and a 706-step positive proof for twelve originals. Twelve remain
structurally unknown. Union storage is 37,580,800 SQLite / 1,883,472 gzip bytes;
trial snapshots have their own 1,884,969-byte serialization. Every trial snapshot
and the union is retained. The next target is case 6, whose saved pivot-13 false
child is already covered and whose true sibling remains uncovered.

## Evidence and reproduction

- `protocol.json` binds the parent, target, source ledger, limits and run order.
- `report.json` binds all eight stream reports; each stream binds its batch
  report and compressed database. `producer.txt` preserves raw progress output.
- `parent-profile.*` records a diagnostic profile of the frozen parent. Its
  instrumented timings and overlapping cumulative costs are not raw benchmarks.
- `reconstruction.json` and `reconstruction.txt` record independent replay with
  the frozen full auditor, query checks, original bindings, reachable catalogs,
  immutable prefixes and exact cross-mode equality. This retrospective validation
  took 119.72 seconds, outside operational timings and partly concurrent with tests.
- `checkpoint.json`, `queries.json`, `proof.json`, `pending.json` and `union/`
  retain the complete conflict-checked continuation; `next-discovery.json` binds
  the next target to that checkpoint. `explanation.json` and `target-proof.json`
  describe the new proof.
- `tests.txt` records 360 passing tests, including four new auditor controls.
  Existing SQLite ResourceWarnings remain visible. `test-command.txt` has the
  full command. `targeted-tests.txt` records the four targeted tests separately.
- `paper-check.json` and `paper-build.txt.gz` record a 181-page build, no undefined
  references or overfull boxes, new results in the PDF and 64 unchanged proofs.
- `validation.json` binds 294 source files and preservation of all 290 parent
  sources, 3,290 prior artifacts and 55 manifests. `manifest.json` hashes every
  artifact in this directory except itself.

From the repository root, choose a new output directory to avoid replacing any
retained result:

```sh
python3 experiments/compare_cnf_canonical_audit.py /tmp/cnf-canonical-audit-reproduction
python3 experiments/validate_cnf_canonical_audit.py /tmp/cnf-canonical-audit-reproduction
python3 -m unittest solver.test_cnf_canonical_audit
```

The producer's `PARENT` is pinned to this experiment's parent. Future discovery
should restore the new checkpoint instead; do not rerun acquisition from the
older parent as a continuation. See the
[analysis](../../../research/canonical-cold-audit.md) for fallback accounting,
negative prior experiments, limitations and next gaps.
