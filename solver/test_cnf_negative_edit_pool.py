from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from itertools import product
import unittest
from experiments.cnf_negative_edit_pool import NegativeEditPoolSolver,BoundedCausalExtractor,SupportBudget
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_residual_dag import holds
from experiments.cnf_cross_family import truth_table
from solver.test_cnf_publication_batches import replay


class NegativeEditPoolTests(unittest.TestCase):
    def make(self,**kw):
        s=NegativeEditPoolSolver(**kw);self.addCleanup(s.close);return s

    def test_irrelevant_deletion_and_addition_reuses_checked_core(self):
        s=self.make();s.solve([[1],[-1],[2,3]])
        with patch.object(WitnessPoolSolver,'_expand',side_effect=AssertionError('Fresh solving')):
            r=s.solve([[1],[-1],[2,-3]])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['negative_hits'],1)
        self.assertEqual(r['metrics']['negative_discover_attempts'],1)

    def test_needed_deletion_does_not_reuse_unsat(self):
        s=self.make();s.solve([[1],[-1],[2,3]])
        r=s.solve([[1],[2,3]])
        self.assertTrue(r['answer']);self.assertTrue(holds([[1],[2,3]],r['model']))
        self.assertEqual(r['metrics'].get('negative_hits',0),0)

    def test_addition_reuses_full_origin_without_extraction(self):
        s=self.make();s.solve([[1],[-1]])
        with patch.object(WitnessPoolSolver,'_expand',side_effect=AssertionError('Fresh solving')):
            r=s.solve([[1],[-1],[2,3]])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['negative_hits'],1)
        self.assertEqual(r['metrics'].get('negative_discover_attempts',0),0)

    def test_empty_input_invalid_input_and_limits(self):
        s=self.make(negative_capacity=2,negative_literal_limit=4)
        self.assertTrue(s.solve([])['answer']);self.assertFalse(s.solve([[]])['answer'])
        with self.assertRaises(ValueError):s.solve([[],[True]])
        for source in ([[1],[-1]],[[1,2],[-1],[-2]],[[1,2],[1,-2],[-1,2],[-1,-2]]):s.solve(source)
        self.assertLessEqual(len(s.negative_pool),2)
        self.assertTrue(all(sum(map(len,e['clauses']))<=4 for e in s.negative_pool.values()))
        for kw in (dict(negative_capacity=0),dict(negative_node_limit=True)):
            with self.assertRaises(ValueError):NegativeEditPoolSolver(**kw)

    def test_bounded_extractor_and_no_discovery_publications(self):
        s=self.make(leaves=False,decompose=False,positive_subsumption=False)
        source=[list(c) for c in product((-1,1),(-2,2),(-3,3))]+[[4,5]];r=s.solve(source)
        with patch.object(s,'_store',side_effect=AssertionError('Proposal publication')):
            with self.assertRaises(SupportBudget):BoundedCausalExtractor(s,materialize=False,node_limit=1).extract(r['root'])
            core=BoundedCausalExtractor(s,materialize=False).source_core(source)
        self.assertFalse(truth_table(core['source'])['answer'])
        s.negative_node_limit=1
        result=s.solve(source[:-1]+[[-4,5]])
        self.assertFalse(result['answer'])
        self.assertEqual(result['metrics']['negative_discover_budget_stops'],1)

    def test_stale_origin_is_not_authority(self):
        s=self.make();s.solve([[1],[-1],[2,3]]);key=next(iter(s.negative_pool))
        del s.checked[key]
        with s.db:s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(key,))
        r=s.solve([[1],[-1],[2,-3]])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics'].get('negative_hits',0),0)
        self.assertGreater(r['metrics']['negative_stale_origins'],0)

    def test_cold_replay_uses_ordinary_certificates(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=NegativeEditPoolSolver(path)
            try:s.solve([[1],[-1],[2,3]]);s.solve([[1],[-1],[2,-3]])
            finally:s.close()
            self.assertTrue(replay(path))
            s=NegativeEditPoolSolver(path)
            try:
                self.assertFalse(s.negative_pool)
                with patch.object(s,'_expand',side_effect=AssertionError('Cold expansion')):
                    self.assertFalse(s.solve([[1],[-1],[2,-3]])['answer'])
            finally:s.close()

    def test_exhaustive_two_variable_stream(self):
        s=self.make();clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];r=s.solve(source)
            self.assertEqual(r['answer'],truth_table(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))


if __name__=='__main__':unittest.main()
