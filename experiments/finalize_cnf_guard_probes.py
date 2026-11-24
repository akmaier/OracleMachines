#!/usr/bin/env python3
"""Seal the passive guard-probe census without claiming a policy speedup."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_probes as study
base=study.base;old=study.old


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json');a=base.load(out/'analysis.json')
    assert v['passed'] and (v['targets_checked'],v['contexts_checked'],v['certificates_checked'])==(8,648,394)
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(162,14809)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_probes.py':base.sha(__file__)}
    assert len(sources)==943
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='3751e4a532e59b056a7718ccf9eaa6622b64b237'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1722 tests in .*\n\nOK',full)
    assert re.search(r'Ran 78 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    assert (a['distinct_certificates'],a['distinct_untried'],a['distinct_different_variable'])==(394,260,232)
    assert a['summary']['contexts_with_proposals']==248 and a['summary']['untried_absent_unit_conflicts']==260
    assert sum(t['subset_proposals'] for t in a['targets'])==134
    assert a['observer_counts']['guard_candidate_checks']==32044 and a['observer_counts']['guard_pair_checks']==262032
    decision=dict(status='passive census only; no default change',
        result='Saved guards propose 394 distinct locally unit-refutable cofactors at 648 ordinary probe contexts. 260 polarities are untried there; 232 use a different variable. Every untried proposal is absent at the first probe in its context.',
        limitation='All eight exposed cold edits still stop at 256 dispatches with byte-identical original/observed SQLite files. Observation costs more; no live policy or whole-input coverage improvement is measured.',
        next_target='Test a bounded live guard-guided selector at ordinary probe sites, using existing native unit/split/model composition and actual local checking. Avoid diagnostic event retention; charge matching and coordinate maintenance and compare an order-matched control.',
        second_target='Share repeated source restriction and template validation, with explicit rollback, support deletion and component-binding conditions. Automatic origin recognition and fresh unlabelled evaluation remain open.',
        scope='Provisioned chronological origin banks and exposed edits, not a uniform algorithm for cheap arbitrary SAT expansion.')
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,summary=a['summary'],targets=a['targets'],times=a['times'],
        observer_counts=a['observer_counts'],solve_observation_change=a['times']['observed_solve_seconds']/a['times']['native_solve_seconds']-1,
        limitations=v['limitations']+a['limitations']))
    cp['source_fingerprints']=sources;cp['guard_probe_census'].update(decision=old.binding(out/'decision.json'),next_target=old.binding(out/'next-target.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=938,final_sources=len(sources),
        prior_artifacts=14809,prior_manifests=162,full_tests=1722,focused_tests=78,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=14809+len(files),
        next_manifests=163,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
