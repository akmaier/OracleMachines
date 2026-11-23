#!/usr/bin/env python3
"""Seal bounded joint consequence evidence after independent replay and tests."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_backbone as study
from experiments.cnf_binary_backbone import check_path
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==90
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(136,11420)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_joint_backbone.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==763
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='75dcbeed'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1468 tests in .*\n\nOK',full) and re.search(r'Ran 176 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['joint_backbone']['partitions'],cp['joint_backbone']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    for entry in target['profiles']+target['observations']:
        trial=study.bound(entry['trial']);assert entry['output_matches_trial']
        if 'extra_ids' in entry:
            delta=study.read_zip(trial['delta'])
            for table,ids in entry['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
        for event in entry.get('events',[]):
            cnf=tuple(map(tuple,event['source']))
            assert study.normalize(cnf)[0]==cnf and study.token(cnf,Counter())==event['root']
            assert 1<=len(event['evidence'])<=2
            for evidence in event['evidence']:check_path(cnf,evidence,Counter())
    ablation=study.bound(target['ablation'])
    assert ablation['script_sha256']==base.sha(diagnostic)
    study.bound(ablation['query']);study.read_zip(ablation['delta'])
    assert v['previous_partition_records']==258
    cp['source_fingerprints']=sources;cp['joint_backbone']['next_target']=study.binding(out/'next-target.json')
    cp['joint_backbone']['decision']='Keep joint discovery optional. Exposed branch and sign variants improve 9 to 4 expansions; original query time falls 24.10% and native payload 24.86%. Same-discovery single-selected ablation takes six expansions. Six new edits regress 4.05% in query time and retain 8.65% more payload despite 58 to 55 expansions. Next compare useful versus harmful full-CNF continuations, preserving case 61 and its later-query reuse effect. No coverage or unrestricted bound is added.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=755,final_sources=763,prior_artifacts=11420,prior_manifests=136,
        full_tests=1468,focused_tests=176,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint preserves previous record payloads; alternative valid proofs remain in trial and exploratory deltas. Both native readers recheck the cumulative union. Older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=11420+len(files),next_manifests=137,final_sources=763,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
