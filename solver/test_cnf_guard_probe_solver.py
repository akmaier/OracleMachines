from collections import Counter
from copy import deepcopy
from itertools import product
import random,unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_fresh_mixtures import attempt,generate


class GuardProbeSolverTests(unittest.TestCase):
    def fixture(self):
        source=native.normalize([[-1,2],[-1,3],[-2,-3,4],[-1,-4],[1,5,6],
            [5,7,8],[-5,7,9],[5,-7,9],[-5,-7,-9]])[0]
        return source,conditional_unit(source,[[1,True]],Counter())

    def test_tracking_control_preserves_native_search(self):
        for seed in range(4):
            source=generate('random-three',24,0,seed=77+seed)[0]
            a=LazyBinaryClosureSolver(node_limit=32);b=GuardProbeSolver(node_limit=32,guard_mode='tracking')
            try:
                x,y=attempt(a,source),attempt(b,source);self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
                self.assertEqual(dict(a.db.execute('SELECT * FROM cnf_residual_v1')),dict(b.db.execute('SELECT * FROM cnf_residual_v1')))
                self.assertEqual(b.guard_summary['pending_end'],0)
            finally:a.close();b.close()

    def test_guided_probe_preserves_positive_source_witness(self):
        source,t=self.fixture();self.assertIsNotNone(t)
        for mode in ('variable','guided'):
            s=GuardProbeSolver(templates=[t],guard_mode=mode);self.addCleanup(s.close)
            result=s.solve(source);self.assertTrue(result['answer']);self.assertTrue(native.holds(source,result['model']))
            self.assertGreater(s.guard_summary['counts'].get('guard_selected_sites',0),0)
            for key, in s.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(s._read(key))

    def test_guard_matching_uses_exact_source_coordinates(self):
        source,t=self.fixture();s=GuardProbeSolver(templates=[t]);self.addCleanup(s.close)
        renamed=[[l*7 for l in cl] for cl in source];result=s.solve(renamed)
        self.assertTrue(result['answer']);self.assertTrue(native.holds(renamed,result['model']))
        self.assertGreater(s.guard_summary['counts'].get('guard_selected_sites',0),0)

    def test_truth_on_unlabelled_small_cnfs_with_conditional_hints(self):
        rng=random.Random(202611240809)
        for sample in range(36):
            source=native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(10)])[0]
            names=sorted({abs(l) for c in source for l in c});truth=False;templates=[]
            for bits in product((False,True),repeat=len(names)):
                fixed=dict(zip(names,bits));truth|=native.holds(source,fixed)
                t=conditional_unit(source,[[v,b] for v,b in fixed.items()],Counter())
                if t is not None:templates.append(t)
            s=GuardProbeSolver(templates=templates,node_limit=256)
            try:
                result=s.solve(source);self.assertEqual(result['answer'],truth)
                if truth:self.assertTrue(native.holds(source,result['model']))
            finally:s.close()

    def test_deleted_support_is_ineligible(self):
        source,t=self.fixture();s=GuardProbeSolver(templates=[t]);self.addCleanup(s.close)
        s.solve([[1,2,3]]);self.assertEqual(s.guard_summary['eligible'],0);self.assertEqual(s.guard_summary['counts']['deleted_supports'],1)

    def test_invalid_certificate_rejected_before_search(self):
        source,t=self.fixture();bad=deepcopy(t);bad['conflict']=10000
        s=GuardProbeSolver(templates=[bad]);self.addCleanup(s.close)
        with self.assertRaises(ValueError):s.solve(source)
        self.assertFalse(s.guard_active)

    def test_tracking_and_matching_budgets_leave_correct_fallback(self):
        source,t=self.fixture();s=GuardProbeSolver(templates=[t],guard_checks=1,tracking_slots=1)
        self.addCleanup(s.close);result=s.solve(source)
        self.assertTrue(result['answer']);self.assertTrue(native.holds(source,result['model']))
        self.assertLessEqual(s.guard_summary['counts'].get('guard_checks',0),1)
        self.assertGreater(s.guard_summary['counts'].get('pending_limit_skips',0),0)

    def test_budget_stop_and_second_query_release_all_contexts(self):
        s=GuardProbeSolver(node_limit=1);self.addCleanup(s.close)
        source=generate('random-three',24,0,seed=77)[0]
        self.assertEqual(attempt(s,source)['status'],'unresolved')
        self.assertEqual(s.guard_summary['pending_end'],0);self.assertFalse(s.guard_active)
        self.assertTrue(s.solve([[1]])['answer']);self.assertEqual(s.guard_summary['pending_end'],0)

    def test_empty_bank_matches_native_and_invalid_limits_rejected(self):
        source,_=self.fixture();a=LazyBinaryClosureSolver();b=GuardProbeSolver()
        try:
            x,y=a.solve(source),b.solve(source);self.assertEqual(x['metrics'],y['metrics']);self.assertEqual(x['model'],y['model'])
        finally:a.close();b.close()
        for kwargs in ({'guard_mode':'bad'},{'guard_checks':0},{'tracking_slots':False},{'tracking_pending':-1}):
            with self.assertRaises(ValueError):GuardProbeSolver(**kwargs)


if __name__=='__main__':unittest.main()
