#!/usr/bin/env python3
"""Seal shared support plans and separate, source-checked frontier evidence."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys,sysconfig
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_support_plan as study
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_negative import check_negative
base=study.base
POSTHOC=('experiments/validate_cnf_support_plan.py','experiments/profile_cnf_support_plan.py','experiments/finalize_cnf_support_plan.py')


def check_screen(out,p):
    screen=base.load(out/'affine-screen.json');cases=study.bound(screen['cases'])
    assert screen['cases']==p['cases']['holdout']
    queries=base.load(out/'holdout-plan-0/queries.json');assert len(screen['records'])==len(cases)==len(queries)==108
    negative=[];stopped=[]
    for c,r,q in zip(cases,screen['records'],queries,strict=True):
        cnf,names=normalize(c['source']);assert r['case']==c['case'] and r['root']==c['root']==token(cnf,Counter())
        assert r['native_status']==q['status']
        summary=check_affine(cnf,r['affine'],Counter());assert summary==r['summary']
        proof=r['negative_proof'];assert (proof is not None)==summary['inconsistent']
        if proof is not None:
            check_negative(cnf,len(names),proof,Counter());assert q['status']!='sat'
            negative.append(c['case'])
            if q['status']=='unresolved':stopped.append(c['case'])
    assert len(negative)==screen['checked_negative']==14
    assert stopped==[42,43] and screen['budget_stops_refuted']==2
    frontier=base.load(out/'frontier.json');assert frontier['affine_screen']==study.binding(out/'affine-screen.json')
    assert len(frontier['budget_stops'])==10 and len(frontier['end_missing_roots'])==6
    assert sum(r['committed_negative'] for r in frontier['budget_stops'])==2622
    assert all(r['committed_positive']==0 for r in frontier['budget_stops'])
    assert {r['case'] for r in frontier['budget_stops']}=={c['case'] for c,q in zip(cases,queries) if q['status']=='unresolved'}
    return dict(inputs=108,negative_observations=len(negative),refuted_budget_stops=stopped,
        certificates_published_in_union=False,native_outcomes_unchanged=True)


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==658 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(121,8197)
    assert (v['query_audits'],v['exact_plan_queries'],v['old_composed_records'],v['old_pilot_records'],v['old_larger_queries'],v['old_inventory_nodes'],v['old_witness_observations'],v['old_negative_observations'])==(1296,432,5650,444,108,624,864,864)
    assert v['new_records']==dict(cnf_residual_v1=5850)
    assert v['preserved_tables']['cnf_residual_v1']==45061 and v['tiny']['formulas']==512
    assert v['tiny']['statuses']==dict(sat=95,unsat=417)
    assert v['alternative_payload_observations']==dict(cnf_residual_v1=260)
    assert v['novelty']==dict(exposed=dict(distinct_roots=72,known_queries=108,queries=108),holdout=dict(distinct_roots=72,known_queries=0,queries=108))
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode'] in ('negative','plan'):
            assert data['summary']['negative_peak_entries']<=16 and data['summary']['negative_peak_literals']<=16*4096
            assert data['reconstruction']['negative_seed_entries']==0
    analysis=base.load(out/'analysis.json')
    for split,arms in report['summary'].items():
        expected=dict(sat=70,unsat=36,unresolved=2) if split=='exposed' else dict(sat=57,unsat=41,unresolved=10)
        for arm in arms.values():assert arm['statuses']==expected
        for f in ('native_digest','native_nodes','native_payload','database_bytes','extension_digest'):
            assert arms['negative'][f]==arms['plan'][f]
        assert arms['plan']['plan_peak_bytes']==(711610 if split=='exposed' else 1378956)
        assert arms['plan']['plan_peak_bytes']<=p['plan_byte_limit']==4*1024*1024
        assert arms['plan']['counters'].get('plan_discovery_fallbacks',0)==0
        assert arms['plan']['counters'].get('negative_materialize_support_nodes',0)==0
        for delta in analysis[split]['paired_plan_minus_baselines']:
            assert delta['negative']['query_seconds']<0 and delta['negative']['complete_worker_seconds']<0
    # Keep the holdout latency regression against witness-only search visible.
    assert analysis['holdout']['plan_reductions']['pool']['mean_query_seconds']<0
    assert analysis['holdout']['paired_plan_minus_baselines'][0]['pool']['query_seconds']>0
    assert analysis['holdout']['paired_plan_minus_baselines'][1]['pool']['query_seconds']<0
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==664
    profile=base.load(out/'profile.json');assert profile['source']['sha256']==sources['experiments/profile_cnf_support_plan.py']
    assert all(r['outputs_and_counters_identical'] for r in profile['profiles'].values())
    screen=check_screen(out,p)
    cp=base.load(out/'checkpoint.json')
    for field in ('larger_mixtures','witness_pool_study','negative_edit_pool_study'):assert cp[field]==parent[field]
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    cp['support_plan_study'].update(profile=study.binding(out/'profile.json'),frontier=study.binding(out/'frontier.json'),affine_screen=study.binding(out/'affine-screen.json'))
    cp['source_fingerprints']=sources
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','8dc9cda'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1336 tests in .*\n\nOK',full) and re.search(r'Ran 197 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    def sites(text):return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current=sites(full);repo=str(Path.cwd())+'/';stdlib=sysconfig.get_path('stdlib')+'/'
    warning_origins=Counter()
    for site in current:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):
            assert filename[len(repo):] in parent['source_fingerprints'];warning_origins['unchanged_project_files']+=current[site]
        else:
            # GC reports where collection occurs, not necessarily where a DB
            # was opened. Retain new stdlib sites rather than misattribute them.
            assert filename.startswith(stdlib);warning_origins['stdlib_collection_sites']+=current[site]
    assert warnings==dict(full=44,focused=0)
    assert warning_origins==dict(unchanged_project_files=42,stdlib_collection_sites=2)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    base.write(out/'checkpoint.json',cp)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=658,final_sources=664,prior_artifacts=8197,prior_manifests=121,
        full_tests=1336,focused_tests=197,exhaustive_formulas=512,warnings=warnings,warning_sites=dict(current),warning_origins=dict(warning_origins),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),final_union_native=45061,affine_screen=screen,
        source_fingerprints=sources,final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=['Optional plan optimization: improves against negative reuse but holdout mean query time remains 0.87% above witness-only search, with mixed paired signs.',
        'Mean cold/warm time, checked-object bytes and worker RSS rise slightly against negative reuse. Actual proof bytes and persistent storage are identical.',
        'Same six designed generators with a fresh size holdout; no representative or arbitrary-SAT runtime claim and no timed decision/family closure gain.',
        'Plans confer no proof authority and clear after each query. Negative candidates start empty on restart.',
        'Plan charge is checked after insertion; temporary oversized allocation, encoding/decoding transients, emission workspace and checked graph are excluded. Capacity fallback can repeat work.',
        'Support budgets exclude prerequisite checks, emitted proof size, transient allocation and fallback; native expansion counts exclude materialization.',
        'Posthoc affine certificates are separate artifacts, not integrated policy timings or changed native observations. Consistent subsystems leave remaining CNF unresolved.',
        'Every earlier authoritative payload remains; 260 differing valid-payload observations remain in full trial archives.',
        'Full suite emits 44 SQLite ResourceWarnings: 42 at unchanged project files and two at stdlib collection sites. Focused tests emit none; collection sites do not establish allocation origins.',
        'First finalization assumed every stdlib collection site matched the preceding run. Failure/source/state are preserved; corrected audit records the new collections site explicitly. Timed results and tests are unchanged.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8197+len(files),next_manifests=122,final_sources=664,pages=pages,warnings=warnings,affine_screen=screen)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
