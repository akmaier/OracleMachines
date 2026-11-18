# Publish checked negative affine evidence

The positive affine bridge left two kinds of checked negative result on the
native fallback path: an inconsistent equation system, and an exhausted complete
affine space. This experiment adds an optional, versioned negative certificate
interface. It uses the retained extraction and basis evidence instead of solving
the target again. It does not change the native search or its proof reader.

## Certificate and composition

A `cnf-affine-negative-v1` node binds the full normalized CNF to its extraction
and a negative decision. The checker validates clause ownership, complete parity
halves and every triangular Gaussian row operation. A linear-conflict decision
names a checked row equal to `0 = 1`. Leftover clauses need no further examination
in that case: the extracted equations already contradict each other.

An exhaustion decision supplies a particular solution, a complete kernel basis
and one rejecting leftover-clause index for each point. The checker computes
`d = n - rank` from the whole target, including variables absent from equations.
It rejects `d > 8` before basis checking or enumeration. Equation checks and
identity free coordinates establish a complete basis. The verifier reconstructs
each candidate directly from its Gray coefficient vector, independently of the
producer's incremental walk, and checks that the named clause is false. Every
coefficient vector occurs once, so no solution of the equations can satisfy all
leftover clauses. A missing vector or a few selected rejections cannot certify
UNSAT. The discovery status and summary are not proof authority.

Certificates live in a separate SQLite table, `cnf_affine_negative_v1`, keyed by
the full canonical source. Native payloads stay in `cnf_residual_v1`. The native
search never reads the extension table, so it cannot silently create a native
parent that depends on a proof an older reader cannot check. An explicit
`NegativeStore.lookup(source)` checks and reuses a retained exact-source negative
result without discovery or search; a miss returns no decision. The checked
memory cache assumes an exclusively owned append-only database session.

An `affine-negative-chain-v1` record composes the negative terminal with earlier
checked clause-deletion guards. The terminal must exist in the extension table,
even when a native alternative is also preserved. Its reader is explicit;
legacy chain readers are not modified. Publication validates before writing,
retains the first stored bytes on duplicate insertion, and reloads/checks that
stored certificate rather than caching a different proposed alternative.

## Costs and scope

Let `E` be the number of extracted equations, `r` their rank, `n` the target's
variables, `d = n-r`, and `B = max(1, ceil(n/W))` the mask length in machine words.
Publication rechecks source extraction and Gaussian dependencies, with at most
`O(E r B)` row work in addition to source scans, mask construction and sorting.
A conflict needs no basis or assignment enumeration. Exhaustion also checks the
complete basis in `O(E(d+1)B)` equation work. Direct coefficient reconstruction
uses `d 2^(d-1)` direction XORs when `d > 0`, plus `2^d` packed rejection tests;
packing the distinct named clauses is a separate charge. Source normalization,
full keys, JSON serialization, SQLite writes and lookup are all additional.

The basis occupies `O((d+1)B)` words; the rejection list retains `2^d` indices.
Extraction and row-dependency history, the whole source and packed rejection
clauses also consume space. The cap bounds this optional exhaustion certificate;
it says nothing about unrestricted native fallback. The new checker extends the
experimental certificate authority. It is not a translation into the existing
native proof kinds or a new Lean theorem.

The matched pilot replays thirteen exact prefixes from preserved experiments:
seven selected negative affine targets and six positive or unresolved controls.
Two opposite orders give 52 arms. Both policies pay the preceding discovery;
the new policy replaces only the already-retained negative outcome. Each arm
charges archive opening, discovery, publication, composition, warm reuse,
per-target cold replay and serialization. Full inherited-native replay is a
separate preservation check. These retrospectively selected cases measure the
publication mechanism, not held-out structural coverage or a fresh stream.

## Measured result

Results are recorded in `experiments/results/cnf-affine-negative/`.

Seven negative targets replace **134 native nodes / 175,449 payload bytes** with
**seven extension certificates / 21,561 bytes**, avoiding 20,949 native
propagation visits. The six controls keep their 47 native nodes and 54,547 bytes.
All thirteen answers agree with the preceding checked solver. The positive
case 57 retains a different valid witness from the union's first witness; its
four comparison occurrences remain in the arm deltas, without replacing the
union's payload.

