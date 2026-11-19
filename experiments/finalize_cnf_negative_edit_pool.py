#!/usr/bin/env python3
"""Seal the negative-edit reuse tradeoff, preserving every measured regression."""
from pathlib import Path
from collections import Counter
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_negative_edit_pool as study
base=study.base
POSTHOC=('experiments/validate_cnf_negative_edit_pool.py','experiments/profile_cnf_negative_edit_pool.py','experiments/finalize_cnf_negative_edit_pool.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==652 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(120,8141)
    assert (v['query_audits'],v['old_composed_records'],v['old_pilot_records'],v['old_larger_queries'],v['old_inventory_nodes'],v['old_witness_observations'])==(864,5650,444,108,624,864)
    assert v['new_records']==dict(cnf_residual_v1=4785)
    assert v['preserved_tables']['cnf_residual_v1']==39211 and v['tiny']['formulas']==512
    assert v['novelty']==dict(exposed=dict(distinct_roots=72,known_queries=108,queries=108),holdout=dict(distinct_roots=72,known_queries=0,queries=108))
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode']=='negative':
            assert data['summary']['negative_peak_entries']<=16 and data['summary']['negative_peak_literals']<=16*4096
            assert data['reconstruction']['negative_seed_entries']==0
    for split,arms in report['summary'].items():
        expected=dict(sat=70,unsat=36,unresolved=2) if split=='exposed' else dict(sat=57,unsat=48,unresolved=3)
        for arm in arms.values():assert arm['statuses']==expected
        assert arms['negative']['counters']['negative_hits']==10
        for delta in base.load(out/'analysis.json')[split]['paired_negative_minus_pool']:
            assert delta['query_seconds']>0 and delta['complete_worker_seconds']<0 and delta['warm_seconds']>0
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==658
    profile=base.load(out/'profile.json');assert profile['source']['sha256']==sources['experiments/profile_cnf_negative_edit_pool.py']
    assert all(v['outputs_and_counters_identical'] for v in profile['profiles'].values())
    cp=base.load(out/'checkpoint.json')
    for field in ('larger_mixtures','witness_pool_study'):assert cp[field]==parent[field]
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    cp['source_fingerprints']=sources;base.write(out/'checkpoint.json',cp)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','f0c3ae0'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1327 tests in .*\n\nOK',full) and re.search(r'Ran 188 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    def sites(text):return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current=sites(full);previous=sites((study.PARENT/'full-tests.log').read_text());repo=str(Path.cwd())+'/'
    for site in current:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):assert filename[len(repo):] in parent['source_fingerprints']
        else:assert any(old.split(':',1)[0]==filename for old in previous)
    assert warnings==dict(full=44,focused=0)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    checks=dict(passed=True,baseline_commit=commit,prior_sources=652,final_sources=658,prior_artifacts=8141,prior_manifests=120,
        full_tests=1327,focused_tests=188,exhaustive_formulas=512,warnings=warnings,warning_sites=dict(current),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),final_union_native=39211,
        source_fingerprints=sources,final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=['Optional space/replay tradeoff: query and warm time regress in both orders. Keep the witness pool as the latency baseline.',
        'Same six designed generators with a fresh size holdout; no representative or arbitrary-SAT runtime claim and no decision/family closure gain.',
        'Candidate descriptions and causal proposals have no proof authority. Deleted premises require another checked support or fallback.',
        'Support node/literal budgets exclude prerequisite checks, emitted proofs, transient allocation, and fallback; native expansion counts exclude materialization.',
        'Negative candidates start empty on restart. Cold exact replay can readmit roots but does not restore candidate order/proposals.',
        'Every earlier authoritative payload remains; 164 differing valid-payload observations remain in full trial archives.',
        'First profiler comparison failed on JSON string model keys versus in-memory integers. Source/log preserved; corrected comparison passes without changes to timed runs.',
        'Full-suite SQLite ResourceWarnings remain at unchanged files; focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8141+len(files),next_manifests=121,final_sources=658,pages=pages,warnings=warnings)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
