# Current-answer certificates with complete knowledge retained

The frozen transfer study improves coverage through reuse but carries every
surviving and newly learned resolution record into later checks. This experiment
separates the certificate for the current answer from the archive needed for
future edits. It changes neither search nor active clause admission.

## Exact projection and its limits

First check the entire input archive against the original CNF, including records
that the projection will omit. For SAT, copy the checked model and omit all
derivations. For UNSAT, follow every premise of the selected empty-clause
conclusion, retain exactly its reachable derived records in their original
topological order, and remap derived-clause indices. Original clause indices
refer to the same complete canonical source. An original empty clause needs no
derived records. Unknown remains an unknown marker and supplies no answer.
Finally check the projected certificate with the unchanged checker.

**Correctness.** Each retained resolution record has all of its original or
derived premises retained. Induction in the original proof order shows that
index remapping preserves its resolvent. Thus the selected empty conclusion
remains justified. SAT uses the identical full-source model check, and unknown
has no decision authority. No clause is reused solely because adding it would
preserve satisfiability. The operation does not mutate the original archive.

This extracts the dependency closure of one recorded refutation, not a smallest
refutation or a minimum original-clause support. A large part of a proof can
remain reachable. Work is polynomial in the explicit formula and archive size,
which need not be polynomial in formula size. Full input validation is charged;
the constructor still loads the archive. Retaining fewer records for an answer
is not permission to delete knowledge or skip its checks before future reuse.

## Fixed traces and accounting

The protocol binds 32 existing traces from the preceding transfer checkpoint:
fresh and reused searches on the same sixteen related edited targets. Its
primary comparison uses all sixteen reused results, which already contain five
SAT models and eleven UNSAT refutations. The fresh control has three SAT, six
UNSAT and seven unknown results. Unknowns are reported separately so that
discarding their answerless records cannot masquerade as faster SAT solving.

Construct each projection once. Transcode full and projected certificates using
the same canonical JSON encoder and per-case gzip. This JSON is compact rather
than the preceding study's indented files, so compare only matched columns in
this study. Keep every historical file unchanged. The additional full transcode
is a measurement control; the projected sidecar is additional deployment storage.

Two reversed pairs of fresh processes replay the arms. They read and hash raw
CNFs, read/hash/decompress certificates, and run the same checker. Search,
transport and projection are disabled in replay. Hashes identify artifacts and
do not replace checking. Process wall time includes startup; per-case timing
and worker time do not. OS caches are not flushed. Construction, its peak memory,
sidecar writes and compression are reported separately from replay; prior search
and parent acquisition remain owed. No new external sample or answer is acquired.

## Measured result

| Reused targets: same five SAT and eleven UNSAT answers | Full certificate | Answer certificate |
| --- | ---: | ---: |
| Derived records | 87,054 | 46,960 |
| Compact JSON bytes | 26,364,575 | 14,107,112 |
| Per-case gzip bytes | 4,964,077 | 2,740,517 |
| Mean read/hash/decompress/check seconds | 4.77053 | 2.59003 |
| SAT replay seconds | 1.30999 | 0.00816 |
| UNSAT replay seconds | 3.46054 | 2.58187 |

Replay on this fully answered stratum improves **45.71%**. Preparing its
answer sidecars costs **9.79502 s**, including original-archive
reads/hashes, full validation, projection, output validation, encoding, compression
and writes. That is approximately **5 repetitions** to repay preparation using these
per-case replay measurements. Shared input/protocol setup and process startup
are additional to that estimate; it is neither a lifetime guarantee nor a
measured end-to-end solver speedup. Construction was measured once.

Matched full-plus-answer payloads total **40,471,687 compact JSON bytes**
or **7,704,594 per-case gzip bytes**. These are representation totals,
not a claim that historical files were shrunk. The actual previous indented
archive files remain **132,091,258 bytes**; the new gzip answer sidecars add
**2,740,517 bytes**, giving **134,831,775 bytes** for those files alone.
Historical combined gzip files, parents and metadata also remain. The study
additionally stores full transcoded controls; they are experimental overhead.

The secondary fresh stratum preserves **3 SAT / 6 UNSAT / 7 unknown** results.
Its aggregate replay falls 2.28807 to
0.52325 seconds, but much of that reduction removes learned
records from the seven unknown markers. It must not be presented as nine
answers becoming that much cheaper. Complete timing and byte totals by verdict
are in `analysis.json`.

Across both strata (32 trace replays), mean fresh-process wall time is
7.24189 versus 3.24801 seconds, and maximum process RSS
is 96,550,912 versus 87,851,008 bytes. These memory measurements cover the
combined worker, not the sixteen-query stratum in isolation. Constructing and
persisting both sets of controls takes 17.93170 seconds and peaks at
207,929,344 bytes. This does not improve construction memory or search work.

All **2,708 full and 11 focused tests pass**. The two independent small-case
runs reproduce byte-identical audit data. An explicit shared-ancestor control
and all 32 fixed traces pass independent reverse-ancestry checks. Four fresh
workers reproduce results and checking counters. Validation preserves
**255 prior manifests, 85,130 prior artifact entries,
1,384 scientific sources and all 92 previous proof blocks**. Four scientific
files and one proof block are added. The checkpoint preserves earlier coverage
unions, tables and all three published snapshots.

Resume `experiments/results/cnf-answer-certificate/checkpoint.json`, key
`answer_certificate`. This is a checked representation improvement on exposed
traces, with **no new answers, no losses and no new tractable class**.

## Validation and remaining work

The focused tests cover malformed unused records, false conclusions, missing or
forward references, source edits, pivot tampering, sparse labels, duplicates,
tautologies, original empty clauses, shared ancestry, deep iterative traversal,
idempotence and archive/model isolation. The independent audit checks 7,760
projections on 3,880 formulas: all 512 two-variable clause sets, 3,304
three-variable sets of at most three clauses, and 64 signed sparse mixtures.
Caps zero and 128 exercise unknown and complete outcomes; valid unused trailing
copies deliberately test removal. Full truth enumeration verifies decided
outcomes and models; a reverse scan independently reconstructs the ancestor
closure. All archived and projected traces retain the same checked results.

Remaining gaps include the still-retained archive, acquisition/expansion cost,
alternative supports after premise deletion, admission that preserves coverage,
broader input distributions and efficient structural recognition. Answer
projection does not establish a new tractable CNF class or remove unrestricted
SAT obligations.