The following totals are across thirteen exact-prefix cases, averaged over the
two orders. The last timing row includes per-target cold replay and artifact
delta/record serialization. It excludes shared prefix reconstruction, final
timing-report JSON encoding and the separately measured full historical replay.

| Cost | Positive-only affine policy | Negative publication |
| --- | ---: | ---: |
| New native nodes | 181 | 47 |
| New extension nodes | 0 | 7 |
| Combined new payload bytes | 229,996 | 76,108 |
| Native acquisition propagation visits | 27,306 | 6,357 |
| Query seconds | 0.13998 | 0.05627 |
| Per-target cold replay seconds | 0.48105 | 0.45199 |
| Complete comparison-arm seconds | 1.74035 | 1.62858 |
| Delta/record sidecar bytes | 321,626 | 163,272 |
| All per-arm JSON bytes, including timing reports | 712,432.5 | 532,400 |

Query deltas are -0.08303/-0.08437 seconds, and complete-arm deltas are
-0.11184/-0.11171 seconds. The summed query time falls 59.80% and combined new
payload 66.91% on these selected cases. These percentages are not a fresh-stream
or unrestricted-SAT performance claim. The six unchanged controls each pay an
8,192-byte empty-table overhead. The seven negative arms save 8,192 to 57,344
SQLite bytes each relative to their paired native fallback. Process peak memory
was not measured in this pilot.

The preservation archive retains all **26,743 native payloads byte-for-byte**
and adds seven extension alternatives. It occupies 82,423,808 SQLite bytes /
6,222,266 compressed bytes, an increase of 45,056 / 4,627 bytes over the parent.
Preservation growth therefore differs from the counterfactual per-arm savings.
All native proofs replay without acquisition. The seven new chains also replay
cold: three row conflicts, four exhausted spaces, 28 rejecting assignments and
40 direct coefficient XORs. Their certificate checks visit 1,236 extraction
literals, verify 157 elimination XORs, and check 15 particular/basis vectors.

The new chain view currently prefers a native alternative when one is already
stored. In the preservation union, checking the seven extension chains therefore
also reads 134 native nodes; the measured phase takes about 0.02581 seconds.
The 26,743-node native-only audit takes about 4.95 seconds. Neither phase is the
full earlier end-to-end replay of all historical composed decisions, so those
timings should not be compared with the preceding 12.7-second full-worker figure.

## Remaining work

Run this versioned backend on a newly excluded stream, with both cold and warm
extension lookup, and integrate extension availability into discovery and
support scheduling. Its checkpoint explicitly names the native parent and the
extension reader; existing production checkpoint consumers do not automatically
use it. Choose which checked certificate to read when both native and extension
alternatives exist, charging the choice and maintaining backward compatibility.
These are adoption and reuse gaps, not missing correctness evidence for the
seven published refutations.

Broader recognition remains open. No-equation targets, hidden affine encodings
and free dimension above eight still use the preceding fallback. Projection of
an affine space onto variables that occur in leftover clauses may reduce the
relevant dimension; it needs a complete projected basis, exact recomposition
and measured discovery costs. The earlier random-three-CNF frontier (169 native
nodes on its sixty-query stream) is unchanged by this targeted publication pilot.

All **1,177 tests**, 16 focused tests, 52 independently reconstructed comparison
arms and fourteen negative publication-counter audits pass. All **544 prior
sources, 7,171 artifacts and 102 manifests** remain unchanged. The final source
ledger contains 548 entries. All 26,743 native proofs and seven new negative
chains replay without acquisition. The 218-page manuscript builds with its
64 existing proof blocks unchanged and a clean final compiler log. The full
suite retains 44 existing unclosed-SQLite warnings; focused tests have none.

New manifest: **228 artifacts**. Next preservation audit: **7,399 artifacts / 103 manifests**. Final source ledger: **548**.
