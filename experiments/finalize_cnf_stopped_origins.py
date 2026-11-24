#!/usr/bin/env python3
"""Seal the unfinished-origin census, negative controls and resumable history."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_stopped_origins as study
base=study.base


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==72 and v['comparison_trials']==24
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(160,14522)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_stopped_origins.py':base.sha(__file__)}
    assert len(sources)==933
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='5c2217b9179d4ee307d5be2ac81baaa006c87715'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    blocks=re.findall(pattern,old,re.S)
    assert len(blocks)==64 and blocks==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1708 tests in .*\n\nOK',full)
    assert re.search(r'Ran 64 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',text)) for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    census=base.load(out/'census.json');origins=[study.bound(e) for e in census['origins']]
    assert [r['origin'] for r in origins]==list(study.ORIGINS)
    assert sum(r['template_count'] for r in origins)==395
    assert sum(r['template_count'] for r in origins if r['status']=='unresolved')==342
    assert sum(r['endpoint_kinds'].get('unretained',0) for r in origins)==3
    assert all(r['open_plan_templates']==1 for r in origins)
    for r in origins:
        assert len(study.bound(r['materialized']))==r['template_count']
    summary=base.load(out/'analysis.json')['summary'];comparisons={};pairs=[]
    for target,arms in summary.items():
        assert all(a['status']=='unresolved' and a['expanded']==256 for a in arms.values())
        a,b=arms['open'],arms['plan']
        comparisons[target]={k:b[k]/a[k]-1 for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes')}
        for repeat in range(4):
            x=base.load(out/f'comparison-{target}-open-{repeat}/report.json')
            y=base.load(out/f'comparison-{target}-plan-{repeat}/report.json')
            change=y['solve_seconds']/x['solve_seconds']-1
            assert change>0
            pairs.append(dict(target=int(target),repeat=repeat,solve_change=change,
                worker_change=y['complete_seconds']/x['complete_seconds']-1))
    decision=dict(status='experimental; no default change',
        result='342 checked conditional templates from seven unfinished origins, plus 53 from the completed control; every template survives its paired edit.',
        limitation='Both diagnostic targets remain unresolved and the supported tree regresses against its identical all-open control. No broader whole-input coverage or speed benefit.',
        next_target='Measure guard subsumption, overlap and shared prefixes, then test a bounded shared representation or checked conditional exclusions that avoid the first-compatible tree order.',
        second_target='Share source restriction and unit-extraction prefixes; retain independent support checks and causal origin binding.',
        total_cost='Source capture, extraction, construction, prefix storage and conditional publication are additional to cold reuse workers.',
        incremental_audit='Earlier full-history and 342 partition audits remain hash-bound; new cumulative nodes and dependencies are replayed by both readers and all old payloads remain unchanged.')
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,comparisons=comparisons,pairs=pairs,
        origins=v['origin_audits'],summary=summary,limitations=v['limitations']+base.load(out/'comparison-protocol.json')['limitations']))
    cp['source_fingerprints']=sources
    cp['stopped_origins'].update(decision=study.binding(out/'decision.json'),next_target=study.binding(out/'next-target.json'))
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=926,final_sources=len(sources),
        prior_artifacts=14522,prior_manifests=160,full_tests=1708,focused_tests=64,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=14522+len(files),
        next_manifests=161,pages=pages,warnings=warnings,tables=v['preserved_tables'],comparisons=comparisons)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
