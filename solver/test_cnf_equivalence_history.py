"""Joint repair checks final states, all older clauses, counts and cold archives."""
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_residual_dag import holds
from solver import test_cnf_affected_history as affected_tests


class EquivalenceHistoryTests(unittest.TestCase):
    assert_state = affected_tests.AffectedHistoryTests.assert_state

    def test_transitive_signed_blocks_counts_and_no_warm_source_scan(self):
        h = EquivalenceRepairHistory()
        # x1=x2, x2!=x3, with duplicates and a tautology.
        source = [(-1, 2, 2), (1, -2), (2, 3), (-2, -3), (1, -1, -1)]
        root = h.prepare(source)['version']
        self.assertFalse(h.equivalence_blocks)
        model = h.witness(root)['model']
        lit = -1 if model.get(1, False) else 1
        result = h.append_repair(root, [lit])
        self.assertEqual(result['metrics']['verified_joint_repairs'], 1)
        self.assertEqual(result['metrics']['equivalence_index_builds'], 1)
        self.assertEqual(result['metrics'].get('changed_joint_clause_counts', 0), 0)
        self.assertEqual(result['solver_metrics'].get('expanded_nodes', 0), 0)
        self.assert_state(h, result['version'], source + [(lit,)])
        self.assert_state(h, root, source)
        # A distinct branch reuses the already discovered base blocks.
        branch = h.append_repair(root, [lit, lit])
        self.assertEqual(branch['metrics'].get('equivalence_source_literals', 0), 0)
        self.assert_state(h, branch['version'], source + [(lit, lit)])
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(result['version'], [-lit])
        self.assertEqual(h.storage()['bases'], 1)
        h.close()

    def test_couplings_repeated_changes_and_earlier_additions(self):
        h = EquivalenceRepairHistory()
        source = [(-1, 2), (1, -2), (-3, 4), (3, -4)]
        root = version = h.prepare(source)['version']
        self.assertFalse(h.witness(root)['model'].get(1, False))
        versions = [(root, list(source))]
        for clause in [(1, 3), (-1, 3), (-1,)]:
            result = h.append_repair(version, clause)
            self.assertEqual(result['metrics']['verified_joint_repairs'], 1)
            version = result['version']
            source.append(clause)
            versions.append((version, list(source)))
            self.assert_state(h, version, source)
        for v, src in versions:
            self.assert_state(h, v, src)
        before = list(h.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(version, [-3])
        self.assertEqual(before, list(h.db.iterdump()))
        # A base coupling also blocks a proposed equivalence flip.
        blocked = h.prepare([(-1, 2), (1, -2), (1, 3), (-3,)])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(blocked, [-1])
        h.close()

    def test_explicit_discovery_limits_budgets_and_unsat(self):
        h = EquivalenceRepairHistory(repair_budget=1)
        root = h.prepare([(-1, 2), (1, -2)])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [1])
        self.assertGreater(h.counts['repair_budget_exhaustions'], 0)
        h.close()
        h = EquivalenceRepairHistory()
        root = h.prepare([])['version']
        for clause in [(-1, 2), (1, -2)]:
            root = h.append_repair(root, clause)['version']
        # Equivalences acquired only through deltas are not indexed yet.
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [1])
        cycle = [(-1, 2), (-2, 3), (-3, 1)]
        root = h.prepare(cycle)['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [1])
        bad = h.prepare([()])['version']
        result = h.append_repair(bad, [])
        self.assertFalse(result['answer'])
        self.assertIsNone(h.states[result['version']])
        self.assertFalse(h.equivalence_blocks[h.checked[root][0]])
        h.close()

    def test_reference_coverage_random_branches_and_exact_counts(self):
        rng = random.Random(70321)
        h = EquivalenceRepairHistory(repair_budget=100000)
        sources = [[(-1, 2), (1, -2), (3, 4), (-3, -4)],
                   [(-1, 2), (1, -2), (1, 3), (-2, 3, 4)],
                   [(-1, 2), (1, -2), (1, -1), (-3, 4), (3, -4)]]
        versions = [h.prepare(source)['version'] for source in sources]
        clauses = [list(c) for width in range(4)
                   for c in itertools.combinations((-4, -3, -2, -1, 1, 2, 3, 4), width)]
        for _ in range(500):
            parent, clause = rng.choice(versions), rng.choice(clauses)
            source, model = h.materialize(parent)['cnf'], h.witness(parent)['model']
            base_id = h.checked[parent][0]
            blocks = h._blocks(base_id)
            moves = [{abs(lit)} for lit in clause] + [set(blocks[abs(lit)]) for lit in clause if abs(lit) in blocks]
            can_accept = holds([clause], model) or any(
                holds(source + (tuple(clause),), {**model, **{v: not model.get(v, False) for v in move}})
                for move in moves)
            before = list(h.db.iterdump())
            try:
                result = h.append_repair(parent, clause)
            except UnsupportedExpansion:
                self.assertFalse(can_accept)
                self.assertEqual(before, list(h.db.iterdump()))
                continue
            self.assertTrue(can_accept)
            versions.append(result['version'])
            self.assert_state(h, result['version'], source + (tuple(clause),))
            self.assert_state(h, parent, source)
        h.close()

    def test_cold_legacy_and_independent_joint_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.sqlite3'
            old = AffectedRepairHistory(path)
            source = [(-1, 2), (1, -2)]
            root = old.prepare(source)['version']
            parent = old.append_repair(root, [-10])['version']
            source.append((-10,))
            old.close()
            h = EquivalenceRepairHistory(path)
            version = h.append_repair(parent, [1])['version']
            source.append((1,))
            version = h.append_decision(version, [2, 11])['version']
            source.append((2, 11))
            self.assert_state(h, version, source)
            before = list(h.db.iterdump())
            h.close()
            h = EquivalenceRepairHistory(path, repair_budget=0)
            self.assertTrue(h.query(version)['answer'])
            self.assertFalse(h.equivalence_blocks)  # recognition not trusted/repeated on cold replay
            self.assert_state(h, version, source)
            self.assertEqual(before, list(h.db.iterdump()))
            h.close()
            old = AffectedRepairHistory(path)
            self.assertTrue(old.query(parent)['answer'])
            with self.assertRaises(ValueError):
                old.query(version)
            old.close()

    def test_forged_joint_records_fail_cold(self):
        for mutation in ('missing', 'bool', 'negative', 'zero', 'duplicate', 'unordered',
                         'wrong_clause', 'extra_key', 'parent_unit', 'cycle', 'cross_base'):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'history.sqlite3'
                h = EquivalenceRepairHistory(path)
                root = h.prepare([(-1, 2), (1, -2)])['version']
                blocked = h.append_repair(root, [-1])['version']
                child = h.append_repair(root, [1])['version']
                other = h.prepare([(5,)])['version']
                payload = dict(kind='append-joint', clause=[1], variables=[1, 2])
                with h.db:
                    if mutation in ('parent_unit', 'cycle', 'cross_base'):
                        target = dict(parent_unit=blocked, cycle=child, cross_base=other)[mutation]
                        h.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (target, child))
                    else:
                        replacements = dict(missing=[1, 3], bool=[True, 2], negative=[-1, 2], zero=[0, 2],
                                            duplicate=[1, 1, 2], unordered=[2, 1])
                        if mutation in replacements: payload['variables'] = replacements[mutation]
                        if mutation == 'wrong_clause': payload['clause'] = [-1]
                        if mutation == 'extra_key': payload['trusted'] = True
                        h.db.execute('UPDATE cnf_positive_versions_v1 SET payload=? WHERE id=?', (json.dumps(payload), child))
                h.close()
                h = EquivalenceRepairHistory(path)
                with self.assertRaises(ValueError, msg=mutation):
                    h.query(child)
                h.close()


if __name__ == '__main__':
    unittest.main()
