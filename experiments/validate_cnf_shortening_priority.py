#!/usr/bin/env python3
"""Check exact root ordering, every positive program, native archives and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_priority as study
base=study.base;old=study.old;previous=study.previous


def diagnose(out):
    p=base.load(out/'protocol.json');losses=[];started=time.perf_counter()
    for target in p['targets']:
        source,templates,refs,events=study.prior.inputs(p,target)
        def events_for(mode):
            r=base.load(out/f'census-{target}-{mode}-0/report.json')
            return {e['event']:e for e in old.bound(r['events'])['rows']}
        control=events_for('cached64');candidate=events_for('priority64')
        for event,row in candidate.items():
            if row['program']['status']=='refuted' or control[event]['program']['status']!='refuted':continue
            local,hints,_=previous.local_hints(source,templates,events[event],Counter());ts=[h['template'] for h in hints]
            c=Counter();fixed={};states=[];program=row['program'];frozen=study.candidate.frozen
            for round_id in range(len(program['steps'])+1):
                state=frozen._state(local,ts,fixed,c);model,proof=study.native.two_cnf(state['graph'],c);assert proof is None
                roots=study.candidate.priority_roots(state['local'],model,c);outgoing={};incoming={};parents={}
                def find(v):
                    parents.setdefault(v,v)
                    while parents[v]!=v:parents[v]=parents[parents[v]];v=parents[v]
                    return v
                for cl in state['graph']:
                    a,b=cl[0],cl[-1]
                    for u,v in {(-a,b),(-b,a)}:
                        outgoing.setdefault(u,set()).add(v);incoming.setdefault(v,set()).add(u);parents[find(u)]=find(v)
                empty_out={r for r in roots if not outgoing.get(r)};empty_in={r for r in roots if not incoming.get(-r)}
                disconnected={r for r in roots if find(r)!=find(-r)};excluded=empty_out|empty_in|disconnected
                states.append(dict(round=round_id,eligible=len(roots),empty_outgoing=len(empty_out),empty_target_incoming=len(empty_in),
                    different_weak_component=len(disconnected),excluded_union=len(excluded),excluded_first64=len(set(roots[:64])&excluded)))
                if round_id<len(program['steps']):
                    step=program['steps'][round_id]
                    frozen._bind_path(step['path'],step['forced'],state,local,ts,fixed,set(),c,program['path_limit'])
                    fixed[abs(step['forced'])]=step['forced']>0
            losses.append(dict(target=target,event=event,reason=program['reason'],candidate_steps=len(program['steps']),
                control_steps=len(control[event]['program']['steps']),states=states))
    base.write(out/'diagnostics.json',dict(losses=losses,seconds=time.perf_counter()-started,
        limitations='Endpoint/weak-component exclusions are sufficient no-path conditions, measured after the fact on eligible candidates. These counts overlap, include cache hits and do not equal avoided fresh BFS. No filter was added to the measured policy.'))


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(176,20356)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_shortening_priority.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    rows={m:{} for m in study.MODES};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss={m:0 for m in study.MODES}
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==64
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];target=sample['target'];es=old.bound(r['events'])['rows']
        assert r['mode']==mode and r['target']==target
        for event in es:
            c=event['counts'];assert c.get('reach_roots',0)<=(128 if mode=='expanded128' else 64)
            assert c.get('rounds',0)<=33 and sum(c.get(k,0) for k in ('reach_edge_visits','reuse_invalidation_checks'))<=16384
            assert c.get('cache_peak_vertices',0)<=16384
            if mode=='priority_plain64':assert c.get('cache_stores',0)==0 and c.get('negative_reuses',0)==0
            if sample['repeat']==0:rows[mode][(target,event['event'])]=event
        groups.setdefault((target,mode),[]).append(es)
        totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','binding_seconds','complete_seconds')})
        counts[mode].update({k:v/2 for k,v in r['counts'].items()});rss[mode]=max(rss[mode],r['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(r['root'],r['program'],r['counts']) for r in pair[0]]==[(r['root'],r['program'],r['counts']) for r in pair[1]]
    for mode in study.MODES:assert len(rows[mode])==615 and rows[mode].keys()==rows['cached64'].keys()
    checks=Counter()
    for target in p['targets']:
        source,templates,refs,events=study.prior.inputs(p,target)
        for mode in ('cached64','expanded128'):
            r=base.load(study.PARENT/f'census-{target}-{mode}-0/report.json')
            for e in old.bound(r['events'])['rows']:
                now=rows[mode][(target,e['event'])];assert now['program']==e['program'] and now['counts']==e['counts']
        for ref in refs:
            key=(target,ref['event']);positive=[m for m in study.MODES if rows[m][key]['program']['status']=='refuted']
            if not positive:continue
            local,hints,_=previous.local_hints(source,templates,events[ref['event']],Counter())
            for mode in positive:
                study.candidate.validate(local,[h['template'] for h in hints],rows[mode][key]['program'],Counter());checks[mode]+=1
    success={m:{k for k,r in rs.items() if r['program']['status']=='refuted'} for m,rs in rows.items()}
    coverage={m:dict(outcomes=dict(Counter('refuted' if r['program']['status']=='refuted' else r['program']['reason'] for r in rs.values())),
        roots=len({rs[k]['root'] for k in success[m]}),gained_events=sorted(success[m]-success['cached64']),lost_events=sorted(success['cached64']-success[m])) for m,rs in rows.items()}
    oldroots={rows['cached64'][k]['root'] for k in success['cached64']|success['expanded128']}
    newroots={rows['cached64'][k]['root'] for k in success['priority64']|success['priority_plain64']}-oldroots
    new_roots_by_mode={m:sorted({rows[m][k]['root'] for k in success[m]}-oldroots) for m in ('priority64','priority_plain64')}
    case_data=base.load(out/'cases.json');cases=[old.bound(b) for b in case_data['cases']]
    assert {c['root'] for c in cases}==newroots and len(cases)==len(newroots)
    for case in cases:study.candidate.validate(case['source'],case['templates'],case['program'],Counter())
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4
    tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);index=sample['index'];mode=sample['mode'];assert r['case']==case_data['cases'][index] and r['mode']==mode
        if mode=='support':assert r['result']['status']=='unsat'
        if r['result']['status']=='unsat':assert r['result']['result']['root']==cases[index]['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],cases[index]['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);assert base.sha(path)==a['database_sha256']
                stored,readers=previous.audit(path,[dict(source=cases[index]['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=cases[index]['root'],readers=readers);archives.append(a)
        tg.setdefault((index,mode),[]).append(r)
    trial_totals={m:Counter() for m in ('fresh','support')};trial_rss={m:0 for m in trial_totals};summary=[]
    for index,case in enumerate(cases):
        row=dict(name=case['name'],present_after_query=case['present_after_query'],arms={})
        for mode in trial_totals:
            a,b=tg[(index,mode)]
            for key in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[key]==b[key],(index,mode,key)
            assert a['result']['status']==b['result']['status']
            met={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            met['records']=sum(a['authority_tables'].values());trial_totals[mode].update(met)
            trial_rss[mode]=max(trial_rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=dict(status=a['result']['status'],**met)
        summary.append(row)
    edits=base.load(out/'edits.json');assert len(edits['cases'])==48 and len(edits['rows'])==384
    eg={};edit_totals={m:Counter() for m in study.MODES};edit_success={m:set() for m in study.MODES}
    for r in edits['rows']:
        case=edits['cases'][r['index']];mode=r['mode'];eg.setdefault((r['index'],mode),[]).append(r)
        if r['program']['status']=='refuted':
            study.candidate.validate(case['source'],case['templates'],r['program'],Counter());edit_success[mode].add(r['index'])
        edit_totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','verification_seconds')})
    for pair in eg.values():
        a,b=pair;assert a['program']==b['program'] and a['counts']==b['counts']
    edit_coverage={m:dict(refuted=len(s),gained=sorted(s-edit_success['cached64']),lost=sorted(edit_success['cached64']-s)) for m,s in edit_success.items()}
    analysis=dict(coverage=coverage,census_totals=totals,census_counts=counts,census_max_rss_bytes=rss,positive_program_checks=checks,
        new_roots=len(cases),new_roots_by_mode=new_roots_by_mode,
        not_previously_saved=sum(not c['present_after_query'] for c in cases),trial_totals=trial_totals,trial_max_rss_bytes=trial_rss,
        trial_statuses={m:dict(Counter(r['arms'][m]['status'] for r in summary)) for m in trial_totals},summary=summary,
        edit_coverage=edit_coverage,edit_totals=edit_totals,unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        shortening_priority={**{k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','comparisons','edits','analysis','diagnostics')},'supplemental_archives':archives})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(passed=True,coverage=coverage,totals=totals,trial_totals=trial_totals,edit_coverage=edit_coverage,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','eef7de6f:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1844 tests in .*\n\nOK',full) and re.search(r'Ran 29 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shortening_priority']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1844,focused_tests=29,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1021,final_sources=len(cp['source_fingerprints']),prior_manifests=176,prior_artifacts=20356,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=177,next_artifacts=20356+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
