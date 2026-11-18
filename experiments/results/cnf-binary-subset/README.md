# Binary-subset refutation in fresh native expansion

An optional mixed-CNF leaf emits the existing native implication-path proof when
its binary subset is contradictory. A satisfiable subset is inconclusive. Units,
all-binary inputs and uniformly satisfiable binary cores avoid redundant SCCs.
The authority and native format are unchanged.

On sixty new queries, **eight refutation leaves remove 22 native nodes and 16,393
payload bytes**. Native additions fall 281 -> 259 and child propagation visits
32,980 -> 30,779. The three affine extensions and all preceding discovery traces
remain unchanged. Both policies return 40 SAT / 20 UNSAT. These are finite
structural gains, without an unrestricted-SAT complexity claim.

The candidate pays 76 failed SCCs. Mean query time falls 3.40%, but paired changes
have mixed signs. Mean complete-worker time **increases 0.82%**. Full cold replay
is about 13.5 seconds. SQLite falls 16,384 bytes, gzip falls 2,319 bytes, diagnostic
sidecars grow about 5.1 KB and mean peak RSS falls about 21.2 MB. Two orders do not
establish runtime or memory scaling. Keep the policy optional and preserve the
regression. The detailed counts, cost model and next targets are in
[the research note](../../../research/binary-subset-refutation.md).

## Reproduction

Run from the repository root, with a new output directory:

```sh
python3 experiments/compare_cnf_binary_subset.py prepare /tmp/cnf-binary-subset-new
python3 experiments/compare_cnf_binary_subset.py /tmp/cnf-binary-subset-new
python3 experiments/validate_cnf_binary_subset.py /tmp/cnf-binary-subset-new
python3 experiments/analyze_cnf_binary_subset.py /tmp/cnf-binary-subset-new
python3 experiments/diagnose_cnf_binary_subset.py /tmp/cnf-binary-subset-new
python3 -m unittest solver.test_cnf_binary_subset solver.test_cnf_affine_session solver.test_cnf_affine_negative
python3 -m unittest discover -s solver -p 'test_*.py'
```

`protocol.json` freezes all runtime sources and two serial opposite orders in
separate worker processes. No tests/profiles ran concurrently with these workers.
`cases.json` records twelve neighbours and 48 family cases excluded from every
inherited source/native key. Family labels are diagnostic metadata. Worker costs
include preparation, discovery misses, checking, persistence, warm reuse,
serialization, compression and full historical cold replay. Final report rewrites,
posthoc analysis/diagnosis/validation and test/build work are outside those timings.
`diagnosis.json` retains the retrospective opportunity census and five untimed
empty-archive mechanism checks; they are not exact-prefix timing comparisons.

## Resume and preservation

Restore `checkpoint.json`'s `reference_union`. It contains **27,368 native keys /
thirteen extensions**, preserving 27,087 prior native payloads and ten extensions
byte-for-byte. It adds 114 native and six negative composed records to 5,110
inherited records. The union grows 688,128 SQLite / 79,234 compressed bytes,
including comparator history. Eight alternative native proofs remain in the
trial archives and are identified in `validation.json`; the union preserves its
first payload for each root. Shorter certificates are not silently substituted.

Use `experiments.cnf_binary_subset.AccountedBinarySubsetSolver` to enable the
optional leaf for fresh native work. The unchanged ordinary native reader also
checks these proofs. Affine negatives retain the explicit
`experiments.cnf_affine_session.TerminalStore` reader and checked chain bank.
Original default solver behavior and all old experiment files remain untouched.

Validation independently checks 240 chronological queries, twelve affine negative
publication-counter records, exhaustive truth for 48 family cases, warm answers
and full historical replay of every trial and the union. All **1,188 tests** and
**nineteen focused tests** pass. Seven new tests include all 4,096 binary subsets
on three variables with a wide clause, corrupt indices, signed names, incomplete
positive cores and cold replay with acquisition forbidden. The full suite retains
44 existing SQLite resource warnings; focused tests have none. The **220-page**
manuscript builds with a clean final log and all **64 old proof blocks unchanged**.
All 553 prior sources, 7,439 artifacts and 104 manifests remain unchanged.

The next targets are new random-three cases 56/44 and the 76 failed SCC calls:
recognize compatibility with the wide clauses, or reuse graph work across related
residuals. Graph cover discovery and cheaper choice among native certificates
remain separate opportunities. No new Lean theorem is claimed.

Final source ledger: **560**. New manifest: **39 artifacts**. Next preservation
audit: **7,478 artifacts / 105 manifests**.
