# Preserving proof order during affected-clause propagation

The previous profile identified first-time unit propagation as the largest named
own-time cost on the expensive unresolved source. This experiment accelerates
that acquisition while retaining the exact original proof trace. Clause-counter
updates through occurrences are established: [Chaff, Section 2](https://www.princeton.edu/~chaff/publication/DAC2001v56.pdf)
describes them before presenting watched literals. This is a compatibility and
resource-accounting experiment, not an algorithmic novelty claim. It does not
change the discovered structural classes, the independent proof checker or the
ordinary residual SAT solver.

## State and update rule

For each clause, maintain its number and signed sum of unassigned literal
occurrences, plus a satisfied flag. The count and sum need only remain accurate
for unsatisfied clauses. A signed-literal occurrence map lists clause IDs, with
multiplicity. Assigning literal l first marks clauses containing l satisfied;
it then subtracts each occurrence of -l in the remaining unsatisfied clauses.
A count of one identifies the remaining literal through the sum; zero is a
conflict. Marking satisfaction first handles tautologies. Counting occurrences,
rather than distinct variables, preserves the old routine's behavior on raw
clauses with repeated literals.

The old engine scans clauses by increasing ID, then repeats the scan if it made
any assignment. It therefore imposes a proof-order policy as well as computing
a closure. A generic unit queue may change reason clauses, the first conflict,
subsequent learning selection and persistent identities even when satisfiability
is preserved.

The replacement uses events ordered lexicographically by (scan round, clause ID).
Every initial unit or empty clause is scheduled in round zero. If assigning at
position (r,i) first makes clause j actionable, schedule (r,j) when j>i and
(r+1,j) otherwise. A scheduled clause is not rescheduled if it subsequently loses
its last literal; the same event will report that conflict. Discard an event if
the clause became satisfied. Each clause is queued at most once: after an
unsatisfied unit event the clause is satisfied permanently, and after an
unsatisfied empty event the routine terminates.

Two early exits are exact. With no initial unit or empty clause, no assignment
can begin and no index is built. If an empty clause precedes the first initial
unit, the original scan also reports it with an empty assignment and trace.

## Trace equivalence argument

Assume the two routines have produced the same trace prefix and have not stopped.
Their assignments agree. For every unsatisfied clause, the maintained count and
sum describe exactly the literal occurrences unassigned under that assignment:
this holds initially and each assignment removes precisely its false occurrences,
after satisfied clauses are marked. Thus both routines agree on whether each
clause is satisfied, empty, unit or non-actionable, and on any forced literal.

A clause can first become actionable only initially or because the most recent
assignment removed an occurrence. The scheduling rule places it at the next
position where the repeated scan would inspect it. Counts cannot increase and
satisfaction cannot be undone. Consequently, before the least scheduled
unsatisfied event there is no unit or conflict that the old scan could act on.
Discarding satisfied events has the same effect as skipping satisfied clauses.
At the next event, both routines therefore append the same literal/reason pair
or return the same first conflict. This extends the induction. If no event
remains, no unsatisfied unit or empty clause remains; the old scan's final
possibly empty pass adds no trace entry either. Both return the same assignment,
trace and conflict index.

This is an algorithm-level argument supported by exhaustive differential tests.
It is not a Lean refinement of this Python implementation. The existing
independent reason checker still validates every newly acquired certificate.

## Resource account and limitations

Let m be the clause count, L the literal-occurrence count and v the variable
count. A no-unit call inspects m lengths without constructing an occurrence
index. Otherwise construction scans L occurrences and allocates O(1+L+m+v) words
of transient state under a word-size input model. Each variable is assigned at
most once, so at most L occurrences are visited in all assignment updates. There
are at most m event insertions and m removals. With constant-time dictionary
operations and word arithmetic, the resulting bound is O(1+L+m log(m+1)) work and
O(1+L+m+v) extra space. The repeated-scan reference may instead inspect O((v+1)L)
literals. These are bounds on one propagation call, not on SAT search or an
entire expansion.

The Python dictionary implementation does not provide adversarial constant-time
lookup for arbitrary integer labels. Long labels also incur hashing, signed-sum
arithmetic and comparison bit costs; a sum can need b+log(w+1) bits for b-bit
literals and width w. The conditional word-operation account does not erase
these costs. Counters distinguish clause-length inspections, index entries,
affected occurrences and heap events; they are different operations, not a
single comparable instruction count. Actual preparation and all such work are
included in operation timing. Per-query peak counters must be maximized, not
summed, to obtain a run-wide maximum.

Every call builds and discards its own index. This guarantees fresh bindings
under arbitrary edits or assumptions, but does not yet share preparation across
related probes. An early conflict following a unit can make full-index
construction unnecessary work relative to the scan engine. The control suite
retains that regression. There is no claim of pointwise speed dominance.

The optional inventory scopes its engine with a ContextVar around ordinary/probe
discovery and ordinary rediscovery during certificate checking. Nested calls and
exceptions restore the preceding engine; the default baseline and separate SAT
decider retain their existing propagation. No persistent format, recognition
policy, budget, source identity or proof-order change is introduced.

## Evidence

The [pilot](../experiments/results/cnf-ordered-propagation-pilot/README.md) checks
eight matched sources and identical cold archive replay. The
[full study](../experiments/results/cnf-ordered-propagation/README.md) records
matched acquisition, warm reuse, cold replay, allocation, repeated timing and
adversarial propagation controls. Full-source structural coverage is unchanged;
this work reduces the cost of the existing discovery experiment.
