import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted, BudgetedInventory
from solver.test_cnf_fused_conditioning import mixed_source


def rows(h):
    return dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'))


class CompleteAdmissionTests(unittest.TestCase):
    def test_both_entrances_require_budget_before_recognition(self):
        h = CompleteAdmissionInventory()
        try:
            with self.assertRaises(ValueError):
                h._conditioning_edge(((1, 2),), 1, False, 0)
            for bad in (-1, True, 1.5):
                with self.assertRaises(ValueError):
                    h.set_admission_budget(bad)
            h.set_admission_budget(0)
            with patch.object(h, '_profile', side_effect=AssertionError('acquisition')):
                with self.assertRaises(AdmissionExhausted):
                    h._edge(((1, 2),), 0)
                with self.assertRaises(AdmissionExhausted):
                    h._conditioning_edge(((1, 2),), 1, False, 0)
            self.assertFalse(rows(h))
            self.assertEqual(h.admission_counts['denied_states'], 2)
        finally:
            h.close()

    def test_transient_simplification_is_charged_before_child(self):
        h = CompleteAdmissionInventory(max_depth=0)
        try:
            # A connected, nonterminal restriction exposes a unit. Its profile
            # is computed, but only its simplified descendant is persisted.
            source = mixed_source() + [(1, 6)]
            h.set_admission_budget(1)
            with self.assertRaises(AdmissionExhausted):
                h._conditioning_edge(source, 6, False, 0)
            self.assertEqual(len(h.admitted), 1)
            self.assertEqual(h.admission_counts['entered_fused_profile'], 1)
            self.assertFalse(rows(h))
            h.set_admission_budget(2)
            edge = h._conditioning_edge(source, 6, False, 0)
            self.assertIn('closure', edge)
            self.assertEqual(len(h.admitted), 2)
            self.assertEqual(len(rows(h)), 1)
            self.assertTrue(set(rows(h)) <= h.admitted)
            # Independent verification reconstructs profiles. It is not fresh
            # acquisition and must still work with a zero acquisition budget.
            h.set_admission_budget(0)
            with patch.object(h, '_admit', side_effect=AssertionError('acquisition')):
                h._check_conditioning_edge(edge, source, 6, False, 0)
        finally:
            h.close()

    def test_direct_profile_recording_and_reentry_are_charged(self):
        h = CompleteAdmissionInventory(max_depth=0)
        try:
            h.set_admission_budget(1)
            edge = h._conditioning_edge(((1, 2, 3),), 1, False, 0)
            self.assertNotIn('closure', edge)
            self.assertEqual(h.admission_counts['entered_fused_profile'], 1)
            self.assertEqual(set(rows(h)), h.admitted)
            h._admit(edge['key'], 'discover')
            self.assertEqual(len(h.admitted), 1)
            self.assertEqual(h.admission_counts['reentered_states'], 1)
            h.set_admission_budget(0)
            self.assertEqual(h._conditioning_edge(((1, 2, 3),), 1, False, 0), edge)
            self.assertFalse(h.admitted)
            with self.assertRaises(ValueError):
                h._record_node('not-admitted', {})
        finally:
            h.close()

    def test_restart_preserves_rows_and_zero_budget_cold_replay(self):
        source = ((1, 2), (3, 4, 5))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'history'
            h = CompleteAdmissionInventory(path, max_depth=0)
            try:
                h.set_admission_budget(2)
                with self.assertRaises(AdmissionExhausted):
                    h.inspect(source)
                saved = rows(h)
                self.assertEqual(len(saved), 1)
            finally:
                h.close()
            h = CompleteAdmissionInventory(path, max_depth=0)
            try:
                h.set_admission_budget(2)
                root = h.inspect(source)['root']
                self.assertTrue(saved.items() <= rows(h).items())
            finally:
                h.close()
            h = CompleteAdmissionInventory(path, max_depth=0)
            try:
                h.set_admission_budget(0)
                with patch.object(h, '_admit', side_effect=AssertionError('acquisition')):
                    self.assertTrue(h._load(root['key'])['summary']['closed'])
            finally:
                h.close()

    def test_exhaustive_small_graph_compatibility(self):
        clauses = [tuple(s * (i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        old = BudgetedInventory(max_depth=1)
        new = CompleteAdmissionInventory(max_depth=1)
        try:
            for mask in range(1 << len(clauses)):
                source = tuple(c for i, c in enumerate(clauses) if mask >> i & 1)
                old.set_admission_budget(200)
                new.set_admission_budget(200)
                self.assertEqual(old.inspect(source)['root'], new.inspect(source)['root'])
            self.assertEqual(rows(old), rows(new))
        finally:
            old.close()
            new.close()


if __name__ == '__main__':
    unittest.main()
