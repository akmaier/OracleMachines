#!/usr/bin/env python3
"""Seal bounded witness retrieval evidence, including cold misses and audit failure."""
from pathlib import Path
from collections import Counter
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_witness_pool as study
base=study.base
POSTHOC=('experiments/validate_cnf_witness_pool.py','experiments/finalize_cnf_witness_pool.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    assert len(parent['source_fingerprints'])==647 and v['passed']
    for ledger in (parent['source_fingerprints'],p['source_fingerprints'],v['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];items=base.load(path)['artifacts'];assert len(items)==entry['artifacts_checked']
        for f,h in items.items():assert base.sha(f)==h,f
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(119,8088)
    assert (v['query_audits'],v['old_composed_records'],v['old_pilot_records'],v['old_larger_queries'],v['old_inventory_nodes'])==(864,5650,444,108,624)
    assert v['new_records']==dict(cnf_residual_v1=3285)
    assert v['preserved_tables']['cnf_residual_v1']==34426 and v['tiny']['formulas']==512
    assert v['novelty']==dict(exposed=dict(distinct_roots=72,known_queries=108,queries=108),holdout=dict(distinct_roots=72,known_queries=0,queries=108))
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    for sample in report['samples']:
        data=study.bound(sample);study.bound(data['queries']);assert base.sha(data['archive']['path'])==data['archive']['sha256']
        if sample['mode']=='pool':
            assert data['summary']['witness_peak_entries']<=64 and data['summary']['witness_peak_bytes']<14200
            assert data['reconstruction']['seed_counts']['witness_seed_rows']==64
            assert data['reconstruction']['pool_entries']==(0 if sample['split']=='exposed' else 33)
    for split,arms in report['summary'].items():
        expected=dict(sat=70,unsat=36,unresolved=2) if split=='exposed' else dict(sat=64,unsat=42,unresolved=2)
        for arm in arms.values():assert arm['statuses']==expected
        for delta in base.load(out/'analysis.json')[split]['paired_pool_minus_baseline']:assert delta['query_seconds']<0 and delta['complete_worker_seconds']<0
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==652
    cp=base.load(out/'checkpoint.json');assert cp['larger_mixtures']==parent['larger_mixtures']
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    cp['source_fingerprints']=sources;base.write(out/'checkpoint.json',cp)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','2e3db30'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1319 tests in .*\n\nOK',full) and re.search(r'Ran 150 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    def sites(text):return Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in text.splitlines() if 'ResourceWarning: unclosed database' in line)
    current=sites(full);previous=sites((study.PARENT/'full-tests.log').read_text());repo=str(Path.cwd())+'/'
    for site in current:
        filename=site.split(':',1)[0]
        if filename.startswith(repo):assert filename[len(repo):] in parent['source_fingerprints']
        else:assert any(old.split(':',1)[0]==filename for old in previous)
    assert warnings['focused']==0
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M);pages=int(re.search(r'\((\d+) pages,',latex)[1])
    checks=dict(passed=True,baseline_commit=commit,prior_sources=647,final_sources=652,prior_artifacts=8088,prior_manifests=119,
        full_tests=1319,focused_tests=150,exhaustive_formulas=512,warnings=warnings,warning_sites=dict(current),
        proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),final_union_native=34426,
        source_fingerprints=sources,final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=['Same six designed generators with a fresh size holdout; two orders, no representative or arbitrary-SAT runtime claim.',
        'No structural closure gain; two budget stops remain in every arm/split. Some family timings and holdout warm time regress.',
        'Vectors use compact ranks as arbitrary proposals, never donor equivalence. Every target is checked fully; misses give no UNSAT evidence.',
        'Candidate caps exclude whole solver, temporary allocations and seed JSON payload bytes; the native expansion budget does not bound all work.',
        'The exposed cold seed is empty after an UNSAT tail; holdout reconstructs 33 vectors. Warm exact hits do not establish cold hint persistence.',
        'All prior payloads remain authoritative; 130 differing valid-payload observations remain in full trial archives.',
        'Initial audit accessed the preceding recovery result through an incorrect nested result key; failed source/log preserved. Timed runs were unchanged.',
        'Full-suite SQLite ResourceWarnings remain at unchanged files; focused tests emit none.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=8088+len(files),next_manifests=120,final_sources=652,pages=pages,warnings=warnings)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
