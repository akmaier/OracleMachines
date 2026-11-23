from collections import Counter
from contextlib import contextmanager
from dataclasses import FrozenInstanceError,replace,fields
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,unittest
from experiments import cnf_cofactor_handoff as handoff
from experiments import cnf_residual_dag as native
from experiments.cnf_bipolar_routing import bipolar_expand
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_bipolar_routing import SOURCE,FLIPPED


@contextmanager
def policy(s):
    with s.handoff_session(),patch.object(TargetedBackboneMixin,'_expand',handoff.handoff_expand),patch.object(native,'propagate',handoff.handoff_propagate):yield


def rows(s):return list(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))


class CofactorHandoffTests(unittest.TestCase):
    def solver(self,**kw):
        s=handoff.CofactorHandoffSolver(**kw);self.addCleanup(s.close);return s

    def test_partial_propagation_and_original_names_survive_mutation(self):
        s=self.solver(leaves=False);source=[[10],[20,30],[-20,30],[99,100]]
        with policy(s):
            self.assertIsNone(s._probe_cofactor(source,99,True,retain=True));offer=s._offer
            source[0][0]=-10;model,key=s._visit_offer(offer)
            self.assertTrue(native.holds(offer.raw,model));self.assertTrue(model[10]);self.assertIn(30,model)
            self.assertEqual(s.counts['handoff_canonical_reuses'],1)
            self.assertEqual(s.counts['handoff_propagation_reuses'],1)
        self.assertEqual(s._handoff_held,0);self.assertIsNone(handoff._PROPAGATION.get())

    def test_both_signs_preserve_models_and_all_proof_bytes(self):
        for source in (SOURCE,FLIPPED):
            a=InputSafeAffineProbeSolver();self.addCleanup(a.close);b=self.solver()
            with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):x=acquire(a,source,256)
            with policy(b):y=acquire(b,source,256)
            self.assertTrue(native.holds(source,y['result']['model']))
            self.assertEqual(rows(a),rows(b));self.assertEqual(x['metrics']['expanded_nodes'],y['metrics']['expanded_nodes'])
            if source==FLIPPED:self.assertEqual(b.handoff_summary['consumed'],1)

    def test_propagation_binding_is_identity_counter_scoped_and_one_use(self):
        s=self.solver(leaves=False)
        with policy(s):
            s._probe_cofactor(((1,),(2,3),(9,10)),9,True,retain=True);offer=s._offer
            def inspect(raw):
                cnf,_,key=s._canonical(raw);other=Counter();twin=tuple(list(cnf));self.assertIsNot(cnf,twin)
                with patch.object(handoff,'original_propagate',wraps=handoff.original_propagate) as real:
                    handoff.handoff_propagate(cnf,other);handoff.handoff_propagate(twin,s.counts)
                    before=real.call_count;fixed,trace,conflict=handoff.handoff_propagate(cnf,s.counts)
                    self.assertEqual(real.call_count,before);self.assertTrue(fixed)
                    fixed.clear();trace.clear()
                    handoff.handoff_propagate(cnf,s.counts);self.assertEqual(real.call_count,before+1)
                return None,key
            with patch.object(s,'_visit',inspect):s._visit_offer(offer)
        self.assertIsNone(handoff._PROPAGATION.get())

    def test_forged_foreign_and_repeated_offers_are_rejected(self):
        a=self.solver();b=self.solver()
        with a.handoff_session(),b.handoff_session():
            a._probe_cofactor(((1,2),),2,False,retain=True);offer=a._offer
            with self.assertRaises(FrozenInstanceError):offer.charge=0
            with self.assertRaises(ValueError):a._visit_offer(replace(offer,raw=((-1,),)))
            with self.assertRaises(ValueError):b._visit_offer(offer)
            a._visit_offer(offer)
            with self.assertRaises(ValueError):a._visit_offer(offer)

    def test_capacity_skip_and_disabled_handoff_preserve_proofs(self):
        expected=None
        for cap in (0,1,256*1024):
            s=self.solver(handoff_bytes=cap)
            with policy(s):r=acquire(s,FLIPPED,256)
            if expected is None:expected=rows(s)
            else:self.assertEqual(rows(s),expected)
            self.assertLessEqual(s.handoff_summary['peak_bytes'],cap)
            if cap==1:self.assertGreater(s.handoff_summary['oversized'],0)
            self.assertTrue(r['result']['answer'])
        for cap in (-1,True):
            with self.assertRaises(ValueError):handoff.CofactorHandoffSolver(handoff_bytes=cap)

    def test_nested_live_offers_are_charged_together(self):
        s=self.solver();active=[]
        def size(obj,seen):
            if id(obj) in seen:return 0
            seen.add(id(obj));n=sys.getsizeof(obj)
            if isinstance(obj,handoff._Offer):n+=sum(size(getattr(obj,f.name),seen) for f in fields(obj))
            elif isinstance(obj,(tuple,list)):n+=sum(size(x,seen) for x in obj)
            return n
        with s.handoff_session():
            s._probe_cofactor(((1,2),),2,False,retain=True);outer=s._offer
            def visit(raw):
                s._canonical(raw)
                if not active:
                    active.append(outer);s._probe_cofactor(((3,4),),4,False,retain=True);inner=s._offer
                    actual=sum(size(x,set()) for x in (outer,inner));self.assertLessEqual(actual,s._handoff_held)
                    self.assertEqual(s._handoff_held,outer.charge+inner.charge)
                    return s._visit_offer(inner)
                return {},'diagnostic'
            with patch.object(s,'_visit',visit):s._visit_offer(outer)
            self.assertEqual(s._handoff_held,0)
            s._probe_cofactor(((1,2),),2,False,retain=True);outer=s._offer;s.handoff_bytes=outer.charge
            def limited(raw):
                s._canonical(raw);s._probe_cofactor(((3,4),),4,False,retain=True)
                self.assertIsNone(s._offer);return {},'diagnostic'
            with patch.object(s,'_visit',limited):s._visit_offer(outer)
            self.assertGreater(s.handoff_summary['oversized'],0)

    def test_retained_budget_stop_and_cold_readers(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=handoff.CofactorHandoffSolver(path)
            try:
                with policy(s):r=acquire(s,FLIPPED,1,retain_stop=True)
                self.assertEqual(r['status'],'unresolved');self.assertEqual(s._handoff_held,0)
                self.assertIsNone(s._offer);self.assertIsNone(s._handoff_canonical);self.assertIsNone(handoff._PROPAGATION.get())
                keys=[k for k,v in rows(s)];self.assertTrue(keys)
                root=s._canonical(FLIPPED)[2];self.assertIsNone(s._read(root))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(reader._read(key))
                finally:reader.close()

    def test_publication_failure_cleans_offer_and_allows_retry(self):
        s=self.solver()
        def fail(event,*unused):
            if event=='after_insert':raise RuntimeError('injected publication failure')
        s.publication_hook=fail
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with policy(s):acquire(s,FLIPPED,256)
        self.assertIsNone(s._offer);self.assertIsNone(s._handoff_canonical);self.assertEqual(s._handoff_held,0)
        self.assertIsNone(handoff._PROPAGATION.get());s.publication_hook=None
        with policy(s):r=acquire(s,FLIPPED,256)
        self.assertTrue(native.holds(FLIPPED,r['result']['model']))

    def test_small_mixtures_and_complements_match_truth_and_payloads(self):
        a=InputSafeAffineProbeSolver();self.addCleanup(a.close);b=self.solver()
        clauses=[[-1,-2],[-1,2],[1,-2],[1,2],[-2,-3],[-2,3],[2,-3],[2,3]]
        for mask in range(256):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]+[[1,2,3]]
            expected=any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
            for signed in (source,[[-l for l in c] for c in source]):
                with patch.object(TargetedBackboneMixin,'_expand',bipolar_expand):x=acquire(a,signed,256)
                with policy(b):y=acquire(b,signed,256)
                self.assertEqual(y['result']['answer'],expected)
                for k in ('answer','model','root'):self.assertEqual(x['result'][k],y['result'][k])
                self.assertEqual(x['metrics'].get('expanded_nodes',0),y['metrics'].get('expanded_nodes',0))
        self.assertEqual(rows(a),rows(b))

    def test_cached_cofactors_keep_normal_checks_and_skip_propagation(self):
        s=self.solver()
        with policy(s):
            cnf=native.normalize(SOURCE)[0];key=s._probe_cofactor(cnf,3,False)
            self.assertIsNotNone(key)
            with patch.object(handoff,'original_propagate',side_effect=AssertionError('Repeated probe')):
                self.assertEqual(s._probe_cofactor(cnf,3,False,retain=True),key)
            self.assertIsNone(s._offer)
            raw=((1,2),);s._visit(((1,),))
            with patch.object(handoff,'original_propagate',side_effect=AssertionError('Cached model')):
                self.assertIsNone(s._probe_cofactor(raw,2,False,retain=True));self.assertIsNone(s._offer.propagation)
                self.assertTrue(s._visit_offer(s._offer)[0][1])
            with self.assertRaises(ValueError):s._probe_cofactor(raw,1,1)


if __name__=='__main__':unittest.main()
