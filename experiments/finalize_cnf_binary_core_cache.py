#!/usr/bin/env python3
"""Seal discovery-cache evidence and the unchanged-certificate checkpoint."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_core_cache as study
base=study.base
POSTHOC=('experiments/validate_cnf_binary_core_cache.py','experiments/finalize_cnf_binary_core_cache.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==591
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==110 and v['prior_artifacts_unchanged']==7683
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==596
    checkpoint=base.load(out/'checkpoint.json');checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[26,42,42,28691]
    assert (v['new_cache_entries'],v['query_audits'],v['truth_tables'],v['old_composed_records'],v['old_pilot_records'],v['new_records'])==(34,408,68,5650,204,68)
    assert v['equal_acquisition']==dict(chronological_acquisitions=136)
    summaries=base.load(out/'report.json')['summary']
    for mode in ('memory','persistent'):
        for field in ('native_digest','extension_digest'):assert summaries[mode][field]==summaries['compact'][field]
        assert summaries[mode]['cache_entries']==34 and summaries[mode]['cache_payload']==11906
        assert summaries[mode]['counters']['equiv_cache_memory_hits']==22
        assert summaries[mode]['counters']['equiv_scc_edge_visits']==4744
    assert summaries['compact']['counters']['equiv_scc_edge_visits']==8552
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','19950e7'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1236 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 67 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=591,final_sources=len(sources),prior_artifacts=7683,prior_manifests=110,
        source_fingerprints=sources,full_tests=1236,focused_tests=67,warnings=warnings,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['Same 68-input pilot; no new coverage or recursive production integration.',
            'Acquisition SCC work falls 44.53%; acquisition plus persisted-cache cold validation rises 10.94%.',
            'Memory-mode total timing has mixed signs. Persistent query timing has mixed signs and total changes are small.',
            'No new Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7683+len(files),next_manifests=111,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
