# Reuse propagated residuals before premise discovery

Twenty-one exact-prefix arms and six fresh workers compare native baseline,
previous child admission and the new optional propagated-residual check. The
protocol binds 487 sources before measurement; the final validation adds the
posthoc analyzer for 488. Tests, profiles and builds did not overlap production.
The original native solver and certificate format remain unchanged.

At preceding fresh case 85's exact prefix, the new route uses 955 rather than
5,750 propagation literal visits and removes all four premise probes. It retains
the same one row / 1,672 native bytes. One explicit trace publication replaces
the expansion call; the source's 23 forced variables expose an already checked
positive binary residual. The other six controls preserve the previous gate's
payloads and propagation, including useful nonterminal cases it still rejects.

The fresh catalogue excludes all earlier ordinary/composed query and native
roots: 64 double-deletion neighbours per old template, with 1,152 previous
query roots excluded per template. Selection costs 1.663 seconds separately.
Workers run baseline/admitted/propagated and the reverse order.

| Measure | Baseline | Admitted | Propagated |
| --- | ---: | ---: | ---: |
| SAT / UNSAT answers | 99 / 93 | 99 / 93 | 99 / 93 |
| New native rows | 215 | 199 | 199 |
| Added native bytes | 469,640 | 445,570 | 445,570 |
| Expansion calls | 37 | 11 | 11 |
| Explicit trace publications | 0 | 10 | 10 |
| Propagation literal visits | 9,528 | 14,907 | 14,907 |
| Mean complete worker seconds | 27.071 | 28.277 | 28.119 |

There are no successful propagated-residual admissions on the new set. Both
admission policies produce identical native payloads and propagation counts;
the earlier gate earns the row saving against baseline. The new lookup and
family scan costs remain charged, with 0.12% larger query/warm sidecars.
Opposite signs in the two new-versus-previous timing pairs establish no stable
speedup. All modes acquire zero rows on warm replay. Cold replay is the largest
measured complete-time component. Process RSS is not a live-state space bound.

Cases 36/186 contribute all eleven remaining child expansions, after retaining
baseline traces with thirteen and one forced variables. Reusing those traces
after rejection is the next candidate. A posthoc diagnostic also retains both
two-CNF restrictions of case 36 under canonical variable 6 and checks their
pointwise equivalence on 2,048 assignments. Case 186 has no such single-variable
decomposition. No alternate acquisition, row saving or timing is claimed for
either unimplemented candidate.

The 22,259-key union preserves every one of the 22,036 previous native payloads,
adding 223 keys and no alternative payloads. It retains 597 new composed records
alongside 1,230 earlier composed records, 2,957 ordinary decisions and six
projections. The evidence union uses 71,503,872 database bytes and 5,163,292
compressed bytes; it is not a single policy's working storage. Ready/pending
frontiers remain 132/38, 140/67, 84/92 and 84/119. Structural and supplemental
authority are unchanged; all prior 483 sources, 5,222 artifacts and 90 manifests
are preserved.

All 1,085 tests and 21 focused tests pass. The full suite emits 44 existing
SQLite ResourceWarnings; focused tests emit none. The independent validator
reconstructs all control prefixes, regenerates the excluded catalogue, checks
selection and publication, and verifies warm/cold proofs without acquisition.
The paper builds to 207 pages without overfull or undefined warnings and retains
all 64 prior proof blocks.

Reproduce from the repository root into a new output directory:

```sh
python3 experiments/compare_cnf_propagated_reuse.py /tmp/cnf-propagated-reuse-reproduction
python3 experiments/validate_cnf_propagated_reuse.py /tmp/cnf-propagated-reuse-reproduction
python3 experiments/analyze_cnf_propagated_reuse.py /tmp/cnf-propagated-reuse-reproduction
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
python3 -m unittest solver.test_cnf_propagated_reuse solver.test_cnf_child_admission solver.test_cnf_local_guard
```

The new selector is experimental and optional. Fresh roots remain neighbours of
three old templates; complete coverage alone would not prove efficient solving.
No new Lean theorem, general speedup or unrestricted-SAT bound is established.

New manifest: **107 artifacts**. Next preservation audit: **5329 artifacts / 91 manifests**. Final source ledger: **488**.
