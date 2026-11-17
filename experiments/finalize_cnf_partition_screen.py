#!/usr/bin/env python3
"""Merge control discoveries append-only and check all preserved authorities."""
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as study
from experiments.validate_cnf_partition_screen import check_composed
from experiments.validate_cnf_unsat_support import bound
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_incremental_support import check_proposals
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def run(out):
    tick=time.perf_counter();parent=study.PARENT;v=base.load(parent/'validation.json');manifests=dict(v['parent_manifests']);path=str(parent/'manifest.json');manifests[path]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']));count=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        artifacts=base.load(path)['artifacts'];assert len(artifacts)==entry['artifacts_checked']
        for f,h in artifacts.items():assert base.sha(f)==h,f
        count+=len(artifacts)
    for f,h in v['source_fingerprints'].items():assert base.sha(f)==h,f
    assert (len(v['source_fingerprints']),count,len(manifests))==(435,4762,83)
    base.write(out/'parent-manifests.json',manifests);base.write(out/'preservation.json',dict(prior_sources_unchanged=435,prior_artifacts_unchanged=count,prior_manifests_unchanged=len(manifests),seconds=time.perf_counter()-tick))
    p=base.load(out/'protocol.json');fresh=base.load(out/'checkpoint.json');controls=base.load(out/'historical-controls.json');original=bound(p['parent']);bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.previous.ordinary.compose(indices,bindings);used=[(n,bound(original[n])) for n in study.OLD_FIELDS];records=[];alternates=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'union';base.restore_archive(fresh['reference_union'],path);s=study.ResidualSolver(path)
        try:
            before=study.rows(s);union=dict(before)
            for entry in controls['samples']:
                data=bound(entry);records+=bound(data['records'])
                for k,val in bound(data['delta']):
                    if k in union and union[k]!=val:assert base.load_json(union[k])['answer']==base.load_json(val)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),delta=data['delta']))
                    union.setdefault(k,val)
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,val) for k,val in union.items() if k not in before])
            assert study.rows(s)==union and before.items()<=union.items();s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Final replay search')),patch.object(s,'_store',side_effect=AssertionError('Final replay publication')):
                for r in records:check_composed(s,r)
        finally:s.close()
        composed=study.inherited(original)+bound(fresh['partition_screen_decisions'])+records;cold=study.audit_records(path,composed,prepared,used,indices)
        base.write(out/'historical-decisions.json',records);dest=out/'control-union';dest.mkdir();archive=base.archive(path,dest)
        final=copy.deepcopy(fresh);final.update(parent_checkpoint=study.binding(out/'checkpoint.json'),reference_union=archive,partition_screen_controls=study.binding(out/'historical-controls.json'),partition_screen_control_decisions=study.binding(out/'historical-decisions.json'));base.write(out/'expanded-checkpoint.json',final)
        # Ordinary catalogs retain their own schema; composed sidecars are separate.
        frontiers={};s=SnapshotResidualSolver(path)
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Frontier search')),patch.object(s,'_store',side_effect=AssertionError('Frontier publication')):
                for name in ('active_support_proposals','extended_support_proposals','causal_support_proposals','incremental_causal_proposals'):
                    bank=bound(final[name]);names={o['catalog'] for o in bank['origins']};catalogs=[(f,bound(final[f])) for f in study.FIELDS if f in names];assert set(n for n,_ in catalogs)==names
                    lineage=check_proposals(s,bank,catalogs);ready=0
                    for core in bank['cores']:
                        cnf,_,key=s._canonical(core['source']);node=s._read(key,cnf)
                        if node is not None:assert node['answer'] is False;ready+=1
                    frontiers[name]=dict(binding=final[name],catalogs=len(catalogs),lineage=lineage,retained=len(bank['cores']),ready=ready,pending=len(bank['cores'])-ready)
        finally:s.close()
        _,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'expanded-checkpoint.json',tmp/'patterns');assert structural==old_structural;supplemental=check_supplement(out/'expanded-checkpoint.json')
    changed=[k for k in original if final[k]!=original[k]];added=sorted(set(final)-set(original));assert set(changed)=={'parent_checkpoint','reference_union','source_fingerprints'};assert added==['partition_screen_control_decisions','partition_screen_controls','partition_screen_decisions','partition_screen_study']
    result=dict(passed=True,checkpoint=study.binding(out/'expanded-checkpoint.json'),fresh_checkpoint=study.binding(out/'checkpoint.json'),fresh_keys=len(before),union_keys=len(union),control_new_keys=len(union)-len(before),retained_composed=len(composed),control_records=len(records),alternate_certificates=alternates,cold=cold,frontiers=frontiers,structural=structural,supplemental=supplemental,changed_checkpoint_fields=changed,added_checkpoint_fields=added,seconds=time.perf_counter()-tick)
    base.write(out/'frontier-check.json',result);print(base.encode({k:result[k] for k in ('passed','fresh_keys','union_keys','control_new_keys','retained_composed','control_records','seconds')}),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
