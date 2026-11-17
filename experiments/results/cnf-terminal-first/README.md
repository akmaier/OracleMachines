# Preserved incomplete harness run

The original terminal-first comparison completed six nonterminal control arms
before the exclusive archive-restoration helper rejected reuse of an existing
temporary `initial` path at the second cohort. `failure.txt` retains the exception.
No solver correctness failure occurred. These six arms are preserved unchanged
and independently match the complete run's plans, deltas and composed records.

Use [the complete checkpoint](../cnf-terminal-first-complete/checkpoint.json).
Its protocol binds the wrapper that refreshes only paths restored earlier in
its own invocation after readers close. Its manifest covers this directory too.
