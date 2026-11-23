#!/usr/bin/env python3
"""Seal exact joint-prefix reuse after native replay, testing and manuscript build."""
from collections import Counter
from pathlib import Path
import json,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_prefix as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==60
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(139,12236)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_joint_prefix.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==788
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='f76931d5'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1496 tests in .*\n\nOK',full) and re.search(r'Ran 204 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['joint_prefix']['partitions'],cp['joint_prefix']['analysis']):assert base.sha(b['path'])==b['sha256']
    target=base.load(out/'next-target.json');assert target['script_sha256']==base.sha(diagnostic)
    for entry in target['profiles']+target['observations']:
        trial=study.bound(entry['trial']);assert entry['output_matches_trial'];delta=study.read_zip(trial['delta'])
        if 'extra_ids' in entry:
            for table,ids in entry['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
        for event in entry.get('acquisitions',[]):
            cnf,_=study.normalize(event['source']);assert study.token(cnf,Counter())==event['root']
            for table,ids in event['extra_ids'].items():assert set(ids)<=dict(delta[table]).keys()
        if 'proof_census' in entry:
            census=entry['proof_census'];event=entry['acquisitions'][census['acquisition_index']]
            assert census['root']==event['root']
            initial=study.read_zip(event['prefix'])[study.TABLES[0]]
            records=dict(initial+delta[study.TABLES[0]])
            before={k for k,v in initial}|set(event['extra_ids'][study.TABLES[0]])
            rows={r['key']:r for r in census['nodes']};todo=[census['root']];seen=set()
            while todo:
                key=todo.pop()
                if key in seen:continue
                seen.add(key);r=rows[key];node=json.loads(records[key]);proof=node['proof']
                reasons={cid for _,cid in proof.get('trace',[])}
                if proof.get('conflict') is not None:reasons.add(proof['conflict'])
                assert r['kind']==proof['kind'] and r['available_before']==(key in before)
                assert r['children']==[proof[f] for f in ('child','low','high') if f in proof]
                assert r['reason_indices']==sorted(reasons)
                assert r['reason_literals']==sum(len(node['cnf'][i]) for i in reasons)
                assert r['reason_widths']=={str(k):v for k,v in Counter(len(node['cnf'][i]) for i in reasons).items()}
                assert r['literals']==sum(map(len,node['cnf'])) and r['clauses']==len(node['cnf'])
                assert r['trace_steps']==len(proof.get('trace',[]));todo.extend(r['children'])
            assert seen==rows.keys() and census['kinds']==dict(Counter(r['kind'] for r in rows.values()))
    assert v['previous_partition_records']==322
    cp['source_fingerprints']=sources;cp['joint_prefix']['next_target']=study.binding(out/'next-target.json')
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=780,final_sources=788,prior_artifacts=12236,prior_manifests=139,
        full_tests=1496,focused_tests=204,warnings=warnings,warning_sites=dict(sites),manuscript_pages=pages,
        paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'),
        limitations=p['limitations']+v['limitations']+target['limitations']+[
            'The saved normalizer result was already live; no new retained CNF or memory bound for arbitrary SAT is claimed. Native proof checking is unchanged.',
            'Two paired orders on nearby inputs do not establish statistical significance or external benchmark performance. Individual regressions remain preserved.',
            'The source census is untimed and reproduces prior proof bytes. Unfinished source frames remain work states, not stored-answer authority.',
            'Full-suite unclosed SQLite warning sites can be collection rather than allocation sites. No new Lean refinement theorem.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=12236+len(files),next_manifests=140,final_sources=788,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
