# Close native residuals before expanding saved reasoning

Checkpoint: 25 November 2026. Bounded ordinary unit propagation now checks
whether a canonical source residual already has a short native contradiction
before the compiler expands its saved layered reasoning. On the eleven existing
B4-feedback roots, complete local trial time falls **78.35%**, encoded proof
bytes **80.33%**, and records from **2,246 to 306** versus the unchanged compiler.
Both independent readers accept all resulting certificates. Coverage remains
**217/246**, with **29 unresolved**; no new search or recognized family is added.

The new method also beats fresh bounded solving in aggregate on these positives:
complete time falls 65.27% and bytes 80.19%. One case, `new-28-62`, remains slower
than fresh solving. Acquisition, discovery and unresolved fallback are excluded
from that comparison, so it does not establish a complete workload advantage.

## Why this was the next cost target

The [previous feedback study](cursor-feedback.md) found 12 additional recognized
events but made their native proofs expensive: 2,065 split nodes and 60% more
complete trial time than fresh solving. The two biggest byte-growth cases were
`new-28-62` and `new-61-70`. Profiles of the unchanged compiler show 362 and 527
trace splits respectively. On the latter, 1,070 frame constructions, 2,126
canonicalizer calls and 3,045 source restrictions dominate the profiled path.
The instrumented profiles are preserved separately and are not benchmark times.

The compiler previously checked for an empty clause, then expanded saved unit
reasons through the earlier banks and binary splits. Many intermediate source
residuals could already be refuted by ordinary unit propagation. A direct unit
certificate summarizes that contradiction using fewer native nodes. This avoids
building and later checking a larger derivation of the same negative answer.

## Exact contract and resource allowance

Incoming source, guards, old failure proofs, all closure layers, cursor binding
and the B4 conflict are checked as before. Support selection is unchanged. At a
trace-walk entry, the compiler constructs the canonical source residual and
checks for an existing native record or empty clause first. The optional new
step runs unconditional unit propagation on that residual alone. A conflict
publishes the ordinary native `units` rule with clause-indexed trace and conflict.
The unchanged native verifier checks the proof before inserting it. No derived
bank unit is silently admitted as a source clause.

An open or interrupted attempt publishes nothing and falls back to the original
layered compiler. Partial assignments are discarded. Each attempt builds its
own occurrence index; there is no cross-context index, negative-result cache or
new persistent proof format. The previous publication-only immutable header
handoff remains in use; all child relations and independent cold checks remain.
Warm reuse still validates the supplied old provenance before returning the
cached whole-root result. Exclusive synchronous solver use remains the inherited
publication-handoff contract.

One allowance per inner compilation charges each scanned gate clause, then
index clause/literal slots and propagation occurrence visits. The experiment
allows 262,144 charged work units and 256 retained unit-trace steps per attempt.
An index is built only if the gate found a unit and its whole construction charge
fits the remaining allowance. Gate work is charged even when index construction
is rejected. When the allowance is exhausted, further candidates fall back.
This allowance excludes the unchanged source/frame preparation, old provenance
checking, publication, native verification and outer binary-prefix lifting.

With K trace-walk entries and allowance B, additional gate/index/propagation
work is O(K+B) expected word work, plus the native checking/publication of accepted
shortcuts. One index is live per attempt, with O(C+L) slots for its current C
clauses and L occurrences, plus the bounded trace. The number of baseline contexts
K, total retained proofs, encoded integer costs and lifetime storage are still
unbounded. A fallback can lose time; this is not a uniform improvement theorem.

## Matched evidence

The eleven parent cases are unchanged and were exposed during the pilot. Four
methods run in forward and reverse order per case, giving **88 isolated trials**:
fresh bounded solving, the unchanged B4 compiler, shortcut attempts only at entry
to a proof layer (`layer`), and attempts at every trace-walk entry (`all`). The
disabled candidate exactly reproduces the baseline's payloads and counters in
the pilot and tests. Both measured controls reproduce their parent checkpoint's
deterministic counters and authority tables.

