#!/usr/bin/env python3
"""Seal reproducible source, proof, test and artifact preservation checks."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_backbone as study
base=study.base
POSTHOC=('experiments/validate_cnf_binary_backbone.py','experiments/analyze_cnf_binary_backbone.py',
         'experiments/diagnose_cnf_binary_backbone.py','experiments/finalize_cnf_binary_backbone.py')
BASE_COMMIT='47c1609'


def finalize(out):
    v=base.load(out/'validation.json');checkpoint=base.load(out/'checkpoint.json')
    p=base.load(out/'protocol.json');prior=study.bound(p['parent'])
    for f,h in prior['source_fingerprints'].items():assert base.sha(f)==h,f
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert len(prior['source_fingerprints'])==567
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'],path
        m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
    assert v['prior_artifacts_unchanged']==7517 and len(v['parent_manifests'])==106
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC})
    assert len(sources)==574
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    commit=subprocess.check_output(['git','rev-parse',BASE_COMMIT],text=True).strip()
    previous=subprocess.check_output(['git','show',commit+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    old=re.findall(pattern,previous,re.S);new=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==64 and old==new
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1204 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 35 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];assert '(221 pages,' in latex
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    assert v['native_preserved']==27600 and v['native_union']==27888
    assert v['extension_preserved']==18 and v['extension_union']==22
    assert v['counter_audits']=={'publication_counter_audits':24,'query_audits':360}
    correction=base.load(out/'preflight-failure.json');old_protocol=base.load(out/'preflight-protocol.json');test='solver/test_cnf_binary_backbone.py'
    assert not correction['production_started']
    assert base.sha(out/'preflight-tests.py.txt')==correction['old_test_sha256']==old_protocol['source_fingerprints'][test]
    assert base.sha(test)==correction['new_test_sha256']==p['source_fingerprints'][test]
    frontier=base.load(out/'attribution.json')['frontier'];split=[r for r in frontier['missed'] if r['native_kind']=='split']
    assert len(split)==6 and all(r['native_split_matches'] for r in split)
    checks=dict(passed=True,prior_sources=567,final_sources=len(sources),prior_artifacts=7517,prior_manifests=106,
        baseline_commit=commit,proof_blocks_unchanged=64,full_tests=1204,focused_tests=35,warnings=warnings,
        manuscript_pages=221,paper_sha256=base.sha(paper),source_fingerprints=sources,
        limitations=['No new Lean theorem; old proof blocks preserved byte-for-byte.',
            'Frequency query timing improves, but complete timing remains mixed; first-path storage regresses. Both stay optional.',
            'Manifest is written after this check; inherited manifests and runtime sources remain immutable.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7517+len(files),next_manifests=107,final_sources=len(sources))),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
