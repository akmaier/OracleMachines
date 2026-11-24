#!/usr/bin/env python3
"""Audit parent-plus-delta publication against the preserved full snapshot."""
from copy import deepcopy
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_history_layers as study
base=study.base;old=study.old;layers=study.layers


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent_checkpoint'])
    assert old.binding(study.PARENT/'manifest.json')==p['parent_manifest']
    pv=base.load(study.PARENT/'validation.json');assert pv['passed']
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(169,16266)
    failed=out/'failed-clean-ledger';failed_protocol=base.load(failed/'protocol.json')
    for f in study.FILES:assert base.sha(failed/Path(f).name)==failed_protocol['source_fingerprints'][f]
    assert 'Unclean accounting state' in (failed/'comparison.log').read_text()
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert p['target_archive']==parent['reference_union']
    assert p['base_archive']==old.bound(p['base_checkpoint'])['reference_union']
    c=base.load(out/'comparisons.json');assert c['protocol']==old.binding(out/'protocol.json')
    groups={'full':[],'layer':[]};audit=[]
    for entry in c['samples']:
        r=old.bound(entry);assert r['protocol']==c['protocol']
        groups[r['mode']].append(r)
    assert all({r['repeat'] for r in g}=={0,1} and len(g)==2 for g in groups.values())
    reference=groups['full'][0]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);target=temp/'target';before=temp/'before'
        layers.restore_archive(p['target_archive'],target);layers.restore_archive(p['base_archive'],before)
        prep=layers.prepare_append(p['base_archive'],before,target,p['target_archive']['database_sha256'])
        assert prep['added_rows']=={t:(173 if t==layers.TABLES[0] else 0) for t in layers.TABLES}
        for mode,rows in groups.items():
            for r in rows:
                for key in ('added_rows','added_ids','preserved_rows'):assert r[key]==prep[key]
                for key in ('counts','readers'):assert r[key]==reference[key]
                restored=temp/'restored';layers.restore_archive(r['archive'],restored)
                assert study.equal_tables(restored,target)==r['counts']==pv['preserved_tables']
                original=base.sha(restored)
                if mode=='full':assert original==p['target_archive']['database_sha256'] and r['byte_identical_to_target']
                assert original==r['archive']['database_sha256']
                # All four physical archives and tables are checked; one fresh
                # dependency replay per policy supplements every timed replay.
                checked=study.replay(restored,prep['added_ids']) if r['repeat']==0 else None
                if checked is not None:assert checked==r['readers']
                assert base.sha(restored)==original
                audit.append(dict(mode=mode,repeat=r['repeat'],archive=r['archive'],readers=checked))
                restored.unlink()
            assert rows[0]['archive']['database_sha256']==rows[1]['archive']['database_sha256']
    fields=('publication_complete_seconds','cold_restore_seconds','logical_equality_seconds',
            'new_dependency_replay_seconds','complete_worker_seconds','peak_rss_bytes',
            'new_retained_bytes','required_compressed_bytes')
    means={m:{k:sum(r[k] for r in rows)/len(rows) for k in fields} for m,rows in groups.items()}
    phases={m:{k:sum(r['statistics'][k] for r in rows)/len(rows) for k in rows[0]['statistics']} for m,rows in groups.items()}
    changes={k:means['layer'][k]/means['full'][k]-1 for k in fields}
    pairs=[dict(repeat=i,publication_change=groups['layer'][i]['publication_complete_seconds']/groups['full'][i]['publication_complete_seconds']-1,
                worker_change=groups['layer'][i]['complete_worker_seconds']/groups['full'][i]['complete_worker_seconds']-1) for i in range(2)]
    base.write(out/'analysis.json',dict(means=means,phases=phases,relative_changes=changes,pairs=pairs,
        input_preparation=base.load(out/'input-preparation.json'),limitations=p['limitations']))
    sources={**p['source_fingerprints'],'experiments/validate_cnf_history_layers.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent_checkpoint'],reference_union=groups['layer'][0]['archive'],
        reference_union_reader='experiments.cnf_history_layers.restore_archive',full_snapshot_control=p['target_archive'],
        source_fingerprints=sources,history_layers={k:old.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis')})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,preserved_tables=reference['counts'],added_records_this_run=0,
        publication_delta_records=prep['added_rows'],failed_trial_preserved=True,archive_audits=audit,checkpoint=old.binding(out/'checkpoint.json'),
        seconds=time.perf_counter()-began,limitations=p['limitations']))
    print(base.encode(dict(passed=True,prior_manifests=len(manifests),prior_artifacts=artifacts,
        changes=changes,phases=phases,counts=reference['counts'])),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
