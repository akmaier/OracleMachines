#!/usr/bin/env python3
"""Seal fixed-path conditional certificate transport and its measured limits."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_certificates as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['comparison_trials'],v['distinct_trial_archives'])==(8,64,16)
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(164,15303)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_certificates.py':base.sha(__file__)}
    assert len(sources)==954
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='66752d32'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1740 tests in .*\n\nOK',full)
    assert re.search(r'Ran 96 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    aggregate=a['aggregates'];changes={}
    for mode in study.MODES[1:]:
        changes[mode]={k:aggregate[mode]['costs'][k]/aggregate['guided']['costs'][k]-1
            for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes','native_checked_bytes')}
    completed={mode:8-row['statuses'].get('unresolved',0) for mode,row in aggregate.items()}
    assert completed['certificate']==completed['guided']
    decision=dict(status='experimental; no default change',completed=completed,aggregate_changes=changes,
        result='Transport checked conditional unit traces under further assignments into an actual local cofactor. Surviving support containment, exact coordinate bindings and native proof checking are required. Same guided probe selection and observed ordered search path.',
        limitation='Four alternating comparisons cover only eight exposed chronological edits with provisioned banks. Query caps bound specific counters, not total runtime or process memory. Whole-cofactor preparation/checking and the opposite branch remain.',
        next_target='Investigate the interaction structure of guards with more than one unfixed assumption: group by exact current support/component, identify overlapping and complementary regions, and distinguish compact reusable closure from regions still requiring acquisition. Keep local certificate reuse optional until fresh end-to-end evidence repays matching/preparation.',
        scope='Preserve all regressions, alternate proofs and unresolved roots. Automatic origin discovery, general coordinate transport, fresh unlabelled evaluation and unrestricted resource bounds remain open.')
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],pairs=a['pairs'],traces=a['traces'],
        limitations=v['limitations']+a['limitations']))
    cp['source_fingerprints']=sources;cp['guard_certificate_reuse'].update(decision=old.binding(out/'decision.json'),
        next_target=old.binding(out/'next-target.json'),traces=old.binding(out/'traces.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=949,final_sources=len(sources),
        prior_artifacts=15303,prior_manifests=164,full_tests=1740,focused_tests=96,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=15303+len(files),
        next_manifests=165,pages=pages,warnings=warnings,tables=v['preserved_tables'],completed=completed,aggregate_changes=changes)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
