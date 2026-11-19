#!/usr/bin/env python3
"""Seal automatic order-preserving residual transport and its cost comparison."""
from collections import Counter
from pathlib import Path
import json,re,subprocess,sys,sysconfig,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_residual_transport as study
from experiments.finalize_cnf_affine_probe import check_frontier
from experiments.cnf_residual_dag import normalize,token
base=study.base
POSTHOC=('experiments/validate_cnf_residual_transport.py','experiments/analyze_cnf_residual_transport.py','experiments/finalize_cnf_residual_transport.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==678 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts']
        assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(125,8462)
    fields=('query_audits','old_composed_records','old_pilot_records','old_larger_queries',
            'old_inventory_nodes','old_witness_observations','old_negative_observations',
            'old_support_plan_observations','old_affine_probe_observations','old_partial_observations')
    assert tuple(v[f] for f in fields)==(720,5650,444,108,624,864,864,1296,1296,864)
    assert v['tiny']['formulas']==512 and v['tiny']['statuses']==dict(sat=95,unsat=417)
    assert v['prior_tables']['cnf_residual_v1']==63254 and v['prior_tables']['cnf_affine_negative_v1']==59
    for t,n in v['preserved_tables'].items():assert n==v['prior_tables'][t]+v['new_records'].get(t,0)
    assert v['novelty']['holdout']==dict(distinct_roots=72,known_queries=0,queries=108)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries'])
        assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode']!='base':
            assert data['summary']['transport_peak_entries']<=p['transport_limits']['transport_capacity']
            for counter,limit in (('transport_peak_bytes','transport_bytes'),('transport_stage_peak_bytes','transport_bytes'),('transport_map_peak_bytes','transport_map_bytes')):
                assert data['summary'][counter]<=p['transport_limits'][limit]
            assert data['reconstruction']['transport_seed_entries']==data['summary']['hint_rows']
            assert data['reconstruction']['transport_replay_entries']==data['summary']['hint_rows']
    analysis=base.load(out/'analysis.json');paired={}
    for split,arms in report['summary'].items():
        for mode,arm in arms.items():assert sum(arm['statuses'].values())==(12 if split=='mapping' else 108)
        paired[split]=analysis[split]['paired_mapped_minus_baseline']
    assert report['summary']['mapping']['mapped']['counters']['transport_hits']>0
    assert report['summary']['mapping']['compact']['counters'].get('transport_hits',0)==0
    diagnostic=base.load(out/'mismatch-analysis.json');study.bound(diagnostic['source'])
    assert diagnostic['outputs_counters_and_digests_identical']
    assert diagnostic['candidates']==report['summary']['holdout']['mapped']['counters'].get('transport_candidates',0)
    assert sum(diagnostic['missing_clause_histogram'].values())==diagnostic['candidates']
    assert len({r['case'] for r in diagnostic['records']})==len(diagnostic['records'])<=108
    assert base.sha(diagnostic['archive']['path'])==diagnostic['archive']['sha256']
    for r in diagnostic['records']:
        assert r['plan_counts'].get('support_nodes',0)<=32
        assert r['plan_counts'].get('support_source_literals',0)<=8192
        assert r['plan_counts'].get('plan_peak_bytes',0)<=128*1024
        if r['status']=='checked-support':
            assert r['core_missing']==0
            target,_=normalize(r['target']);assert token(target,Counter())==r['root']
    assert diagnostic['cold']['completed']==diagnostic['statuses'].get('checked-support',0)
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==684
    frontier=check_frontier(out,p)
    cp=base.load(out/'checkpoint.json')
    for field in ('larger_mixtures','witness_pool_study','negative_edit_pool_study','support_plan_study','affine_probe_study','partial_residual_study'):
        assert cp[field]==parent[field]
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    mapped=study.bound(next(s for s in report['samples'] if (s['split'],s['mode'],s['repeat'])==('holdout','mapped',1)))
    cp['residual_transport_study'].update(hint_resume_archive=mapped['archive'],mismatch_analysis=study.binding(out/'mismatch-analysis.json'),
        decision='Optional transport study. Keep the input-safe affine policy as baseline until total-cost and broader coverage gains are established.')
    cp['source_fingerprints']=sources
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    commit=subprocess.check_output(['git','rev-parse','95f254f'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1366 tests in .*\n\nOK',full) and re.search(r'Ran 227 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    origins=Counter();repo=str(Path.cwd())+'/';stdlib=Path(sysconfig.get_path('stdlib')).resolve()
    for site,count in sites.items():
        filename=site.split(':',1)[0]
        if filename.startswith(repo):
            assert filename[len(repo):] in parent['source_fingerprints'];origins['unchanged_project_files']+=count
        else:
            assert Path(filename).resolve().is_relative_to(stdlib);origins['stdlib_collection_sites']+=count
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    base.write(out/'checkpoint.json',cp)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=678,final_sources=684,
        prior_artifacts=8462,prior_manifests=125,full_tests=1366,focused_tests=227,
        exhaustive_formulas=512,warnings=warnings,warning_sites=dict(sites),warning_origins=dict(origins),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        final_union_tables=v['preserved_tables'],frontier=frontier,paired_cost_differences=paired,
        source_fingerprints=sources,
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=[
        'Only stable source-variable IDs carried by normalization propose a map. Arbitrary cross-input renaming and semantic/isomorphism discovery remain open.',
        'The compact ablation follows the same capture, admission and persistence rules but stores compact matching clauses. Representation charges and resulting evictions can differ; it is not a fixed-candidate-state comparison.',
        'Whole-clause containment and exact normalized child identity pass unchanged native checks. Conditional residual refutations never imply unconditioned-source refutations.',
        'Hint metadata is mutable, bounded and separate from proof authority. Cold trial archives retain each policy state; the union merges proofs only. Exact cold hint order is checked under identical limits.',
        'Retained pool/stage/map caps exclude transient copies, root/input normalization, prerequisite proof checks, full checked graph, publication and fallback. Persistent proof storage is uncapped.',
        'Three tiny designed mapping cases expose transport with affine discovery disabled equally. The fresh larger holdout retains normal affine limits. Neither is representative external coverage evidence.',
        'The mismatch census reproduces frozen decisions/counters/digests. Bounded causal trials are posthoc on one selected candidate per query, not an integrated policy or exhaustive support search.',
        'No uniform polynomial arbitrary-SAT expansion or P-versus-NP result follows. Keep outcome and cost regressions visible.',
        'An initial test indexed an absent zero-work metric after an exact cache hit; its source and failure log are retained. The solver implementation did not require a correction.',
        'All earlier payloads remain authoritative. Alternative valid trial proofs and unchanged full-suite SQLite warning sites are retained; focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8462+len(files),
        next_manifests=126,final_sources=684,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
