#!/usr/bin/env python3
"""Post-timing recovery using a later checked model; preserve initial unknowns."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from collections import Counter
import copy,sqlite3,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_larger_mixtures as study
from experiments.cnf_checked_model_reuse import reuse_checked_model
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
base=study.base
FILES=('experiments/cnf_checked_model_reuse.py','experiments/resume_cnf_larger_mixtures.py','solver/test_cnf_checked_model_reuse.py')


def resume(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);rows=base.load(out/'batch32-0/queries.json')
    parent=base.load(out/'checkpoint.json');base.write(out/'pre-recovery-checkpoint.json',parent)
    trial=base.load(out/'batch32-0/report.json')['archive'];donor,target=75,76
    assert rows[donor]['status']==rows[target]['status']=='unresolved'
    assert cases[77]['root']==cases[donor]['root'] and rows[77]['status']=='sat'
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    with TemporaryDirectory() as td:
        path=Path(td)/'trial';base.restore_archive(trial,path);s=study.BatchedPublicationSolver(path,node_limit=0)
        try:
            before=study.prior.native_rows(s);assert cases[target]['root'] not in before
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh solving forbidden')):
                recovered=reuse_checked_model(s,cases[donor]['source'],cases[target]['source'])
            assert recovered['status']=='sat' and not recovered['metrics'].get('expanded_nodes',0)
            after=study.prior.native_rows(s);assert before.items()<=after.items()
            assert set(after)-set(before)=={cases[target]['root']};payload=after[cases[target]['root']]
        finally:s.close()
        verification={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            reader=cls(path)
            try:
                for key in after:assert reader._read(key) is not None
                statuses={c['root']:'sat' if reader._read(c['root'])['answer'] else 'unsat' for c in cases}
                verification[cls.__name__]=dict(nodes=len(after),source_roots=dict(Counter(statuses.values())))
            finally:reader.close()
        dest=out/'recovery';dest.mkdir();recovery_archive=base.archive(path,dest)
        union=Path(td)/'union';base.restore_archive(parent['reference_union'],union);con=sqlite3.connect(union)
        try:
            original=dict(con.execute('SELECT id,payload FROM cnf_residual_v1'))
            assert cases[target]['root'] not in original
            with con:con.execute('INSERT INTO cnf_residual_v1(id,payload) VALUES (?,?)',(cases[target]['root'],payload))
            final=dict(con.execute('SELECT id,payload FROM cnf_residual_v1'))
            assert original.items()<=final.items() and len(final)==len(original)+1
        finally:con.close()
        s=CanonicalVerifySnapshot(union)
        try:assert s._read(cases[target]['root'])['answer'] is True
        finally:s.close()
        dest=out/'recovered-union';dest.mkdir();union_archive=base.archive(union,dest)
    result=dict(source_fingerprints={f:base.sha(f) for f in FILES},parent_checkpoint=study.binding(out/'pre-recovery-checkpoint.json'),
        donor_case=donor,donor_became_available_at=77,target_case=target,result=recovered,archive=recovery_archive,reference_union=union_archive,
        verified=verification,new_nodes=1,new_payload=len(cases[target]['root'])+len(payload),final_union_native=len(final),
        limitations=['Separate post-timing step; neither original budget-stop record is rewritten.',
        'The related donor is supplied by catalog metadata; candidate discovery/indexing and stream-wide counterfactual savings are not implemented.',
        'Shared original variable IDs bind the donor assignment. All target literals are validated and the full target witness is checked before native publication.',
        'A failed candidate means no result, not UNSAT. No claim about all arbitrary CNFs.'])
    base.write(out/'recovery.json',result)
    checkpoint=copy.deepcopy(parent);checkpoint['reference_union']=union_archive
    checkpoint['larger_mixtures']['recovery']=study.binding(out/'recovery.json')
    checkpoint['source_fingerprints'].update(result['source_fingerprints'])
    base.write(out/'checkpoint.json',checkpoint)
    print(base.encode(dict(status=recovered['status'],expanded_nodes=recovered['metrics'].get('expanded_nodes',0),new_payload=result['new_payload'],final_union_native=len(final))),flush=True)


if __name__=='__main__':resume(Path(sys.argv[1]))
