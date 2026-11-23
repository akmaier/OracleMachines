#!/usr/bin/env python3
"""Seal the bounded-target study after tests, replay and manuscript checks."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_interactions as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==60
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(134,11043)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_binary_interactions.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==748
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='fbde83da'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1446 tests in .*\n\nOK',full) and re.search(r'Ran 154 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['binary_interactions']['partitions'],cp['binary_interactions']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    from experiments.cnf_binary_backbone import check_path
    for item in target['second_target_evidence']:
        check_path(tuple(map(tuple,item['source'])),item['evidence'],Counter())
    for entry in target['records'].values():
        study.bound(entry['trial']);assert entry['output_matches_frozen_trial']
    boundary=study.bound(target['probe_boundary'])
    for mode,entry in boundary['cases'].items():
        trial=study.bound(entry['trial']);queries=study.bound(trial['queries'])
        query=queries[1];direct=entry['direct_query']
        assert entry['root']==query['result']['root']==direct['result']['root']
        assert direct['result']['answer']==query['result']['answer']
        assert entry['wrapped_expansions']==query['expanded_nodes']
        assert entry['direct_expansions']==direct['metrics']['expanded_nodes']
        assert (entry['direct_expansions'],entry['wrapped_expansions'])==({'binary1':(11,17),'binary2':(8,8)}[mode])
        assert entry['all_payloads_in_frozen_trial']
        delta=study.read_zip(trial['delta'])
        for table,ids in entry['delta_ids'].items():assert set(ids)<=dict(delta[table]).keys()
    cp['source_fingerprints']=sources;cp['binary_interactions']['next_target']=study.binding(out/'next-target.json')
    cp['binary_interactions']['decision']='Keep second-target recognition optional: new-edit query time improves 8.29%, controls regress 1.14%, and exposed branches still take nine expansions. The main gain crosses the eight-expansion probe boundary: wrapped 17 to 8, direct 11 to 8. Investigate preserving unfinished acquisition continuations with no answer authority. Native checking is unchanged; alternative proofs and regressions are retained.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=740,final_sources=748,prior_artifacts=11043,prior_manifests=134,
        full_tests=1446,focused_tests=154,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+boundary['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint inherits all previous record payloads and preserves alternative proofs in trial deltas. Both native readers recheck the cumulative union; older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=11043+len(files),next_manifests=135,final_sources=748,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
