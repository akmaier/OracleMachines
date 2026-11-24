#!/usr/bin/env python3
"""Seal the layer-publication comparison without changing prior proof blocks."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_history_layers as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and len(v['archive_audits'])==4 and v['added_records_this_run']==0
    assert v['checkpoint']==old.binding(out/'checkpoint.json')
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(169,16266)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_history_layers.py':base.sha(__file__)}
    assert len(sources)==983
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='375b53c8'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1789 tests in .*\n\nOK',full)
    assert re.search(r'Ran 24 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    cp['source_fingerprints']=sources
    cp['history_layers'].update({k:old.binding(out/(k+'.json')) for k in ('decision','next-target')})
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=978,final_sources=len(sources),
        prior_artifacts=16266,prior_manifests=169,full_tests=1789,focused_tests=24,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),
        limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=16266+len(files),
        next_manifests=170,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
