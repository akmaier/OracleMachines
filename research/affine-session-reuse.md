# Resume checked affine negatives in a fresh query stream

The negative-affine pilot now has a resumable query path. Before repeating local
discovery, the session attempts exact-target lookup in the versioned extension
table. A hit supplies a checked negative terminal. A miss runs the preceding
selector and publishes a checked affine refutation only when that selector has
already retained a contradictory row or complete-space exhaustion evidence.
Positive and unresolved cases retain their previous publication or native
fallback. The discovery policy remains fixed at four candidate variables and
the affine exhaustion cap remains eight free coordinates.

All extension terminals use the existing `cnf-affine-negative-v1` checker.
Native search still cannot read the extension table. Versioned chain replay
first checks its required extension terminal, then uses that checked result for
the terminal read instead of loading an alternative native derivation. Guard
premises retain their existing checked reads. This changes certificate selection,
not the statement proved or the certificate's logical authority. The cache
assumes an exclusively owned append-only database session.

A checked negative-chain bank indexes the complete normalized query source.
It supports warm reuse of guarded conclusions, whereas direct extension lookup
addresses the final target. Both interfaces normalize and bind the source; a
miss is not a negative answer. The checkpoint now preserves the native parent,
all extension certificates, native and negative chain catalogs, and the explicit
`TerminalStore` reader. Older readers continue to see native proofs only.

## Fresh comparison

The new sixty-query stream excludes every inherited query key and native root.
It contains twelve neighbouring controls and 48 generated inputs from random
three-CNF, coupled parity, gated Horn and graph colouring, with requested sizes
12, 16 and 20. Family metadata never reaches selection. Eleven neighbours become
known after shared preparation; one neighbour (case 2) and all 48 generated
family targets remain unfamiliar. Both modes return **37 SAT / 23 UNSAT**.

Four independent serial workers run affine/session and session/affine. Both
modes preserve and replay the seven inherited extension certificates. Only the
session publishes new affine negatives and attempts target lookup. Preparation,
lookup misses, discovery, checking, persistence, warm banks, full historical
native/composed/projection replay, serialization, compression and process RSS
remain charged. Preflight finished before production; truth checks and attribution
run afterwards. All 120 paired discovery records and discovery-counter sets are
identical across the policies.

| Cost across sixty queries | Positive-only affine policy | Resumable negative session |
| --- | ---: | ---: |
| New native nodes | 344 | 277 |
| New extension certificates | 0 | 3 |
| Combined new payload bytes | 460,091 | 384,362 |
| Native expanded nodes | 264 | 197 |
| Discovery/acquisition propagation visits | 89,223 | 80,384 |
| Mean query seconds | 0.39420 | 0.36360 |
| Mean full cold replay seconds | 13.07370 | 13.01006 |
| Mean complete worker seconds | 26.88647 | 26.76518 |
| Mean peak RSS bytes | 811,286,528 | 809,385,984 |

Three coupled inputs replace **67 native nodes / 84,421 bytes** with **three
extension certificates / 8,692 bytes**. Cases 17 and 41 contain contradictory
rows; case 33 exhausts a complete space with three free coordinates. Nine other
coupled inputs publish positive models. Thus all twelve coupled inputs in this
stream avoid native expansion, while still paying 2,112 discovery propagation
visits and their extraction/checking costs. This is a result for these inputs,
not complete coverage of all encodings of coupled or general SAT.

Combined retained additions fall 18.60%, combined new payload 16.46%, propagation
visits 9.91%, and mean query time 7.76%. Paired query deltas are
-0.03700/-0.02420 seconds; complete-worker deltas are -0.18291/-0.05968 seconds.
Mean complete time falls only about 0.121 seconds (0.45%). About 0.064 seconds
of that mean difference is cold-replay variation. Two orders do not establish a
stable end-to-end scaling advantage, and historical replay remains much larger
than the current query work.

