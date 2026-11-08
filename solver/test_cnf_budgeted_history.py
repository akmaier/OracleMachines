"""Budget escalation is bounded discovery, never a relaxation of checking."""
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_budgeted_history import BudgetedRepairHistory
from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_matching_history import MatchingRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.compare_cnf_matching import domain_cnf
from experiments.probe_structured_repair_gaps import source_for
from solver import test_cnf_affected_history as affected_tests


class BudgetedHistoryTests(unittest.TestCase):
    assert_state = affected_tests.AffectedHistoryTests.assert_state

    def test_large_block_retry_preserves_branches_and_charges_failed_work(self):
        source = source_for('equivalence', 1024, 1)
        old = MatchingRepairHistory()
        root = old.prepare(source)['version']
        with self.assertRaises(UnsupportedExpansion):
            old.append_repair(root, [1])
        old.close()
        h = BudgetedRepairHistory()
        root = h.prepare(source)['version']
        result = h.append_repair(root, [1])
        counts = result['metrics']
        self.assertEqual(counts['escalation_repairs'], 1)
        self.assertEqual(counts['escalation_used_visits'], 1024 + 4092)
        self.assertEqual(sum(counts[k] for k in ('candidate_clause_visits',
                         'candidate_joint_variables', 'candidate_joint_postings')), 4096 + 5116)
        self.assertEqual(counts['checked_joint_variables'], 1024)
        self.assertEqual(result['solver_metrics'].get('expanded_nodes', 0), 0)
        self.assert_state(h, root, source)
        self.assert_state(h, result['version'], source + ((1,),))
        branch = h.append_repair(root, [2])
        self.assertEqual(branch['metrics'].get('equivalence_source_literals', 0), 0)
        self.assert_state(h, branch['version'], source + ((2,),))
        self.assertEqual(h.storage()['bases'], 1)
        h.close()

    def test_limits_and_no_partial_database_mutation(self):
        source = source_for('equivalence', 32, 1)
        for options in (dict(escalation_budget=0), dict(escalation_budget=100),
                        dict(max_block_variables=31), dict(max_variable_bits=5),
                        dict(repair_budget=0)):
            h = BudgetedRepairHistory(**(dict(repair_budget=8) | options))
            root = h.prepare(source)['version']
            before = list(h.db.iterdump())
            with self.assertRaises(UnsupportedExpansion):
                h.append_repair(root, [1])
            self.assertEqual(before, list(h.db.iterdump()))
            self.assertLessEqual(h.counts['escalation_used_visits'], h.escalation_budget)
            h.close()
        # A small block with many postings receives only 8*q visits, not 32768.
        h = BudgetedRepairHistory(repair_budget=8)
        root = h.prepare([(-1, 2), (1, -2)] + [(1, -1)] * 100)['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [1])
        self.assertEqual(h.counts['escalation_granted_visits'], 16)
        self.assertEqual(h.counts['escalation_used_visits'], 16)
        h.close()

    def test_old_addition_conflict_is_not_bypassed(self):
        source = source_for('equivalence', 32, 1)
        h = BudgetedRepairHistory(repair_budget=8)
        root = h.prepare(source)['version']
        version = h.append_repair(root, [1])['version']
        before = list(h.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(version, [-1])
        self.assertEqual(h.counts['escalation_failures'], 1)
        self.assertEqual(before, list(h.db.iterdump()))
        self.assert_state(h, version, source + ((1,),))
        h.close()

    def test_no_escalation_for_other_structures_or_completed_rejections(self):
        for source, additions in (
                (domain_cnf([range(3)] * 3), [(2,)]),
                ([(-1, 2), (-2, 3), (-3, 1)], [(1,)]),
                ([], [(-1, 2), (1, -2), (1,)])):
            h = BudgetedRepairHistory(repair_budget=1)
            version = h.prepare(source)['version']
            for clause in additions:
                try:
                    version = h.append_repair(version, clause)['version']
                except UnsupportedExpansion:
                    pass
                self.assertEqual(h.counts['escalation_attempts'], 0)
            h.close()
        # The complete ordinary check rejects an actual conflict; no retry.
        h = BudgetedRepairHistory()
        root = h.prepare([(-1, 2), (1, -2), (-1,)])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [1])
        self.assertEqual(h.counts['escalation_attempts'], 0)
        h.close()

    def test_cold_replay_with_no_discovery_and_older_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'archive.sqlite3'
            h = BudgetedRepairHistory(path, repair_budget=8)
            source = source_for('equivalence', 32, 1)
            root = h.prepare(source)['version']
            version = h.append_repair(root, [1])['version']
            h.close()
            raw = path.read_bytes()
            for cls, options in ((BudgetedRepairHistory, dict(escalation_budget=0)),
                                 (EquivalenceRepairHistory, {})):
                h = cls(path, repair_budget=0, **options)
                self.assert_state(h, version, source + ((1,),))
                self.assert_state(h, root, source)
                self.assertEqual(h.storage()['versions'], 2)
                h.close()
                self.assertEqual(raw, path.read_bytes())
            h = BudgetedRepairHistory(path, repair_budget=8)
            self.assertEqual(h.append_repair(root, [1])['version'], version)
            h.close()
            self.assertEqual(raw, path.read_bytes())

    def test_configuration_and_decision_only(self):
        for name in ('repair_budget', 'escalation_budget', 'max_block_variables', 'max_variable_bits'):
            for value in (-1, True, 1.5):
                with self.assertRaises(ValueError):
                    BudgetedRepairHistory(**{name: value})
        h = BudgetedRepairHistory(repair_budget=1)
        root = h.prepare([(-1, 2), (1, -2)])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_decision(root, [1])
        self.assertEqual(h.counts['escalation_attempts'], 0)
        result = h.append_repair(root, [-1])
        self.assertEqual(result['metrics'].get('escalation_attempts', 0), 0)
        bad = h.prepare([()])['version']
        self.assertFalse(h.append_repair(bad, [1])['answer'])
        h.close()

    def test_branching_histories_keep_exact_counts_after_escalation(self):
        rng = random.Random(82519)
        h = BudgetedRepairHistory(repair_budget=1)
        source = source_for('equivalence', 4, 3)
        root = h.prepare(source)['version']
        histories = [(root, source)]
        accepted = 0
        for _ in range(120):
            parent, old_source = rng.choice(histories)
            clause = tuple(rng.choice((-1, 1))*rng.randrange(1, 13)
                           for _ in range(rng.randrange(1, 4)))
            try:
                result = h.append_repair(parent, clause)
            except UnsupportedExpansion:
                continue
            accepted += result['metrics'].get('escalation_repairs', 0)
            new_source = old_source + (clause,)
            self.assert_state(h, result['version'], new_source)
            self.assert_state(h, parent, old_source)
            histories.append((result['version'], new_source))
        self.assertGreater(accepted, 10)
        h.close()


if __name__ == '__main__':
    unittest.main()
