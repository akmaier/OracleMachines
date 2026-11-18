#!/usr/bin/env python3
"""Seal the bounded-cache regression, unchanged history and tested next target."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_query_canonical_cache as study
base=study.base
POSTHOC=('experiments/validate_cnf_query_canonical_cache.py','experiments/profile_cnf_query_canonical_cache.py','experiments/finalize_cnf_query_canonical_cache.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==607
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==113 and v['prior_artifacts_unchanged']==7807
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==613
    checkpoint=base.load(out/'checkpoint.json');assert checkpoint['reference_union']==parent['reference_union']
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[22,26,34,42,53,28886]
    assert v['reference_union_unchanged'] and v['new_native']==v['new_extensions']==0
    assert (v['query_audits'],v['truth_tables'],v['choice_audits'],v['known_hit_audits'],v['exact_cache_query_comparisons'])==(832,104,144,84,416)
    assert (v['old_composed_records'],v['old_pilot_records'])==(5650,444)
    summaries=base.load(out/'report.json')['summary'];a=summaries['known'];b=summaries['cached'];small=summaries['small']
    for arm in (b,small):
        for k in ('native_digest','extension_digest','database_bytes','compressed_bytes','native_payload','extension_payload','cache_digest'):
            assert arm[k]==a[k]
        assert arm['canonical_cache_peak_bytes']<=arm['canonical_cache_capacity']
        assert arm['mean_complete_worker_seconds']>a['mean_complete_worker_seconds']
    assert (b['counters']['canonical_cache_hits'],small['counters']['canonical_cache_hits'])==(368,14)
    assert (a['counters']['normalization_literal_visits'],b['counters']['normalization_literal_visits'],small['counters']['normalization_literal_visits'])==(175148,140863,174541)
    attribution=base.load(out/'attribution.json')
    assert all(p['complete_worker_seconds']>0 for p in attribution['pairs'])
    assert all(hits==[0,0] for hits in attribution['warm_cache_hits'].values())
    profile=base.load(out/'profile.json')
    assert all(p['outputs_and_counters_identical'] for p in profile['profiles'].values())
    assert profile['profile_source']['sha256']==sources['experiments/profile_cnf_query_canonical_cache.py']
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','8e020a7'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1262 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 93 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=607,final_sources=len(sources),prior_artifacts=7807,prior_manifests=113,
        source_fingerprints=sources,full_tests=1262,focused_tests=93,warnings=warnings,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['Exact cache reuse reduces normalization work but increases complete time in both orders at both tested capacities.',
            'All 104 inputs replay the preceding study; no new SAT pattern coverage.',
            'Retained cache-object cap excludes transient allocations, allocator overhead and other solver state.',
            'No new persisted proofs or answers; the previous archive and all decisions are referenced unchanged.',
            'Direct canonical-result transport is a next investigation, not an implemented saving or a new proof authority.',
            'No production-default change, new Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7807+len(files),next_manifests=114,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
