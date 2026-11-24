#!/usr/bin/env python3
"""Replay selective live closures and retain all prior six-table authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, shutil, sqlite3, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_closure as study
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_archive_parts import restore_archive,split_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
base=study.base;old=study.old;TABLES=old.previous.ALL_TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    assert old.binding(study.PARENT/'manifest.json')==p['parent_manifest']
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(166,15614)
    cases=old.bound(p['cases']);report=base.load(out/'comparisons.json')
    assert report['protocol']==old.binding(out/'protocol.json') and len(report['samples'])==64
    groups={};trials=[]
    for sample in report['samples']:
        r=old.bound(sample);v=old.bound(r['result']);key=(sample['target'],sample['mode'])
        assert r['protocol']==old.binding(out/'protocol.json')
        assert (r['target'],r['mode'])==key and r['origin']==r['target']-1
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        if key not in groups:groups[key]=[];trials.append((key,r,v))
        else:
            first,first_v=groups[key][0]
            for k in ('digest','added','native_checked_bytes'):assert r[k]==first[k],(key,k)
            for k in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert r['archive'][k]==first['archive'][k]
            for k in ('status','metrics'):assert v['result'][k]==first_v['result'][k]
            for k in ('guard','certificate','closure'):assert v[k]==first_v[k]
        groups[key].append((r,v))
    assert set(groups)=={(t,m) for t in p['targets'] for m in study.MODES}
    assert all(len(g)==2 for g in groups.values())
    for target,mode in groups:
        assert {s['repeat'] for s in report['samples'] if (s['target'],s['mode'])==(target,mode)}=={0,1}
    for target in p['targets']:
        # Previously exposed controls must retain their exact semantics and work.
        prior=base.load(f'experiments/results/cnf-guard-probe-census/target-{target}/report.json')
        ordinary,ov=groups[(target,'ordinary')][0]
        assert ordinary['archive']['database_sha256']==prior['archives']['native']['database_sha256']
        prior_result=old.bound(prior['results'])['native']
        for k in ('status','metrics'):assert ov['result'][k]==prior_result[k]
        prior_cert=base.load(f'experiments/results/cnf-guard-certificate-reuse/target-{target}-certificate-0/report.json')
        cert,cv=groups[(target,'certificate')][0];oldcv=old.bound(prior_cert['result'])
        assert cert['digest']==prior_cert['digest']
        for k in ('status','metrics'):assert cv['result'][k]==oldcv['result'][k]
        assert cv['guard']==oldcv['guard'] and cv['certificate']==oldcv['certificate']
        origin=old.bound(p['inputs'][p['targets'].index(target)])
        templates=old.bound(origin['extraction'])['templates']
        source,names=old.native.normalize(cases[target]['source'])
        before,before_names=old.native.normalize(cases[target-1]['source'])
        assert names==before_names and all(check_template(t)<=set(before) for t in templates)
        eligible=sum(check_template(t)<=set(source) for t in templates)
        for mode in ('units','binary'):
            r,v=groups[(target,mode)][0]
            assert v['guard']['mode']=='tracking' and v['guard']['eligible']==eligible and v['guard']['pending_end']==0
            closure=v['closure'];c=closure['counts'];assert closure['mode']==mode
            for field,limit in (('candidate_checks','closure_checks'),('reserved_support_literals','closure_literals'),('reserved_edges','closure_edges')):
                assert c.get(field,0)<=p[limit]
            if mode=='units':assert not c.get('accepted_width_2',0) and not c.get('closed_binary_guards',0)
    profiles=base.load(out/'profiles.json');profile_protocol=old.bound(profiles['protocol'])
    assert profile_protocol['comparisons']==old.binding(out/'comparisons.json')
    profile_source=profile_protocol['source']
    assert Path(profile_source['path']).resolve()==Path('experiments/profile_cnf_guard_closure.py').resolve()
    assert base.sha(profile_source['path'])==profile_source['sha256']
    assert len(profiles['samples'])==2
    relative={t:sum(r['solve_seconds'] for r,v in groups[(t,'binary')])/sum(r['solve_seconds'] for r,v in groups[(t,'ordinary')])-1 for t in p['targets']}
    assert profile_protocol['relative_changes']=={str(t):v for t,v in relative.items()}
    assert profile_protocol['target']==max(p['targets'],key=lambda t:(relative[t],-t))
    for sample in profiles['samples']:
        r=old.bound(sample['report']);v=old.bound(r['result']);reference,rv=groups[(r['target'],r['mode'])][0]
        assert r['target']==profile_protocol['target'] and r['mode'] in ('ordinary','binary')
        assert r['digest']==reference['digest'] and r['archive']['database_sha256']==reference['archive']['database_sha256']
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        for k in ('status','metrics'):assert v['result'][k]==rv['result'][k]
        for k in ('guard','certificate','closure'):assert v[k]==rv[k]
        old.bound(sample['profile']);assert base.sha(sample['raw']['path'])==sample['raw']['sha256']
    added={t:[] for t in TABLES};alternatives=Counter();audits=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union'
        restore_archive(parent['reference_union'],original);shutil.copyfile(original,union);con=sqlite3.connect(union)
        for key,r,v in trials:
            path=temp/'trial';restore_archive(r['archive'],path)
            stored,checked=audit(path,[cases[key[0]]],[v['result']])
            assert r['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            result=v['result'];assert result['metrics'].get('expanded_nodes',0)<=256
            if result['status']=='unresolved':assert result['result'] is None and result['metrics']['expanded_nodes']==256
            with con:
                for table,rows in stored.items():
                    for root,payload in rows.items():
                        prior=con.execute(f'SELECT payload FROM {table} WHERE id=?',(root,)).fetchone()
                        if prior is None:
                            con.execute(f'INSERT INTO {table}(id,payload) VALUES (?,?)',(root,payload));added[table].append(root)
                        else:
                            assert json.loads(prior[0]).get('answer')==json.loads(payload).get('answer')
                            alternatives[table]+=prior[0]!=payload
            audits.append(dict(target=key[0],mode=key[1],readers=checked));path.unlink()
            print('audited',key,flush=True)
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:
            assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close();readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(union);affine=TerminalStore(s);equiv=MultiEquivalenceStore(s);cache=BinaryCoreCache(s)
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
            restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union)
            Path(single['path']).unlink()
        else:
            assert base.sha(union)==base.sha(original);archive=parent['reference_union']
    summary={};pairs=[]
    aggregates={m:dict(statuses=Counter(),costs=Counter(),closure_counts=Counter()) for m in study.MODES}
    for (target,mode),values in groups.items():
        r,v=values[0]
        row=dict(status=v['result']['status'],expanded=v['result']['metrics']['expanded_nodes'],
            added=r['added'],guard=v['guard'],certificate=v['certificate'],closure=v['closure'],
            payload_bytes=r['payload_bytes'],native_checked_bytes=r['native_checked_bytes'],
            database_bytes=r['archive']['database_bytes'],compressed_bytes=r['archive']['compressed_bytes'],
            **{'mean_'+k:sum(a[k] for a,b in values)/len(values) for k in
               ('restore_seconds','setup_seconds','solve_seconds','warm_seconds','cold_seconds','complete_seconds','peak_rss_bytes')})
        summary.setdefault(str(target),{})[mode]=row
        aggregates[mode]['statuses'][row['status']]+=1
        if v['closure'] is not None:aggregates[mode]['closure_counts'].update(v['closure']['counts'])
        aggregates[mode]['costs']['payload_bytes']+=sum(r['payload_bytes'].values())
        for k in ('inserted_bytes','inserted_nodes','expanded_nodes'):
            aggregates[mode]['costs'][k]+=v['result']['metrics'].get(k,0)
        aggregates[mode]['costs'].update({k:v for k,v in row.items() if k.startswith('mean_') or k in ('database_bytes','compressed_bytes','native_checked_bytes')})
    for target in p['targets']:
        for mode in study.MODES[1:]:
            for repeat,((a,_),(b,_)) in enumerate(zip(groups[(target,'ordinary')],groups[(target,mode)])):
                pairs.append(dict(target=target,mode=mode,repeat=repeat,
                    solve_change=b['solve_seconds']/a['solve_seconds']-1,worker_change=b['complete_seconds']/a['complete_seconds']-1))
    base.write(out/'analysis.json',dict(summary=summary,aggregates=aggregates,pairs=pairs,profiles=profiles,limitations=p['limitations']))
    sources={**p['source_fingerprints'],'experiments/validate_cnf_guard_closure.py':base.sha(__file__),
        'experiments/profile_cnf_guard_closure.py':base.sha('experiments/profile_cnf_guard_closure.py')}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_closure=dict(protocol=old.binding(out/'protocol.json'),comparisons=old.binding(out/'comparisons.json'),
            analysis=old.binding(out/'analysis.json'),profiles=old.binding(out/'profiles.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,targets_checked=8,comparison_trials=64,distinct_trial_archives=32,
        audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=tables,
        alternative_payload_observations=dict(alternatives),readers=readers,checkpoint=old.binding(out/'checkpoint.json'),
        archive_roundtrip_byte_identical=True,seconds=time.perf_counter()-began,limitations=[
            'Both readers fully check one database per target/arm. The two repetitions have identical six-table payloads, counters and binary archive hashes within each arm. The frozen ordinary/certificate controls retain their prior payloads.',
            'Every admitted guard is RUP-checked locally; both implication paths publish source-bound native unit/split evidence. The adapter has truth-table, transport, invalidation, exhausted-limit and live-routing tests, without a new Lean refinement proof.',
            'Incremental cumulative audit: every old payload is byte-identical, new nodes/dependencies replay through both readers, and previous full-history/342-partition checks remain hash-bound rather than rerun.',
            'Exposed inputs and provisioned banks remain limitations. No total work/memory cap or polynomial arbitrary-SAT expansion bound follows from native dispatch or gate allowances.']))
    print(base.encode(dict(passed=True,tables=tables,new_records={t:len(v) for t,v in added.items()},aggregates=aggregates)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
