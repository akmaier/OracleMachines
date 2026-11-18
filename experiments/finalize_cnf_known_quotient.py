#!/usr/bin/env python3
"""Seal known-quotient results, failures and the next measured reuse opportunity."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_known_quotient as study
base=study.base
POSTHOC=('experiments/validate_cnf_known_quotient.py','experiments/profile_cnf_known_quotient.py','experiments/finalize_cnf_known_quotient.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==601
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==112 and v['prior_artifacts_unchanged']==7761
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==607
    checkpoint=base.load(out/'checkpoint.json');checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[11,26,34,42,42,28736]
    assert (v['native_union'],v['new_native'],v['v2_union'],v['v3_union'])==(28886,150,53,22)
    assert (v['query_audits'],v['truth_tables'],v['fresh_exclusions'],v['choice_audits'],v['known_hit_audits'])==(624,104,36,48,28)
    assert (v['old_composed_records'],v['old_pilot_records'],v['new_records'])==(5650,340,104)
    assert not v['alternate_native_occurrences']
    summaries=base.load(out/'report.json')['summary'];a=summaries['all'];b=summaries['known']
    assert a['native_nodes']-b['native_nodes']==8
    assert a['native_payload']+a['extension_payload']-b['native_payload']-b['extension_payload']==3406
    assert b['counters']['quotient_choice_first_hits']==4 and b['counters']['quotient_choice_lookups']==38
    profile=base.load(out/'profile.json');assert profile['outputs_and_counters_identical']
    assert profile['profile_source']['sha256']==sources['experiments/profile_cnf_known_quotient.py']
    c=profile['canonical_census'];assert (c['calls'],c['exact_repeats'],c['within_query_repeats'],c['max_query_encoded_state'])==(1715,505,469,73860)
    failed=out/'failed-reader-dispatch';original=base.load(failed/'protocol.json')
    assert original['source_fingerprints']['experiments/compare_cnf_known_quotient.py']==base.sha(failed/'compare-source.py.txt')
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','cfe2a7c'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1253 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 84 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=601,final_sources=len(sources),prior_artifacts=7761,prior_manifests=112,
        source_fingerprints=sources,full_tests=1253,focused_tests=84,warnings=warnings,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['Eight native savings occur on the pilot; the 36 fresh queries have equal native additions across arms.',
            'Extra choice work raises mean runtime; no total speedup established.',
            'Canonical-result reuse is a measured opportunity, not an implemented cache.',
            'No recursive production integration, new Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7761+len(files),next_manifests=113,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
