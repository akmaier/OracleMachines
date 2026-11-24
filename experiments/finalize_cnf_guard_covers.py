#!/usr/bin/env python3
"""Seal the wider-guard coverage checkpoint without replacing old authority."""
from pathlib import Path
import gzip,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_covers as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and v['reference_union_unchanged'] and v['new_cumulative_records']==0
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(171,16500)
    for p,e in v['parent_manifests'].items():
        assert base.sha(p)==e['sha256']
        for f,h in base.load(p)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_covers.py':base.sha(__file__)}
    assert len(sources)==1000
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='7a35126b'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1807 tests in .*\n\nOK',full)
    assert re.search(r'Ran 37 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    decision=base.load(out/'decision.json');base.write(out/'next-target.json',dict(decision=decision,
        event_counts=a['event_counts'],closure_summary=a['closure_summary'],expanded_discovery=a['expanded_discovery']))
    cp['source_fingerprints']=sources;cp['guard_covers'].update({k:old.binding(out/(k+'.json')) for k in ('decision','next-target')})
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=990,final_sources=len(sources),
        prior_artifacts=16500,prior_manifests=171,full_tests=1807,focused_tests=37,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        cumulative_tables=v['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=len(v['supplemental_archive_audits']),final_checkpoint=old.binding(out/'checkpoint.json')))
    # Preserve exact logs, then strip terminal/trailing whitespace for readable git diffs.
    for f in out.rglob('*.log'):
        raw=f.read_bytes();backup=Path(str(f)+'.raw.gz')
        assert not backup.exists();backup.write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=16500+len(files),
        next_manifests=172,pages=pages,warnings=warnings)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
