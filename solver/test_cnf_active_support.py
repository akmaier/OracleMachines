from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,json,sqlite3,unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_cofactor_support import prepare
from experiments.cnf_deferred_support import discover,DeferredCoreBank
from experiments.cnf_incremental_support import extend
from experiments.cnf_active_support import ActiveCoreBank,extend_active,audit_with_lineage
from experiments.cnf_snapshot_replay import FROZEN_AUDIT
from solver.test_cnf_cofactor_support import CORE,record


class ActiveSupportTests(unittest.TestCase):
    def make(self,**kwargs):
        s=ResidualSolver(**kwargs);self.addCleanup(s.close);return s
    def test_constructor_and_misses_do_not_read_proofs(self):
        s=self.make();r=record(s,CORE+[[9,10]],[3]);bank=discover(s,[('old',[r])])
        with patch.object(s,'_read',side_effect=AssertionError('Unrelated proof read')):
            active=ActiveCoreBank(s,bank['cores']);self.assertIsNone(active.reuse([[77]]))
    def test_matched_ready_core_is_checked_independently_of_origin(self):
        s=self.make();r=record(s,CORE,[3]);bank=prepare(s,[('old',[r])]);bank['cores'][0]['origin']='unneeded historical root'
        target=CORE+[[8,9],[9,10]]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            self.assertIsNotNone(ActiveCoreBank(s,bank['cores']).reuse(target));self.assertFalse(s.solve(target)['answer'])
    def test_false_or_misbound_active_core_rejects(self):
        s=self.make();positive=s.solve([[1]]);proposal=dict(source=[[1]],root=positive['root'],origin='missing')
        with self.assertRaisesRegex(ValueError,'negative support'):ActiveCoreBank(s,[proposal]).reuse([[1],[2]])
        proposal['root']='foreign'
        with self.assertRaisesRegex(ValueError,'Unbound active'):ActiveCoreBank(s,[proposal]).reuse([[1],[2]])
    def test_pending_core_materializes_and_repeats_without_search(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False)
        r=record(s,CORE+[[9,10]],[3]);bank=discover(s,[('old',[r])]);active=ActiveCoreBank(s,bank['cores']);target=CORE+[[11,12],[12,13]]
        self.assertIsNone(s._read(bank['cores'][0]['root']))
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            self.assertTrue(active.reuse(target)['inserted']);self.assertFalse(active.reuse(target)['inserted'])
        self.assertEqual(active.counts['materialization_attempts'],1)
    def test_missing_pending_origin_cannot_publish(self):
        s=self.make();target=CORE+[[8,9],[9,10]];proposal=dict(source=CORE,root=s._canonical(CORE)[2],origin='missing')
        with self.assertRaises(ValueError):ActiveCoreBank(s,[proposal]).reuse(target)
        self.assertIsNone(s._read(s._canonical(target)[2]))
    def test_constructor_copies_caller_proposals(self):
        s=self.make();r=record(s,CORE,[3]);bank=prepare(s,[('old',[r])]);active=ActiveCoreBank(s,bank['cores']);bank['cores'][0]['source']=[[88]]
        self.assertIsNone(active.reuse([[88]]));self.assertIsNotNone(active.reuse(CORE+[[8,9]]))
    def test_active_extension_matches_full_index_and_rejects_duplicate_batch(self):
        s=self.make();old=[('old',[record(s,CORE,[3])])];new=[('new',[record(s,[[1],[-1]],[3])])];bank=prepare(s,old)
        with patch.object(s,'_store',side_effect=AssertionError('Premature publication')):
            a=extend(s,bank,old,new);b=extend_active(s,bank,old,new)
        for f in ('cores','all_cores','origins','retained_indices','dominance'):self.assertEqual(a[f],b[f])
        with self.assertRaises(ValueError):extend_active(s,bank,old,old)
    def test_joint_audit_preserves_full_proof_and_query_checks(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);r=record(s,CORE,[3]);bank=prepare(s,[('old',[r])]);s.close();before=path.read_bytes()
            a=FROZEN_AUDIT(path,[r]);b=audit_with_lineage(path,[r],bank,[('old',[r])])
            for field in ('checked_nodes','query_answers','no_acquisition'):self.assertEqual(a[field],b[field])
            self.assertEqual(b['lineage']['prior_sources_checked'],1);self.assertEqual(b['snapshot']['censuses'],1);self.assertEqual(before,path.read_bytes())
    def test_unused_bad_provenance_and_unqueried_corruption_still_reject(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);r=record(s,CORE,[3]);bank=prepare(s,[('old',[r])]);unused=s.solve([[77]]);s.close()
            bad=copy.deepcopy(bank);bad['origins'][0]['query_root']='foreign'
            with self.assertRaises(ValueError):audit_with_lineage(path,[r],bad,[('old',[r])])
            db=sqlite3.connect(path);payload=json.loads(db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(unused['root'],)).fetchone()[0]);payload['format']='corrupt'
            db.execute('UPDATE cnf_residual_v1 SET payload=? WHERE id=?',(json.dumps(payload),unused['root']));db.commit();db.close()
            with self.assertRaises(ValueError):audit_with_lineage(path,[r],bank,[('old',[r])])
    def test_joint_audit_closes_snapshot_after_lineage_failure(self):
        from experiments import cnf_active_support as active
        with TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path);r=record(s,CORE,[3]);bank=prepare(s,[('old',[r])]);s.close();instances=[];original=active._HeldSnapshot
            class Tracked(original):
                def __init__(self,*args):super().__init__(*args);instances.append(self)
            with patch.object(active,'_HeldSnapshot',Tracked),patch.object(active,'check_proposals',side_effect=ValueError('lineage')):
                with self.assertRaisesRegex(ValueError,'lineage'):audit_with_lineage(path,[r],bank,[('old',[r])])
            with self.assertRaises(sqlite3.ProgrammingError):instances[0].db.execute('SELECT 1')


if __name__=='__main__':unittest.main()
