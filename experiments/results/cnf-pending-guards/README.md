# Pending alternative-guard proof costs

This historical diagnostic reconstructs pre-query payload prefixes for cases
23, 85 and 103 from the prior alternative-guard stream. It tries all six pending
support matches individually, alongside three baseline residual solves.

- Case 85: six fresh rows become two derived rows; payload 11,350 -> 1,805 bytes.
- Case 23: eleven fresh rows become 35 derived rows; payload rises 9.44%.
- Case 103: one fresh row becomes twelve for each of four alternatives.

All candidate derivations avoid fresh SAT search. Only 85 has a terminal unit
conflict at its checked origin: it visits one source proof and needs at most one
core publication plus one target subset publication. This does not bound bytes,
recognition or checking cost. No new coverage or stable speedup is claimed.

Reproduce in a new output directory from the repository root:

```sh
python3 experiments/probe_cnf_pending_guards.py /tmp/new-pending-guards
python3 experiments/check_cnf_pending_guard_deltas.py /tmp/new-pending-guards
python3 experiments/analyze_cnf_pending_guards.py /tmp/new-pending-guards
python3 -W always::ResourceWarning -m unittest solver.test_cnf_terminal_support_cost solver.test_cnf_causal_support solver.test_cnf_proof_choice solver.test_cnf_alternative_guard
```

The frozen initial `validate_cnf_pending_guards.py` has a temporary-path reuse
bug. Its failure log is retained; use the corrected checker above. Measured
worker, sample data and their original source bindings remain unchanged.

Each arm retains `delta.json`, `queries.json` and `report.json`. Restore the bound
initial union, append only historical query payloads strictly before that arm's
case, then add its delta. The corrected checker independently performs this
reconstruction and full cold proof/query and both-lineage checks. Deltas total
101,284 bytes; complete inherited databases are referenced rather than copied
nine times. Single phase times and different repeat interfaces are diagnostic
only; no peak RSS or later-stream effect was measured.

The expanded union contains 20,340 keys, preserving all 20,270 prior payloads and
adding 70 keys. Three alternative certificate occurrences for one target remain
in arm deltas. Its SQLite/gzip sizes are 63,578,112 / 4,714,800 bytes. All nine
probes and 2,765 inherited decisions pass independent replay. The 32 relevant
tests pass without ResourceWarnings. The paper builds to 202 pages; all 64 prior
proof blocks remain unchanged. There is no new Lean or arbitrary-SAT theorem.

All 403 prior sources and 4,467 artifacts in 78 manifests remain unchanged.
The protocol binds 405 sources; post-hoc checker, analyzer and test bring the
ledger to 408. Retained ready/pending support counts are original 128/42, legacy
134/73, causal 71/105 and optional expanded causal 71/132. Their full lineages
still pass; no origins were acquired. Structural authority remains 2,614
patterns / 259 pairs, original 17/24 with 999 steps, and separately supplemental
24/24 with 208 steps. All prior checkpoint semantic fields remain unchanged.

Resume `checkpoint.json`. Next, evaluate a terminal-origin filter on fresh
excluded inputs and charge full recognition, checking, repeated selection and
persistence. Keep recursive cases 23 and 103 as regression controls; their
now-retained proofs do not erase their historical acquisition costs.

Checkpoint SHA-256: `87e5225a9ca16180b4e753ea8ad067868ba5a279e589674578e880d165ece30f`.

New manifest: **46 artifacts**. Next preservation audit: **4513 artifacts / 79 manifests**.
