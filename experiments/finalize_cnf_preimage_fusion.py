#!/usr/bin/env python3
"""Seal fused causal-preimage evidence after independent replay and tests."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_preimage_fusion as study
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_preimage_fusion import fused_preimage
from experiments.profile_cnf_preimage_fusion import Canonicalizer
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==60
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(138,12026)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    diagnostic='experiments/profile_cnf_preimage_fusion.py'
    repeat_script='experiments/repeat_cnf_preimage_fusion.py'
    sources={**v['source_fingerprints'],diagnostic:base.sha(diagnostic),repeat_script:base.sha(repeat_script),__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)}
    assert len(sources)==780
    for f,h in sources.items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';head='694ddddb'
    before=subprocess.check_output(['git','show',head+':'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1488 tests in .*\n\nOK',full) and re.search(r'Ran 196 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    sites=Counter(re.sub(r'0x[0-9a-f]+','ADDR',line.lstrip('.')) for line in full.splitlines() if 'ResourceWarning: unclosed database' in line)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    for b in (cp['reference_union'],cp['preimage_fusion']['partitions'],cp['preimage_fusion']['analysis']):assert base.sha(b['path'])==b['sha256']
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
            cnf=tuple(map(tuple,event['source']));assert study.normalize(cnf)[0]==cnf
            args=(cnf,event['ids'],dict(event['assignment']),event['child'],event['selected'])
            old=CausalSupportExtractor(Canonicalizer(),materialize=False);new=CausalSupportExtractor(Canonicalizer(),materialize=False)
            assert old._preimage(*args)==fused_preimage(new,*args)==set(event['result'])
    repeat=base.load(out/'repeat-report.json');rp=study.bound(repeat['protocol'])
    assert rp['parent']==study.binding(out/'protocol.json') and rp['script_sha256']==base.sha(repeat_script)
    assert rp['groups']==['controls','novel','branch-original'] and rp['repeats']==6
    samples=repeat['samples'];assert len(samples)==36
    assert sum(len(s['streams']) for s in samples)==84
    assert sum(len(st['queries']) for s in samples for st in s['streams'])==156
    for group in rp['groups']:
        group_samples=[s for s in samples if s['group']==group]
        assert [(s['repeat'],s['mode']) for s in group_samples]==[(i,m) for i in range(6) for m in rp['orders'][i%2]]
        for s in group_samples:
            assert len(s['streams'])==(1 if study.native_split(group) else 3)
            for st in s['streams']:
                ref=out/f"{group}-{st['case']}-{s['mode']}-0/report.json"
                assert st['reference']==study.binding(ref) and st['output_matches_trial']
                expected=study.bound(base.load(ref)['queries']);assert len(expected)==len(st['queries'])
                for a,b in zip(st['queries'],expected):
                    for f in ('variant','expanded_nodes','status'):assert a[f]==b[f]
            assert s['query_seconds']==sum(q['seconds'] for st in s['streams'] for q in st['queries'])
            assert s['mode_setup_seconds']==sum(st['mode_setup_seconds'] for st in s['streams'])
            assert s['query_with_mode_setup_seconds']==s['query_seconds']+s['mode_setup_seconds']
        summary=repeat['summary'][group]
        for m in study.MODES:
            assert summary['means'][m]==sum(s['query_seconds'] for s in group_samples if s['mode']==m)/6
            assert summary['with_mode_setup_means'][m]==sum(s['query_with_mode_setup_seconds'] for s in group_samples if s['mode']==m)/6
        assert summary['percent_change']==100*(summary['means']['fused']/summary['means']['priority']-1)
    assert v['previous_partition_records']==306
    cp['source_fingerprints']=sources;cp['preimage_fusion']['next_target']=study.binding(out/'next-target.json')
    cp['preimage_fusion']['timing_repeats']=study.binding(out/'repeat-report.json')
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    checks=dict(passed=True,baseline_commit=head,prior_sources=771,final_sources=780,prior_artifacts=12026,prior_manifests=138,
        full_tests=1488,focused_tests=196,warnings=warnings,warning_sites=dict(sites),
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        timing_repeat_attempts=156,timing_repeats=study.binding(out/'repeat-report.json'),
        decision='Keep the serial optional fused constructor: nearby query means improve with identical proofs and storage. No full-worker speedup or broader coverage claim; investigate source-bound reuse in the remaining nine-expansion mixed branch.',
        limitations=p['limitations']+v['limitations']+target['limitations']+rp['limitations']+[
            'Full-suite unclosed SQLite warning sites can be collection sites, not allocation sites. Focused tests emit none.',
            'This checkpoint preserves previous record payloads. The exposed census and timing repeats reproduce prior or frozen trial proof bytes and add no distinct proof. Both native readers recheck the cumulative union. Older unrelated audits remain manifest-bound.',
            'No independent external SAT benchmark or machine-checked refinement theorem was added.'])
    base.write(out/'checks.json',checks)
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=12026+len(files),next_manifests=139,final_sources=780,pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
