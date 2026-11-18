#!/usr/bin/env python3
"""Seal the optional equivalence pilot and its preserved regression."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_equivalence as study
base=study.base
POSTHOC=('experiments/validate_cnf_binary_equivalence.py','experiments/finalize_cnf_binary_equivalence.py')


def finalize(out):
    p=base.load(out/'protocol.json');prior=study.bound(p['parent']);v=base.load(out/'validation.json')
    for ledger in (prior['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(prior['source_fingerprints'])==581
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'];artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
    assert len(v['parent_manifests'])==108 and v['prior_artifacts_unchanged']==7608
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC});assert len(sources)==586
    checkpoint=base.load(out/'checkpoint.json');checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    assert (v['native_preserved'],v['native_union'],v['affine_preserved'],v['equivalence_union'])==(28145,28691,26,42)
    assert (v['query_audits'],v['truth_tables'],v['old_records'],v['new_records'])==(272,68,5650,136)
    attribution=base.load(out/'attribution.json');assert len(attribution['multiple_blocks'])==12
    assert len(attribution['binary_repetition']['repeated'])==22
    assert attribution['modes']['quotient']['extension_byte_parts']==dict(id_bytes=21345,payload_bytes=47533,cnf_json_bytes=20673,evidence_json_bytes=2713,child_json_bytes=20535)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';commit=subprocess.check_output(['git','rev-parse','073e4af'],text=True).strip()
    old=subprocess.check_output(['git','show',commit+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    previous=re.findall(pattern,old,re.S);assert len(previous)==64 and previous==re.findall(pattern,Path(paper).read_text(),re.S)
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1220 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 51 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1]);assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    checks=dict(passed=True,baseline_commit=commit,prior_sources=581,final_sources=len(sources),prior_artifacts=7608,prior_manifests=108,
        source_fingerprints=sources,full_tests=1220,focused_tests=51,warnings=warnings,proof_blocks_unchanged=64,manuscript_pages=pages,paper_sha256=base.sha(paper),
        limitations=['Top-level empty-archive pilot only, including counterfactual saved inputs; production admission and recursive integration remain open.',
            'Total certificates, payload and time regress despite fewer propagation visits; solver remains optional.',
            'No new Lean theorem or unrestricted-SAT resource bound.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7608+len(files),next_manifests=109,final_sources=len(sources))),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
