#!/usr/bin/env python3
"""Seal the shared-context experiment and exact prior proof preservation."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_context as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['comparison_trials'])==(8,48)
    assert len(v['reused_prior_audits'])==24 and not v['fresh_archive_audits'] and v['reference_union_unchanged']
    assert not any(v['new_records'].values()) and v['checkpoint']==old.binding(out/'checkpoint.json')
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(170,16313)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_context.py':base.sha(__file__)}
    assert len(sources)==990
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='3d95fd17'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1798 tests in .*\n\nOK',full)
    assert re.search(r'Ran 46 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    changes={m:{k:a['aggregates']['context']['costs'][k]/a['aggregates'][m]['costs'][k]-1 for k in
        ('mean_solve_seconds','mean_complete_seconds','database_bytes','native_checked_bytes','mean_peak_rss_bytes')} for m in ('ordinary','support')}
    decision=base.load(out/'decision.json');decision.update(aggregate_changes=changes)
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],profiles=a['profiles'],limitations=v['limitations']))
    cp['source_fingerprints']=sources;cp['guard_context'].update({k:old.binding(out/(k+'.json')) for k in ('decision','next-target')})
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=983,final_sources=len(sources),
        prior_artifacts=16313,prior_manifests=170,full_tests=1798,focused_tests=46,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],reused_archive_audits=24,fresh_archive_audits=0,
        reference_union_unchanged=True,final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=16313+len(files),
        next_manifests=171,pages=pages,warnings=warnings,aggregate_changes=changes,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
