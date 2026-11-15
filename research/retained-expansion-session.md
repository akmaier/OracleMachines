# Retaining checked state between bounded expansion batches

## The measured bottleneck

The startup profile at the append-export checkpoint separates the previous
worker's preparation. An uninstrumented sample spends **7.56459 s** constructing
and checking routes, compared with **0.15541 s** cloning, **0.42572 s** hashing
tables, **0.67851 s** capturing an export boundary and **8.83102 s** preparation
in total. The checked cache contains **2,264 nodes**, with **5,617,186 serialized
key bytes** and **18,759,928 node JSON bytes**. These are content sizes, not RAM.

The second sample instruments route construction with cProfile. Its route
time rises to **22.32621 s**, so it is diagnostic rather than a speed comparison.
The call tree identifies recursive node checking, probe reconstruction,
normalization and subsumption beneath complete route loading. The profile and
unchanged-database checks are retained under `experiments/results/cnf-startup-profile/`.

## Live reuse and its boundary

`ExpansionSession` retains the same inventory, both verifier views and complete
maintained route catalog across batches. Initial construction still performs
the full check. Before a fresh admission allowance, the helper requires:

- A committed connection and no active recursive certificate checks.
- Unchanged external-write and schema versions.
- No database writes or admissions left outside the maintenance snapshot.
- Identical evidence sidecars, bridges and verifier policies.

It checks this boundary in a short write-reserving transaction, resets only
the admission ledger, and refreshes the maintenance snapshot. Every expansion
operation still uses the existing checked route maintenance. External changes
require reopening checked state. The caller must exclusively own the connection,
policies and cached objects, keep historical rows immutable and report every
acquisition to maintenance. This is not a security boundary against a caller
that mutates those objects or changes the version machinery.

The reason reuse is valid is local: an admission-budget reset changes neither
a stored certificate nor a semantic route. Given the previously checked
inventory and complete maintained catalog, both remain valid at the next
batch's start. Induction across batches depends on the existing maintenance
contract after every operation. Pending targets remain obligations; a reset
cannot promote them to completed proofs. Unstored recognition inputs receive
new admissions when revisited. The helper does not save their unfinished
recursive computation.

For K batches, let V_i denote fresh catalog verification, E_i expansion and
maintenance, P_i preparation/export work shared by both methods, and G_i the
session boundary guard. The comparison removes repeated V_i for i > 0 while
retaining the initial V_0 and charging every G_i, E_i and P_i. It provides a
saving only when avoided verification exceeds the guard and retention costs.
The live caches remain in memory between batches. Their lifetime increases;
no peak-memory reduction, bounded total cache growth or cold-start saving is
claimed. A process restart still reconstructs and verifies the authority.

## Matched two-batch comparison

Two reversed-order repetitions start from independent identical histories.
Each sequence allows two batches of at most twelve advances and **32 admissions
per batch**, hence at most **64 entries**, including repeated unfinished inputs.
Both methods use the same scheduler, selective route maintenance and append
exporter. Restart mode closes and reopens checked state between batches;
retained mode reuses it. Each batch charges its snapshot copy, table digests,
export boundary, proof output and delta checks. The initial cold batch remains
in the aggregate comparison.

| Mean seconds | Restart | Retain |
|---|---:|---:|
| First-batch session startup | 7.36594 | 7.21688 |
| Second-batch session startup | 7.40238 | 0.00404 |
| First complete worker | 11.72258 | 12.06426 |
| Second complete worker | 11.60522 | 4.12185 |
| Sum of both workers | 23.32780 | 16.18611 |
| Full sequence, including merge bookkeeping | 23.70113 | 16.60739 |

The two-worker reduction is **30.61%**, with initial checking included.
First-batch variation is not a retention improvement. The second worker's
remaining preparation averages **3.69664 s**, including snapshot copying and
table digests; these phases need separate profiling before further changes.
Small exporter timings in this run are not a new comparison with the previous
export study: cache state and measurement placement differ.

The complete producer costs **269.56866 s**, including **95.47416 s** historical
restoration and **69.18542 s** final route preparation plus global coverage.
These costs remain outside the paired workers. The results concern two bounded
expansions on reused development inputs; they are neither a holdout estimate
nor completed-original SAT solving times.

