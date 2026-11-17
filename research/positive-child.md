# Publish a target model recovered from a positive child

The optional selector now recovers a satisfying target assignment when a
proposed child closes positively under its saved unit trace. At case 146's
exact prefix this replaces six native rows with one, without acquiring the
negative premise or child node. The next 192-query stream has no activation
of the new route and gives no fresh storage or stable timing improvement.

## Checked reconstruction

The preceding discovery policy still produces the proposal and child trace.
If the child has no conflict and reports zero residual literals, the new path
independently binds it to the proposed restriction, checks every unit reason and
requires the actual restricted CNF to have no remaining clauses. It maps the
child assignment back to target coordinates, restores the proposed condition,
fills unused variables and checks every clause of the full target.

Publication checks that full-target model again before storing an ordinary SAT
node through the existing native verifier. It performs no child search and
adds at most one target row after earlier preparation. Existing accepted guards
remain in the composed result and their source-level witness is checked. The
new proposed negative premise is not acquired: a full satisfying assignment
already certifies the target. Negative results retain their existing proof
obligations; this shortcut supplies no UNSAT inference.

Proposal discovery, its negative unit probe, normalization, model lifting,
reason checking, source verification, serialization and persistence all remain
charged. The method does not guarantee that such a child exists or that finding
it is cheap on arbitrary CNF. Other recognition and fallback choices remain
unchanged. There is no new certificate format or Lean theorem.

## Exact-prefix controls

Thirty-nine arms compare native baseline, retained-prefix discovery and positive
model recovery on thirteen saved prefixes. They retain the prior nine controls
and add the preceding stream's 0/131/146/159. Original preparation is shared
outside the arm; prefix reconstruction, guard replay and copying are recorded.

| Case 146 measure | Baseline | Previous policy | Positive child |
| --- | ---: | ---: | ---: |
| New native rows | 6 | 6 | 1 |
| Added native bytes | 6,688 | 6,688 | 1,798 |
| Serialized delta/record bytes | 30,595 | 30,595 | 25,527 |
| Propagation literal visits | 1,847 | 3,304 | 2,045 |
| Expansion calls | 6 | 5 | 0 |
| Trace / model publications | 0 / 0 | 1 / 0 | 0 / 1 |
| Evaluation seconds, one sample | 0.006706 | 0.007754 | 0.004768 |

The 26 child unit deductions now yield a checked whole-target model. New native
rows fall by five and native bytes by 4,890 (73.12%). The serialized delta/record
saving is 5,068 bytes (16.56%). Visits fall 38.11% against the preceding policy,
but still exceed native baseline by 198 visits. Zero expansions include one
explicit model publication and the paid discovery/checking work. The timing
sample is not a stable speedup result.

The other twelve controls preserve the preceding policy's native payloads.
Across all thirteen, previous/new rows fall 88 -> 83, native bytes
118,329 -> 113,439, and propagation visits 39,448 -> 38,189. Native baseline uses
96 rows but only 23,795 visits. Discovery overhead and useful nonterminal
children rejected by the gate remain unresolved.

## Fresh stream: known targets dominate after preparation

The generator selects 64 double-deletion neighbours per old template, excluding
all inherited query and native roots, including 1,280 previous query roots per
template. Selection takes 1.583 seconds separately. Six fresh workers run
baseline/retained/positive and the reverse order. Tests, profiles and builds do
not overlap production. All policies answer 93 SAT and 99 UNSAT queries.

Every policy adds the same 197 native rows and 441,084 native bytes, with identical
native payloads. Ordinary preparation adds 195 rows; target acquisition adds
two. After preparation, 190 of 192 target roots are already known. Only two
queries reach optional discovery: one known propagated residual and one unit
conflict. Both preceding and new policies publish their saved traces, reducing
native expansion calls from two to zero without changing propagation (1,831
visits) or storage. The new positive-model route never activates. Warm replay
acquires no rows.

| Mean measurement | Baseline | Previous policy | Positive child |
| --- | ---: | ---: | ---: |
| Query seconds | 0.828 | 0.794 | 0.834 |
| Full cold replay seconds | 10.282 | 10.111 | 10.107 |
| Complete worker seconds | 21.126 | 20.697 | 20.700 |
| Process peak RSS, MB | 793 | 729 | 793 |

The two complete-time differences against the preceding policy are +0.399 and
-0.394 seconds. No stable timing or memory gain follows, and no timing difference
can be attributed to successful model recovery here. Process RSS is not a
live-state bound. Every database uses 73,793,536 bytes and every compressed
archive 5,266,412 bytes. Serialized query/warm records differ slightly through
timings and accounting metadata: means 5,305,437 / 5,328,746 / 5,328,722.5 bytes.

## Next gaps

This stream tests preservation and reuse within familiar templates, but scarcely
tests acquisition of new residual structure. Raw query novelty is not child
novelty after preparation. The next evaluation should add different template
families and report target familiarity before optional discovery, alongside
matched discovery, preparation, checking and cold costs. Preserve these already
covered cases as warm-reuse controls rather than calling them arbitrary-SAT
coverage.

Retain case 146 as a positive model-recovery control and earlier cases 0/131/159
as unresolved structural controls. The latter still have nonfamily children
after the proposed condition and propagation. Price alternative small
conditioning sets and reuse of cached dependencies at those exact prefixes,
with the prior case-36 two-CNF decomposition as a positive structural control.
The complete single-variable test for immediate syntactic two-CNF did not close
the four earlier baseline residuals; it did not test further propagation or
mixed-family closure. No small-decomposition guarantee for every CNF follows.

Cold checking remains the largest complete-time component. Shared verification
and compact source references remain supporting targets. The current result
establishes a checked saving for one known case, not broad fresh coverage,
uniform polynomial expansion or a P-versus-NP result.

## Validation and resume point

All 1,102 tests and 26 focused tests pass. The new tests cover full-target model
transport, empty children, baseline prefixes, disabled leaves, corrupted child
traces, invalid models, zero search budget, cold replay and 256 small clause
subsets in two representations. Independent validation reconstructs all 39
control prefixes, regenerates the excluded catalogue, checks each selection and
lifted model, and validates native/composed proofs and warm/cold replay without
acquisition. Other control choices retain their preceding native payloads.

Resume `experiments/results/cnf-positive-child/checkpoint.json`: 22,729 native
keys, all 22,532 previous payloads preserved, 615 new composed records alongside
2,430 earlier composed records, 2,957 ordinary decisions and six projections.
There are no alternative payloads. All 493 prior sources, 5,455 artifacts and
92 manifests remain unchanged. Ready/pending frontiers are 132/38 (active),
141/66 (extended), 86/90 (causal) and 86/117 (incremental causal); these are
retained-bank availability counts, not new structural authority. Original and
supplemental structural coverage are unchanged.

The evidence union occupies 73,793,536 database bytes and 5,266,420 compressed
bytes. It preserves all arms rather than describing a single policy's working
storage. The 209-page paper builds cleanly and retains all 64 previous proof
blocks. No new Lean theorem or unrestricted-SAT bound is established.
