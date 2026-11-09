# Pilot: preserving scan traces with affected-clause propagation

Eight fixed inputs compare `CheckedProbeReuseInventory` with
`OrderedPropagationInventory`, both with the same 1 MiB exact-check cache and
unchanged discovery policy. Every answer, root, profile and persistent database
byte agrees. Both cold audits verify every retained node/source/solver record
without changing bytes. The complete shared pilot archive is retained here.

Single-sample total time is 3.28860 -> 2.88153 s; discovery 3.14073 -> 2.74053 s.
Cold audit is 1.45422 -> 1.43121 s. These selected synthetic cases are a screening
result, not a full-corpus or general speedup claim. All preparation and event work
is charged. Full measurements and regressions follow in the main study.

Repeated scanning counts 3,240,522 literal visits. The candidate instead records
564,772 clause-length checks, 949,288 occurrence-index entries, 225,330 affected
occurrence visits and 31,351 event pops across 7,916 calls. Of those, 2,808 need
no index because no initial unit/empty clause exists. These counters describe
different work; they are not interchangeable operation costs. Per-query peak
counters must be maximized, not summed, to derive a run-wide maximum.

The index is reconstructed per call and discarded afterward. Event priority is
(scan round, clause index), preserving all original unit reasons and the first
conflict. The independent checker and ordinary SAT decision engine are unchanged.
This does not expand the recognized families or bound arbitrary SAT search.
