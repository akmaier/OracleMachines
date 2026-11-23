#!/usr/bin/env python3
"""Seal bounded joint consequence evidence after independent replay and tests."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_consequence_priority as study
from experiments.cnf_binary_backbone import check_path
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==90
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(137,11721)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_consequence_priority.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==771
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='38ebc440'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1478 tests in .*\n\nOK',full) and re.search(r'Ran 186 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['consequence_priority']['partitions'],cp['consequence_priority']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    for entry in target['profiles']+target['observations']:
        trial=study.bound(entry['trial']);assert entry['output_matches_trial']
        if 'extra_ids' in entry:
            delta=study.read_zip(trial['delta'])
            for table,ids in entry['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
        for event in entry.get('acquisitions',[]):
            delta=study.read_zip(trial['delta'])
            cnf,_=study.normalize(event['source']);assert study.token(cnf,Counter())==event['root']
            for table,ids in event['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
        for event in entry.get('events',[]):
            cnf=tuple(map(tuple,event['source']))
            assert study.normalize(cnf)[0]==cnf and study.token(cnf,Counter())==event['root']
            assert 1<=len(event['evidence'])<=2
            for evidence in event['evidence']:check_path(cnf,evidence,Counter())
    for match in target['identical_delta_streams']:
        for repeat in range(2):
            entries=[base.load(out/f"{match['split']}-{match['case']}-{mode}-{repeat}/report.json") for mode in (match['baseline'],'priority')]
            assert study.read_zip(entries[0]['delta'])==study.read_zip(entries[1]['delta'])
    for split in ('branch-original','branch-flip','branch-complement'):
        for repeat in range(2):
            entries=[base.load(out/f'{split}-31-{mode}-{repeat}/report.json') for mode in ('joint','priority')]
            assert study.read_zip(entries[0]['delta'])==study.read_zip(entries[1]['delta'])
    assert v['previous_partition_records']==282
    cp['source_fingerprints']=sources;cp['consequence_priority']['next_target']=study.binding(out/'next-target.json')
    cp['consequence_priority']['decision']='Keep priority optional: six new edits improve 4.54% query time and 3.91% native payload versus joint, and 3.34% time versus one-target; controls remain 0.80% slower than one-target. Exposed joint branches preserve proof bytes, and case61 recovers baseline proof bytes. The largest new replacement takes fewer expansions yet more time than joint. Next inspect repeated source-bound preparation and causal support in its saved six-expansion branch, acquisition index 4 with 242 remaining budget and 42 earlier native IDs.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=763,final_sources=771,prior_artifacts=11721,prior_manifests=137,
        full_tests=1478,focused_tests=186,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint preserves previous record payloads; alternative valid proofs remain in trial and exploratory deltas. Both native readers recheck the cumulative union. Older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=11721+len(files),next_manifests=138,final_sources=771,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
