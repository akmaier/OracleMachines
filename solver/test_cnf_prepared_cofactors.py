from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,unittest
from experiments import cnf_bipolar_routing as bipolar
from experiments.cnf_prepared_cofactors import PreparedCofactorSolver,prepared_probe_child
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,restrict,holds,token
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_bipolar_routing import SOURCE,FLIPPED


class PreparedCofactorTests(unittest.TestCase):
    def solver(self,**kw):
        s=PreparedCofactorSolver(**kw);self.addCleanup(s.close);return s

    def test_probe_miss_can_supply_visit_normalization_only(self):
        s=self.solver();cnf,_=normalize(FLIPPED)
        with s.cofactor_session():
            self.assertIsNone(s.prepare_probe(cnf,3,False));child=restrict(cnf,{3:False})
            model,key=s._visit(child);self.assertTrue(holds(child,model));self.assertGreater(s.cofactor_summary['hits'],0)
        self.assertIsNone(s._cofactors)

    def test_negative_binding_still_rejects_wrong_missing_positive_children(self):
        s=self.solver();cnf,_=normalize(SOURCE)
        with s.cofactor_session():
            key=s.prepare_probe(cnf,3,False);child=restrict(cnf,{3:False});s._negative_child(key,child)
            with self.assertRaises(ValueError):s._negative_child('wrong',child)
            s.checked.pop(key,None);s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(key,));s.db.commit()
            with self.assertRaises(ValueError):s._negative_child(key,child)
            source=normalize([[1,2]])[0];self.assertIsNone(s.prepare_probe(source,1,False))
            model,key=s._visit(restrict(source,{1:False}));self.assertIsNotNone(model)
            with self.assertRaises(ValueError):s._negative_child(key,restrict(source,{1:False}))

    def test_invalid_equal_literals_never_hit(self):
        s=self.solver()
        with s.cofactor_session():
            s.prepare_probe(((1,2),),2,False)
            for value in (True,1.0,0):
                with self.assertRaises(ValueError):s._visit(((value,),))

    def test_names_and_mutable_inputs_are_exactly_bound(self):
        s=self.solver();raw=[[10,20]]
        with s.cofactor_session():
            s.prepare_probe(raw,10,False);raw[0][1]=30
            model,_=s._visit([[20]]);self.assertEqual(model,{20:True})
            model,_=s._visit([[30]]);self.assertEqual(model,{30:True})
            self.assertGreater(s.cofactor_summary['hits'],0)

    def test_capacity_oversize_and_independent_graph_charge(self):
        for cap in (sys.getsizeof({}),1024,128*1024):
            s=self.solver(cofactor_bytes=cap)
            with s.cofactor_session():
                for i in range(1,12):
                    s.prepare_probe(((i,20),(i,30)),i,False)
                    seen=set()
                    def size(obj):
                        if id(obj) in seen:return 0
                        seen.add(id(obj));n=sys.getsizeof(obj)
                        if isinstance(obj,dict):n+=sum(size(k)+size(v) for k,v in obj.items())
                        elif isinstance(obj,(tuple,list)):n+=sum(map(size,obj))
                        return n
                    self.assertLessEqual(size(s._cofactors),sys.getsizeof(s._cofactors)+s._cofactor_payload)
                    self.assertLessEqual(s.cofactor_summary['peak_bytes'],cap)
            if cap==sys.getsizeof({}):self.assertGreater(s.cofactor_summary['oversized'],0)
        for cap in (-1,0,True):
            with self.assertRaises(ValueError):PreparedCofactorSolver(cofactor_bytes=cap)

    def test_failure_nested_session_and_probe_cleanup(self):
        s=self.solver()
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with s.cofactor_session():
                with self.assertRaises(RuntimeError):
                    with s.cofactor_session():pass
                s.prepare_probe(((1,2),),2,False);raise RuntimeError('injected')
        self.assertIsNone(s._cofactors);self.assertIsNone(s._cofactor_consumer);self.assertFalse(s._cofactor_producer)
        with s.cofactor_session():
            with self.assertRaises(ValueError):s.prepare_probe(((1,2),),1,1)
            self.assertFalse(s._cofactor_producer)

    def test_exact_proof_payloads_and_truth_on_small_mixtures(self):
        a=InputSafeAffineProbeSolver();self.addCleanup(a.close);b=self.solver()
        clauses=[[-1,-2],[-1,2],[1,-2],[1,2],[-2,-3],[-2,3],[2,-3],[2,3]]
        with patch.object(TargetedBackboneMixin,'_expand',bipolar.bipolar_expand):
            for mask in range(256):
                source=[c for i,c in enumerate(clauses) if mask>>i&1]+[[1,2,3]]
                expected=any(holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
                for signed in (source,[[-l for l in c] for c in source]):
                    x=acquire(a,signed,256)
                    with b.cofactor_session(),patch.object(bipolar,'probe_child',prepared_probe_child):y=acquire(b,signed,256)
                    self.assertEqual(x['result']['answer'],expected);self.assertEqual(y['result']['answer'],expected)
                    for field in ('root','model','answer'):self.assertEqual(x['result'][field],y['result'][field])
                    self.assertEqual(x['metrics'].get('expanded_nodes',0),y['metrics'].get('expanded_nodes',0))
        self.assertEqual(list(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),list(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))

    def test_retained_stop_and_both_cold_readers(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=PreparedCofactorSolver(path)
            try:
                with s.cofactor_session(),patch.object(bipolar,'probe_child',prepared_probe_child),patch.object(TargetedBackboneMixin,'_expand',bipolar.bipolar_expand):
                    r=acquire(s,FLIPPED,1,retain_stop=True)
                self.assertEqual(r['status'],'unresolved');self.assertIsNone(s._cofactors)
                keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')];self.assertTrue(keys)
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                s=cls(path)
                try:
                    for k in keys:self.assertIsNotNone(s._read(k))
                finally:s.close()


if __name__=='__main__':unittest.main()
