#!/usr/bin/env python3
"""Seal the bounded-target study after tests, replay and manuscript checks."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cofactor_handoff as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==90
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(132,10493)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_cofactor_handoff.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==733
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='c15ca83a'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1428 tests in .*\n\nOK',full) and re.search(r'Ran 136 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['cofactor_handoff']['partitions'],cp['cofactor_handoff']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json')
    assert target['script_sha256']==base.sha(diagnostic)
    memory=target['memory_audit'];assert memory['checks']>0
    assert memory['max_actual_bytes']<=memory['max_charged_bytes']<=p['handoff_bytes']
    builds=target['partition_preparation_audit']
    for position in {r['query_position'] for r in builds}:
        rows=[r for r in builds if r['query_position']==position]
        assert len(rows)==4 and {r['branches'] for r in rows}=={6}
        assert len({r['input_sha256'] for r in rows})==len({r['result_sha256'] for r in rows})==1
    assert len(builds)==8
    for entry in target['records'].values():
        study.bound(entry['trial']);assert entry['output_matches_frozen_trial']
    cp['source_fingerprints']=sources;cp['cofactor_handoff']['next_target']=study.binding(out/'next-target.json')
    cp['cofactor_handoff']['decision']='Keep optional: direct handoff lowers new-edit query time 2.66% with both orders improving, identical proof payloads and unchanged expansions. Complete worker time changes +0.15% with mixed signs. Next share the identical six-branch partition structure built four times per selected query, preserving independent source/child checks. Probe admission and continuation costs remain open.'
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=726,final_sources=733,prior_artifacts=10493,prior_manifests=132,
        full_tests=1428,focused_tests=136,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint inherits all previous record payloads and preserves alternative proofs in trial deltas. Both native readers recheck the cumulative union; older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=10493+len(files),next_manifests=133,final_sources=733,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
