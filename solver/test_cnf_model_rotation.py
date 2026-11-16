from collections import Counter
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_model_rotation import ModelRotation,publish
from experiments.cnf_residual_dag import ResidualSolver,holds


class ModelRotationTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);return s
    def setup_cycle(self,limit=64):
        s=self.make();f=[[1],[-1,2],[-2]];g=[[-1,2],[-2]];old=s.solve(f);seed=s.solve(g)
        e=ModelRotation(s,[dict(source=f,root=old['root'])],[dict(source=g,root=seed['root'])],flip_limit=limit)
        return s,e,f
    def test_rotation_publishes_and_replays_without_search(self):
        s,e,f=self.setup_cycle()
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            e.drain()
            for cid in range(len(f)):
                source=[c for i,c in enumerate(f) if i!=cid];r=s.solve(source)
                self.assertTrue(r['answer']);self.assertTrue(holds(source,r['model']))
        self.assertEqual(len(e.templates[0]['models']),3)
    def test_global_budget_does_not_reset_between_queries(self):
        s,e,f=self.setup_cycle(1);e.drain();first=e.state();e.drain()
        self.assertEqual(e.state(),first);self.assertEqual(len(first['templates'][0]['attempts']),1)
        self.assertGreater(len(first['templates'][0]['models']),first['templates'][0]['cursor'])
    def test_zero_budget_retains_seed_but_performs_no_flips(self):
        s,e,f=self.setup_cycle(0);e.drain();self.assertFalse(e.templates[0]['attempts']);self.assertEqual(len(e.templates[0]['models']),1)
    def test_missing_or_satisfiable_template_and_foreign_seed_reject(self):
        s=self.make();f=[[1]];key=s._canonical(f)[2]
        with self.assertRaises(ValueError):ModelRotation(s,[dict(source=f,root=key)],[])
        s.solve(f)
        with self.assertRaises(ValueError):ModelRotation(s,[dict(source=f,root=key)],[])
        old=s.solve([[1],[-1]])
        with self.assertRaises(ValueError):ModelRotation(s,[dict(source=[[1],[-1]],root=old['root'])],[dict(source=[[1]],root='wrong')])
    def test_invalid_model_never_publishes(self):
        s=self.make()
        with self.assertRaises(ValueError):publish(s,[[1]],{1:False},Counter())
        with self.assertRaises(ValueError):publish(s,[[1]],{1:1},Counter())
        self.assertEqual(s.archive_storage()[0],0)
    def test_exhaustive_two_variable_rotations_have_valid_publications(self):
        clauses=[tuple(a*(i+1) for i,a in enumerate(signs) if a) for signs in product((-1,0,1),repeat=2) if any(signs)]
        assignments=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        for mask in range(1,1<<len(clauses)):
            f=[c for i,c in enumerate(clauses) if mask>>i&1]
            if any(holds(f,a) for a in assignments):continue
            seeds=[([c for c in f if c!=removed]) for removed in f]
            seeds=[g for g in seeds if any(holds(g,a) for a in assignments)]
            if not seeds:continue
            s=ResidualSolver()
            try:
                old=s.solve(f);g=seeds[0];answer=s.solve(g)
                engine=ModelRotation(s,[dict(source=f,root=old['root'])],[dict(source=g,root=answer['root'])],flip_limit=16)
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
                    engine.drain()
                    for row in engine.templates[0]['models']:
                        query=[c for i,c in enumerate(engine.templates[0]['source']) if i!=row['clause']]
                        self.assertTrue(holds(query,row['model']))
            finally:s.close()


if __name__=='__main__':unittest.main()
