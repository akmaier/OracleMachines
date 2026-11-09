import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_retained_plans import RetainedPlanInventory
from experiments.cnf_residual_dag import holds
from solver.test_cnf_pattern_inventory import assignments


class RetainedPlanRegressionTests(unittest.TestCase):
    def test_mixed_policy_cold_audit_uses_one_connection(self):
        from experiments.compare_cnf_retained_plans import audit
        from experiments.cnf_polarity_horn import PolarityHornInventory
        from experiments.cnf_residual_dag import ResidualSolver
        for cls in (BinaryPathInventory,RetainedPlanInventory):
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'history.db';old=PolarityHornInventory(path,max_depth=1)
                old.inspect([(-1,2)]);old.close();h=cls(path,max_depth=1)
                h.inspect([(-1,2)]);h.inspect([(1,2)]);h.close()
                solver=ResidualSolver(path);solver.solve([(-1,2)]);solver.close()
                result=audit(path,cls,dict(max_depth=1))
                self.assertTrue(result['bytes_unchanged']);self.assertEqual(result['sources'],3)

    def test_lost_variable_one_plan_is_reused_without_new_choices(self):
        data=json.loads(Path('experiments/results/cnf-binary-paths-full/loss-alternatives.json').read_text())
        fixture=next(r for r in data['shared_reductions']
                     if r['old']['summary']['closed'] and not r['after']['summary']['closed'])
        h=RetainedPlanInventory(max_depth=1);old=h.prepared.inspect(fixture['cnf'])
        self.assertTrue(old['summary']['closed'])
        fresh=BinaryPathInventory(max_depth=1)
        self.assertFalse(fresh.inspect(fixture['cnf'])['summary']['closed'])
        with patch.object(h,'_choices',side_effect=AssertionError('reacquired search')):
            result=h.inspect(fixture['cnf'])
        node=h._load(result['root']['key'])
        self.assertTrue(result['summary']['closed']);self.assertEqual(node['kind'],'retained_plan')
        self.assertEqual(node['reference'],old['root']['key'])
        h.close();fresh.close()

    def test_small_prepared_graphs_and_models(self):
        rng=random.Random(202611091714);h=RetainedPlanInventory(max_depth=1);hits=0
        for _ in range(30):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,5),rng.choice((2,3,4)))) for _ in range(14)]
            old=h.prepared.inspect(source);result=h.inspect(source)
            if old['summary']['closed']:
                hits+=1;node=h._load(result['root']['key'])
                self.assertTrue(result['summary']['closed']);self.assertEqual(node['kind'],'retained_plan')
                for model in assignments(node['cnf']):
                    if holds(node['cnf'],model):self.assertTrue(holds(node['cnf'],h.lift(result['root']['key'],model)))
        self.assertGreater(hits,0);h.close()
