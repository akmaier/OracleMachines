# Witness signatures: historical discovery, no fresh-stream saving

Bounded exploration reaches two historical hard SAT cases, but adds no transfers
on the next 192 queries. All 96 SAT cases already use the existing witness route;
all 214 remaining expansions belong to 25 UNSAT cases. Exploration increases
complete runtime 6.04%, so remains optional. Equal false-clause signatures preserve
lookup coverage but not flip transitions: the tested two-variable counterexample
explains why all distinct accepted assignments remain in the exploration state.
See [analysis](../../../research/witness-signatures.md).

Reproduce in fresh directories; timed workers must run alone:

```sh
python3 experiments/probe_cnf_witness_signatures.py /tmp/cnf-witness-probe
python3 experiments/compare_cnf_witness_signatures.py /tmp/cnf-witness-signatures
python3 experiments/validate_cnf_witness_signatures.py /tmp/cnf-witness-signatures
python3 experiments/analyze_cnf_witness_signatures.py /tmp/cnf-witness-signatures
```

The historical probe excludes the active-support answers from seeds. Caps 0, 64
and 256 cover 95 SAT cases; 1,024 reaches case 137; 4,096 also reaches case 2,
covering all 97 historical SAT cases. No single flip repairs any of six diagnostic
targets. All budget transcripts persist in `../cnf-witness-signature-probe`.
Its unused preliminary validator is preserved separately; the timed protocol
binds the final stronger transfer-event validator.

`protocol.json` binds 374 runtime sources and the current 17,532-key union.
Selection excludes 1,344 prior sidecar answers and cached full roots, then takes
64 new neighbours per template. Three balanced process triples visit each twice.
All modes actively load the same 170-entry negative index; the two candidates
add a fixed batch of prior SAT witnesses, with caps zero and 4,096 per template.
The cap was chosen before the new stream, using the historical probe.

Mean complete runtime is 10.68687 / 10.73314 / 11.33255 seconds for control /
lookup / exploration. All produce byte-identical proof databases, 214 expansions,
68 splits and 415 new proof rows. Exploration regresses in every triple. Mean
RSS rises 9.02%, with mixed paired signs; there is no persistent-space saving.
Gzip plus raw sidecars grows 12,158,436 -> 15,671,480 bytes. The expanded bank
keeps 3,282 assignments, 945 lookup signatures and 12,288 attempts. Failed and
duplicate flips, every lookup miss and all queue/origin data persist.

Complete time includes restoration, preparation, discovery, lookup, checking,
publication, persistence, full cold proof/query and negative-lineage audit,
witness-bank serialization/reconstruction, compression, digest and transfer
serialization. Imports, initial CLI reads and final wrapper rewrite are excluded.
Historical acquisition and selection are separately charged. Fixed seed batches
are sealed before exploration; interleaved seeding is unsupported. Current raw
coordinate matching excludes foreign clauses and rejects tautological inputs.
An exhausted budget or miss never justifies UNSAT.

All 473 tests, nine complete archive audits / 3,456 trial replays, every union
node, 1,613 inherited decisions and 192 new decisions pass with fresh validation
search disabled. The union adds 415 keys and preserves every previous payload:
17,947 keys / 55,951,360 SQLite / 4,291,520 gzip bytes. No alternate certificates
arise; the new catalog has 133 direct roots and 59 guarded negative children.
The old negative frontier and its six ordered provenance catalogs remain intact.

`checkpoint.json` preserves earlier fields and adds `witness_signatures_study`,
`witness_signatures_decisions` and `witness_signatures_index`. The model bank is
optional, and restore must validate its complete saved transcript without
resetting the budget. All 369 earlier sources and 4,097 artifacts / 72 manifests
are unchanged; the post-hoc analyzer brings the source ledger to 375.
Structural authority stays 2,614 patterns / 259 pairs / 17 missing children,
original 17/24 / 999 steps, separate supplemental 24/24 / 208, and original
case 7's discovery pointer. No new Lean or arbitrary-SAT complexity result.

The manuscript builds to 198 pages without warnings and preserves all 64 proof
blocks. Next coverage target: negative template-6 cases 123/189 share guard
[130,140] and cost 17/16 expansions. Test conditional support/proof sharing and
then genuinely different guards; do not treat positive-bank growth as a coverage gain.

The preserved negative frontier now has **113 available retained roots / 57 pending**;
pending descriptions still require checked materialization. The new manifest binds
**77 artifacts**, including the historical probe. The next preservation audit
inherits **4174 artifacts / 73 manifests**.
