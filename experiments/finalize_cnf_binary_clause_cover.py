#!/usr/bin/env python3
"""Seal reproducible source, proof, test and artifact preservation checks."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_clause_cover as study
base=study.base
POSTHOC=('experiments/validate_cnf_binary_clause_cover.py','experiments/analyze_cnf_binary_clause_cover.py',
         'experiments/diagnose_cnf_binary_clause_cover.py','experiments/finalize_cnf_binary_clause_cover.py')
BASE_COMMIT='a1a0836'


def finalize(out):
    v=base.load(out/'validation.json');checkpoint=base.load(out/'checkpoint.json')
    p=base.load(out/'protocol.json');prior=study.bound(p['parent'])
    for f,h in prior['source_fingerprints'].items():assert base.sha(f)==h,f
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert len(prior['source_fingerprints'])==560
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'],path
        m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
    assert v['prior_artifacts_unchanged']==7478 and len(v['parent_manifests'])==105
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC})
    assert len(sources)==567
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    commit=subprocess.check_output(['git','rev-parse',BASE_COMMIT],text=True).strip()
    previous=subprocess.check_output(['git','show',commit+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    old=re.findall(pattern,previous,re.S);new=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==64 and old==new
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1196 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 27 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings=={'full-tests.log':44,'focused-tests.log':0}
    latex=logs['latex-final.log'];assert '(220 pages,' in latex
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    assert v['native_preserved']==27368 and v['native_union']==27600
    assert v['extension_preserved']==13 and v['extension_union']==18
    assert v['counter_audits']=={'publication_counter_audits':20,'query_audits':240}
    checks=dict(passed=True,prior_sources=560,final_sources=len(sources),prior_artifacts=7478,prior_manifests=105,
        baseline_commit=commit,proof_blocks_unchanged=64,full_tests=1196,focused_tests=27,warnings=warnings,
        manuscript_pages=220,paper_sha256=base.sha(paper),source_fingerprints=sources,
        limitations=['No new Lean theorem; old proof blocks preserved byte-for-byte.',
            'Both paired timing orders improve modestly, but RSS rises. Candidate stays optional.',
            'Manifest is written after this check; inherited manifests and runtime sources remain immutable.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7478+len(files),next_manifests=106,final_sources=len(sources))),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
