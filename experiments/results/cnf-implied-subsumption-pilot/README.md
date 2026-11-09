# Original-implication subset pilot

The twelve selected inputs include eight implication opportunities and four
previous signed-subsumption gains. The new policy closes **1185, 1289 and 1368**;
977, 1044, 1053 and 1365 remain closed. Sources 1064, 1120, 1245, 1299 and 1410
retain one open leaf each, with 520, 520, 19, 501 and 62 literals. No pilot
closure is lost. Every independent solver decision agrees across modes.

Original signed subsets retain priority. On failure, the candidate materializes
all distinct binary implications already justified by original probe traces and
looks for a recognized subset core. It makes no fresh probe pass. Equal-width
distinct clauses are skipped, exact duplicates use a set lookup, and repeated
literals use the old fallback. The old witness policy is preserved by indexing.
Source reasons are checked before implication origins or subset certificates.

| Measurement | Signed-subset baseline | Implication subsets |
| --- | ---: | ---: |
| Operation seconds | 9.03940 | 7.40206 |
| SQLite bytes | 22,654,976 | 19,824,640 |
| Pattern nodes | 1,742 | 1,458 |
| Cold replay seconds | 3.86019 | 3.29274 |

These single samples deliberately select promising inputs and do not establish
a general runtime benefit. Full-corpus costs and balanced timing controls are
separate. All three archives replay byte-identically, including every alternative,
twelve source records and 372 ordinary solver residuals. Warm reuse inserts nothing.
All 403 tests and the full Lean audit pass; the new composition lemma establishes
model equivalence after an entailed batch and a checked retained core. It does
not refine Python's encoding, persistence or resource costs.

Reproduce with a new output path:

```sh
python3 experiments/compare_cnf_implied_subsumption.py --pilot --output /tmp/new-implied-pilot
```
