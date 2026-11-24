#!/usr/bin/env python3
"""Audit live guard selection, paired controls and append-only proof history."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,shutil,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_probes as study
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
    assert old.bound(p['parent_manifest'])==base.load(study.PARENT/'manifest.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json';manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(163,14882)
    cases=old.bound(p['cases']);report=base.load(out/'comparisons.json')
    assert report['protocol']==old.binding(out/'protocol.json') and len(report['samples'])==128
    groups={};trials=[]
    for sample in report['samples']:
        r=old.bound(sample);v=old.bound(r['result']);key=(sample['target'],sample['mode'])
        assert r['protocol']==old.binding(out/'protocol.json')
        assert (r['target'],r['mode'])==key and r['origin']==r['target']-1
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        if key not in groups:groups[key]=[];trials.append((key,r,v))
        else:
            a,b=groups[key][0]
            for k in ('digest','added','native_checked_bytes'):assert r[k]==a[k],(key,k)
            for k in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert r['archive'][k]==a['archive'][k]
            for k in ('status','metrics'):assert v['result'][k]==b['result'][k]
            assert v['guard']==b['guard']
        groups[key].append((r,v))
    assert set(groups)=={(t,m) for t in p['targets'] for m in study.MODES} and all(len(g)==4 for g in groups.values())
    for target,mode in groups:
        assert {s['repeat'] for s in report['samples'] if (s['target'],s['mode'])==(target,mode)}==set(range(4))
    for target in p['targets']:
        ordinary,observed=groups[(target,'native')][0],groups[(target,'tracking')][0]
        assert ordinary[0]['digest']==observed[0]['digest']
        assert ordinary[0]['archive']['database_sha256']==observed[0]['archive']['database_sha256']
        for k in ('status','metrics'):assert ordinary[1]['result'][k]==observed[1]['result'][k]
        prior=base.load(study.PARENT/f'target-{target}/report.json');prior_result=old.bound(prior['results'])['native']
        assert ordinary[0]['digest']==prior['native_digest']
        for k in ('status','metrics'):assert ordinary[1]['result'][k]==prior_result[k]
        origin=base.load(study.ORIGINS/f'origin-{target-1}/report.json');templates=old.bound(origin['extraction'])['templates']
        source,names=old.native.normalize(cases[target]['source']);before,before_names=old.native.normalize(cases[target-1]['source'])
        assert names==before_names and all(check_template(t)<=set(before) for t in templates)
        eligible=sum(check_template(t)<=set(source) for t in templates)
        for mode in study.MODES[1:]:
            guard=groups[(target,mode)][0][1]['guard']
            assert guard['mode']==mode and guard['eligible']==eligible and guard['pending_end']==0
            assert guard['counts'].get('guard_checks',0)<=p['guard_checks']
            assert guard['counts'].get('pending_peak_slots',0)<=p['tracking_slots']
            assert guard['limits']=={k:p[k] for k in ('guard_checks','tracking_slots','tracking_pending')}
    profiles=base.load(out/'profiles.json');pp=old.bound(profiles['protocol'])
    assert pp['comparisons']==old.binding(out/'comparisons.json') and pp['parent_protocol']==old.binding(out/'protocol.json')
    assert Path(pp['source']['path']).resolve()==Path('experiments/profile_cnf_guard_selection.py').resolve()
    assert pp['source']['sha256']==base.sha('experiments/profile_cnf_guard_selection.py')
    relative={t:sum(r['solve_seconds'] for r,v in groups[(t,'guided')])/sum(r['solve_seconds'] for r,v in groups[(t,'native')])-1 for t in p['targets']}
    assert pp['target']==max(p['targets'],key=lambda t:(relative[t],-t))
    assert pp['relative_changes']=={str(k):v for k,v in relative.items()}
    assert [sample['mode'] for sample in profiles['samples']]==['native','guided']
    for sample in profiles['samples']:
        r=old.bound(sample['report']);v=old.bound(r['result']);reference,rv=groups[(pp['target'],sample['mode'])][0]
        assert r['digest']==reference['digest'] and r['archive']['database_sha256']==reference['archive']['database_sha256']
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        for k in ('status','metrics'):assert v['result'][k]==rv['result'][k]
        assert v['guard']==rv['guard'];old.bound(sample['profile'])
        assert base.sha(sample['raw']['path'])==sample['raw']['sha256']
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
            audits.append(dict(target=key[0],mode=key[1],readers=checked));path.unlink();print('audited',key,flush=True)
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:
            assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close()
        readers={}
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
        (out/'union').mkdir();single=base.archive(union,out/'union');archive=split_archive(single,out/'union-parts')
        restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union)
        Path(single['path']).unlink()
    summary={};pairs=[];aggregates={m:dict(statuses=Counter(),costs=Counter(),guard_counts=Counter()) for m in study.MODES}
    for (target,mode),values in groups.items():
        r,v=values[0];guard=v['guard'];counts={} if guard is None else guard['counts']
        row=dict(status=v['result']['status'],expanded=v['result']['metrics']['expanded_nodes'],
            added=r['added'],guard=guard,native_checked_bytes=r['native_checked_bytes'],
            database_bytes=r['archive']['database_bytes'],compressed_bytes=r['archive']['compressed_bytes'],
            **{'mean_'+k:sum(a[k] for a,b in values)/4 for k in ('restore_seconds','setup_seconds','solve_seconds','warm_seconds','cold_seconds','complete_seconds','peak_rss_bytes')})
        summary.setdefault(str(target),{})[mode]=row
        aggregates[mode]['statuses'][row['status']]+=1;aggregates[mode]['guard_counts'].update(counts)
        aggregates[mode]['costs'].update({k:v for k,v in row.items() if k.startswith('mean_') or k in ('database_bytes','compressed_bytes','native_checked_bytes')})
    for target in p['targets']:
        for mode in study.MODES[1:]:
            for repeat,((a,_),(b,_)) in enumerate(zip(groups[(target,'native')],groups[(target,mode)])):
                pairs.append(dict(target=target,mode=mode,repeat=repeat,
                    solve_change=b['solve_seconds']/a['solve_seconds']-1,worker_change=b['complete_seconds']/a['complete_seconds']-1))
    base.write(out/'analysis.json',dict(summary=summary,aggregates=aggregates,pairs=pairs,profiles=profiles,limitations=p['limitations']))
    sources={**p['source_fingerprints'],'experiments/validate_cnf_guard_selection.py':base.sha(__file__),
        'experiments/profile_cnf_guard_selection.py':base.sha('experiments/profile_cnf_guard_selection.py')}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_probe_selection=dict(protocol=old.binding(out/'protocol.json'),comparisons=old.binding(out/'comparisons.json'),analysis=old.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,targets_checked=8,comparison_trials=128,distinct_trial_archives=32,
        audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=tables,alternative_payload_observations=dict(alternatives),
        readers=readers,checkpoint=old.binding(out/'checkpoint.json'),archive_roundtrip_byte_identical=True,seconds=time.perf_counter()-began,
        limitations=[
            'Incremental cumulative audit: every old six-table payload is byte-identical; new nodes and dependencies replay through both readers. Earlier complete-history and 342-partition checks remain hash-bound, not rerun.',
            'Both readers fully check one database per target/arm. Four repetitions have identical six-table payloads, native counters, guard counters and binary archive hashes. All raw trials remain preserved.',
            'Exact local native proof checks establish every published result independently of hint correctness. Coordinate hints are tested by unchanged-order controls, renamings, small exhaustive truth cases and native proof replay, not a Lean refinement proof.',
            'All inputs are exposed and banks provisioned. Changed probe order can change search paths; a bounded local gain is not uniformly cheaper arbitrary SAT expansion.']))
    print(base.encode(dict(passed=True,tables=tables,new_records={t:len(v) for t,v in added.items()},aggregates=aggregates)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
