#!/usr/bin/env python3
"""Seal the bounded-target study after tests, replay and manuscript checks."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_preparation as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==96
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(133,10783)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_partition_preparation.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==740
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='47a30c6c'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1438 tests in .*\n\nOK',full) and re.search(r'Ran 146 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['partition_preparation']['partitions'],cp['partition_preparation']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    audits=target['preparation_audit'];seen=0
    for r in audits['binary-prepared']:
        if r['kind']=='prepared':
            assert r['retained_graph_bytes']<=r['conservative_charge'];seen+=1
    assert seen>0
    for position in {r['query_position'] for r in audits['binary1']}:
        left=[r for r in audits['binary1'] if r['query_position']==position]
        right=[r for r in audits['binary-prepared'] if r['query_position']==position]
        assert len(left)==4 and len(right)==2
        assert len({r['input_sha256'] for r in left+right})==len({r['result_sha256'] for r in left+right})==1
    for entry in target['records'].values():
        study.bound(entry['trial']);assert entry['output_matches_frozen_trial']
    branch=target['branch_candidate'];assert branch['target_absent'] and branch['extra_count']==len(branch['extra_ids'])
    study.bound(branch['trial_report']);cnf,_=study.normalize(branch['source']);assert study.token(cnf,Counter())==branch['root']
    cp['source_fingerprints']=sources;cp['partition_preparation']['next_target']=study.binding(out/'next-target.json')
    cp['partition_preparation']['decision']='Keep optional: shared partition preparation lowers new-edit query time 6.15% under binary-frequency routing and 4.01% with cofactor handoff, preserving exact proof bytes. Full worker means regress 1.07% and 0.23%. Next inspect the saved 125-variable binary/ternary branch requiring nine expansions from its exact pre-acquisition seed.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=733,final_sources=740,prior_artifacts=10783,prior_manifests=133,
        full_tests=1438,focused_tests=146,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint inherits all previous record payloads and preserves alternative proofs in trial deltas. Both native readers recheck the cumulative union; older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=10783+len(files),next_manifests=134,final_sources=740,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
