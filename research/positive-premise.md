# Reusing positive premise screens

## Result

The optional `cnf_positive_premise.select` policy recovers a complete target
model from a positive premise screen already retained by the binary-filtered
selector. It changes fallback acquisition only; admitted guards, propagated
results and positive-child models keep their existing priority. It does not
perform additional probes or stop the existing discovery pass early.

At the motivating saved prefix, case 50's assumption `-169` yields a checked
target model. Native acquisition falls from three nodes / 2,503 payload bytes
to one node / 1,482 bytes. The two extra nodes and 1,021 bytes are avoided in a
new acquisition; earlier stored certificates are preserved. The thirteen older
controls keep their exact native payloads and composed records. Case 50 is
repeated in opposite policy order, giving thirty control arms in total.

On sixty fresh excluded queries, the policy additionally recovers gated-Horn
cases 26 and 54, with twelve and sixteen variables. Each replaces three search
nodes with one directly checked model node. These cases have no prior guards
and remain unknown after preparation. Their native bytes fall respectively
2,585 -> 1,513 and 3,503 -> 1,908. Family labels never enter selection.

| Fresh-stream quantity | Native baseline | Binary filtered | Positive recovery |
|---|---:|---:|---:|
| New native nodes | 410 | 410 | 406 |
| New native payload bytes | 472,534 | 472,534 | 469,867 |
| Expanded nodes | 399 | 398 | 392 |
| Direct model publications | 0 | 0 | 2 |
| Discovery/acquisition propagation visits | 67,029 | 171,882 | 170,891 |
| Mean query seconds | 0.3507 | 0.4220 | 0.4018 |
| Mean complete worker seconds | 21.9867 | 22.1767 | 22.1122 |
| Mean full cold replay seconds | 10.7654 | 10.8607 | 10.8148 |

The matched query differences are -0.03553 and -0.00485 seconds. Complete worker
differences are -0.21437 and +0.08545 seconds: no stable end-to-end gain is
established. Native baseline remains cheaper on this corpus. Diagnostic
query/warm sidecars grow about 0.36%, from 1.977 to 1.984 MB, because recovery
retains model and accounting fields. Trial database/compressed sizes fall
76,537,856/5,571,576 -> 76,529,664/5,570,042 bytes. Mean process RSS is effectively
unchanged, 727.892/727.728 MB; two trials do not establish a memory scaling gain.
All sizes include the inherited state where indicated.

Case 50's query evaluation falls 3.623 -> 3.257 ms and 3.580 -> 2.996 ms in the
two orders. Prefix copying/opening and query-local cold replay dominate its
roughly 0.2-second complete arms, whose differences have opposite signs.
Delta/record sidecars fall 8,184 -> 7,099 bytes. These are selected-case results,
separate from the fresh-stream evaluation and its full inherited-bank replay.

## Exact condition and resource accounting

For a target F and source literal u, a saved screen refers to F AND u. Recovery
binds that exact canonical formula, checks each unit reason, and independently
checks that the restricted formula is empty. The saved zero-residual counter
is only a hint. It transports canonical values to source names, assigns false
to unconstrained variables, and checks every original clause and the assumption.
The model therefore satisfies F. No negative premise proof, child proof or
search is needed for this publication. Conversely, UNSAT of F AND u alone
would not establish UNSAT of F.

A valid unit trace cannot use a reason clause twice: after its forced literal
is assigned, the clause is satisfied. Thus the total reason-clause length is
at most the length of the canonical premise. With L source literal occurrences,
n active variables and at most k retained attempts, incremental recovery costs
O(k + L + n) expected dictionary operations **after separately charging both
canonicalizations and full-key construction**. Copying the premise, checking
the residual and verifying the model are included; temporary state is O(L+n)
words. Variable-name bit lengths, JSON bytes, native publication checks,
archive census, persistence and inherited replay remain separate costs. The
earlier discovery propagation is not removed by this bound.

The sixty-query run scans 187 saved attempts, copies 466 premise literals,
checks reason clauses containing 82 literals and checks 466 source/assumption
literals. These counters, source-coordinate transport and canonicalization
counters are retained. The posthoc auditor independently recomputes all added
recovery counters and the previous filter counters in 135 records. It checks
that reason-clause identifiers are distinct in each recovered trace.

## Scope and next gaps

This is an implementation of ordinary positive witness transport, with no
new tractability theorem or Lean refinement. Seven new tests include 2,048
small clause-set/coordinate variants, corrupted roots and reasons, false
zero-residual hints, disabled search budgets and cold persistence. A concrete
miss is preserved: `(x OR a OR b) AND (x OR NOT a OR NOT b)` is satisfied under
x=true, although the negative-probe filter skips x because no binary clause
exists. This policy does not claim complete positive discovery.

The next highest-value discovery target is checked solving and model transport
for **nonterminal conditioned Horn, dual-Horn and two-CNF residuals**, using
the already saved unit prefix and variable mapping. The previous study recorded
89 such constant/recognized candidates across twenty queries. Recognition alone
does not solve a condition, and refuting one condition does not refute its
parent. Preserve successful cases 50/26/54, earlier positive-child case 146,
useful guards 43/172, regression 144 and unresolved 0/131/159 as controls.

Discovery remains expensive: gated-Horn queries use 73,886 propagation visits
before acquisition, versus 5,751 afterward. Stop-on-positive discovery and
separate positive-witness screening could help, but must be priced without
silently expanding the candidate budget. The signed negative-probe refinement
remains unimplemented. Random three-CNF and coupled parity still require 257
acquisition nodes and 46,651 propagation visits; this policy does not help them.
Full cold replay still dominates the complete worker. There is no uniform
polynomial bound for arbitrary SAT, efficient exhaustive partition, or compact
closure claim.

Reproduction and immutable evidence are in
[`experiments/results/cnf-positive-premise/`](../experiments/results/cnf-positive-premise/).


All **1,120 tests**, 31 focused tests, 135 counter audits and independent
reconstruction pass. Resume `experiments/results/cnf-positive-premise/checkpoint.json`:
**23,987 native keys**, preserving all 23,577 prior payloads, with 210 new
composed records alongside 3,371 inherited records, 2,957 ordinary decisions
and six projections. The union uses 76,537,856 database bytes / 5,571,577
compressed bytes. Three alternate model payloads remain in measured evidence
(six occurrences); preserved native payloads are never replaced. Ready/pending
banks remain 132/38, 141/66, 86/90 and 86/117. All 508 earlier source fingerprints,
5,780 artifacts and 95 manifests remain intact. The paper builds at 212 pages
with all 64 existing proof blocks unchanged. The initial replay validator's
scratch-directory failure and its separate corrected replay revision are retained.
No new Lean theorem, structural authority or unrestricted-SAT bound is claimed.
