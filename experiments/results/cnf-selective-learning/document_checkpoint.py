"""Write the evidence summary after matched runs and independent validation."""
from pathlib import Path
import json
out=Path(__file__).parent;a=json.loads((out/'analysis.json').read_text());t=a['totals'];tr=a['transport'];b=t['fresh'];c=t['reuse'];ratio=100*tr['retained']/tr['original']
refs=a['reference_counts'];answers={m:sum(n for k,n in a['coverage'][m].items() if k!='unresolved') for m in ('fresh','reuse')}
measure=f'''The whole-collection guard rejects all **32/32 targets**. Selective transport
retains nonempty knowledge on **{tr['nonempty']}/32**, keeping **{tr['retained']:,} of
{tr['original']:,} derivation occurrences ({ratio:.2f}%)** across the two edits per
parent. These occurrences are not distinct clauses or independent samples.
Each target retains between {tr['retained_min']:,} and {tr['retained_max']:,} records.
Transport statuses are {tr['statuses']}; lost refutations remain unknown.

On the **16 expansion targets**, fresh search certifies **{answers['fresh']}/16**
and reuse certifies **{answers['reuse']}/16**: {a['coverage']['reuse']}. There are
{len(a['gains'])} new answers and {len(a['losses'])} lost answers; the union leaves
**{len(a['remaining'])} unresolved**, all reference-UNSAT (not yet project-certified).
The three new refutations actually depend on 1,400, 1,600 and 3,037 retained
derivations, respectively. All 32 targets remain connected in the variable
incidence graph; no bounded interaction-width certificate is claimed.
Reference results over all 32 targets are
{refs}; reference verdicts are kept distinct from project certificates.

| Measured expansion quantity | Fresh target search | Selective reuse |
| --- | ---: | ---: |
| Entered contexts | {a['states']['fresh']:,} | {a['states']['reuse']:,} |
| Mean complete seconds | {b['complete_seconds']:.5f} | {c['complete_seconds']:.5f} |
| Mean acquisition including internal checks, seconds | {b['phases']['acquisition_seconds']:.5f} | {c['phases']['acquisition_seconds']:.5f} |
| Mean explicit checking, seconds | {b['phases']['checking_seconds']:.5f} | {c['phases']['checking_seconds']:.5f} |
| Mean warm reload/check, seconds | {b['warm_seconds']:.5f} | {c['warm_seconds']:.5f} |
| Mean two cold reload/checks, seconds | {b['cold_seconds']:.5f} | {c['cold_seconds']:.5f} |
| Mean writes, seconds | {b['phases']['writing_seconds']:.5f} | {c['phases']['writing_seconds']:.5f} |
| Mean three compressions, seconds | {b['persistence_seconds']:.5f} | {c['persistence_seconds']:.5f} |
| Proof JSON bytes | {int(b['proof_bytes']):,} | {int(c['proof_bytes']):,} |
| Combined gzip bytes | {b['compressed_bytes']['combined']:,} | {c['compressed_bytes']['combined']:,} |
| Maximum observed process RSS bytes | {a['peak_rss_bytes']['fresh']:,} | {a['peak_rss_bytes']['reuse']:,} |

Mean complete cost changes **{a['comparison_percent']:+.2f}%**; paired changes
are {a['paired_percent'][0]:+.2f}% and {a['paired_percent'][1]:+.2f}%. This is a
coverage gain with greater charged cost, not a speedup. Retaining all available
knowledge enlarges both propagation and proof replay. Historical parent discovery
is additional; these measurements cannot establish a total-cost saving.
'''
p=Path('research/selective-learned-knowledge.md');text=p.read_text();assert 'SELECTIVE_RESULTS' in text;p.write_text(text.replace('SELECTIVE_RESULTS',measure))
summary=f'''[Selective learned knowledge after edits](selective-learned-knowledge.md) replaces
whole-collection rejection with a dependency filter. Every old derivation is
checked; records with missing source premises or rejected ancestors are dropped,
while independent records survive. Fresh augmented search substitutes those
records back into a certificate checked against the edited target alone.
Survival is exact for recorded proof paths, not every semantic consequence.

All **32** controlled edits defeat the old whole-collection guard. The filter
retains nonempty knowledge on **{tr['nonempty']}/32**, keeping **{tr['retained']:,}/{tr['original']:,}
derivation occurrences ({ratio:.2f}%)** across related targets. All transported
results remain unknown. On sixteen edits of previously refuted parents, a frozen
2,000-context expansion budget improves certified answers **{answers['fresh']}/16 → {answers['reuse']}/16**,
leaving **{len(a['remaining'])} unresolved**. These are controlled edits of exposed parents,
not new external transfer. Prior SAT-parent deletions are excluded from this
comparison because old models already provide cheap answers there.

Mean charged cost rises **{b['complete_seconds']:.5f} → {c['complete_seconds']:.5f} seconds
({a['comparison_percent']:+.2f}%)**. Proof JSON grows **{int(b['proof_bytes']):,} → {int(c['proof_bytes']):,}
bytes**; two cold replays rise **{b['cold_seconds']:.5f} → {c['cold_seconds']:.5f} seconds**.
Historical parent acquisition is additional. This expands guarded reuse and
certified coverage at substantial cost; it does not make expansion cheaper.

All **2,640 full and 22 focused tests pass**. A reproduced truth audit checks
13,624 edited small formulas; independent transitive support sets agree with
all filter decisions. Validation preserves 250 prior manifests, 84,291 artifacts,
1,362 scientific sources and 89 earlier proofs; five source files and one proof
are added. Previous panels and cumulative records remain separate. Resume
`experiments/results/cnf-selective-learning/checkpoint.json`, key
`selective_learning`.

**Largest remaining gaps:** the {len(a['remaining'])} capped edited targets; economical selection
and propagation of surviving knowledge; alternative supports for rejected
consequences; and new frozen external transfer. Whole-collection guard failure
no longer forces total knowledge loss, but efficient preprocessing and
unrestricted SAT expansion remain open.

'''
for file,old,new in [('research/sat-pattern-discovery.md','## Latest evidence: checked learning closes the eleven larger-input gaps','## Latest evidence: selective knowledge survives edits, with costly expansion'),('research/implementation-gaps.md','## Latest evidence: checked learning closes the eleven larger-input gaps','## Latest evidence: selective knowledge survives edits, with costly expansion'),('research/structural-reuse-priorities.md','## Current investigation: guarded learning, active-index cost and fresh transfer','## Current investigation: selective survival and economical expansion')]:
 p=Path(file);text=p.read_text();assert text.count(old)==1;previous=old.replace('Latest evidence','Previous evidence').replace('Current investigation','Previous investigation');p.write_text(text.replace(old,new+'\n\n'+summary+previous,1))
