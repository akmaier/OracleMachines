#!/usr/bin/env python3
"""Seal early pool scheduling and the measured template-construction target."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pool_priority as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==1254 and v['previous_partition_records']==342 and v['partition_records']==0
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(142,12606)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==810
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='3adf30ba'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1528 tests in .*\n\nOK',full) and re.search(r'Ran 236 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))};assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],*([x for x in cp['pool_priority'].values() if isinstance(x,dict) and 'sha256' in x])):assert base.sha(b['path'])==b['sha256']
    profile=base.load(out/'profile.json');assert profile['proofs_and_routes_unchanged']
    assert profile['script_sha256']==base.sha('experiments/profile_cnf_pool_priority.py')
    analysis=base.load(out/'analysis.json');work=analysis['work']['pools-native']
    assert work['templates_checked']==173 and work['pool_priority_negative_pool_hits']==8 and work['pool_priority_witness_pool_hits']==4
    assert work['pool_priority_misses']==19
    for name in ('pools-native-0','pools-native-1','profile-pools-native'):
        a=base.load(out/'compact-0/report.json');b=base.load(out/name/'report.json')
        assert study.read_zip(a['delta'])==study.read_zip(b['delta'])
    cp['source_fingerprints']=sources;base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=804,final_sources=810,prior_artifacts=12606,prior_manifests=142,
        full_tests=1528,focused_tests=236,warnings=warnings,warning_sites=dict(sites),manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+profile['limitations']+v['limitations']+base.load(out/'analysis.json')['limitations']+[
            'Earlier pool hits preserve identical compact proof bytes. Local timing changes do not establish an end-to-end improvement. Recovery still regresses; repeated template preparation is the next target.',
            'Full-suite unclosed SQLite warnings are retained; collection sites need not be allocation sites. Focused tests close their own databases. No new Lean refinement theorem.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=12606+len(files),next_manifests=143,final_sources=810,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