| Summed per-case means | Fresh | Baseline | Layer entry | Every entry |
| --- | ---: | ---: | ---: | ---: |
| Solve/compile (s) | 1.17547 | 2.25700 | 1.13853 | 0.46211 |
| Warm check (s) | 0.01771 | 0.09758 | 0.09795 | 0.09722 |
| Cold readers (s) | 1.27065 | 1.71485 | 0.87909 | 0.36093 |
| Persistence (s) | 0.43069 | 0.60803 | 0.28093 | 0.07730 |
| Complete local trial (s) | 2.93913 | 4.71358 | 2.43027 | 1.02071 |
| Encoded key/payload bytes | 5,702,467 | 5,744,105 | 2,910,847 | 1,129,929 |
| Records | 489 | 2,246 | 1,004 | 306 |

Every-entry shortcuts reduce compile time 79.53% and complete time 78.35%
against baseline. All eleven cases improve in compilation, complete time and
bytes against both baseline and layer-entry-only attempts. Against fresh solving,
ten improve in runtime and all eleven in bytes. Preserve the exception:
`new-28-62` takes 0.13321 seconds complete versus 0.10758 fresh, despite shrinking
to 172,078 bytes versus 184,766. `new-61-70` shrinks from 1,585,067 to 296,342
bytes and from 1.23575 to 0.20024 seconds complete versus baseline.

The every-entry method makes 244 unit attempts: 112 produce direct conflicts
and 132 remain open and fall back. Another 26 candidates have no unit. No work
or trace cap interrupts these trials. The additional gate/index/occurrence charge
is 124,853 units summed over eleven separate allowances. Native trace splits
fall from 2,065 to 148, frames from 4,255 to 317, native normalization visits
from 1,534,343 to 199,899 and native restriction visits from 777,206 to 91,478.
All 306 produced records still receive ordinary native verification. Fewer
verified nodes reflect smaller proofs, not omitted checks.

Peak process RSS is 88,752,128 bytes fresh, 75,661,312 baseline, 66,961,408
layer-entry and 53,985,280 every-entry. These are local positive-worker maxima,
not a general memory guarantee. Isolated archives may duplicate records that
could be shared. The old larger certificates remain preserved; the experiment
does not delete or shrink cumulative history.

Complete local trials include setup, compilation, warm checking, both cold
readers and serialization. Input loading/startup, earlier acquisition/discovery,
unresolved fallback and final audits are additional. Two orders are descriptive
evidence, not a statistical production guarantee or a new complexity result.

## Validation and continuation

Both independent cold readers verify **44 unique archive/root pairs**, and table
digests are stable across repetitions and warm lookups. All **1,961 solver tests**
and **96 focused tests** pass. Tests exhaust all 512 formulas formed from the nine
non-tautological clauses on two variables, including the empty clause. They also
check full/support compilation, guards, sparse coordinates, shared budget with
separate contexts, forced budget fallback, corrupted native traces and rejection
of malformed old provenance before warm reuse. All 64 existing manuscript proof
blocks remain byte-identical. The audit preserves 1,090 earlier sources and 191
manifests covering 26,477 artifact entries; the new source ledger has 1,094 entries.

Carry the every-entry variant forward as the measured **B4 proof-compilation
baseline**, with caps, fallback and all checks intact. Production defaults remain
unchanged. Broader proof layers, novel SAT categories, growing instances and
streams with little unit closure still require evaluation. Repeated warm
provenance preparation remains visible, but its cost alone does not justify a
cache without exact binding and a matched total-cost test.

The next coverage target remains the **19 strengthened open B4 closures**. Their
old B3 skip histories cannot be reused on changed banks. The other ten cases
need untried candidates or stronger interaction. Resume from
`experiments/results/cnf-direct-unit-closure/checkpoint.json`; its inherited
`cursor_feedback` entry still binds the complete 29 open states in
`experiments/results/cnf-cursor-feedback/remaining-closures.json`. The new
`analysis.json`, profiles, pilot and native archives preserve measured gains,
open-attempt costs and the fresh-solving regression.
