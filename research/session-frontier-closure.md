# Completing a conditional interaction through an all-true terminal

The previous checkpoint leaves one target missing from the saved split of a
**36-variable / 144-clause / 434-literal** interaction. Its false child already
reaches an empty-clause refutation through a checked probe node. Its true child
has **32 variables / 110 clauses / 308 literals** and a checked SAT witness, but
its structural reduction is unfinished. The next step is to complete that
reduction while preserving the false branch.

## Acquisition and exact reuse

Two independent copies of the same history resume the same saved pair. Each
permits up to two consecutive batches of 32 admissions, using the existing
session, scheduler, maintenance and append exporter. Both stop after the first
advance of the first batch: **29 admissions produce 29 stored patterns**. No
second budget is used. These are reproducibility runs, not competing policies.

The new true-branch chain contains **five probe nodes, five binary-path nodes,
eighteen elimination nodes and one family terminal**. Its terminal has
**7 variables / 21 clauses / 85 literal occurrences** and accepts the all-true
assignment. It is neither Horn, dual-Horn nor 2-CNF, and is not zero-valid. This
exposes an existing recognized family through a source-bound conditional chain;
it is not a new tractability theorem. Terminal recognition alone does not bound
the cost of reaching that terminal from other inputs.

The false branch is inherited, including its stored empty-clause refutation.
Both branch obligations are retained. A checked SAT witness was already
available before this experiment; the new result concerns completing the
structural decomposition, not first deciding satisfiability.

The enclosing retained focus has **39 variables / 161 clauses / 495 literals**.
It closes, and the saved-split frontier becomes empty. **Original-input coverage
remains 66/83.** The original navigator still identifies unresolved leaves for
seventeen inputs; case 1062, for example, retains a different 40-variable leaf.
An empty saved-split frontier therefore means those acquired obligations have
closed, not that every original input has a complete decomposition. Resume
through the global original navigator rather than continuing to expand the
completed focus.

## Resource accounting

The mean complete worker takes **12.41063 s**, comprising **12.16111 s** of
preparation, **0.15429 s** of expansion and the remaining output/checking costs.
Preparation includes **7.38139 s** initial session construction and verification.
Expansion comprises **0.05167 s** selection, **0.08840 s** acquisition,
**0.01277 s** route maintenance and **0.00145 s** coverage. Mean append export
takes **0.01920 s**. These phase measurements are not a cold end-to-end speedup.
The second retained batch is unnecessary, so this run supplies no new measurement
of the benefit of retaining a session across batches.

Both repeats produce the same **438,272-byte SQLite / 15,542-byte compressed**
delta. The history grows **364,544 bytes** to **777,236,480 bytes / 42,214
patterns**. No new split sidecar or external probe row is required. The live
index retains **701 routes** and has no missing-target link after acquisition.
Logical database size does not measure peak RAM, and reuse does not establish
bounded total state.

The producer takes **221.94795 s**, including **99.77114 s** historical
restoration and **70.02150 s** final route preparation plus global coverage.
The positive global certificate remains **3,360 steps**, and all **3,830
reference nodes** are reused without enlarging the reference archive. The
infrastructure around the **0.15429 s** expansion remains the dominant measured
cost. Profiling cold restoration and snapshot preparation remains worthwhile;
this discovery run does not compare alternative implementations of either.

## Next discovery target

Resume `experiments/results/cnf-session-frontier/report.json` through
`continue_cnf_session_frontier.restore_checkpoint`, SHA-256
`8349c88556f684eaaed5d0ea296e465cddf85086c2d240d30644ecb2e7436625`.
Keep evidence **(1, 42, 156, 48, 1)** and **two bridges**. The selected source is
**39 variables / 162 clauses / 510 literals**, bound to original **case 1120**
(retained case index **22**):

`4270b94e85e15c2b76fb43fe6a320f98d3908c0020fa3a27e6daf5404c3831f5`.

There is no pending split to resume. The global navigator selects an original
leaf with `learning_clear` status and an ordinary-probe offset of twelve.
For the next producer, select `read_archive(report['next_selection'])['source']`
and preserve its original-case bindings; `report['source']` denotes the now
completed focus of this experiment and must not be expanded again.
Further exploration must retain its original binding and charge any new
acquisition. Finishing unrelated retained candidates cannot be counted as a
gain in original-input coverage. General small decomposition, bounded
recognition chains and compact retained state remain open obligations.

The independently reconstructed next profile contains **16 saved split pairs**
with **32 distinct canonical target keys**, all currently absent. The leading
variable-5 pair has target shapes **37/154/468** and **37/138/416**. Variable 22
also has a true target of shape **37/138/416**, but its full key differs. Equal
counts therefore do not establish reusable identity. The bound
`candidate-target-overlap.json` preserves this negative check. A verified
renaming or another checked transformation could still expose sharing;
neither key inequality nor a failed exact lookup rules out that possibility.

## Validation

Independent cold replay passes in **346.50085 s**, reproducing both workers
and every intermediate catalog without fresh discovery or reference search.
It checks all **3,830 reference nodes**, verifies both cofactor results and
confirms the seven previously interrupted states are now stored. All **233
tests** pass. The manuscript builds to **162 pages**, with no overfull boxes
or undefined references; all **64 previous proof blocks** are unchanged.
All **1,321 artifacts across 26 prior manifests** and all prior reference
payloads are preserved. The reference archive and global positive certificate
are byte-identical to the parent. The new manifest binds **40 artifacts /
4,103,023 bytes**, including the local/global frontier distinction and the
negative exact-overlap check on the next 32 candidate targets. Commands, source
fingerprints and concurrency notes are in
`experiments/results/cnf-session-frontier/validation.json`.

## Reproduction

Run from the repository root with a fresh output directory:

```sh
python3 experiments/continue_cnf_session_frontier.py /tmp/cnf-session-frontier
python3 experiments/validate_cnf_session_frontier.py /tmp/cnf-session-frontier
```

The producer imports the previous frozen worker. The independent validator
reconstructs each starting history and every intermediate catalog, disables
fresh recognition and reference search, checks all reference certificates and
requires early termination only after the focus closes. Previous archives and
implementations remain unchanged.
