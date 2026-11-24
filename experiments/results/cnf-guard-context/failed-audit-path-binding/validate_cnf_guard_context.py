#!/usr/bin/env python3
"""Check shared source preparation without replacing earlier proof authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_context as study
base=study.base;old=study.old
DIFFERENT={'normalization_literal_visits','position_clauses','context_preparations','context_hint_checks',
           'context_literal_slots','context_peak_clause_slots','context_peak_literal_slots'}


def semantic(value):
    result=deepcopy(value);result['result'].pop('solve_seconds',None);return result


def same_except_context(a,b):
    assert set(a)==set(b)
    for k in a:
        if k!='counts':assert a[k]==b[k],k
    assert {k:v for k,v in a['counts'].items() if k not in DIFFERENT}=={k:v for k,v in b['counts'].items() if k not in DIFFERENT}
    assert b['counts'].get('context_hint_checks',0)==b['counts'].get('verified_core_hints',0)
    assert b['counts'].get('context_preparations',0)<=b['counts'].get('witness_support_checks',0)


def validate(out):
    started=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    assert p['parent_manifest']==old.binding(study.PARENT/'manifest.json')
    pv=base.load(study.PARENT/'validation.json');assert pv['passed']
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(170,16313)
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    control=old.bound(p['control_checkpoint']);cv=base.load(study.CONTROL/'validation.json');assert cv['passed']
    pp=base.load(study.CONTROL/'protocol.json')
    for field in ('cases','origins','targets','inputs','node_limit','handoff_bytes','closure_checks','closure_literals','closure_edges','path_limit','witness_retries','graph_checks'):assert p[field]==pp[field],field
    known={}
    for sample in base.load(study.CONTROL/'comparisons.json')['samples']:
        if sample['repeat']==0 and sample['mode'] in ('ordinary','support'):
            r=old.bound(sample);known[(r['target'],r['mode'])]=(r,old.bound(r['result']),sample)
    audited={(r['target'],r['mode']) for r in cv['reused_prior_audits']+cv['fresh_archive_audits']}
    assert set(known)<=audited
    comparison=base.load(out/'comparisons.json');assert comparison['protocol']==old.binding(out/'protocol.json')
    groups={};reused=[]
    for sample in comparison['samples']:
        r=old.bound(sample);v=old.bound(r['result']);key=(r['target'],r['mode'])
        assert r['protocol']==comparison['protocol'] and key==(sample['target'],sample['mode'])
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        old_mode='support' if r['mode']=='context' else r['mode'];pr,pvr,authority=known[(r['target'],old_mode)]
        for f in ('digest','added','payload_bytes','native_checked_bytes'):assert r[f]==pr[f],(key,f)
        for f in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert r['archive'][f]==pr['archive'][f],(key,f)
        assert semantic(v)['result']==semantic(pvr)['result'] and v['guard']==pvr['guard'] and v['certificate']==pvr['certificate'],key
        if r['mode']=='context':same_except_context(pvr['closure'],v['closure'])
        else:assert v['closure']==pvr['closure'],key
        if key not in groups:
            reused.append(dict(target=key[0],mode=key[1],authority=authority,
                               validation=old.binding(study.CONTROL/'validation.json'),archive=old.binding(Path(r['archive']['path']))))
        else:
            a,b,_=groups[key][0]
            assert semantic(v)==semantic(b) and r['archive']['database_sha256']==a['archive']['database_sha256']
        groups.setdefault(key,[]).append((r,v,sample['repeat']))
    assert len(comparison['samples'])==48 and set(groups)=={(t,m) for t in p['targets'] for m in study.MODES}
    assert all(len(g)==2 and {repeat for _,_,repeat in g}=={0,1} for g in groups.values())
    profiles=base.load(out/'profiles.json');prof_protocol=old.bound(profiles['protocol'])
    assert prof_protocol['comparisons']==old.binding(out/'comparisons.json')
    assert prof_protocol['source']==old.binding(Path('experiments/profile_cnf_guard_context.py'))
    relative={t:sum(r['solve_seconds'] for r,_,_ in groups[(t,'context')])/sum(r['solve_seconds'] for r,_,_ in groups[(t,'ordinary')])-1 for t in p['targets']}
    assert prof_protocol['relative_changes']=={str(t):v for t,v in relative.items()}
    assert prof_protocol['target']==max(p['targets'],key=lambda t:(relative[t],-t))
    assert {r['mode'] for r in profiles['samples']}==set(study.MODES)
    for entry in profiles['samples']:
        r=old.bound(entry['report']);v=old.bound(r['result']);ref,vr,_=groups[(r['target'],r['mode'])][0]
        assert r['target']==prof_protocol['target'] and semantic(v)==semantic(vr) and r['digest']==ref['digest']
        assert r['archive']['database_sha256']==ref['archive']['database_sha256']
        assert base.sha(r['archive']['path'])==r['archive']['sha256']==ref['archive']['sha256']
        old.bound(entry['profile']);assert base.sha(entry['raw']['path'])==entry['raw']['sha256']
    summary={};pairs=[];aggregates={m:dict(statuses=Counter(),costs=Counter(),closure_counts=Counter()) for m in study.MODES}
    for (target,mode),values in groups.items():
        r,v,_=values[0]
        row=dict(status=v['result']['status'],closure=v['closure'],database_bytes=r['archive']['database_bytes'],
                 native_checked_bytes=r['native_checked_bytes'],compressed_bytes=r['archive']['compressed_bytes'],
                 **{'mean_'+k:sum(a[k] for a,_,_ in values)/2 for k in
                    ('restore_seconds','setup_seconds','solve_seconds','warm_seconds','cold_seconds','complete_seconds','peak_rss_bytes')})
        summary.setdefault(str(target),{})[mode]=row;ag=aggregates[mode];ag['statuses'][row['status']]+=1
        if v['closure']:ag['closure_counts'].update(v['closure']['counts'])
        ag['costs'].update({k:n for k,n in row.items() if k.startswith('mean_') or k in ('database_bytes','native_checked_bytes','compressed_bytes')})
        assert v['result']['status']=='unresolved' and v['result']['result'] is None and v['result']['metrics']['expanded_nodes']==p['node_limit']
    for target in p['targets']:
        for baseline in ('ordinary','support'):
            for (a,_,repeat),(b,_,repeat2) in zip(groups[(target,baseline)],groups[(target,'context')]):
                assert repeat==repeat2
                pairs.append(dict(target=target,baseline=baseline,repeat=repeat,solve_change=b['solve_seconds']/a['solve_seconds']-1,
                                  worker_change=b['complete_seconds']/a['complete_seconds']-1))
    base.write(out/'analysis.json',dict(summary=summary,aggregates=aggregates,pairs=pairs,profiles=profiles,limitations=p['limitations']))
    from experiments.cnf_guard_wide_gap import evidence
    gap=base.load(out/'wide-clause-gap.json')
    assert gap['source_implementation']['sha256']==base.sha('experiments/cnf_guard_wide_gap.py')
    assert gap['evidence']==evidence()
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in ('experiments/validate_cnf_guard_context.py','experiments/profile_cnf_guard_context.py','experiments/cnf_guard_wide_gap.py')}}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        guard_context={k:old.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','profiles','wide-clause-gap')})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,targets_checked=8,comparison_trials=48,reused_prior_audits=reused,fresh_archive_audits=[],
        preserved_tables=pv['preserved_tables'],new_records={t:0 for t in pv['preserved_tables']},
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],checkpoint=old.binding(out/'checkpoint.json'),
        seconds=time.perf_counter()-started,limitations=p['limitations']+[
            'Same-case identical compressed/raw archive hashes, table digests and verdicts reuse prior manifest-bound two-reader audits for all 24 target/arm archives. Every current trial and profile separately performs cold native replay. No novel rows are merged or new cumulative archive published.',
            'The full prior cumulative bank and layered reader are preserved unchanged. No claim is made to re-prove all historical records in this audit.']))
    print(base.encode(dict(passed=True,targets=8,reused_audits=24,aggregates=aggregates)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
