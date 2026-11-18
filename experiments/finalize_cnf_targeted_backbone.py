#!/usr/bin/env python3
"""Seal source, history, diagnostic, test and manuscript preservation checks."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_targeted_backbone as study
base=study.base
POSTHOC=('experiments/validate_cnf_targeted_backbone.py','experiments/analyze_cnf_targeted_backbone.py',
         'experiments/diagnose_cnf_targeted_backbone.py','experiments/finalize_cnf_targeted_backbone.py')
BASE_COMMIT='4d9e7dc'


def finalize(out):
    v=base.load(out/'validation.json');checkpoint=base.load(out/'checkpoint.json')
    p=base.load(out/'protocol.json');prior=study.bound(p['parent'])
    for ledger in (prior['source_fingerprints'],p['source_fingerprints']):
        for f,h in ledger.items():assert base.sha(f)==h,f
    assert len(prior['source_fingerprints'])==574
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256'],path
        m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
    assert v['prior_artifacts_unchanged']==7568 and len(v['parent_manifests'])==107
    sources=dict(p['source_fingerprints']);sources.update({f:base.sha(f) for f in POSTHOC})
    assert len(sources)==581
    checkpoint['source_fingerprints']=sources;base.write(out/'checkpoint.json',checkpoint)
    v['source_fingerprints']=sources;v['checkpoint']=study.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    commit=subprocess.check_output(['git','rev-parse',BASE_COMMIT],text=True).strip()
    previous=subprocess.check_output(['git','show',commit+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    old=re.findall(pattern,previous,re.S);new=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==64 and old==new
    logs={name:(out/name).read_text() for name in ('full-tests.log','focused-tests.log','latex-final.log')}
    assert re.search(r'Ran 1212 tests in .*\n\nOK',logs['full-tests.log'])
    assert re.search(r'Ran 43 tests in .*\n\nOK',logs['focused-tests.log'])
    warnings={k:len(re.findall('ResourceWarning: unclosed database',x)) for k,x in logs.items() if k!='latex-final.log'}
    assert warnings['focused-tests.log']==0
    latex=logs['latex-final.log'];pages=int(re.search(r'\((\d+) pages,',latex)[1])
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    assert v['native_preserved']==27888 and v['extension_preserved']==22
    report=base.load(out/'report.json')
    publications=sum(study.bound(r)['summary']['new_extension_nodes'] for r in report['samples'])
    assert v['counter_audits']=={'publication_counter_audits':publications,'query_audits':240}
    diagnosis=base.load(out/'diagnosis.json');saved=diagnosis['saved_opportunities']
    assert len(saved)==14 and sum(r['native_kind']=='split' for r in saved)==6
    assert all(abs(r['evidence']['literal'])==r['default_variable'] for r in saved)
    frontier=base.load(out/'attribution.json')['frontier']
    assert frontier['counts'].get('missed_frequency_backbone',0)==0
    assert frontier['counts']['equivalence_counterchecks']==242
    unforced=[r for r in frontier['interactions'] if r['equivalence_blocks'] and not r['forced_literals']]
    assert len(unforced)==20 and sum(r['native_kind']=='split' for r in unforced)==11
    checks=dict(passed=True,prior_sources=574,final_sources=len(sources),prior_artifacts=7568,prior_manifests=107,
        baseline_commit=commit,proof_blocks_unchanged=64,full_tests=1212,focused_tests=43,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),source_fingerprints=sources,
        limitations=['No new Lean theorem; old proof blocks preserved byte-for-byte.',
            'Extra discovery and changed proof costs remain workload-dependent; both policies stay optional.',
            'Manifest is written after this check; inherited manifests and runtime sources remain immutable.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=7568+len(files),next_manifests=108,final_sources=len(sources))),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
