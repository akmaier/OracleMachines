# Check the restricted child before acquiring a local guard

The optional child-admission gate repairs the observed case-144 regression at
an identical saved state. It retains two positive controls but rejects useful
nonterminal children too. This is a controlled policy experiment, not evidence
that expansion is uniformly cheap or that the gate improves a fresh stream.

## Policy and exact scope

After shared ordinary and near-guard preparation, inspect an unknown target.
Preserve native handling of syntactic two-CNF, Horn and dual-Horn sources. A
single scan records these predicates; target lookup, normalization and source
eligibility are charged. Tautological source clauses use native fallback because
the existing source-bound deletion-guard interface excludes them.

For other targets, use the fixed four-variable binary-incidence ranking from
[local discovery](local-guard.md). A unit-refuted premise proposes a forced
assignment. Before publishing it, inspect the restricted child: admit an existing
checked native answer or a retained unit-conflict trace; otherwise reject without
publishing either proposal. Reuse both premise and child traces when admitted.
The native checker and unchanged guard-chain format establish the answer and
lift positive models. Discovery failure or rejection is not an UNSAT verdict.

For an admitted guard, publication inserts at most two native rows: at most one
for its retained unit-refuted premise and at most one for its unit-refuted child.
An already checked child needs no new row. No general child expansion occurs in
this path. This bound excludes earlier preparation, fallback, checked-dependency
loads, the size of keys/traces and composed sidecars. It is not an optimality
claim: native solving can sometimes require fewer rows. With variable budget b,
there are at most 1+2b discovery propagation calls and one child propagation call.
The checked lookup may traverse a large stored proof; it is not constant-cost.

## Equal-state measurements

Eighteen arms cover three earlier historical cases and three selected cases
from the preceding 192-query trial. Each policy starts from identical native
rows and an empty checked-node cache, then checks the same accepted guards.
Fresh-trial prefixes include only their recorded ordinary/near preparation.
No later native result leaks into these controls. These six cases are selected
retrospectively; no new excluded query stream was measured in this run.

| Case | Native baseline rows | Unconditional local rows | Admitted rows | Admission outcome |
| --- | ---: | ---: | ---: | --- |
| Historical 43 | 10 | 7 | 10 | Reject nonterminal child |
| Historical 70 | 4 | 5 | 4 | Reject nonterminal child |
| Historical 172 | 9 | 7 | 9 | Reject nonterminal child |
| Prior fresh 144 | 3 | 11 | 3 | Reject nonterminal child |
| Prior fresh 167 | 8 | 2 | 2 | Accept unit conflict |
| Prior fresh 190 | 4 | 2 | 2 | Accept unit conflict |

For the three prior fresh controls, admitted rows fall 15 -> 7 relative to both
baseline and unconditional local discovery. Added native bytes are
28,490 / 23,872 / 12,840 (baseline / local / admitted); serialized deltas and
records are 78,189 / 90,645 / 73,439 bytes. The admitted path uses three general
expansions plus four explicit trace publications. Cases 167/190 each have zero
child expansions because the checked child trace is published directly; their
native rows and propagation equal the unconditional local path. This is trace
reuse, not elimination of all work.

Counted propagation for those three controls is 4,821 / 5,984 / 5,285 visits.
The gate saves work against unconditional local discovery but still exceeds
native baseline propagation because rejected case 144 is probed before fallback.
In the historical controls it rejects all proposals: rows are 23 / 19 / 23,
while propagation is 4,501 / 5,763 / 8,666. Thus it loses the useful 43/172 guards
and nearly doubles historical propagation against baseline.

Single-sample evaluation totals for the prior fresh controls are approximately
0.01994 / 0.02068 / 0.01795 seconds, and complete arm totals are
0.751 / 0.746 / 0.755 seconds. These do not establish a stable speedup. Prefix
reconstruction costs 0.922 seconds separately; original discovery/preparation
costs remain in the bound earlier trials. Cold replay here checks each selected
composed result, rather than the entire previous catalog. Do not compare these
arm times directly with the earlier complete 192-query worker times. Full
inherited cold validation is separately retained in reconstruction.json.

## Remaining structural gap

A posthoc diagnostic normalizes each rejected child after unit propagation.
All four remaining roots are absent from the exact prefix and outside the
syntactic two-CNF, Horn and dual-Horn families:

| Case | Forced unit steps | Remaining variables | Clauses | Literals |
| --- | ---: | ---: | ---: | ---: |
| Historical 43 | 10 | 12 | 23 | 53 |
| Historical 70 | 2 | 19 | 44 | 111 |
| Historical 172 | 3 | 20 | 45 | 112 |
| Prior fresh 144 | 2 | 22 | 58 | 161 |

An absolute monotone literal-count threshold cannot accept beneficial case 172
while rejecting regressing case 70: the latter has fewer remaining literals.
These observations do not rule out richer relative or structural criteria.
Recognition of useful nonterminal children must account for their proof structure
and reusable dependencies, rather than size alone. Cached dependency transport
through conditioning remains open; no such transport is implemented here.

Next, test this fixed gate on another excluded query set with repeated and novel
structure, keeping all six exact-prefix controls. Charge failed probes and
fallback, including opportunities to reuse their existing propagation traces.
Investigate bounded child proofs or checked dependency reuse with explicit
recognition/publication budgets; do not fit an untested threshold to these six
cases. Compact sidecar references and shared cold checking remain supporting
cost targets. Keep the gate optional until measured total costs justify admission.

## Preservation

Resume `experiments/results/cnf-child-admission/checkpoint.json`. It retains the
same 21,801-key native archive byte-for-byte: all control payloads were already
present in the preceding union. Eighteen new composed records preserve every
arm, alongside 828 earlier composed records, 2,957 ordinary decisions and six
projections. All 475 prior sources / 5,115 artifacts / 88 manifests and four
frontier lineages pass preservation. Structural coverage authority is unchanged.

All 1,076 tests and 19 focused tests pass. The new suite includes 512 guarded
mixtures and transported versions (1,024 representations), known positive-child
lifting, native-family priority, no-publication rejection and tautology fallback.
The full suite retains 44 existing SQLite ResourceWarnings. No new Lean theorem,
minimum-cost guarantee or unrestricted-SAT resource bound is added.
