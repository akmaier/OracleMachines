#!/usr/bin/env python3
"""Seal selected-support cover evidence and exact prior preservation."""
from pathlib import Path
import gzip,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cover_support as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and v['reference_union_unchanged'] and v['new_cumulative_records']==0
    assert v['comparison_trials']==156 and len(v['controls_unchanged'])==22
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(172,16947)
    for p,e in v['parent_manifests'].items():
        assert base.sha(p)==e['sha256']
        for f,h in base.load(p)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_cover_support.py':base.sha(__file__)}
    assert len(sources)==1006
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='a4b66016'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1815 tests in .*\n\nOK',full)
    assert re.search(r'Ran 45 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    total={mode:{metric:sum(a['aggregates'][category][mode][metric] for category in ('bounded','relaxed'))
                for metric in ('mean_solve_seconds','mean_complete_seconds','record_bytes','records','mean_peak_rss_bytes')}
           for mode in study.MODES}
    changes={metric:total['support'][metric]/total['full'][metric]-1 for metric in total['support']}
    decision=base.load(out/'decision.json')
    base.write(out/'next-target.json',dict(decision=decision,local_totals=total,support_vs_full=changes,
        stream=a['stream'],gap=old.binding(out/'shortening-gap.json')))
    cp['source_fingerprints']=sources;cp['guard_cover_support'].update({k:old.binding(out/(k+'.json')) for k in ('decision','next-target')})
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=1000,final_sources=len(sources),
        prior_artifacts=16947,prior_manifests=172,full_tests=1815,focused_tests=45,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        cumulative_tables=v['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=len(v['supplemental_archive_audits']),local_totals=total,support_vs_full=changes,
        final_checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();backup=Path(str(f)+'.raw.gz');assert not backup.exists()
        backup.write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=16947+len(files),
        next_manifests=173,pages=pages,warnings=warnings,support_vs_full=changes)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
