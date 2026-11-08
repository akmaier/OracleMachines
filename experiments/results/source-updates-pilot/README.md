# Preserved source-update pilot

All 48 runs and 1,824 queries completed correctly, including 48 UNSAT answers.
RSS sampling succeeded. This run recorded query costs and timed restart, but
omitted initial service setup and final shutdown from its stream total.

The final study in `../source-updates/` repeats the same frozen inputs and solver
configuration, adding explicit setup/shutdown accounting and whole-worker elapsed
time. No solver policy or workload was tuned. This is a lifecycle-accounting
correction, not a new blind holdout. `run_source_updates.py` is the exact captured
harness whose hash appears in this pilot's metadata; it is kept as evidence.