## Persisted progress and the next frontier

Each sequence enters **64 states across two budgets**, storing **19** in the
first batch and **25** in the second. Thirteen first-batch entries are unstored
and revisited in the next batch; seven final entries remain unstored. The union
retains **44 patterns**, including two family terminals, one polarity change,
eleven binary-path nodes, twenty-two elimination nodes, seven probe nodes and
one unresolved node. Both methods produce identical delta bytes per batch.

The new terminals have shapes **6/7/18** (Horn, one-valid and zero-valid) and
**4/3/6** (Horn, 2-CNF and zero-valid). These are checked conditional reductions,
not a new general recognition theorem. Coverage remains **66/83**, while the
frontier now has **two open splits / no acquired open leaf / one pending target**.

Cold replay distinguishes recurrence from exact reuse. The first batch stores
nineteen nodes closing the false 24-variable cofactor; the second reuses all
nineteen unchanged. The true cofactor reaches a 10-variable interaction through
sixteen new nodes. Splitting that interaction adds eight nodes on its false
branch to the second Horn terminal, while its true branch reuses the stored
empty-CNF terminal. On the next 36-variable split, one new probe node connects
the false child to a stored empty-clause refutation. The true child has a checked
SAT witness but remains structurally pending. SAT decision evidence and complete
structural classification remain separate. All eleven interrupted inputs from
the parent checkpoint are reentered, charged and now stored.

History grows **540,672 bytes** to **776,871,936 bytes / 42,185 patterns**.
The union delta is **622,592 SQLite bytes / 22,766 compressed bytes**, with
**two new split sidecars** and no external probe rows. The positive certificate
still has **3,360 steps**; reference evidence grows **3,803 -> 3,830 nodes**.
The live index ends with **701 routes / one missing-target link**. Neither
export method nor session retention reduces persistent storage on this test.

Resume `experiments/results/cnf-expansion-session/report.json` through
`compare_cnf_expansion_session.restore_checkpoint`, SHA-256
`a9133c94e01789bb80298de290f17177f71ae428f6d827142bd287722dca9793`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. The selected source is
`e1cbca2079165713c5e3f147e52019e180bc476521cddf2e0383ed46130b153a`,
the remaining **36/144/434** interaction. Its targets are:

- False **31/120/344**:
  `aa198cbc4558e51a28a037a813439ab8c3d49cf793cddfdf53080f543e836a85`.
- True **32/110/308**:
  `a05a3c56338c449a76cad1d43ae775640c025873e85a7f5d05d82e2a080c05ea`.

The true target is pending. Resume the saved split before ranking new candidates,
preserve its acquired false branch and charge the seven unfinished inputs again.
Cold reconstruction and
snapshot preparation are now the larger measured total-cost targets. General
SAT decomposition, bounded recognition chains and compact retained state
remain unresolved.

## Validation

Independent cold replay passes in **518.83008 s**, reproducing all eight
workers and their intermediate catalogs without fresh discovery or reference
search. It verifies **3,830 reference nodes**. All **233 tests** pass. The
manuscript builds to **162 pages**, with no overfull boxes or undefined
references; all **64 previous proof blocks** remain unchanged. All **1,220
artifacts across 25 prior manifests** and all **3,803 previous reference
payloads** are preserved. The new manifest binds **101 artifacts / 4,289,703
bytes**, including the startup profile, eight workers, cold replay, structural
findings and test/build logs. The initial failed external-write test fixture
is retained and explained; its correction changes stored bytes rather than
issuing an external no-op update. Exact commands, source fingerprints and
concurrency notes are in
`experiments/results/cnf-expansion-session/validation.json`.

## Reproduction

From the repository root, choose fresh output directories:

```sh
python3 -m unittest solver.test_cnf_expansion_session
python3 experiments/profile_cnf_expansion_startup.py /tmp/cnf-startup-profile
python3 experiments/compare_cnf_expansion_session.py /tmp/cnf-session-replay
python3 experiments/validate_cnf_expansion_session.py /tmp/cnf-session-replay
```

The independent validator uses fresh inventories and the original full catalog
builder at every recorded prefix. It does not use `ExpansionSession` to validate
its own reuse. Discovery and reference search are disabled during replay.
