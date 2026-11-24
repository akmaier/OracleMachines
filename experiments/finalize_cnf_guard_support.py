#!/usr/bin/env python3
"""Seal support-subset compilation and its measured resource costs."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_support as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['comparison_trials'],v['audited_target_arm_archives'])==(8,48,24)
    assert len(v['reused_prior_audits'])+len(v['fresh_archive_audits'])==24
    assert v['checkpoint']==old.binding(out/'checkpoint.json')
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(168,16078)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_support.py':base.sha(__file__)}
    assert len(sources)==978
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='d9906072'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1778 tests in .*\n\nOK',full)
    assert re.search(r'Ran 56 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1]);changes={}
    for baseline in ('ordinary','witness'):
        changes[baseline]={k:a['aggregates']['support']['costs'][k]/a['aggregates'][baseline]['costs'][k]-1
            for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes','native_checked_bytes')}
    completed={mode:8-row['statuses'].get('unresolved',0) for mode,row in a['aggregates'].items()}
    decision=base.load(out/'decision.json')
    decision.update(completed=completed,aggregate_changes=changes,support_comparison=a['support_comparison'])
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],
        profiles=a['profiles'],limitations=v['limitations']+a['limitations']))
    cp['source_fingerprints']=sources;cp['guard_support'].update(decision=old.binding(out/'decision.json'),
        next_target=old.binding(out/'next-target.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=972,final_sources=len(sources),
        prior_artifacts=16078,prior_manifests=168,full_tests=1778,focused_tests=56,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],reused_archive_audits=len(v['reused_prior_audits']),
        fresh_archive_audits=len(v['fresh_archive_audits']),final_checkpoint=old.binding(out/'checkpoint.json'),
        limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=16078+len(files),
        next_manifests=169,pages=pages,warnings=warnings,tables=v['preserved_tables'],completed=completed,
        reused_audits=len(v['reused_prior_audits']),fresh_audits=len(v['fresh_archive_audits']),
        aggregate_changes=changes)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
