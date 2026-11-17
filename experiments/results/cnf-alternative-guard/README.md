# Bounded alternative guards after a first-target reuse miss

One extra fresh-query transfer reduces expansions **142 -> 135** and new proof
rows **362 -> 356**. Mean complete time rises **1.30%** with large paired
variation; a runtime or memory win is not established. See
[analysis](../../../research/alternative-guard.md).

Reproduce in a fresh directory, with timed workers running alone:

```sh
python3 experiments/compare_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/validate_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/analyze_cnf_alternative_guard.py /tmp/cnf-alternative-guard
python3 experiments/check_cnf_guard_control.py /tmp/cnf-alternative-guard
```

The protocol binds 401 runtime sources and the 19,907-key starting union.
Selection excludes 2,304 prior sidecar answers and cached roots. Four alternating
pairs visit 192 fresh queries twice. Both modes load the same old 389-origin
legacy/causal portfolio; the larger optional index remains preserved and unloaded.
No new support discovery occurs. The alternative policy checks at most one
additional matching extension after the first guarded target misses the archive
and support bank. It selects only checked known targets or ready negative
supports; pending matches are skipped. Ordinary guard, subset-publication,
child-check and model-lifting paths remain required.

Case 36 changes guard, saving seven expansions with one subset publication.
All modes answer 100 SAT / 92 UNSAT; materialization remains 49 rows. Repeated
visits add no rows, but case 36 repeats selection and then finds its alternate
target cached. Fifteen first-visit calls and one repeat add 1,729 extension
comparisons and 5,709 support inspections. These costs are fully charged.

Mean complete seconds are 13.60267 / 13.77944. Paired changes are -28.44%,
+36.27%, -28.34%, +48.04%, tracking order; cause is untraced. Peak RSS averages
4.85% higher with mixed paired signs. Cold audit and compression consume
52.62% / 27.04% of candidate time. Guard traces increase gzip plus first-trial
sidecars 2.23%. Lower mean query time does not establish a total-cost speedup.

Independent validation reconstructs eligibility, candidate order, ready proofs
and chosen guards from pre-query history. Complete proof/query and both lineage
checks remain required. Untimed frozen-worker replay confirms baseline parity.
Historical case 121, restored from its original snapshot, selects the diagnosed
ready alternative with zero fresh SAT expansions and one checked subset row;
its archive is separately retained. The earlier 20-node count belongs to its
historical stream, not a new isolated matched runtime.

Case 101 differs from first-origin guard but matches another recorded origin.
No hit uses a removed-clause assignment absent from all origins of its selected
core. Next, price pending alternative derivations for cases 23/85 (11/six
expansions), with one-expansion case 103 as a control. A candidate bound does not
establish optimal expansion, compact closure or polynomial arbitrary-SAT cost.

## Validation and retained authority

Independent validation passes **518 tests**, eight complete fresh-trial
archive checks / **3,072 query replays**, every union node, **2,573 inherited
decisions** and all 192 new decisions. Archive validation disables fresh search
and reconstructs guard selection and proof choice from pre-query append history.
Separate untimed frozen-worker replay recomputes the baseline, matching semantic
queries and proof bytes. The historical regression adds one proof row without
fresh SAT search and passes full cold proof/query and both-lineage checks.

The fresh-query union retains **20,270 keys / 63,492,096 SQLite / 4,704,611 gzip
bytes**, adding 363 keys and preserving every prior payload. There are no
alternate certificates. New decisions have **144 direct roots / 48 negative
guards**. The historical regression's additional target proof is not in this
union; its complete archive and guarded result remain separately retained in
`experiments/results/cnf-alternative-guard/historical-control/` and bound by
`control-check.json`. It is not counted as a fresh-query coverage gain.

Resume `experiments/results/cnf-alternative-guard/checkpoint.json`. It preserves
all prior semantic fields and adds `alternative_guard_study` and
`alternative_guard_decisions`. The measured banks retain the same eight-catalog /
389-origin history, with **132/75 legacy** and **67/109 causal** ready/pending
entries. The original 170-entry frontier has **126/44**; the optional 203-entry
expanded causal frontier has **67/136**, retaining its eleven-catalog / 526-origin
lineage. All four lineage checks pass. The two newest catalogs contain 98
negative guarded records not acquired into that larger optional frontier.

All prior **397 sources / 4,406 artifacts / 77 manifests** remain unchanged.
Runtime binds 401 sources; analyzer and control checker bring the ledger to 403.
Structural authority stays **2,614 patterns / 259 pairs / 17 missing children**,
original **17/24 / 999 steps**, separate supplemental **24/24 / 208**, and original
case 7's discovery pointer. The paper builds cleanly to **202 pages** with
**64 unchanged proof blocks**. No new Lean or unrestricted-SAT resource theorem.
The full test log retains 24 unclosed-SQLite ResourceWarnings from older tests;
eight focused new tests emit none with warnings enabled. Allocation origins
remain untraced.

Checkpoint SHA-256: `ff7c124f610f1a7e11207b6f248d8f420d7bd0272ff91df0c9c9d75d4e8b729d`.
Report SHA-256: `4f15e41ec39a67b7df6172cb64eba7b9c863c492655fdc1b44d9ee674d766909`.

The new manifest binds **61 artifacts**. The next preservation audit inherits
**4467 artifacts / 78 manifests**.
