# Additive elimination: verification record

Runtime checkpoint `5894bd8`. All **516 Python tests** pass. The complete Lean
build and axiom audit pass at **4,216 declarations / 2,028 theorem declarations**.
The manuscript compiles without warnings, overfull or underfull boxes; all **63**
earlier proof environments remain byte-for-byte identical to checkpoint
`9538b04`, and all **228** labels are unique. Rendered PDF pages **131–133** were
reviewed for text, equations, margins, headings and the transition to discussion.
The output has 140 pages; `pdf-review.json` records output and rendered-page hashes.

The validator binds the 57-leaf, 83-original and 96-control input sets, runtime
fingerprints, policies and paid-prefix identities. It verifies all **nine
acquisition archives** and **nine separate endpoint-reference archives**, including
archive/database hashes, sizes and SQLite integrity. The ordinary residual
proof tables agree across the three policies in each suite; answers, profiles
and search counters match. The original-input baseline exactly reproduces the
preceding clause-count database. Earlier files and proof history remain intact.

All **4,219 new edge records** have persistent source/target decisions, proof
roots and models bound to their actual CNFs. The validator reads the referenced
proofs without solving, checks every SAT model and confirms paired answers.
The comparison driver additionally checks model restoration and all reference
nodes, full acquisition cold replay, unchanged bytes, warm non-acquisition,
old-row preservation, and the stated chain bounds. Those phase costs appear in
the reports. No independent endpoint-solving check is repeated for old rule edges;
their full cold proof checks and earlier tests remain the relevant evidence.

`growth-barriers.json` is separately bound to its exact candidate helper and
all input reports. `discovery-profile.json` and raw pstats are bound to the
profile script, source report and retained profile archive. That archive preserves
prior rows and passed acquisition checking plus integrity/hash checks; an
additional full cold audit is **not** claimed for it. Profiling was performed
separately after all timed comparisons; cumulative timings overlap and profiler
overhead is not a query-time estimate.

The Lean statements are conditional counting bounds on one normalized accepted
chain. They do not prove Python refinement, useful-pivot availability, an efficient
order or a polynomial complete SAT classifier. The selected prior failures and
reused controls are not untouched holdouts or a fresh full-corpus measurement.
The additive budgets remain optional negative controls.

Validation commands:

```sh
python3 -m unittest discover -s solver
/tmp/oraclemachines-lean/lean-4.24.0-darwin_aarch64/bin/lake -d formal build
python3 experiments/analyze_cnf_additive_frontier.py /tmp/additive-growth-new.json
python3 experiments/profile_cnf_additive_elimination.py experiments/results/cnf-additive-elimination-originals
python3 experiments/validate_cnf_additive_elimination.py
```

Saved-output generators reject existing destinations. Use new comparison output
paths or a separate checkout to repeat them without overwriting evidence. The
validator also creates a fresh output directory; this committed record is retained.
Run measured comparisons without concurrent tests, builds, profiling or archive
analysis. See the [implementation and result account](../../../research/additive-elimination.md)
and the [next priorities](../../../research/structural-reuse-priorities.md).
