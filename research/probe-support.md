# Compile causal probe supports instead of full cofactors

Checkpoint: 25 November 2026. [Complement scheduling](complement-probes.md)
expanded detector coverage but made native proof reconstruction the largest
measured cost regression. This experiment keeps all 60 previously recognized
local roots fixed and changes their certification. Selecting causal source
supports cuts compilation time by 73.43% and encoded record bytes by 78.93%
relative to the full compiler. Every case improves on both measures. Ordinary
local solving remains faster in aggregate.

## Exact support selection and reuse

First validate the entire original program, including unused probe traces and
guard provenance. For the terminal conflict, work backwards through its unit
trace. Retain a unit only if its assigned variable is needed by the conflict or
by a retained later reason; replace that dependency by the other variables in
its reason clause. The original checked signs and forward order are preserved.
The remaining dependency must be contained in the probe assumption. If neither
the conflict nor any retained reason needs that assumption, this branch already
provides an unconditional refutation and the other branch can be omitted.

For every retained reason and final conflict, select either its original source
clause or the complete source-clause support of its checked guard. Take their
union, normalize its variable names, transport the required templates and trace
clause indices, and independently validate the resulting compact program.
A missing required coordinate falls back to the full compiler. None of the
measured cases needs this fallback.

The unchanged compiler refutes the selected source subset using existing native
rules. One existing `component` certificate then lifts that UNSAT subset to the
original source. Despite the rule's name, negative subset lifting does not
require independent variable components: a conjunction containing an UNSAT
subset is UNSAT. No guard becomes a native axiom. Recomposition through earlier
binary-prefix steps remains unchanged. No new inference or authority table is
introduced, and all portable checks precede archive reuse or publication.

This selection is sufficient, not minimum. Backward dependency closure proves
that discarded unit assignments do not justify any retained step. Including each
used guard's full source support preserves its original proof. Bijection of the
remaining names preserves the compact trace, and the independently checked
subset wrapper binds it back to the whole formula. These are representation
changes to an already recognized proof, not stronger SAT recognition.

Exact normalized support keys also permit reuse between different supersets.
A regression grows one formula by 1, 4 and 16 irrelevant binary clauses, closing
and reopening the database between queries. Each later formula reuses the same
stored core and adds exactly one wrapper record; all earlier payloads remain
unchanged and cold verification accepts all roots. Discovery, source checking,
support selection and coordinate transport still run. A missing core clause,
changed guard or different canonical key requires fresh binding; arbitrary
semantic equivalence is not recognized. Wrapper storage still includes the
whole current source and can grow with the stream.

## Matched native costs

The 23 roots from the first full-clause probe study and 37 from complement
scheduling form a fixed 60-root set. Two alternating isolated repetitions compare
fresh local solving, the frozen full compiler and support compilation: 360
workers. Both controls reproduce their previous deterministic verdicts, counters,
authority tables, digests and byte counts. The audit initially compared embedded
wall-clock fields too; that failed check and validator version are preserved.
The correction excludes only the two known timing fields, retaining all semantic,
counter and stored-content checks.

| Summed per-case mean | Fresh local solver | Full compiler | Support compiler |
|---|---:|---:|---:|
| Solve or compile | 2.10379 s | 12.56235 s | 3.33724 s |
| Warm check | 0.09542 s | 0.58340 s | 0.58335 s |
| Cold readers | 2.61144 s | 11.55219 s | 2.83166 s |
| Persistence | 0.68554 s | 3.39429 s | 0.63738 s |
| Complete local trial | 5.71311 s | 28.27209 s | 7.52341 s |
| Encoded record bytes | 9,465,124 | 38,159,763 | 8,040,728 |
| Records | 863 | 4,443 | 2,615 |

Compilation includes source/prefix validation, causal selection, transport,
compact-program checking and native publication. The complete trial includes
warm checking, both cold readers and persistence. Earlier acquisition and
pattern discovery, saved-input loading, process startup and the final preservation
audit are additional. These are proof costs on exposed saved cases, not a live
whole-query speed comparison. Two repetitions do not establish universal timing
ratios.

All 60 support trials are faster and smaller than full compilation. Relative to
fresh local solving, support compilation is faster on 15 cases, complete local
trials are faster on 21, and record bytes are lower on 35. The remaining 45, 39
and 25 cases respectively are retained as regressions. Aggregate support bytes
are 15.05% below fresh solving, but compilation and complete local trials remain
slower. More records do not imply more bytes: the selected cofactors are smaller.
Isolated database sums can duplicate shared subproofs and are not cumulative-bank
growth.

All 60 selected sources are strictly smaller. Their aggregate source support
falls from 19,937 clauses / 54,157 literals to 2,151 / 5,104. Causal slicing keeps
1,900 of 3,786 terminal unit steps. Native probe splits fall from 3,846 to 1,960;
the 122 earlier binary-prefix splits remain. Sixty subset wrappers lift the
compact proofs. Peak process RSS is 72.71 MB for the full compiler, 67.49 MB for
support compilation and 62.18 MB for fresh solving. These maxima include input
and interpreter state and do not establish a general RAM bound.

## Bounds, preservation and next gaps

Let L be the full source size, T the terminal trace length, R the literals in
retained reasons, and G the selected guard supports counted with traversal
multiplicity. Dependency and support collection use O(L+T+R+G) expected word
work before normalization, sorting, transport and validation. The native compiler
then works on the selected subset; if it is large or its proof expands heavily,
there is no guaranteed saving. The full-source wrapper, checked templates and
stored child keys are additional space. Exact subset reuse avoids reconstructing
a known core, but does not make recognition, validation or an unlimited stream
polynomially bounded in total size independently of its inputs.

Both cold readers verify all 180 unique archive/root pairs; warm replay adds no
authority rows. The cumulative bank is unchanged. Validation preserves 182 prior
manifests, 23,167 artifacts and 1,050 prior source files; the new checkpoint binds
1,055 sources. All 1,889 tests pass, including 24 focused tests, and the 64 existing
manuscript proof blocks are unchanged. Earlier failed audit output and the test
run before the reuse test were retained. Existing full-suite SQLite warnings are
recorded; focused tests have none.

The original 180 unresolved all-guard events remain unresolved: coverage is
unchanged. Checked feedback of the 851 exclusions in 160 of those events remains
the next coverage experiment, now with a cheaper certification path. For cost,
profile the remaining binary-prefix compilation and repeated transport/checking
before extending support selection. Warm validation did not improve, and the
support compiler still loses to ordinary solving on most cases. No minimum
support, efficient arbitrary-CNF partition or unrestricted-SAT bound is proved.

Resume [the checkpoint](../experiments/results/cnf-probe-support/checkpoint.json).
The [protocol](../experiments/results/cnf-probe-support/protocol.json),
[analysis](../experiments/results/cnf-probe-support/analysis.json) and
[support plans](../experiments/results/cnf-probe-support/support-plans.json)
preserve all inputs, choices, native archives and regressions.
