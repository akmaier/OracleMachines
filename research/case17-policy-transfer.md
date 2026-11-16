# Policy transfer and the cost of retaining unrelated history

The unchanged nested refinement policy closes case 17 in one bounded batch,
raising structural coverage from **6/24 to 7/24**. A matched history control
shows that the records acquired for case 16 do not reduce this acquisition:
both histories produce identical new records, choices and target proofs.
This establishes transfer of the scheduling policy on this development input,
without establishing useful transfer of case-16-specific stored components.

## Comparison and accounting

[The frozen protocol](../experiments/results/cnf-case17-transfer/protocol.json)
continues the selected 60-variable / 255-clause / 765-literal residual. Both arms
use the unchanged `NestedRefinement` implementation and allow at most four
batches, each with 128 distinct recognition admissions and sixteen pair attempts.
Source assumptions are charged separately. The retained arm starts from the
complete 1,701-pattern / 162-pair union; the control starts from the pre-case-16
1,154-pattern / 96-pair union. Both already contain the same four case-17 source
splits. The omitted 547 patterns and 66 pairs are precisely the successful and
unsuccessful acquisitions of the case-16 investigation.

Two repetitions reverse arm order. Each stream runs in a fresh Python process.
Case 17 was selected from known unresolved development inputs; this is neither
a new holdout nor an estimate of generalization across arbitrary CNFs. No policy
change or tuning was made after inspecting its outcome.

Both arms close the target after **89 admissions / 89 new patterns / 9 new pairs /
18 fresh source assumptions / 531 probes**. Neither reaches a limit. The
incremental record payloads, selected operations and target proofs match exactly,
including across the two repetitions. Each arm gains one original: the retained
arm reaches 7/24 and the older-history control reaches 6/24 because it starts one
covered original lower. That difference is not an acquisition failure.

The [report](../experiments/results/cnf-case17-transfer/report.json) contains these
means; storage sizes are final per-arm archive sizes, not the preservation union:

| Resource | Before case 16 | Full retained history |
| --- | ---: | ---: |
| Startup, seconds | 3.55586 | 5.42760 |
| Local expansion, seconds | 0.59661 | 0.62379 |
| Bookkeeping, seconds | 0.03176 | 0.06842 |
| Cold replay, seconds | 3.94310 | 6.07793 |
| Compression, seconds | 0.43576 | 0.61016 |
| Whole stream, seconds | 8.59953 | 12.86418 |
| Mean peak process RSS, bytes | 318,136,320 | 443,883,520 |
| SQLite bytes | 23,425,024 | 33,972,224 |
| Gzip bytes | 1,164,197 | 1,644,419 |

Whole-stream time includes restoration, checking, discovery, all report and
archive construction, and cold replay. It excludes interpreter/import startup
and the final summary write. Peak RSS includes imports and all phases, and is
not isolated cache memory. There are only two repetitions; the raw samples are
preserved. The retained stream takes about **49.6% longer** and has about
**125.75 MB more mean peak RSS**, without a reduction in target acquisition.
It also checks more retained evidence and an additional covered original, so this
is a cost of the current complete-history workflow, not an equal-coverage
replacement benchmark or a reason to delete earlier results.

## What the checked proof reuses

The [target explanation](../experiments/results/cnf-case17-transfer/retained-explanation.json)
has **96 distinct steps**: ten conditional nodes, 84 unary reductions and two
constant family leaves. The reductions are 53 probe rewrites, nineteen
eliminations, eleven binary-path reductions and one projection. Maximum
conditional depth is six, with changing branch-local coordinates and reductions
between choices. It is neither a fixed six-variable backdoor nor a minimum-depth
result. Both polarities remain in the checked conditional proof.

Seven pattern steps predate case 16 and 89 are new. **No pattern step or split
step comes from the case-16 additions.** The contradiction terminal appears on
ten paths and the empty conjunction on one; only the contradiction is shared.
There are 105 unfolded step occurrences and 96 distinct nodes. Thus the observed
sharing remains terminal sharing, rather than broad nonterminal reuse between
categories. The earlier seven steps and saved source split still contribute;
the negative finding concerns the marginal case-16 history, not all prior reuse.

## Preservation, remaining gaps and next step

[The new checkpoint](../experiments/results/cnf-case17-transfer/checkpoint.json)
preserves both parents and every acquired alternative: **1,790 patterns / 171
pairs / 17 inherited missing children**, with a **446-step positive proof** for
seven originals. It occupies **33,972,224 SQLite bytes / 1,640,046 gzip bytes**.
The union's serialization differs from a single arm's archive; use its own byte
counts and hashes. Seventeen originals remain structurally unknown; this is not
an UNSAT classification. All 345 tests pass. The validator independently restores
both parents, all four trial archives and the union without fresh acquisition,
and checks every original binding and positive proof.

The largest measured cost in this continuation is complete-history startup and
cold replay: **11.50553 seconds**, versus **0.62379 seconds** local expansion.
A promising supporting improvement is a checked working view restricted to the
needed sources, with exact lookup into the preserved global archive. Existing
source-local infrastructure handles older probe tables; it does not yet support
the new split registry's schema and complete route scans. Any extension must
retain all relevant alternatives, distinguish a local miss from global absence,
bind checks to immutable source/policy/record contents and preserve an independent
cold proof check. No such speedup is claimed by this experiment.

For broader discovery, [the next target](../experiments/results/cnf-case17-transfer/next-discovery.json)
is case 22, the largest remaining historical mean query. It is a **disjoint binary
mixture**, whose selected 48-variable / 204-clause / 612-literal residual remains
uncovered. All eight children of its four saved source pairs are present; one
child is covered, but no complete pair is covered. Reuse that checked work.
Test the same nested policy on that mixture before adding heuristics,
and distinguish reuse of its easy component from closure of its random core.
Keep the history ablation as a control when claiming cross-input reuse. These
finite results do not bound conditional depth, retained space or construction
time uniformly over unrestricted SAT.
