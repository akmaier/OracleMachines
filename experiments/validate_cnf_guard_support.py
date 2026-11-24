#!/usr/bin/env python3
"""Check support-subset composition and preserve prior native authorities."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,shutil,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_support as study
from experiments import validate_cnf_guard_closure as prior
from experiments.cnf_archive_parts import restore_archive,split_archive
base=study.base;old=study.old;TABLES=prior.TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    parent_validation=base.load(study.PARENT/'validation.json')
    parent_audits=parent_validation['reused_prior_audits']+parent_validation['fresh_archive_audits']
    assert parent_validation['passed'] and len(parent_audits)==32
    assert old.binding(study.PARENT/'manifest.json')==p['parent_manifest']
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(parent_validation['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(168,16078)
    parent_protocol=base.load(study.PARENT/'protocol.json')
    for field in ('cases','inputs','targets','node_limit','handoff_bytes'):assert p[field]==parent_protocol[field]
    old_comparisons=base.load(study.PARENT/'comparisons.json');old_groups={};known={}
    audited={(r['target'],r['mode']) for r in parent_audits}
    for sample in old_comparisons['samples']:
        if sample['repeat']!=0:continue
        r=old.bound(sample);v=old.bound(r['result']);key=(r['target'],r['mode'])
        assert key in audited
        old_groups[key]=(r,v)
        identity=(r['target'],r['archive']['sha256'],r['archive']['database_sha256'])
        known[identity]=(r,v,dict(report=dict(path=sample['path'],sha256=sample['sha256']),
                                validation=old.binding(study.PARENT/'validation.json')))
    cases=old.bound(p['cases']);comparison=base.load(out/'comparisons.json')
    assert comparison['protocol']==old.binding(out/'protocol.json') and len(comparison['samples'])==48
    groups={};trials=[]
    for sample in comparison['samples']:
        r=old.bound(sample);v=old.bound(r['result']);key=(r['target'],r['mode'])
        assert r['protocol']==old.binding(out/'protocol.json') and key==(sample['target'],sample['mode'])
        assert r['origin']==r['target']-1 and base.sha(r['archive']['path'])==r['archive']['sha256']
        if key not in groups:groups[key]=[];trials.append((key,r,v))
        else:
            first,first_v=groups[key][0]
            for field in ('digest','added','native_checked_bytes'):assert r[field]==first[field],(key,field)
            for field in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert r['archive'][field]==first['archive'][field]
            for field in ('status','metrics'):assert v['result'][field]==first_v['result'][field]
            for field in ('guard','certificate','closure'):assert v[field]==first_v[field]
        groups[key].append((r,v))
    assert set(groups)=={(t,m) for t in p['targets'] for m in study.MODES}
    assert all(len(g)==2 for g in groups.values())
    for target,mode in groups:
        assert {s['repeat'] for s in comparison['samples'] if (s['target'],s['mode'])==(target,mode)}=={0,1}
    equivalent={}
    for target in p['targets']:
        for mode,old_mode in (('ordinary','ordinary'),('witness','witness')):
            r,v=groups[(target,mode)][0];pr,pv=old_groups[(target,old_mode)]
            assert r['digest']==pr['digest'] and r['archive']['database_sha256']==pr['archive']['database_sha256']
            for field in ('status','metrics'):assert v['result'][field]==pv['result'][field]
            for field in ('guard','certificate','closure'):assert v[field]==pv[field]
        baseline,bv=groups[(target,'witness')][0];support,sv=groups[(target,'support')][0]
        equivalent[str(target)]=dict(payloads_identical=support['digest']==baseline['digest'],
            database_identical=support['archive']['database_sha256']==baseline['archive']['database_sha256'],
            native_metrics_identical=sv['result']['metrics']==bv['result']['metrics'],
            checked_bytes_identical=support['native_checked_bytes']==baseline['native_checked_bytes'])
        for mode in ('witness','support'):
            r,v=groups[(target,mode)][0];c=v['closure']['counts']
            assert v['guard']['mode']=='tracking' and v['guard']['pending_end']==0
            assert v['closure']['mode']=='binary'
            for field,limit in (('candidate_checks','closure_checks'),('reserved_support_literals','closure_literals'),('reserved_edges','closure_edges')):
                assert c.get(field,0)<=p[limit]
            if mode in ('witness','support'):
                assert c.get('tentative_graph_checks',0)<=p['graph_checks']
                assert c.get('verified_core_hints',0)==sum(c.get('accepted_width_'+str(w),0) for w in (0,1,2))
    for target in p['targets']:
        c=groups[(target,'support')][0][1]['closure']['counts']
        assert c.get('support_selected_literals',0)<=c.get('support_source_literals',0)
        assert c.get('support_selected_clauses',0)<=c.get('support_source_clauses',0)
        assert c.get('support_wrappers',0)==c.get('support_root_hits',0)+c.get('support_root_publications',0)
        assert c.get('support_wrappers',0)+c.get('support_full_context_fallbacks',0)==sum(n for k,n in c.items() if k.startswith('closed_') and k!='closed_empty')
    profiles=base.load(out/'profiles.json');pp=old.bound(profiles['protocol'])
    assert pp['comparisons']==old.binding(out/'comparisons.json') and len(profiles['samples'])==3
    assert Path(pp['source']['path']).resolve()==Path('experiments/profile_cnf_guard_support.py').resolve()
    assert base.sha(pp['source']['path'])==pp['source']['sha256']
    relative={t:sum(r['solve_seconds'] for r,v in groups[(t,'support')])/sum(r['solve_seconds'] for r,v in groups[(t,'ordinary')])-1 for t in p['targets']}
    assert pp['relative_changes']=={str(t):v for t,v in relative.items()}
    assert pp['target']==max(p['targets'],key=lambda t:(relative[t],-t))
    assert {s['mode'] for s in profiles['samples']}=={'ordinary','witness','support'}
    for sample in profiles['samples']:
        r=old.bound(sample['report']);v=old.bound(r['result']);reference,rv=groups[(r['target'],r['mode'])][0]
        assert r['target']==pp['target'] and r['mode']==sample['mode']
        assert r['digest']==reference['digest'] and r['archive']['database_sha256']==reference['archive']['database_sha256']
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        for field in ('status','metrics'):assert v['result'][field]==rv['result'][field]
        for field in ('guard','certificate','closure'):assert v[field]==rv[field]
        old.bound(sample['profile']);assert base.sha(sample['raw']['path'])==sample['raw']['sha256']
    added={t:[] for t in TABLES};alternatives=Counter();reused=[];fresh=[];readers={}
    archive=parent['reference_union'];tables=parent_validation['preserved_tables']
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union';con=None
        for key,r,v in trials:
            result=v['result'];assert result['metrics'].get('expanded_nodes',0)<=p['node_limit']
            if result['status']=='unresolved':assert result['result'] is None and result['metrics']['expanded_nodes']==p['node_limit']
            identity=(key[0],r['archive']['sha256'],r['archive']['database_sha256'])
            inherited=known.get(identity)
            # Reuse only an exact previously audited byte stream on the same
            # case with the same verdict. No new successful claim is inferred.
            if inherited is not None and result['status']==inherited[1]['result']['status']:
                pr,pv,authority=inherited
                if result['result'] is None:
                    assert pv['result']['result'] is None
                else:
                    for field in ('answer','root','model'):assert result['result'][field]==pv['result']['result'][field]
                assert r['digest']==pr['digest']
                reused.append(dict(target=key[0],mode=key[1],authority=authority,
                                   archive=old.binding(Path(r['archive']['path']))))
                continue
            path=temp/'trial';restore_archive(r['archive'],path)
            stored,checked=prior.audit(path,[cases[key[0]]],[result])
            assert r['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            if con is None:
                restore_archive(parent['reference_union'],original);shutil.copyfile(original,union);con=sqlite3.connect(union)
            with con:
                for table,rows in stored.items():
                    for root,payload in rows.items():
                        old_row=con.execute(f'SELECT payload FROM {table} WHERE id=?',(root,)).fetchone()
                        if old_row is None:
                            con.execute(f'INSERT INTO {table}(id,payload) VALUES (?,?)',(root,payload));added[table].append(root)
                        else:
                            assert json.loads(old_row[0]).get('answer')==json.loads(payload).get('answer')
                            alternatives[table]+=old_row[0]!=payload
            fresh.append(dict(target=key[0],mode=key[1],readers=checked));path.unlink()
            print('new archive audited',key,flush=True)
        if con is not None:
            con.execute('ATTACH DATABASE ? AS prior',(str(original),))
            for t in TABLES:assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
            tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close()
            for cls in (prior.SnapshotResidualSolver,prior.CanonicalVerifySnapshot):
                s=cls(union);affine=prior.TerminalStore(s);equiv=prior.MultiEquivalenceStore(s);cache=prior.BinaryCoreCache(s)
                try:
                    for key in added[TABLES[0]]:assert s._read(key) is not None
                    for key in added[TABLES[1]]:assert affine.read(key) is not None
                    for t in TABLES[2:5]:
                        for key in added[t]:assert equiv.read(key) is not None
                    for key in added[TABLES[-1]]:
                        payload=s.db.execute(f'SELECT payload FROM {TABLES[-1]} WHERE id=?',(key,)).fetchone()[0];cache.verify(key,payload)
                    readers[cls.__name__]=dict(s.counts)
                finally:s.close()
            assert base.sha(original)==parent['reference_union']['database_sha256']
            if any(added.values()):
                (out/'union').mkdir();single=base.archive(union,out/'union');archive=split_archive(single,out/'union-parts')
                restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union);Path(single['path']).unlink()
            else:assert base.sha(union)==base.sha(original)
    assert len(reused)+len(fresh)==24
    summary={};pairs=[];aggregates={m:dict(statuses=Counter(),costs=Counter(),closure_counts=Counter()) for m in study.MODES}
    for (target,mode),values in groups.items():
        r,v=values[0]
        row=dict(status=v['result']['status'],expanded=v['result']['metrics']['expanded_nodes'],added=r['added'],
            guard=v['guard'],certificate=v['certificate'],closure=v['closure'],payload_bytes=r['payload_bytes'],
            native_checked_bytes=r['native_checked_bytes'],database_bytes=r['archive']['database_bytes'],
            compressed_bytes=r['archive']['compressed_bytes'],
            **{'mean_'+k:sum(a[k] for a,b in values)/len(values) for k in
               ('restore_seconds','setup_seconds','solve_seconds','warm_seconds','cold_seconds','complete_seconds','peak_rss_bytes')})
        summary.setdefault(str(target),{})[mode]=row;aggregates[mode]['statuses'][row['status']]+=1
        if v['closure'] is not None:aggregates[mode]['closure_counts'].update(v['closure']['counts'])
        aggregates[mode]['costs']['payload_bytes']+=sum(r['payload_bytes'].values())
        for k in ('inserted_bytes','inserted_nodes','expanded_nodes'):aggregates[mode]['costs'][k]+=v['result']['metrics'].get(k,0)
        aggregates[mode]['costs'].update({k:v for k,v in row.items() if k.startswith('mean_') or k in ('database_bytes','compressed_bytes','native_checked_bytes')})
    for target in p['targets']:
        for baseline in ('ordinary','witness'):
            for repeat,((a,_),(b,_)) in enumerate(zip(groups[(target,baseline)],groups[(target,'support')])):
                pairs.append(dict(target=target,baseline=baseline,repeat=repeat,solve_change=b['solve_seconds']/a['solve_seconds']-1,
                                  worker_change=b['complete_seconds']/a['complete_seconds']-1))
    base.write(out/'analysis.json',dict(summary=summary,aggregates=aggregates,pairs=pairs,support_comparison=equivalent,
        profiles=profiles,limitations=p['limitations']))
    sources={**p['source_fingerprints'],'experiments/validate_cnf_guard_support.py':base.sha(__file__),
        'experiments/profile_cnf_guard_support.py':base.sha('experiments/profile_cnf_guard_support.py')}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_support=dict(protocol=old.binding(out/'protocol.json'),comparisons=old.binding(out/'comparisons.json'),
            analysis=old.binding(out/'analysis.json'),profiles=old.binding(out/'profiles.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,targets_checked=8,comparison_trials=48,audited_target_arm_archives=24,
        distinct_trial_database_hashes=len({r['archive']['database_sha256'] for _,r,_ in trials}),
        reused_prior_audits=reused,fresh_archive_audits=fresh,new_records={t:len(v) for t,v in added.items()},
        preserved_tables=tables,alternative_payload_observations=dict(alternatives),readers=readers,
        checkpoint=old.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,
        limitations=[
            'Exact compressed and database hashes, same-case verdicts, six-table digests and the preceding manifest-bound two-reader audit justify reused archive audits. Novel archives are replayed with both readers. Worker cold native replay still runs on every trial. These are distinct validation operations.',
            'All old artifact hashes and frozen sources remain checked. Existing cumulative authority is reused unchanged unless novel checked rows require an append-only merge; prior full-history and partition audits remain hash-bound.',
            'Same payloads/counters do not prove identical ordered execution traces. Exposed edits, provisioned banks, counter-only allowances and the lack of a new Lean refinement proof remain explicit.']))
    print(base.encode(dict(passed=True,new_records={t:len(v) for t,v in added.items()},reused_audits=len(reused),fresh_audits=len(fresh),
        tables=tables,support_comparison=equivalent,aggregates=aggregates)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
