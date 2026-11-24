#!/usr/bin/env python3
"""Seal guard-prefix selection, controls and the next measured reuse gap."""
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_frontier as study
base=study.base;old=study.study


def finalize(out):
    v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['origins_checked']==8 and v['comparison_trials']==32
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(161,14672)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/finalize_cnf_guard_frontier.py':base.sha(__file__)}
    assert len(sources)==938
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='a2836da8fb4f1839d82947687b07575f5d9afea3'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1715 tests in .*\n\nOK',full)
    assert re.search(r'Ran 71 tests in .*\n\nOK',focused)
    warnings={k:text.count('ResourceWarning: unclosed database') for k,text in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    analysis=base.load(out/'analysis.json');summary=analysis['summary'];comparisons={};pairs=[]
    for target,arms in summary.items():
        assert all(a['status']=='unresolved' and a['expanded']==256 for a in arms.values())
        comparisons[target]={}
        for control in ('native','old','open'):
            a,b=arms[control],arms['frontier']
            comparisons[target][control]={k:b[k]/a[k]-1 for k in ('mean_solve_seconds','mean_complete_seconds','database_bytes')}
            for repeat in range(4):
                x=base.load(out/f'target-{target}-{control}-{repeat}/report.json')
                y=base.load(out/f'target-{target}-frontier-{repeat}/report.json')
                pairs.append(dict(target=int(target),control=control,repeat=repeat,
                    solve_change=y['solve_seconds']/x['solve_seconds']-1,worker_change=y['complete_seconds']/x['complete_seconds']-1))
    assert sum(r['guards']['templates'] for r in analysis['origins'])==395
    assert sum(r['guards']['dominated_guards'] for r in analysis['origins'])==10
    assert sum(r['guards']['complementary_pairs'] for r in analysis['origins'])==5
    decision=dict(status='experimental; no default change',
        result='Shared-prefix allocation covers more assignment mass within 129 nodes on all eight saved banks. Whole-input coverage remains unchanged on both cold targets.',
        limitation='Assignment mass is not an acquisition-cost model. The new route has mixed costs and the ordinary solver remains faster on both diagnostic edits.',
        next_target='Use checked conditional exclusions at ordinary search contexts, without imposing a separate tree. First audit the existing trace-learning and support-checking code; its binary implications do not already justify arbitrary multi-assumption clauses.',
        second_target='Share repeated source restriction and unit-extraction work while preserving causal source maps and clause-deletion invalidation.',
        evidence='Only 10 of 395 retained guards are subsumed within their origin, with five complementary pairs among inclusion-minimal guards. Full template banks and failed measurements remain preserved.',
        scope='The target pairs are provisioned and exposed. Fresh unlabelled evaluation and automatic origin recognition remain open; no unrestricted-SAT complexity claim.')
    base.write(out/'decision.json',decision)
    base.write(out/'next-target.json',dict(decision=decision,comparisons=comparisons,pairs=pairs,
        origins=analysis['origins'],leaf_costs=analysis['leaf_costs'],summary=summary,
        limitations=v['limitations']+base.load(out/'protocol.json')['limitations']))
    cp['source_fingerprints']=sources;cp['guard_frontier'].update(decision=old.binding(out/'decision.json'),next_target=old.binding(out/'next-target.json'))
    base.write(out/'checkpoint.json',cp);v.update(source_fingerprints=sources,checkpoint=old.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=933,final_sources=len(sources),
        prior_artifacts=14672,prior_manifests=161,full_tests=1715,focused_tests=71,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=old.binding(out/'checkpoint.json'),limitations=v['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,sources=len(sources),artifacts=len(files),next_artifacts=14672+len(files),
        next_manifests=162,pages=pages,warnings=warnings,tables=v['preserved_tables'],comparisons=comparisons)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
