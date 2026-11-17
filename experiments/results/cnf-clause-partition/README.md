# Exact first-false partition experiment

This checkpoint adds checked composition of branches from a negative strengthened
premise T AND C1 AND ... AND Ck. Branch i holds C1,...,C(i-1) true and fixes every
literal of Ci false. The resulting lifted assignments form an exact disjoint
cover of models of T. Residual CNFs without those fixed literals need not be
disjoint. Every branch must be checked negative for UNSAT; a SAT child gives a
lifted original-source model and permits stopping. Native proof formats stay
unchanged; composed answers require the checked partition sidecars.

Eleven historical arms restore exact persistent prefixes for cases 68, 6 and 135
from the preceding premise-first stream. Every arm repeats ordinary preparation
and the failed single-clause selector. Baselines match the original native proof
payloads exactly. Eight candidate plans test the diagnosed nearest ready cores
in forward and reverse order, adding one checked strengthened-premise row each.
Branches share native results within each plan, without cross-plan sharing.

- Case 68: baseline 27 expansions; four plans use **21 / 24 / 21 / 11**. The best
  observed plan adds twelve rows and 16,605 native payload bytes, versus 27 rows
  and 32,827 bytes. Delta-plus-sidecar size falls 49,672 -> 35,676 bytes.
- Case 6: baseline seven expansions; forward/reverse use **seven / three** and
  add eight/four rows. The forward order regresses in retained evidence.
- Case 135: baseline seven expansions; both plans regress to **eight / ten**,
  adding nine/eleven rows. The smaller missing-clause count is not sufficient.

Trying all candidates costs **105 expansions** versus 41 for the baselines.
Best observed partitions total 22, or 21 with baseline fallback for case 135.
Those choices are post-hoc: no efficient selector or fresh-query gain is claimed.
All regressions and every tested plan remain retained. Single-sample query-phase
costs are about 7–22 ms, while full cold replay costs 5.02–5.30 seconds per arm.
No stable total runtime or peak-memory gain follows.

Reproduce from the repository root with a new output directory:

```sh
python3 experiments/compare_cnf_clause_partition.py /tmp/new-clause-partition
python3 experiments/validate_cnf_clause_partition.py /tmp/new-clause-partition
python3 experiments/analyze_cnf_clause_partition.py /tmp/new-clause-partition
python3 experiments/probe_cnf_partition_propagation.py /tmp/new-clause-partition
```

`protocol.json` binds the historical initial archive, prior full trial/query
stream and diagnosis, as well as 433 runtime sources. Reconstruct each arm from
that initial archive, the strict append prefix before its case, and the retained
`delta.json`. Do not substitute the latest union when comparing historical costs:
it already includes later results. Each arm also retains its checked record,
branch metrics, phase times and complete cold audit. Prefix reconstruction and
snapshot/export overhead remain in aggregate study time; preparation, premise
checking/publication, branch construction/solving, composition, warm-bank setup
and lookup, serialization and cold replay have separate measurements. Original
acquisition and inherited discovery remain additional costs. No tests, builds or
profiling overlapped timed production. No peak RSS was measured.

`cost-attribution.json` preserves all plans, regressions, candidate acquisition
cost and post-hoc best outcomes. Native payload means identifier plus ASCII JSON
length; retained trial bytes mean delta plus sidecar. Neither is live memory or
the full historical storage cost. A copied source/guard record and canonical
child keys are not constant-size certificates.

The read-only propagation probe reconstructs candidate branches, runs the frozen
unit propagator without search/publication and compares its traces/conflicts to
the independently checked native child certificates. Case 68's best plan has
two terminal conflicts plus a 122-literal unresolved residual; another two-conflict
plan leaves 153 literals. Case 6's better order makes all three branches terminal.
Case 135 remains a counterexample: a 117-literal residual costs more than its
158-literal baseline. Next, price bounded screening and reuse its unit traces,
then test fresh inputs with all recognition costs included. The probe implements
neither a selector nor a cheaper proof producer.

All **1,035 full-suite tests** and fourteen focused tests pass. Exhaustive coverage,
SAT-after-negative-branch, model lifting, cold lookup and tampering controls are
included. The full suite retains 44 older unclosed-SQLite ResourceWarnings;
focused tests emit none. Independent validation reconstructs all eleven arms,
checks every native proof and both measured index lineages, rebuilds branches
without the partition constructor, and replays 2,957 inherited ordinary decisions,
200 inherited chain records and eight new partition records without fresh search.
The eight records describe three known sources and alternative plans.

Resume `checkpoint.json`: **21,225 native keys**, 97 added and every prior 21,128
payload preserved. No alternate native certificates occur. `union-partitions.json`
is required for composed reuse through `PartitionBank`, which verifies records
on load and assumes an exclusively owned immutable or append-only proof session.
The native source root need not exist. Earlier ordinary and chain catalogs remain
bound unchanged. The union occupies **66,703,360 SQLite / 4,911,472 gzip bytes**;
it preserves all old proofs rather than shrinking to a post-hoc best policy.

All four retained frontier lineages pass: ready/pending counts **130/40 original,
137/70 legacy, 79/97 causal and 79/124 optional expanded causal**. Structural
authority stays 2,614 patterns / 259 pairs / 17 missing children; original coverage
is 17/24 with 999 steps, supplemental coverage 24/24 with 208 steps. No support
origins or discovery pointers are replaced. Prior semantic checkpoint fields
remain, except parent/union/source bindings; two partition fields are added.

The source ledger binds **435 files**, including two post-hoc analysis files.
All **429 prior sources / 4,706 artifacts / 82 manifests** pass preservation.
The paper builds to **204 pages** with all **64 prior proof blocks unchanged**
and no overfull/undefined/LaTeX warnings. No new Lean theorem, arbitrary-SAT
polynomial bound or minimum-cost expansion result is claimed.

New manifest: **56 artifacts**. Next preservation audit: **4762 artifacts / 83 manifests**.
