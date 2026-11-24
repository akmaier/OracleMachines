#!/usr/bin/env python3
"""Seal selective live guard closure, total costs and the next measured gap."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_closure as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['comparison_trials'],v['distinct_trial_archives'])==(8,64,32)
    assert v['checkpoint']==old.binding(out/'checkpoint.json')
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(166,15614)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_closure.py':base.sha(__file__)}
    assert len(sources)==966
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='b6ce4e8d'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1758 tests in .*\n\nOK',full)
    assert re.search(r'Ran 36 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1]);changes={}
    for baseline in ('ordinary','certificate'):
        changes[baseline]={mode:{k:a['aggregates'][mode]['costs'][k]/a['aggregates'][baseline]['costs'][k]-1
            for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes','native_checked_bytes')}
            for mode in ('units','binary')}
    completed={mode:8-row['statuses'].get('unresolved',0) for mode,row in a['aggregates'].items()}
    # Written after inspecting the completed study, with observed claims only.
    decision=base.load(out/'decision.json')
    decision.update(completed=completed,aggregate_changes=changes)
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],
        profiles=a['profiles'],limitations=v['limitations']+a['limitations']))
    cp['source_fingerprints']=sources;cp['guard_closure'].update(decision=old.binding(out/'decision.json'),
        next_target=old.binding(out/'next-target.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    # The validator audits one archive per target/arm. Some unchanged arms can
    # have identical bytes, so distinguish those files from distinct contents.
    trials=base.load(out/'comparisons.json')['samples']
    database_hashes={old.bound(sample)['archive']['database_sha256'] for sample in trials}
    v['audited_target_arm_archives']=v.pop('distinct_trial_archives')
    v['distinct_trial_database_hashes']=len(database_hashes)
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=960,final_sources=len(sources),
        prior_artifacts=15614,prior_manifests=166,full_tests=1758,focused_tests=36,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=15614+len(files),
        next_manifests=167,pages=pages,warnings=warnings,tables=v['preserved_tables'],completed=completed,
        aggregate_changes=changes)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
