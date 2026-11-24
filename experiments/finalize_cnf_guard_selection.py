#!/usr/bin/env python3
"""Seal live selection comparisons and retain mixed results and open cases."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_probes as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['comparison_trials'],v['distinct_trial_archives'])==(8,128,32)
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(163,14882)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_selection.py':base.sha(__file__)}
    assert len(sources)==949
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='e0d73a0f51cdf010d3e6eb7ae0ac4d9a7bdcbe65'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1731 tests in .*\n\nOK',full)
    assert re.search(r'Ran 87 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    aggregate=a['aggregates'];changes={}
    for mode in study.MODES[1:]:
        changes[mode]={k:aggregate[mode]['costs'][k]/aggregate['native']['costs'][k]-1
            for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes','native_checked_bytes')}
    completed={mode:8-row['statuses'].get('unresolved',0) for mode,row in aggregate.items()}
    assert completed['tracking']==completed['native']
    pp=base.load(out/'profile-protocol.json')
    decision=dict(status='experimental; no default change',completed=completed,aggregate_changes=changes,
        result='A live guard-guided probe selector reuses native canonicalization and retires expansion-owned coordinate hints. Exact tracking controls preserve original counters and SQLite files; all selected exclusions use existing checked local certificates.',
        limitation='Four alternating comparisons cover only eight exposed chronological edits with provisioned banks. A polarity-order control retains the same selector, but later paths may differ. Local guarded exclusions do not establish cheap general expansion.',
        next_target='Test direct transport of surviving conditional unit certificates to the actual local cofactor under a fixed probe-selection path, starting from cnf_conditional_unit_support.materialize. Require local support containment, exact fixed/name maps and unchanged native checking; fallback on missing component support. Matching itself is small in the retained profile.',
        prior_work='Broad normalization memos, prepared-cofactor memos, ordered normalization and canonical-header checking already exist, with mixed or negative costs. A new reuse proposal must identify an additional boundary rather than repeat these experiments.',
        profile_target=pp['target'],
        scope='Keep negative timings and unresolved roots. Automatic origin discovery, general coordinate transport, fresh unlabelled evaluation and unrestricted resource bounds remain open.')
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],pairs=a['pairs'],profiles=a['profiles'],
        limitations=v['limitations']+a['limitations']))
    cp['source_fingerprints']=sources;cp['guard_probe_selection'].update(decision=old.binding(out/'decision.json'),
        next_target=old.binding(out/'next-target.json'),profiles=old.binding(out/'profiles.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=943,final_sources=len(sources),
        prior_artifacts=14882,prior_manifests=163,full_tests=1731,focused_tests=87,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=14882+len(files),
        next_manifests=164,pages=pages,warnings=warnings,tables=v['preserved_tables'],completed=completed,aggregate_changes=changes)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
