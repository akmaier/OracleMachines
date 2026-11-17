# Reuse a terminal target before partition discovery

The terminal-first selector fixes the unnecessary repartitioning exposed by the
previous fresh comparison. It checks the unsplit target by unit propagation
before posting searches, core-proof reads or branch construction. When that
probe finds a conflict, the existing trace publisher writes one checked native
proof. The prepared core index is still built and charged; this change does not
make preparation free. Nonterminal targets use the previous selection policy
without repeating the baseline propagation.

## Exact-prefix comparison

Eight matched historical arms reconstruct the original states before cases
6, 68, 135 and 176. Later union results cannot provide answers during these
measurements. The comparator is the previous screening implementation. Both
policies repeat ordinary preparation and the failed additional-guard selector.

| Case | Previous / terminal-first new rows | Added native bytes | Propagation literal visits | Plans examined |
| --- | ---: | ---: | ---: | ---: |
| 6 | 4 / 4 | 6,122 / 6,122 | 2,626 / 2,626 | 2 / 2 |
| 68 | 12 / 12 | 16,605 / 16,605 | 9,355 / 9,355 | 4 / 4 |
| 135 | 7 / 7 | 10,036 / 10,036 | 5,206 / 5,206 | 4 / 4 |
| 176 | **3 / 1** | **6,137 / 2,229** | **5,289 / 1,110** | **4 / 0** |

Case 176 avoids 3,585 posting visits, two core-proof reads and one strengthened
premise. Its two child-proof publications become one unsplit proof publication;
explicit trace-check literal visits fall 68 -> 64. The resulting native payload
is byte-identical to the original single-clause baseline's proof. The other
three cases retain exactly the same choices, native deltas, composed records and
screening operation counts. Both case-176 arms have zero `expanded_nodes` because
they publish saved traces: that counter alone misses the improvement.

The regression's delta-plus-decision size falls 23,918 -> 17,922 bytes. This is
retained evidence, not peak live memory. Index setup remains about 18 ms in those
two samples. Screening falls 4.17 -> 0.50 ms, but complete samples are 6.55 / 6.63
seconds, dominated by preparation and 5.20 / 5.43 seconds of cold replay. These
single samples establish neither a total speedup nor fresh-query generalization.
The baseline implementation already found the unit conflict cheaply; the result
repairs added screening overhead rather than creating a new tractable SAT class.

The initial harness completed six nonterminal arms, then failed when the frozen
archive helper rejected reuse of an existing temporary destination. Those arms
and the failure log remain retained. A small wrapper refreshes only paths that
it successfully restored earlier in that invocation, after readers close. The
complete run has eight arms, and independent validation confirms semantic parity
with the incomplete run and the older stored controls.

## Where further reuse is missing

A read-only probe reconstructs cases 43, 172 and 70 from the preceding fresh
stream, including their accepted extra guard. These account for 10, 9 and 4 of
the 26 remaining expansion calls. No additional single-clause guard is found.
Cases 43/172 admit no raw-core plan under the current two/three-missing-clause
rule. Case 70 tests two orders of core 209; each leaves one terminal and one
nonterminal child and fails the current admission gate. Simply enabling another
identical screen is therefore insufficient on these preserved states.

There is a concrete recognition mismatch: the target has been restricted by its
guards, but the bank still matches original core clauses. Restricting checked
negative cores under the same assignments reveals two-clause gaps:

- **Case 43:** 59 clauses / 157 literals after guards. Conditioned cores 25, 214
  and 295 each miss two clauses. Their native restricted roots are not yet present.
  Core 214 has seven clauses / fourteen literals and misses `[-230]`, `[-10]`.
- **Case 172:** 66 clauses / 180 literals. Conditioned core 209 has only three
  clauses / four literals, misses `[-50]`, `[-40]`, and already has a checked
  negative native root in the exact pre-query archive. Cores 214/295 also have
  two-clause gaps but require restricted-core certification or acquisition.
- **Case 70:** 54 clauses / 141 literals. Conditioned core 209 is already checked;
  other nearest candidates are not. This is a smaller rejection/control case.

The probe also repeats conditioning after the target's forced units, transporting
canonical variable identifiers back to source names. The nearest gap remains two
in all three cases. It publishes no premise, child proof or source conclusion.
A checked negative formula remains negative under restriction, but a new native
restricted root still requires the appropriate checked certificate or acquisition;
that obligation cannot be replaced by a clause-similarity score.

**Next:** price conditioned-core matching on cases 43/172, starting with the
already checked core-209 cofactor in 172. Compare the same branch split without
that core: two missing unit clauses may merely describe an ordinary clause split,
so small conditioned support does not by itself prove a reuse advantage. For
unavailable restricted roots, supply a checked cofactor derivation or charge
fresh acquisition. Any composed model must lift through all prior guards and
forced assignments.

The diagnostic scan conditions 218/219 ready parents per case. Across guard-only
and post-unit passes it visits about 32,000 restriction literals per case, before
proof reads, normalization and clause matching. This is not a cheap deployed
recognizer. Cache projections by checked parent identity and exact assignment,
validate variable transport, and charge discovery, maintenance and invalidation
before widening the stream policy. No compact closure or arbitrary-SAT bound
follows from this finite matching opportunity.

## Persistence and validation

All **1,047 tests**, including another exhaustive 512 two-variable CNFs, pass.
Independent replay checks all eight matched arms, 2,957 ordinary decisions and
414 composed records. All 21,482 native keys are preserved, with no new key or
alternative payload: the checkpoint references the existing compressed archive
instead of duplicating it. Eight additional sidecar records preserve both policies.

Resume [the checkpoint](../experiments/results/cnf-terminal-first-complete/checkpoint.json).
All 443 prior sources and 4,843 artifacts / 84 manifests remain unchanged.
Structural authorities and the 64 prior manuscript proof blocks are unchanged.
No new Lean theorem, fresh coverage result, global minimum-cost guarantee or
uniform polynomial algorithm is claimed.