The fresh stream makes sixty extension lookup attempts and **zero hits**, costing
about 0.00579 seconds per worker. This miss cost is included. Reuse is separately
validated by warm banks, full cold resumption and a focused cold exact-target
lookup test with discovery/search disabled. The new policy does not claim that
its fresh savings came from exact-target cache hits.

Diagnostic query/warm sidecars rise slightly: 2,026,277/2,026,237 ->
2,028,428/2,028,372 bytes. Trial SQLite falls 83,300,352 -> 83,152,896 bytes and
compressed archives fall 6,315,775 -> 6,304,858 bytes. Mean peak RSS falls about
1.90 MB. Those are matched trial measurements, not general space bounds.

## Preservation and replay

The union preserves all **26,743 prior native payloads and seven prior extension
payloads byte-for-byte**, adding 344 native keys and three extensions. It contains
**27,087 native keys and ten extension certificates**, with 117 new native-chain
records and three new negative-chain records alongside all 4,990 inherited
composed records. Comparator proofs remain available, so this preservation union
grows more than the session trial. Its archive uses **83,312,640 SQLite bytes /
6,318,187 compressed bytes**, growing 888,832 / 95,921 bytes over the parent.
No alternative native payload conflicts occur in this comparison.

Independent reconstruction checks all 240 chronological queries, six new-negative
publication-counter records, 48 exhaustive family truth tables, and every warm
answer. Full historical native/composed/projection replay passes on each worker
archive and the union. The union's ten extension chains check five row conflicts
and five exhausted spaces, including 36 rejecting assignments and 52 direct
coefficient XORs. Terminal-first replay loads **zero native alternatives** in
that phase, versus 134 native nodes for the preceding seven-chain pilot. Its
measured 0.01089 seconds covers a different, larger extension catalog and is not
a matched timing ratio against that pilot.

## Largest remaining gaps

Random three-CNF is the largest remaining measured native acquisition cost:
**140 expanded nodes / 27,761 propagation visits**. Case 56 alone expands 33
nodes and visits 8,144 propagation literals; cases 44 and 52 add 3,894 and 3,443
visits. These retained targets have no extracted equations. The next recognition
investigation should examine their conditioned residuals and reusable clause or
component descriptions, with exact coverage and recomposition checks. Another
affine-only speedup cannot explain that unresolved cell.

Graph-colouring discovery costs **25,375 propagation visits**, compared with
5,416 during remaining child acquisition. Cases 47 and 35 retain `no-proposal`
results; case 59 eventually completes a negative cover after 4,271 discovery
visits. Better use of partially covered clauses and earlier stopping are concrete
candidates. The session also retains 87 graph native nodes and twelve expanded
nodes in the unfamiliar neighbour control. Gated Horn has no native expansion
but still pays 12,579 discovery visits. Work counters locate candidates; they
are not interchangeable with wall time.

Across the fresh bridge calls there are eighteen no-equation misses, nine models,
two linear conflicts and one exhausted space. There are no dimension-cap misses
in this stream, so it does not test large-free-dimension performance. Hidden
encodings and complete projection onto leftover variables remain open. Shared
preparation and support scheduling still inspect native availability; they do
not yet exploit extension proofs as internal search premises. This restriction
keeps native proof dependencies compatible, but can miss additional reuse.

All **1,181 tests**, twelve focused tests, 240 chronological query audits and
six negative publication-counter audits pass. All **548 prior sources,
7,399 artifacts and 103 manifests** remain unchanged. The final source ledger
has 553 entries, including the posthoc validator and analyzer. Full
historical native/composed/projection replay passes for every worker and the
union. The 219-page manuscript builds with all 64 existing proof blocks unchanged
and a clean final compiler log. The full suite retains 44 existing unclosed-SQLite
warnings; focused tests have none. No new Lean theorem is claimed.

New manifest: **40 artifacts**. Next preservation audit: **7,439 artifacts / 104 manifests**. Final source ledger: **553**.
