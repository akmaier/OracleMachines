from collections import Counter
from unittest import TestCase
from unittest.mock import patch
from experiments import compare_cnf_reuse_expansion as s
from experiments.audit_cnf_reuse_expansion import assert_prefix
from solver.test_cnf_selective_learning import independent, SQUARE


class ReuseExpansionTests(TestCase):
    def test_fresh_does_not_read_parent(self):
        with patch.object(s.previous, 'parent_data', side_effect=AssertionError):
            p, d = s.discover({'source': SQUARE}, 'fresh8000', Counter())
        self.assertEqual(p['kind'], 'unsat'); self.assertEqual(d['expansion']['node_limit'], 8000)

    def test_mode_is_explicit(self):
        with self.assertRaises(KeyError): s.discover({'source': []}, 'unknown-mode', Counter())

    def test_small_reuse_matches_previous_engine(self):
        source, proof = independent(); row = {'source': source[1:] + [[-3]]}
        with patch.object(s.previous, 'parent_data', return_value=(source, proof)):
            actual = s.discover(row, 'reuse2000', Counter())
        self.assertEqual(actual, s.e.solve(source, proof, row['source'], node_limit=2000))

    def test_large_reuse_preserves_complete_result(self):
        source, proof = independent(); row = {'source': source[1:] + [[-3]]}
        with patch.object(s.previous, 'parent_data', return_value=(source, proof)):
            a = s.discover(row, 'reuse2000', Counter()); b = s.discover(row, 'reuse8000', Counter())
        assert_prefix(a[0], b[0]); self.assertEqual(a[0], b[0])
        self.assertEqual(b[1]['expansion']['node_limit'], 8000)

    def test_interrupted_prefix_extends(self):
        seed = s.e.baseline.prior.prior.proposal(SQUARE, Counter())
        a = s.e.search(SQUARE, seed, node_limit=2)[0]; b = s.e.search(SQUARE, seed, node_limit=8000)[0]
        self.assertEqual(a['kind'], 'unknown'); self.assertEqual(b['kind'], 'unsat'); assert_prefix(a, b)

    def test_changed_prefix_rejected_by_audit(self):
        with self.assertRaises(AssertionError): assert_prefix({'kind': 'unknown', 'derivations': [[1]]}, {'kind': 'unknown', 'derivations': [[2]]})

    def test_lost_completed_answer_rejected_by_audit(self):
        with self.assertRaises(AssertionError): assert_prefix({'kind': 'sat', 'derivations': []}, {'kind': 'unknown', 'derivations': []})

    def test_old_sat_does_not_authorize_edited_target(self):
        source = [[1]]; proof = s.e.baseline.solve(source)[0]
        with patch.object(s.previous, 'parent_data', return_value=(source, proof)):
            result, _ = s.discover({'source': [[1], [-1]]}, 'reuse8000', Counter())
        self.assertEqual(result['kind'], 'unsat')

    def test_missing_premise_does_not_preserve_refutation(self):
        proof = s.e.baseline.solve(SQUARE)[0]
        with patch.object(s.previous, 'parent_data', return_value=(SQUARE, proof)):
            result, _ = s.discover({'source': SQUARE[:-1]}, 'reuse8000', Counter())
        self.assertEqual(result['kind'], 'sat')

    def test_replay_is_target_only(self):
        proof, _ = s.discover({'source': SQUARE}, 'fresh8000', Counter())
        with patch.object(s.e, 'search', side_effect=AssertionError), patch.object(s.e.selective, 'transport', side_effect=AssertionError):
            self.assertFalse(s.check(SQUARE, proof)['answer'])
