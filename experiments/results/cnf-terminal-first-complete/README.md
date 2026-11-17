# Terminal-first screening and conditioned-core discovery

Resume `checkpoint.json`. It preserves **all 21,482 native keys** and references
the preceding compressed archive directly: no new native payload, duplicate
archive or alternative certificate is needed. Eight composed sidecars retain
both control policies, alongside 406 prior composed and 2,957 ordinary decisions.
Native source-root lookup alone need not find a composed answer.

`TerminalFirstScreen` runs unit propagation on the unsplit target before posting
searches, core reads or branch construction. A conflict uses the existing saved
trace publisher and unchanged native verifier to publish one proof. Prepared
core-index construction still occurs and is charged. Nonterminal selection uses
the previous gate, ordering and budgets without repeating the baseline probe.

Eight historical exact-prefix arms compare the previous screen with terminal-first
reuse. On case 176, rows fall **3 -> 1**, native payload **6,137 -> 2,229 bytes**,
propagation visits **5,289 -> 1,110**, posting visits **3,585 -> 0**, core reads
**2 -> 0**, and examined plans **4 -> 0**. Explicit trace checking falls 68 -> 64
literal visits. The new certificate exactly matches the original single-clause
baseline's native proof. Cases 6/68/135 retain identical plans, deltas, composed
records and screening operation counts. Both case-176 policies have zero
expanded_nodes: proof publication is still real work and must be counted.

Case-176 delta-plus-decision bytes fall 23,918 -> 17,922. Screening samples are
4.17 / 0.50 ms, but complete samples 6.55 / 6.63 seconds, dominated by preparation
and cold replay. No tests, builds or profiling overlapped production. One sample
per arm establishes no stable total speedup, fresh coverage or peak-memory result.
The earlier native baseline already solved this target cheaply; this fixes
unnecessary added work.

A separate read-only probe reconstructs cases 43/172/70 after their extra guard.
They account for 10/9/4 expansion calls. No further single-clause candidate is
found; cases 43/172 have no eligible raw-core plan. Conditioning checked negative
cores under the same assignments reveals **two-clause gaps in all three cases**.
Case 172's core-209 cofactor has three clauses / four literals and is already
native-checked at the original prefix. Case 43's nearby restricted roots are
not yet available. Guard-only and post-unit passes visit about 32,000 restriction
literals per case, plus proof reads, normalization and matching. This is a
charged diagnostic scan, not an efficient deployed recognizer.

Next, price conditioned-core matching on cases 43/172. Supply checked restriction
certificates or charge acquisition for missing roots; lift models through all
fixed assignments. Compare against ordinary clause splitting, because a tiny
negative core with two missing unit clauses may merely encode that split.
Cache projections only with bound parent identity, exact assignment and checked
variable transport. The probe publishes no new premise, child proof or answer.
The initial narrower probe is also retained for comparison.

Reproduce the complete workflow from the repository root with a new directory:

```sh
python3 experiments/run_cnf_terminal_first.py compare /tmp/new-terminal-first
python3 experiments/run_cnf_terminal_first.py validate /tmp/new-terminal-first
python3 experiments/analyze_cnf_terminal_first.py /tmp/new-terminal-first
python3 experiments/probe_cnf_guarded_residuals.py /tmp/new-terminal-first
python3 experiments/finalize_cnf_terminal_first.py /tmp/new-terminal-first
```

The unwrapped comparison is retained in `../cnf-terminal-first/`: it completed
six nonterminal arms before the exclusive archive helper rejected reuse of an
existing temporary destination at the second cohort. Its source, protocol,
outputs and failure log are preserved. The wrapper refreshes only destinations
successfully restored earlier in its own invocation, after readers close.
Independent validation confirms semantic parity of all six incomplete-run arms
with the complete run. It also compares current baseline deltas to the older
preserved controls and the regression's native proof to the original baseline.

Before committing, one extra blank line at the end of the new selector source
was removed. `source-normalization.json` binds both hashes, verifies identical
Python ASTs, and retains the original executed source and all earlier records in
`before-source-formatting.tar.gz`. Protocols explicitly record this qualification;
independent replay is repeated against the normalized source. Measured algorithms
and operation counts are unchanged.

`protocol.json` binds **448 runtime sources**, including the wrapper. The final
source ledger binds **451 files**, adding analysis, discovery and preservation
scripts. Each arm retains the strict-prefix digest, native delta, checked composed
record, propagation traces, all stage counts/times and complete cold audit.
Rebuild from the bound historical initial archive and exact append prefix; the
latest union already contains the historical answers and is not a valid cost
comparison starting point. Both incomplete and complete result directories are
covered by the new manifest.

All **1,047 full-suite tests** and twelve focused tests pass, including exhaustive
truth-table agreement on all 512 two-variable CNFs, nonterminal parity, disabled
budgets, pending proofs, trace tampering and no-repeat propagation. The full suite
retains 44 existing unclosed-SQLite ResourceWarnings; focused tests emit none.
Independent replay checks eight arms, 2,957 ordinary and **414 composed records**
without fresh search/publication. Four frontier lineages are unchanged:
ready/pending **131/39 original, 138/69 legacy, 81/95 causal, 81/122 expanded causal**.

All **443 earlier sources / 4,843 artifacts / 84 manifests** remain unchanged.
The checkpoint changes only parent/source bindings, adds two terminal-first
fields and preserves the previous archive binding. Structural authority remains
2,614 patterns / 259 pairs / 17 missing children; original 17/24 / 999 and
supplemental 24/24 / 208 stay separate. The paper builds to **205 pages**, with
**64 unchanged proof blocks** and no overfull/undefined/LaTeX warnings. No new
Lean theorem, arbitrary-SAT bound or minimum-cost claim is made.

See [the research analysis](../../../research/terminal-first-screen.md).

New manifest: **73 artifacts** across complete and incomplete runs. Next preservation audit: **4916 artifacts / 85 manifests**.
