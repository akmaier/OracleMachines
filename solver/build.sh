#!/bin/sh
set -eu
cd "$(dirname "$0")/../formal"
lake build OracleMachines oracleSolver
# Save the pinned toolchain's bundled solver in ignored build metadata.
solver_prefix=$(lake env lean --print-prefix)
if [ -x "$solver_prefix/bin/cadical" ]; then
    printf '%s\n' "$solver_prefix/bin/cadical" > .lake/cadical-path
fi
