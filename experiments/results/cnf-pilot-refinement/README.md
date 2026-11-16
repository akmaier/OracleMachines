# A bounded pilot on case 11

Both modes close case 11 in one batch, raising structural coverage 13/24 -> 14/24.
The optional pilot tries one completed nested acquisition on each of the two best
saved alternatives, then compares their remaining selected frontiers. Both trials
share the same 128-admission / sixteen-operation batch allowance as continuation.
All pilot and losing-route states remain stored. The full parent, acquisition
rules and independent checking are identical in both modes.

Pivot 6 initially scores 1106 remaining literals, versus 1118 for pivot 32. Its
pilot costs three admissions and 28 probes, leaving three obligations / 1535
literals. Pivot 32's trial costs seven admissions and 27 probes, leaving one
obligation / 559 literals. The pilot commits to pivot 32; one more acquisition
completes the original.

Including both trials, committed/pilot totals are 44/19 new patterns, 178/77
probes, eighteen/six source assumptions and nine/three new splits. Two reversed
paired runs give local expansion 0.27211 -> 0.11072 seconds (59.31%), whole stream
8.23501 -> 7.85315 seconds (4.64%), and peak RSS 388,456,448 -> 382,541,824 bytes
(1.52%). Total SQLite/gzip sizes fall 1.17%/1.43%. Full auditing still accounts
for 84% of candidate time. This one development input does not establish a
universal advantage; the earlier negative lookahead experiments remain intact.

Proofs have 53/29 steps and maximum conditional depth five/two, using conditional
splits and unary reductions to expose contradiction. Depth is not a fixed
backdoor size. The pilot proof uses sixteen of its nineteen new patterns; the
three losing-trial rows remain stored. Those three rows and one split are also
acquired by the control, but no new node belongs to both final proofs. This is
common exploration, not demonstrated nonterminal reuse across inputs.

The conflict-checked union preserves sixty distinct new patterns and eleven
splits: 2,178 patterns, 220 pairs, seventeen inherited missing children and an
807-step positive proof for fourteen originals. Ten remain unknown. Union
storage is 40,517,632 SQLite bytes and 2,037,803 gzip bytes. The next target is
case 13; its saved pivot-41 true child is covered and seven other children are open.

## Evidence and reproduction

- `protocol.json` binds the complete parent, target, source versions, common
  limits, fixed pilot width/step count and mode order.
- `report.json` binds four stream reports and their batch snapshots. Every batch
  records its actual scheduler decisions, phase/events, proof, admissions,
  operation counters, archive, query check and full cold audit. `producer.txt`
  preserves raw output.
- The two explanation/proof pairs describe the final routes. `comparison.json`
  measures exact acquisition and proof overlap. Unused pilot states are counted.
- `reconstruction.json` and its text log record frozen independent full auditing,
  exact original bindings, query proofs, complete reachable catalogs, unchanged
  prefixes, global budget bounds and cold recovery of pilot phase/decisions.
  Its 75.45 seconds are outside operational timings and partly concurrent with tests.
- `checkpoint.json`, `queries.json`, `proof.json`, `pending.json` and `union/`
  preserve both continuations. `next-discovery.json` binds the next source and
  records presence of both original recognition-depth roots.
- `tests.txt` records 367 passing tests; `targeted-tests.txt` contains four new
  tests separately. `test-command.txt` preserves the full command. Existing
  SQLite ResourceWarnings remain visible in the raw suite log.
- `budget-interruption-check.*` retains an additional check and its exact script:
  with an eight-admission allowance the first route uses three and the second
  only five, leaving its trial pending. Cold resume acquires nothing on reopen,
  then completes the same 29-step proof. Total admissions are twenty, including
  one reentered unfinished state; final new rows are nineteen. The resumed
  pending pair is reused, with only two fresh source assumptions afterward.
- `paper-check.json` and `paper-build.txt.gz` record a 183-page build, no overfull
  boxes or undefined references, new findings in the PDF and 64 unchanged proofs.
- `validation.json` binds 302 sources and preservation of all 298 parent sources,
  3,378 previous artifacts and 57 manifests. `manifest.json` hashes every file
  in this directory except itself.

The pilot currently requires a unary selected root prefix ending in one stored
unresolved source with at least two saved alternatives. Partial trials stay on
their arm until complete. Phase, scores and decisions schedule work; they never
certify closure. Scores can be poor and pilot work can exceed a committed
continuation. The policy remains optional, with unchanged inference defaults.

From the repository root, reproduce into a new output directory:

```sh
python3 experiments/compare_cnf_pilot_refinement.py /tmp/cnf-pilot-refinement-reproduction
python3 experiments/validate_cnf_pilot_refinement.py /tmp/cnf-pilot-refinement-reproduction
python3 -m unittest solver.test_cnf_pilot_refinement
```

The producer uses its frozen parent for comparison. For later discovery, restore
this new union. See the [analysis](../../../research/pilot-refinement.md) for
resource accounting, the measured losing-trial cost, restrictions and next test.
