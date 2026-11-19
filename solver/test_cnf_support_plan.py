from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,sqlite3,unittest
from experiments.cnf_support_plan import CausalPlan,PlanBudget,PlannedNegativeSolver
from experiments.cnf_negative_edit_pool import NegativeEditPoolSolver,SupportBudget
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_cross_family import truth_table
from solver.test_cnf_publication_batches import replay


def rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))


class SupportPlanTests(unittest.TestCase):
    def make(self,cls=PlannedNegativeSolver,**kw):
        s=cls(**kw);self.addCleanup(s.close);return s

    def test_same_proofs_as_causal_materializer(self):
        sources=[[[10],[-10],[20,30]],[[1,2],[1,-2],[-1,2],[-1,-2],[3,4]],
                 [list(c) for c in product((-1,1),(-2,2),(-3,3))]+[[4],[4,5]]]
        hall=[[3*i+1,3*i+2,3*i+3] for i in range(4)]
        hall += [[-(3*i+h),-(3*j+h)] for h in (1,2,3) for i in range(4) for j in range(i+1,4)]
        sources += [hall, hall+[[13,14,15]], hall+[[1,2,3,13]]]
        for source in sources:
            a=self.make(ResidualSolver);b=self.make(ResidualSolver)
            root=a.solve(source)['root'];self.assertEqual(root,b.solve(source)['root'])
            plan=CausalPlan(a)
            with patch.object(a,'_store',side_effect=AssertionError('Discovery publication')):result=plan.prepare(root)
            with patch.object(a,'_expand',side_effect=AssertionError('Fresh search')):self.assertEqual(plan.emit(root),result)
            expected=CausalSupportExtractor(b).extract(root)
            self.assertEqual(result,expected);self.assertEqual(rows(a),rows(b))

    def test_online_policy_same_records_and_plan_cleared(self):
        a=self.make();b=self.make(NegativeEditPoolSolver)
        for source in ([[1],[-1],[2,3]],[[1],[-1],[2,-3]],[[1],[2,-3]],[]):
            x=a.solve(source);y=b.solve(source)
            self.assertEqual(x['answer'],y['answer']);self.assertEqual(rows(a),rows(b));self.assertIsNone(a._support_plan)
        self.assertGreater(a.counts.get('negative_retained_entries',0),0)

    def test_no_second_support_walk_on_hit(self):
        s=self.make();s.solve([[1],[-1],[2,3]])
        with patch.object(CausalSupportExtractor,'extract',side_effect=AssertionError('Repeated support traversal')):
            r=s.solve([[1],[-1],[2,-3]])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['plan_hits'],1)
        self.assertEqual(r['metrics'].get('negative_materialize_support_nodes',0),0)

    def test_small_byte_budget_falls_back_without_changed_proofs(self):
        a=self.make(plan_byte_limit=1);b=self.make(NegativeEditPoolSolver)
        for source in ([[1],[-1],[2,3]],[[1],[-1],[2,-3]]):
            x=a.solve(source);y=b.solve(source);self.assertEqual(x['answer'],y['answer']);self.assertEqual(rows(a),rows(b))
        self.assertEqual(x['metrics']['plan_discovery_fallbacks'],1);self.assertIsNone(a._support_plan)

    def test_support_budget_and_invalid_limits(self):
        s=self.make(ResidualSolver,leaves=False,decompose=False,positive_subsumption=False)
        source=[list(c) for c in product((-1,1),(-2,2),(-3,3))];root=s.solve(source)['root']
        with self.assertRaises(SupportBudget):CausalPlan(s,node_limit=1).prepare(root)
        with self.assertRaises(PlanBudget):CausalPlan(s,byte_limit=1).prepare(root)
        for opts in (dict(byte_limit=False),dict(node_limit=0),dict(literal_limit=-1)):
            with self.assertRaises(ValueError):CausalPlan(s,**opts)
        with self.assertRaises(ValueError):PlannedNegativeSolver(plan_byte_limit=True)

    def test_tampered_plan_cannot_bypass_native_checker(self):
        s=self.make(ResidualSolver);root=s.solve([[1],[-1],[2,3]])['root'];plan=CausalPlan(s);result=plan.prepare(root)
        # The extracted contradiction is absent until checked publication.
        self.assertNotIn(result['root'],rows(s))
        original=plan.plans[root];recipe=json.loads(original);recipe['core']=[[1]];plan.plans[root]=json.dumps(recipe)
        with self.assertRaises((ValueError,KeyError)):plan.emit(root)
        self.assertNotIn(result['root'],rows(s))
        recipe=json.loads(original);recipe['extra']['trace'][0][0]*=-1;plan.plans[root]=json.dumps(recipe)
        with self.assertRaises(ValueError):plan.emit(root)
        self.assertNotIn(result['root'],rows(s))

    def test_commit_failure_clears_plan_and_preserves_recovery(self):
        s=self.make();s.solve([[1],[-1],[2,3]])
        with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):s.solve([[1],[-1],[2,-3]])
        self.assertIsNone(s._support_plan);self.assertFalse(s.db.pending);self.assertFalse(s.db.in_transaction)
        self.assertFalse(s.solve([[1],[-1],[2,-3]])['answer'])

    def test_persistent_proofs_need_no_planner(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=PlannedNegativeSolver(path)
            try:s.solve([[1],[-1],[2,3]]);s.solve([[1],[-1],[2,-3]])
            finally:s.close()
            self.assertTrue(replay(path))

    def test_exhaustive_two_variable_stream(self):
        s=self.make();clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];r=s.solve(source)
            self.assertEqual(r['answer'],truth_table(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))


if __name__=='__main__':unittest.main()
