#!/bin/sh
set -eu
# Supply the audited source checkout; no implicit download or global install.
if [ "$#" -ne 1 ]; then
  echo 'Usage: solver/build_incremental.sh /path/to/cadical-rel-2.1.2' >&2
  exit 2
fi
solver_source=$(cd "$1" && pwd)
solver_expected=3ff42f04384489916f017acd6d5e7cbfa7257be7
solver_actual=$(git -C "$solver_source" rev-parse HEAD)
if [ "$solver_actual" != "$solver_expected" ]; then
  echo "Expected CaDiCaL commit $solver_expected, got $solver_actual" >&2
  exit 2
fi
git -C "$solver_source" diff --quiet HEAD -- src
cd "$(dirname "$0")/.."
mkdir -p formal/.lake/build/bin
c++ -O3 -std=c++11 -I"$solver_source/src" solver/incremental.cpp \
  "$solver_source/build/libcadical.a" -o formal/.lake/build/bin/oracleIncremental
