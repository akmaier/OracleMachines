# Native compilation of negative clause covers

See [`research/negative-cover.md`](../../../research/negative-cover.md) for
correctness, costs, measurements and limitations. The optional policy uses a
source clause and checked refutations of every corresponding literal condition
to refute the parent. It transports saved unit reasons and SCC paths into existing
native split/unit/implication/empty proofs. Publication performs no SCC solving
or general search; restricted paths can require charged unit repair.

Twenty-six saved contexts compare mixed completion and cover compilation, with
one target repeated in reverse order (54 arms). Three covers reduce acquisition
36 -> 24 nodes / 50,554 -> 33,240 bytes. Other contexts retain their native
certificates. Six serial workers compare baseline/mixed/cover and its reverse
on sixty excluded queries. Every mode returns 42 SAT / 18 UNSAT. One fresh
cover reduces total acquisition 370 -> 364 nodes / 464,868 -> 457,715 bytes.
All fourteen positive publications and 95 discovery probes are preserved.

Query timing has mixed signs; complete-worker timing improves in both orders,
partly through cold-replay variation. Diagnostic sidecars grow about 0.05%, trial
SQLite falls 12,288 bytes and mean RSS rises about 1.57 MB. No stable query-time
or general memory/scaling gain is claimed. Fresh cases 51, 55 and 59 each have a
nearly covered clause requiring a literal outside current candidates. Additional
conditions are not yet probed or certified. The baseline-propagated clause miss
is retained as an explicit regression.

## Reproduce

Run from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_negative_cover.py /tmp/new-negative-cover
python3 experiments/validate_cnf_negative_cover.py /tmp/new-negative-cover
python3 experiments/analyze_cnf_negative_cover.py /tmp/new-negative-cover
python3 -m unittest solver.test_cnf_negative_cover solver.test_cnf_mixed_completion solver.test_cnf_inline_completion -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

Timed workers run serially, without concurrent tests, builds or profiles.
Baseline shares native preparation; labels are not inputs to recognition. All
48 family queries remain unfamiliar after preparation and twelve neighbours
become known. Truth enumeration, independent reconstruction and attribution run
after production. Every saved conditional path and unit reason is checked, and
the unchanged native verifier checks the compiled proofs and all cold prefixes.

`protocol.json` freezes 533 runtime sources. `validation.json` adds the posthoc
analyzer (534 total). The 294 counter audits reconstruct recognition and
premise/reason/edge counts alongside inherited completion/SCC/model audits;
transport and repair counts are instrumented measurements, with resulting
certificates independently checked. Discovery dictionaries agree on all 48
family queries. No support bank gains a new ready core.

All 1,153 tests and 24 focused tests pass. Eight new tests include all 64
four-vertex graphs in two coordinate systems (128 independent colourability
comparisons), a synthetic cycle-restriction repair, corruption rejection,
forced prefixes and cold replay. Full tests retain 44 existing unclosed-SQLite
warnings; focused tests have none. `initial-miss.log` preserves the failed
initial expectation that a gated K4 would be recognized. The final test instead
preserves this miss explicitly; native SAT correctness did not fail.
The 215-page manuscript builds with all 64 proof blocks unchanged and a clean
final compiler log. No new Lean theorem or native proof schema is claimed.

All **1,153 tests**, 24 focused tests, 294 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-negative-cover/checkpoint.json`:
**25,757 native keys**, preserving all 25,334 earlier payloads, with 234 new
composed records alongside 4,245 inherited records, 2,957 ordinary decisions
and six projections. The preservation union uses 80,306,176 database bytes /
5,993,018 compressed bytes. Eight roots have alternate certificates in sixteen
retained evidence occurrences. Ready/pending banks remain 132/38, 141/66,
87/89 and 87/116; there are no new support activations. Original structural
coverage remains 17/24 and supplemental positive coverage 24/24. All 529 prior
sources, 6,431 artifacts and 99 manifests remain unchanged. The 215-page
manuscript builds with all 64 existing proof blocks unchanged. No new Lean
theorem or unrestricted-SAT resource guarantee is claimed.

New manifest: **210 artifacts**. Next preservation audit: **6,641 artifacts / 100 manifests**. Final source ledger: **534**.
