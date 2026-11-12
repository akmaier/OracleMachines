# Validation notes

The initial Lean recheck stopped before processing repository proofs with
`missing data file for module Init.Guard`. Inspection found 16 missing `.olean`
sidecars in the temporary Lean 4.24.0 installation. The original failure is in
`lean-first-attempt.txt`. The evidence validator consequently refused to write a
successful validation record; it did not waive the Lean check.

Only the missing sidecars were restored from the official release archive after
its SHA-256 matched GitHub release metadata. The digest and restored paths are
in `toolchain-recovery.json`. No repository Lean source or existing toolchain
file was replaced. Subsequent build results are recorded separately.

The manuscript builds without warnings, overfull boxes or undefined references.
Pages 125–127 were rendered and visually checked after the accounting update;
all 63 prior proof blocks are unchanged. The PDF contains 134 pages and retains
Andreas Maier as author. Timing runs were completed before rebuilding the PDF,
repairing the toolchain or rerunning validation.