tex=fr'''The selection rule and implementation hashes were frozen before target outcomes.
For each of sixteen exposed parents, one target deletes the original clause
starting its first retained derivation; a second target additionally receives a
shared-variable binary bridge and fresh negative unit.  The old collection guard
rejects all 32 targets.  The new filter keeps nonempty knowledge on {tr['nonempty']}/32,
retaining {tr['retained']:,} of {tr['original']:,} derivation occurrences ({ratio:.2f}\%),
with {tr['retained_min']:,}--{tr['retained_max']:,} surviving records per target.  Occurrences across
the two related edits are not distinct clauses or independent samples.
All transported results remain unknown; none inherits its parent's refutation.

The expansion comparison uses the sixteen edits of eight previously refuted
parents, avoiding trivial reuse of old SAT models after pure deletion.  Both
policies receive 2,000 entered contexts, an explicitly smaller cap than the
parent-acquisition runs.  Fresh search certifies {answers['fresh']}/16 targets; reuse certifies
{answers['reuse']}/16, all UNSAT, leaving {len(a['remaining'])} unresolved in their union.  There are
{len(a['losses'])} lost answers.  These are controlled edits of exposed inputs, not new
external transfer or a representative distribution.  Target reference runs are
kept separate from acquisition and from project-certified coverage.  All thirteen
remaining expansion targets have trusted reference-UNSAT results.  The three
new refutations depend on 1,400, 1,600 and 3,037 retained derivations, respectively,
as checked by tracing their final empty-clause ancestors; their original-premise
supports have sizes 534, 534 and 633.  This diagnoses proof use and does not
measure a pruned-proof implementation.  All 32 targets remain connected in
the variable incidence graph; no bounded interaction-width certificate follows.

Across two fresh-process alternating pairs, contexts fall from
{a['states']['fresh']:,} to {a['states']['reuse']:,}, but mean complete cost rises from
{b['complete_seconds']:.5f} to {c['complete_seconds']:.5f} seconds ({a['comparison_percent']:+.2f}\%).
Paired changes are {a['paired_percent'][0]:+.2f}\% and {a['paired_percent'][1]:+.2f}\%.
Mean acquisition including checks rises from {b['phases']['acquisition_seconds']:.5f} to
{c['phases']['acquisition_seconds']:.5f} seconds, explicit checking from
{b['phases']['checking_seconds']:.5f} to {c['phases']['checking_seconds']:.5f}, warm replay from
{b['warm_seconds']:.5f} to {c['warm_seconds']:.5f}, and two cold reload/checks from
{b['cold_seconds']:.5f} to {c['cold_seconds']:.5f}.  Proof JSON grows from {int(b['proof_bytes']):,} to
{int(c['proof_bytes']):,} bytes and combined gzip from {b['compressed_bytes']['combined']:,} to
{c['compressed_bytes']['combined']:,} bytes.  Maximum observed process RSS changes from
{a['peak_rss_bytes']['fresh']:,} to {a['peak_rss_bytes']['reuse']:,} bytes.

The measured workload charges target reads and hashes, candidate parent reads
and proof checks, filtering, target checks, augmentation, expansion, substitution,
writes, three compressions and replay.  The old acquisition cost is separately
recorded and additional; there is no end-to-end amortization claim.
Imports/startup, reporting and independent audits are additional, and cold replay
does not flush operating-system caches.  The results establish broader guarded
reuse and extra certified answers at higher cost, not cheaper expansion.
'''
assert tr['statuses']=={'unknown':32} and a['coverage']['fresh']=={'unresolved':16} and a['coverage']['reuse']=={'unresolved':13,'unsat':3}
section=(out/'manuscript-section-template.tex').read_text().replace('SELECTIVE_MEASUREMENTS',tex)
p=Path('paper/bounded_domain_sat_and_amortized_reasoning.tex');text=p.read_text();marker=r'\section{System 1, System 2, and the reuse of computation}';assert text.count(marker)==1 and r'\label{sec:selective-learning}' not in text;p.write_text(text.replace(marker,section+marker,1))
print('Wrote measured research and manuscript checkpoint')
