#!/usr/bin/env python3
"""Seal the residual-pool regression and its checked coordinate counterexample."""
from collections import Counter
from pathlib import Path
import json,re,subprocess,sys,sysconfig,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partial_residual_pool as study
from experiments.finalize_cnf_affine_probe import check_frontier
from experiments.cnf_residual_dag import normalize,token
base=study.base
POSTHOC=('experiments/validate_cnf_partial_residual_pool.py',
         'experiments/profile_cnf_partial_residual_pool.py',
         'experiments/finalize_cnf_partial_residual_pool.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==672 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts']
        assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(124,8402)
    fields=('query_audits','old_composed_records','old_pilot_records','old_larger_queries',
            'old_inventory_nodes','old_witness_observations','old_negative_observations',
            'old_support_plan_observations','old_affine_probe_observations')
    assert tuple(v[f] for f in fields)==(864,5650,444,108,624,864,864,1296,1296)
    assert v['tiny']['formulas']==512 and v['tiny']['statuses']==dict(sat=95,unsat=417)
    assert v['prior_tables']['cnf_residual_v1']==54418 and v['prior_tables']['cnf_affine_negative_v1']==47
    for t,n in v['preserved_tables'].items():assert n==v['prior_tables'][t]+v['new_records'].get(t,0)
    assert v['novelty']['holdout']==dict(distinct_roots=72,known_queries=0,queries=108)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries'])
        assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode']=='partial':
            assert data['summary']['partial_peak_entries']<=p['partial_limits']['partial_capacity']
            assert data['summary']['partial_peak_bytes']<=p['partial_limits']['partial_bytes']
            assert data['reconstruction']['partial_seed_entries']<=p['partial_limits']['partial_capacity']
    analysis=base.load(out/'analysis.json')
    paired={}
    for split,arms in report['summary'].items():
        assert arms['base']['statuses']==arms['partial']['statuses']
        assert arms['base']['counters']['expanded_nodes']==arms['partial']['counters']['expanded_nodes']
        assert sum(arms['base']['statuses'].values())==108
        assert analysis[split]['status_changes']['base']==dict(newly_completed=[],newly_stopped=[])
        paired[split]=analysis[split]['paired_partial_minus_baseline']
    profile=base.load(out/'profile.json')
    # The profiler records its invocation's absolute __file__; bind its content
    # to the repository source so verification also works in another checkout.
    assert Path(profile['source']['path']).name==Path(POSTHOC[1]).name
    assert profile['source']['sha256']==base.sha(POSTHOC[1])
    assert profile['outputs_counters_and_digests_identical']
    example=base.load(out/'coordinate-example.json')
    mapping={int(k):v for k,v in example['transport'].items()}
    assert len(set(mapping.values()))==len(mapping) and all(v>0 for v in mapping.values())
    assert sorted(mapping.values())==[mapping[k] for k in sorted(mapping)]
    lifted=[[(1 if l>0 else -1)*mapping[abs(l)] for l in cl] for cl in example['core']]
    assert set(map(tuple,lifted))<=set(map(tuple,example['target']))
    core,_=normalize(lifted);target,_=normalize(example['target'])
    assert token(core,Counter())==example['origin'] and token(target,Counter())==example['root']
    assert example['proposal_miss'].get('partial_hits',0)==0
    assert example['node']['answer'] is False and example['node']['proof']['child']==example['origin']
    assert base.sha(example['archive']['path'])==example['archive']['sha256']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';base.restore_archive(example['archive'],path)
        audit=study.cold(path,[dict(source=example['target'])],[dict(status='unsat',result=dict(
            answer=False,model=None,root=example['root'],authority='native'))])
    assert audit['native']==example['cold']['native'] and audit['completed']==1
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==678
    frontier=check_frontier(out,p)
    cp=base.load(out/'checkpoint.json')
    for field in ('larger_mixtures','witness_pool_study','negative_edit_pool_study','support_plan_study','affine_probe_study'):
        assert cp[field]==parent[field]
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    cp['partial_residual_study'].update(profile=study.binding(out/'profile.json'),
        coordinate_example=study.binding(out/'coordinate-example.json'),
        decision='Retain as an optional negative experiment. Keep the input-safe affine policy as the performance baseline.')
    cp['source_fingerprints']=sources
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    commit=subprocess.check_output(['git','rev-parse','8f60d64'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1355 tests in .*\n\nOK',full) and re.search(r'Ran 216 tests in .*\n\nOK',focused)
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
    checks=dict(passed=True,baseline_commit=commit,prior_sources=672,final_sources=678,
        prior_artifacts=8402,prior_manifests=124,full_tests=1355,focused_tests=216,
        exhaustive_formulas=512,warnings=warnings,warning_sites=dict(sites),warning_origins=dict(origins),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        final_union_tables=v['preserved_tables'],frontier=frontier,paired_cost_differences=paired,
        coordinate_example=study.binding(out/'coordinate-example.json'),source_fingerprints=sources,
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=[
        'The residual pool is an optional negative experiment: unchanged outcomes and expansion counts, increased mean query and complete time. Prior affine policy remains the baseline.',
        'Pool hints are not proof authority. Every matched negative residual/core and target containment pass unchanged native checks; conditional refutations do not imply their original source is UNSAT.',
        'Retained pool/plan charges exclude decoding and insertion transients, prerequisite proof checks, full checked graph, publication and fallback. Persistent proof storage is not capped.',
        'Cold tail seeding is bounded reconstruction, not restoration of the exact former candidate order or conditional variable maps.',
        'The supplied-map counterexample proves one retrieval blind spot; it neither discovers the map automatically nor estimates the frequency of such misses in the timed streams.',
        'Two opposite orders of six designed generators are not representative external benchmarks. Instrumented profile times overlap and are not policy comparisons.',
        'No wider tractable family coverage, uniform polynomial arbitrary-SAT expansion or P-versus-NP result follows.',
        'All earlier payloads remain authoritative. Different valid trial proofs and prefreeze policy revisions are retained. Full-suite SQLite warning sites are recorded; focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8402+len(files),
        next_manifests=125,final_sources=678,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
