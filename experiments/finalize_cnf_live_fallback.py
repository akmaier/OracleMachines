#!/usr/bin/env python3
"""Seal the synchronous-fallback study after tests, replay and manuscript checks."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_live_fallback as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==48
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(135,11279)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_live_fallback.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==755
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='9e54e491'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1456 tests in .*\n\nOK',full) and re.search(r'Ran 164 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['live_fallback']['partitions'],cp['live_fallback']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    for entry in target['profiles']+target['captures']:
        study.bound(entry['trial']);assert entry['output_matches_trial']
    for capture in target['captures']:
        for event in capture['events']:
            assert event['query_root_absent'] and not event['pending_records'] and not event['in_transaction']
        trial=study.bound(capture['trial']);delta=study.read_zip(trial['delta'])
        for acquisition in capture['acquisitions']:
            assert acquisition['target_absent']
            for table,ids in acquisition['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
    matched=0
    for split in ('controls','novel'):
        for index in (25,31,61):
            for repeat in range(2):
                arms=[base.load(out/f'{split}-{index}-{mode}-{repeat}/report.json') for mode in study.MODES]
                assert study.read_zip(arms[0]['delta'])==study.read_zip(arms[1]['delta'])
                assert study.bound(arms[0]['partitions'])==study.bound(arms[1]['partitions'])
                matched+=1
    assert matched==12
    cp['source_fingerprints']=sources;cp['live_fallback']['next_target']=study.binding(out/'next-target.json')
    cp['live_fallback']['decision']='Keep live fallback optional. The boundary improves 17 to 11 expansions and 20.71% query time; six controls improve 2.58% but six fresh edits regress 3.89% with no resumption opportunity. All matched proof deltas and sidecars are identical. Next inspect joint forced binary consequences in the dominant saved partition branch, charging discovery and proof construction.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=748,final_sources=755,prior_artifacts=11279,prior_manifests=135,
        full_tests=1456,focused_tests=164,matched_identical_deltas=matched,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint inherits all previous record payloads and preserves alternative proofs in trial deltas. Both native readers recheck the cumulative union; older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=11279+len(files),next_manifests=136,final_sources=755,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
