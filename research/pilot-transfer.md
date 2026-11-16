# Pilot transfer: extra exploration without a better proof

Case 13 raises structural coverage **14/24 -> 15/24**, but the unchanged pilot
does not improve its chosen route. It produces the **same 38-step proof** as
committing immediately, while adding **ten extra patterns, 51 probes, two source
assumptions and one split record**. Local expansion time rises **37.18%**. This
regression is retained alongside the case-11 success; the pilot remains optional.

## Frozen transfer and the observed mechanism

The [transfer protocol](../experiments/results/cnf-pilot-transfer/protocol.json)
reuses byte-identical scheduler, worker, acquisition, checker and validator
sources. Both modes start from the complete 2,178-pattern / 220-pair parent.
The limits remain four batches, 128 admissions and sixteen operations per batch,
shared by pilot and continuation. Two reversed-order paired runs use fresh
processes. Only the bound original and parent history change; no policy parameter
is tuned. This is another known development input, not a new held-out sample.

The input has 48 variables and 211 clauses before preprocessing; the selected
residual has 47 variables, 213 clauses, 649 literals and maximum width four.
The unary-prefix and saved-alternative preconditions hold. All eight saved
children exist; pivot 41's true child is already covered. The acquisition-free
preflight takes 0.15935 seconds, separately from operational timings. Each timed
worker reconstructs and checks its own state.

The initial remaining-literal scores for pivots 47, 41, 44 and 5 are **1199,
610, 1175 and 1141**. Both modes initially choose pivot 41. The pilot compares
that route with pivot 5:

| Saved route | Trial pivot in its selected cofactor | Admissions | Probes | Remaining tasks / literals |
| --- | --- | ---: | ---: | ---: |
| 41 | 25 | 6 | 32 | 1 / 539 |
| 5 | 32 | 10 | 51 | 2 / 1084 |

The pilot still selects pivot 41, then performs the same remaining operations
as the committed control. In both repetitions, its operation list equals the
control's list with precisely one alternative trial inserted after the first
operation. The target proofs are identical. None of the ten alternative-trial
patterns is needed by this proof, and full-corpus coverage is unchanged by them.
They remain stored for possible later use; future reuse has not been demonstrated.

## Costs, including the timing ambiguity

| Resource | Commit immediately | Pilot two routes |
| --- | ---: | ---: |
| Batches to coverage | 1 | 1 |
| New patterns / distinct admissions | 27 | 37 |
| Probes | 128 | 179 |
| Fresh source assumptions | 6 | 8 |
| New split records | 3 | 4 |
| Restoration and setup, seconds | 0.14166 | 0.14003 |
| Expansion including pilot/scoring, seconds | 0.13244 | 0.18168 |
| Bookkeeping, seconds | 0.09724 | 0.09768 |
| Independent query-proof check, seconds | 0.08602 | 0.08556 |
| Complete cold audit, seconds | 7.00886 | 6.87196 |
| Compression, seconds | 0.78335 | 0.77623 |
| Whole stream, seconds | 8.33858 | 8.24283 |
| Mean peak process RSS, bytes | 391,053,312 | 392,609,792 |
| Final SQLite bytes | 40,927,232 | 41,095,168 |
| Compressed snapshot bytes | 2,061,656 | 2,072,627 |

The pilot adds **37.04% more patterns and 39.84% more probes**, with **37.18%
more local expansion time**. Peak RSS rises **0.40%**, SQLite size **0.41%** and
compressed size **0.53%**. These extra states produce no additional measured
coverage or different target proof.

Whole-stream timing does not consistently rank the modes. The first paired
control/pilot times are **8.28561 / 8.36781 seconds**; the reversed pair gives
**8.39155 / 8.11785**. Their means favor the pilot by 1.15%, despite its greater
expansion work, because the much larger audit phase measures lower in that arm.
Do not report this mean as evidence that unnecessary exploration improves total
runtime. Two pairs leave the small total-time difference unresolved. Full audits
account for about **83--84%** of either stream.

The clock charges restoration, setup, all selection and acquisition, bookkeeping,
snapshots and both cold checks, excluding imports and final summary writing.
RSS includes imports and all phases. Earlier history acquisition remains charged
in parent experiments. Tests and retrospective validation run after timing.

## Proof and retained state

Both proofs contain **38 distinct steps**: four conditional nodes, 32 unary
reductions and two family terminals. The reductions comprise 27 probe steps,
two binary-path steps and three eliminations. Maximum conditional depth is four;
changing local coordinates make this different from a fixed backdoor-size bound.
There is no component decomposition. Eleven pattern steps and one split predate
the continuation; 27 pattern steps and three splits are new.

The terminals are contradiction, with four occurrences, and a five-variable,
five-clause, eleven-literal residual recognized as **dual-Horn and one-valid**.
Only contradiction is shared within the proof: 41 unfolded occurrences become
38 steps. Structural coverage remains distinct from a SAT/UNSAT output API.

All 27 new control patterns and its three new splits are also acquired by the
pilot. This reflects identical work on the same original, not new cross-input
structural sharing. The conflict-checked union keeps **37 distinct new patterns
and four splits**, including every unused trial result. It contains **2,215
patterns / 224 pairs / seventeen inherited missing children**, with an
**844-step positive proof for fifteen originals**. Nine remain unknown. Its own
serialization is **41,099,264 SQLite bytes / 2,073,167 gzip bytes**.

The frozen independent validator checks the parent, four trial archives, union,
query proofs, original bindings, reachable catalogs, immutable prefixes, pilot
phase recovery and shared budgets. Validation takes **76.24 seconds**, outside
operational means and partly concurrent with the test suite. All **367 tests**
pass. All 302 prior sources, 3,417 artifacts and 64 manuscript proof blocks are
unchanged. Only a new transfer driver is added; the algorithm is not modified.

## Next gap: when is a second trial worth acquiring?

The two studies expose a potentially useful signal: on case 11 the first trial
grew unresolved literal mass from 1106 to 1535, whereas on case 13 it shrank
610 to 539 without increasing the number of obligations. A progress-sensitive
gate could test another route only when the first completed step fails to reduce
that mass. This is a hypothesis derived from these development results, **not a
validated rule or a minimum-cost guarantee**. One completed trial also has no
small per-route resource bound beyond the global batch allowance.

Test the proposed gate against both committed and always-pilot controls on the
next input before considering adoption. Retain every interrupted or losing trial
and count repeated work. Do not simply suppress pilots whenever a covered child
exists: the earlier case-6 counterexample already showed that a small remaining
frontier can choose a more expensive route. More broadly, larger reusable
components and cheap full-history auditing remain open gaps.

The next bound input is **case 21, a connected binary mixture**, with a selected
**45-variable / 201-clause / 616-literal / width-four** residual. All eight
children of pivots 2, 1, 23 and 17 are present and uncovered. The original
depth-zero root is present; the optional depth-one root is absent. Check the
pilot's prefix precondition and use the present root. This also tests a new
input category for the pilot; it provides no unrestricted-SAT efficiency bound.
