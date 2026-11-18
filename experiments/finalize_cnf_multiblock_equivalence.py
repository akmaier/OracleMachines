#!/usr/bin/env python3
"""Seal multiblock validation, preserved history and measured regressions."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_multiblock_equivalence as study
base=study.base
POSTHOC=('experiments/validate_cnf_multiblock_equivalence.py','experiments/finalize_cnf_multiblock_equivalence.py')


def finalize(out):
    p=base.load(out/'protocol.json');parent=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (parent['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(parent['source_fingerprints'])==596
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==111 and v['prior_artifacts_unchanged']==7722
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==601
    checkpoint=base.load(out/'checkpoint.json');checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert sorted(v['preserved_tables'].values())==[26,34,42,42,28691]
    assert (v['native_union'],v['new_native'],v['new_multiblock_records'])==(28736,45,11)
    assert (v['query_audits'],v['truth_tables'],v['multiblock_truth_pairs'],v['old_composed_records'],v['old_pilot_records'],v['new_records'])==(408,68,12,5650,272,68)
    assert v['equal_acquisitions']==68 and not v['alternate_native_occurrences']
    summaries=base.load(out/'report.json')['summary']
    for field in ('native_digest','extension_digest'):assert summaries['all'][field]==summaries['cached'][field]
    assert summaries['cached']['counters']['multi_applied_merges']==57
    assert summaries['cached']['counters']['propagation_literal_visits']==51059
    assert summaries['cached']['native_nodes']-summaries['single']['native_nodes']==10
    a=base.load(out/'attribution.json');known=[r for r in a['multiblock_sources'] if r['known_at_prefix']['cached']==[True,False]]
    assert [r['case'] for r in known]==[7,34] and sum(r['native_delta'] for r in known)==8
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','315372e'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1245 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 76 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=596,final_sources=len(sources),prior_artifacts=7722,prior_manifests=111,
        source_fingerprints=sources,full_tests=1245,focused_tests=76,warnings=warnings,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['Same 68-source pilot; broader exact reduction is not fresh source coverage.',
            'Propagation falls 0.52%, but ten more native certificates and 3483 more combined bytes are stored.',
            'Query timing improves in both orders; total time remains mixed. Exact known-quotient selection is diagnosed, not implemented.',
            'No recursive production integration, new Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7722+len(files),next_manifests=112,final_sources=len(sources),pages=pages)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
