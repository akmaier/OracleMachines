"""Post-validation presentation and overlap census; no discovery decisions."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_reuse_transfer as s
out = Path('experiments/results/cnf-reuse-transfer')
a = s.load(out/'analysis.json'); p = s.load(out/'protocol.json'); v = s.load(out/'validation.json')
assert v['passed']
rows=s.source_rows(p)
prior={b['path']:{s.e.canonical(r['source'],Counter()) for r in s.bound(b)} for b in p['prior_panels']}
parents={r['id']:s.e.canonical(r['source'],Counter()) for r in s.source_rows(s.bound(p['parents']))}
seen={}; overlaps=[]
for row in rows:
    key=s.e.canonical(row['source'],Counter())
    overlaps.append(dict(id=row['id'],parent_exact_matches=[i for i,k in parents.items() if k==key],prior_exact_matches=[f for f,ks in prior.items() if key in ks],earlier_target_exact=seen.get(key)))
    seen.setdefault(key,row['id'])
s.write(out/'target-overlaps.json',dict(records=overlaps,scope='Post-hoc exact normalized census; relatedness by edits is retained independently of these exact matches. No semantic-isomorphism conclusion.'))
covered=lambda mode:sum(n for k,n in a['coverage'][mode].items() if k!='unresolved')
union=sum(n for k,n in a['union_counts'].items() if k!='unresolved')
t=a['totals']; fresh=t['fresh8000']; reuse=t['reuse8000']; parent=t['parent20000']
metrics=[('Checked answers',f"{covered('parent20000')}/8",f"{covered('fresh8000')}/16",f"{covered('reuse8000')}/16")]
for title,key in [('Entered contexts',None),('Complete seconds','complete_seconds'),('Warm reload/check seconds','warm_seconds'),('Two reload/check rounds seconds','cold_seconds'),('Three compressions seconds','persistence_seconds'),('Proof JSON bytes','proof_bytes')]:
    values=[a['states'][m] if key is None else t[m][key] for m in s.POLICIES]
    metrics.append((title,*[f'{x:,.5f}' if 'seconds' in title else f'{int(x):,}' for x in values]))
for title,key in [('Acquisition including checks, seconds','acquisition_seconds'),('Explicit checking seconds','checking_seconds'),('Writes seconds','writing_seconds')]:
    metrics.append((title,*[f"{t[m]['phases'][key]:,.5f}" for m in s.POLICIES]))
metrics += [('Combined gzip bytes',*[f"{t[m]['compressed_bytes']['combined']:,}" for m in s.POLICIES]),('Peak RSS bytes',*[f"{a['peak_rss_bytes'][m]:,}" for m in s.POLICIES])]
table='| Quantity | Parent acquisition | Fresh targets | Reused targets |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in metrics)
sat_gains=sum(r['id'] in a['reuse_only'] and r['parent_kind']=='sat' for r in a['outcomes'])
ids=lambda xs:', '.join(xs) if xs else 'none'
phrase=lambda counts:', '.join(f"{counts[k]} {label}" for k,label in [('sat','SAT'),('unsat','UNSAT'),('unresolved','unknown')] if counts.get(k))
strata='| Parent outcome | Fresh target outcomes | Reused target outcomes |\n| --- | --- | --- |\n'+'\n'.join(f"| {kind.upper()} | {phrase(modes['fresh8000'])} | {phrase(modes['reuse8000'])} |" for kind,modes in a['strata'].items())
retained=sum(r['retained'] for r in a['survival'])
discarded=sum(r['discarded'] for r in a['survival'])
semantic=s.load(out/'semantic-audit.json')['counts']
summary=f'''[Frozen external transfer](frozen-external-reuse-transfer.md) evaluates eight new
SATLIB originals and sixteen fixed related edits, including every parent outcome.
At the unchanged 8,000-context target cap, fresh search checks **{covered('fresh8000')}/16**
answers and reuse checks **{covered('reuse8000')}/16**. There are **{len(a['reuse_only'])} reuse-only**,
**{len(a['fresh_only'])} fresh-only**, **{a['overlap_solved']} shared** and **{len(a['remaining'])} jointly unresolved**
targets. **{sat_gains} reuse-only answers come from SAT parents**, showing useful
retained consequences without inheriting a parent model. These are related edits
from the same size/distribution groups used in development, not a representative
external SAT survey.

Mean target workflow costs are **{fresh['complete_seconds']:.2f} s fresh** and
**{reuse['complete_seconds']:.2f} s reused**. New parent acquisition costs
**{parent['complete_seconds']:.2f} s**, bringing parent-plus-reuse to
**{a['parent_plus_reuse_seconds']:.2f} s** before download, target preparation and
independent audits. Coverage and cost must be assessed together; no universal
speedup or efficient unrestricted class follows.

All **2,697 full and eight focused tests pass**. Independent truth checks reproduce
**{semantic['checked_outcomes']:,} outcomes on {semantic['targets']:,} small edited targets**.
All five measured workflows, proofs and counters reproduce. Three fresh workers
replay target-only certificates with discovery and transport disabled. Validation
preserves **254 prior manifests, 84,935 artifact entries, 1,381 scientific sources**
and all **92** previous proof blocks. Resume
`experiments/results/cnf-reuse-transfer/checkpoint.json`, key `reuse_transfer`.

**Next:** explain the observed coverage differences and retained-proof cost;
seek compact supports or a justified admission/dispatch policy before raising
budgets again. Broader distributions, alternative derivations after deleted
premises, structural recognition and unrestricted expansion remain open.
'''
doc=f'''# Frozen external transfer of selective resolution reuse

The previous larger-budget comparison completed sixteen exposed edits of refuted
parents. This checkpoint tests its fixed policy on new external parents, removes
the parent-outcome filter and accounts separately for acquiring those parents.

## Frozen sample and composition

`selection.json` binds all 1,384 scientific sources before downloading selected
members. The four SATLIB archives are uf125-538, uuf125-538, uf150-645 and uuf150-645.
Zero-based member indices 60 and 80 in (basename, full-name) order give eight
originals. Their publisher bytes, archive/member hashes, parsed DIMACS and
provenance are retained. No original has an exact normalized match in the six
specified earlier panels or among the new originals. The additional target
census is in `target-overlaps.json`. Exact inequality is not semantic independence.

Acquire each parent with the unchanged watched learner at 20,000 contexts.
Delete the canonical original clause starting its first stored derivation, or
canonical clause zero if no derivation exists. The paired edit additionally adds
`[smallest_original_variable, maximum_original_variable+101]` and the negative
unit on the fresh variable. Include both edits for every parent, irrespective of
SAT, UNSAT or unknown. The rule, fallbacks and two reversed target process orders
were fixed before observing parent results. The eight external parents are the
selection units; the sixteen targets are related edits. No statistical representativeness or generalization across
distributions is claimed.

Both target modes use the same target-only proposal and 8,000-context watched
search. Reuse checks the parent, filters recorded derivations by surviving
premises, activates all retained clauses, then substitutes their derivations
into a certificate checked against the target alone. SAT witnesses are not
inherited. Unknown retains consequences without granting an answer. This uses
previous exact-composition results; it adds no new structural recognizer or theorem.

## Coverage and resource cost

{table}

{strata}

Reuse-only targets: **{ids(a['reuse_only'])}**. Fresh-only targets:
**{ids(a['fresh_only'])}**. Both modes answer **{a['overlap_solved']}** targets.
Of the reuse-only answers, **{sat_gains} arise from SAT parents**. Thus completed
SAT searches can supply useful retained consequences; the target still requires
its own model or refutation. Their bookkeeping union answers **{union}/16**, leaving **{len(a['remaining'])}**
unknowns; it is not a measured dispatcher. Per-target results, remaining
interaction components and proof-survival counts are retained in `analysis.json`.
All sixteen targets remain connected, with 125–151 variables. Across the paired
edits, **{retained:,}** derivation occurrences survive and **{discarded:,}** are
discarded by the recorded-premise filter; these counts repeat parent records
across edits and are not independent discoveries or minimum support sizes.
Reference answers stay separate. A negative Z3 answer alone supplies no project
refutation; each reported project answer has a checked model or empty-clause proof.

Reused-target cost changes by **{a['reuse_vs_fresh_percent']:+.2f}%** relative to fresh
search. Adding the single measured parent acquisition gives
**{a['parent_plus_reuse_seconds']:.5f} seconds** for acquiring eight parents and
running one sixteen-target reuse workflow. This is an observed aggregate, not a
break-even estimate or equal-answer speedup. Uncompressed certificate files, all three compressed payloads and historical
append-only evidence add storage beyond the quoted combined gzip sizes.

Complete timings include raw reads/hash checks, required parent reads/checks,
proposal, transport, augmentation, search, proof substitution, explicit checks,
writes, three compressions, warm replay and two reload rounds. Target figures
average two reversed fresh-process orders; parent acquisition was measured once.
Download, edit preparation, imports/startup, report encoding and independent
audits are additional. The rounds named cold in inherited report fields create
fresh objects within the same worker and do not flush OS caches. Separate new
workers replay each policy with search/transport disabled as a correctness check.
Context caps count iterations, not equal work or wall time; RSS is observational.

## Validation and limits

All 2,697 full tests and eight focused tests pass. The independent audit runs
all 512 two-variable clause sets, 3,304 three-variable sets of at most three
clauses, and 64 sparse signed mixtures with duplicate clauses and tautologies.
A two-context parent cap yields {semantic['parent_sat']:,} SAT, {semantic['parent_unsat']:,} UNSAT and
{semantic['parent_unknown']:,} unknown parents; both fixed edits and target modes give
{semantic['checked_outcomes']:,} truth-checked outcomes on {semantic['targets']:,} targets. The audit reproduces exactly.
This small audit happens to retain no derivations after the chosen deletions;
it does not independently establish nonempty knowledge reuse. The unchanged
kernel's earlier truth audits remain preserved, while explicit transitive premise
sets check every retained path on the new external targets. All measured parent
and target proofs, diagnostics, counters and repeated target certificates
reproduce; all three fresh-worker replays pass. All 254 prior manifests,
84,935 artifact entries, 1,381 earlier scientific sources, 92 proof blocks and
three published snapshots remain intact. Three scientific files are added.

This experiment supplies finite transfer evidence and explicit failures/costs.
It does not establish polynomial preprocessing, cheap recognition, a compact
complete decomposition or efficient unrestricted SAT. Next inspect the actual
fresh/reuse differences and retained proof cost, then test justified support
selection or dispatch on a separately frozen sample. Raising a cap alone does
not resolve those obligations.
'''
Path('research/frozen-external-reuse-transfer.md').write_text(doc)
for name, heading in [('sat-pattern-discovery.md','Latest evidence'),('implementation-gaps.md','Latest evidence'),('structural-reuse-priorities.md','Current investigation')]:
    path=Path('research')/name; text=path.read_text(); at=text.index('## ')
    text=text[:at]+f'## {heading}: frozen external reuse transfer\n\n'+summary+'\n'+text[at:].replace('## '+heading+':','## Previous evidence:',1)
    path.write_text(text)
text=f'''\\subsection{{Frozen external transfer with parent acquisition charged}}
\\label{{sec:reuse-transfer}}

The preceding exposed-input comparison motivates a frozen transfer test. Before
acquisition, the protocol binds eight SATLIB originals: zero-based lexicographic
member indices 60 and 80 in each of uf125-538, uuf125-538, uf150-645 and uuf150-645.
No original exactly matches a normalized source in the six named earlier panels
or another new original. Archive hashes and original member bytes are retained.
These are new members of already studied distributions, not a representative
sample of arbitrary CNFs.

The unchanged watched learner acquires each parent at 20,000 contexts. For every
parent, delete the canonical original clause starting its first stored derivation;
if there is none, delete the first canonical clause. A second target also adds a
binary clause joining the smallest original variable to a fresh variable and a
negative unit on that fresh variable. Both edits are included regardless of the
parent outcome. The rule, fallbacks, target-only proposal, 8,000-context target
cap, all-surviving-clause activation and two reversed process orders are fixed
before parent outcomes. Eight external parents produce sixteen related targets.
Existing checked transport and exact proof substitution justify recomposition;
only a target model or target empty-clause proof supplies an answer.

Parent acquisition checks four SAT models and four UNSAT proofs. On the edited
targets fresh search checks {covered('fresh8000')}/16 answers and reuse checks {covered('reuse8000')}/16.
There are {len(a['reuse_only'])} reuse-only, {len(a['fresh_only'])} fresh-only and {a['overlap_solved']} shared answers;
the bookkeeping union covers {union}/16 and leaves {len(a['remaining'])} unresolved. It has no
combined dispatcher timing. Of the reuse-only answers, {sat_gains} come from SAT
parents: their consequences transfer without inheriting their models. Reference labels never guide discovery, and negative
reference output does not grant project refutation authority. Full outcomes,
proof-survival counts, remaining components and exact overlap records are retained.
Every target remains connected with 125--151 variables. The paired edits retain
{retained:,} and discard {discarded:,} derivation occurrences; these repeat parent
records and do not measure minimum support or independent discoveries.

Mean complete target workflow times are {fresh['complete_seconds']:.5f} seconds fresh
and {reuse['complete_seconds']:.5f} seconds reused, a {a['reuse_vs_fresh_percent']:+.2f}\\% change.
Their entered-context totals are {a['states']['fresh8000']:,} and {a['states']['reuse8000']:,}.
Single-run parent acquisition costs {parent['complete_seconds']:.5f} seconds;
parent acquisition plus one mean target-reuse workflow costs
{a['parent_plus_reuse_seconds']:.5f} seconds. This is an observed aggregate, not an
acquisition-amortization theorem or equal-answer speedup. Parent, fresh-target
and reused-target proof JSON sizes are {int(parent['proof_bytes']):,},
{int(fresh['proof_bytes']):,} and {int(reuse['proof_bytes']):,} bytes; combined gzip
sizes are {parent['compressed_bytes']['combined']:,}, {fresh['compressed_bytes']['combined']:,}
and {reuse['compressed_bytes']['combined']:,} bytes. Peak RSS in that order is
{a['peak_rss_bytes']['parent20000']:,}, {a['peak_rss_bytes']['fresh8000']:,} and
{a['peak_rss_bytes']['reuse8000']:,} bytes.

Complete cost includes source and parent reads/checks, proposal, transport,
augmentation, search, proof substitution, explicit checks, writes, compression
and replay. Download, edit construction, imports/startup, report encoding and
independent audits are additional. The two reload rounds deserialize within the
same worker and do not flush OS caches. Separate fresh workers replay all three
policies with search and transport disabled. Context caps do not imply equal work.

All 2,697 full and eight focused tests pass. Reproduced truth audits check
{semantic['checked_outcomes']:,} fresh/reuse outcomes on {semantic['targets']:,} edited small targets,
including SAT, UNSAT and unknown parent acquisitions. Those small deletions
retain no derivations; nonempty reuse retains its earlier independent kernel
audits and the new external transitive-support checks. All five measured
workflows, proofs and counters reproduce. Validation preserves 254 earlier
manifests, 84,935 artifact entries, 1,381 scientific sources, all 92 proof blocks
and three published snapshots. Three scientific files are added. This is finite
transfer evidence, not a new tractable class. Compact supports, informed dispatch,
broader distributions, preprocessing and unrestricted expansion remain open.

'''
paper=Path('paper/bounded_domain_sat_and_amortized_reasoning.tex'); textold=paper.read_text()
marker='\\section{System 1, System 2, and the reuse of computation}'
assert textold.count(marker)==1 and '\\label{sec:reuse-transfer}' not in textold
paper.write_text(textold.replace(marker,text+marker))
print(s.encode(dict(coverage=a['coverage'],reuse_only=a['reuse_only'],fresh_only=a['fresh_only'],parent_plus_reuse_seconds=a['parent_plus_reuse_seconds'])))
