# Versioned publication of negative affine results

See [the analysis](../../../research/affine-negative-publication.md) for the
certificate argument, resource accounting, measurements and remaining gaps.
This optional interface stores checked row contradictions or complete-space
exhaustion proofs in `cnf_affine_negative_v1`. Native search and the native table
are unchanged. Exact-source lookup and `affine-negative-chain-v1` composition
require the explicit new reader.

Thirteen retrospectively selected exact prefixes compare positive-only affine
completion with negative publication in two opposite orders (52 arms). Seven
negative targets replace **134 native nodes / 175,449 bytes** with **seven
extension certificates / 21,561 bytes**, avoiding 20,949 propagation visits.
Six controls retain 47 native nodes. Combined new payload across all thirteen
cases falls **229,996 -> 76,108 bytes**. Summed query time, averaged across orders,
falls **0.13998 -> 0.05627 seconds**; both complete-arm changes are also negative.

The complete-arm measurement includes per-target cold replay and delta/record
serialization. Shared prefix reconstruction, final timing-report encoding and
full historical replay are separate. All per-arm JSON occupies 712,432.5 versus
532,400 bytes on average per order. Process peak memory was not measured.
These selected cases are a mechanism pilot, not a fresh-stream coverage estimate.

## Reproduce and resume

From the repository root, choose a new output directory:

```sh
python3 experiments/compare_cnf_affine_negative.py /tmp/new-affine-negative
python3 experiments/validate_cnf_affine_negative.py /tmp/new-affine-negative
python3 -m unittest solver.test_cnf_affine_negative solver.test_cnf_affine_completion -q
python3 -W always::ResourceWarning -m unittest discover -s solver -p 'test_*.py'
```

`checkpoint.json` is an explicit `affine-negative-checkpoint-v1` descriptor. It
references the unchanged native parent, the extended SQLite archive and seven
new negative chain records. To inspect new terminals, open the restored archive
with the existing `ResidualSolver`, construct `NegativeStore(solver)` without
`create=True`, and use `lookup(source)` or `check_composed(store, record)`.
The ordinary production checkpoint remains the preceding
`cnf-affine-completion/checkpoint.json`; its consumers do not automatically adopt
this new proof authority. Native search cannot gain extension dependencies.

The extended archive preserves all **26,743 native payloads byte-for-byte** and
adds seven negative alternatives. It uses **82,423,808 SQLite bytes / 6,222,266
compressed bytes**, growing 45,056 / 4,627 bytes over the parent. Negative arm
storage savings do not remove previously retained proofs. Four arm occurrences
of a different valid positive witness are retained in their native deltas.

All 26,743 native proofs replay without acquisition. The seven new chains replay
cold, checking three conflicts and four exhausted spaces, 28 rejections and
40 direct coefficient XORs. Current chain lookup prefers an existing native
alternative and therefore also reads 134 native nodes in the preservation
union. Certificate choice is a remaining reuse gap; this cost is reported.

## Validation provenance

Preflight completed 26 matched evaluations, with seven checked negative
extensions, before production began. No tests, builds or profiles overlapped the
serial timing workers. Independent validation reconstructed all 52 selections,
verified native fallback certificates and source-bound extension evidence, and
checked fourteen publication-counter records. The full suite and focused tests
were run after production.

The protocol freezes 548 source entries, including the original posthoc
validator. The final validator makes two bookkeeping corrections: valid native
alternatives are preserved rather than required to match the union's first
witness, and guarded tuple targets are compared in their serialized list form.
`validation-v0.py.txt`, `validation-v1.py.txt` and their failure logs preserve both
attempts. `validation.json` binds the original and final validator and verifies
that runtime sources were unchanged; no timing run was redone or omitted.

Eight new tests cover both negative kinds, exact source lookup, signed names,
full cold replay, guard premises, incomplete bases/rejection lists, forged rows,
wrong headers, duplicate/corrupted persistence and the dimension cap. They also
check all 256 subsets of the three-variable full-support clause pool and 128
random affine mixtures against exhaustive truth.

Next: integrate the explicit extension reader into a newly excluded stream and
resumable discovery, evaluate cheaper certificate choice, and investigate a
complete projection onto leftover variables. Hidden/no-equation inputs and
large free dimension still use native fallback. No new Lean theorem or
unrestricted-SAT resource guarantee is claimed.

All **1,177 tests**, 16 focused tests, 52 independently reconstructed comparison
arms and fourteen negative publication-counter audits pass. All **544 prior
sources, 7,171 artifacts and 102 manifests** remain unchanged. The final source
ledger contains 548 entries. All 26,743 native proofs and seven new negative
chains replay without acquisition. The 218-page manuscript builds with its
64 existing proof blocks unchanged and a clean final compiler log. The full
suite retains 44 existing unclosed-SQLite warnings; focused tests have none.

New manifest: **228 artifacts**. Next preservation audit: **7,399 artifacts / 103 manifests**. Final source ledger: **548**.
