"""Alternating repair, persistent matching views, and full-source protection."""
from collections import Counter
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_matching_history import MatchingRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_repair_history import map_get
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_matching import domain_cnf
from experiments.probe_structured_repair_gaps import source_for, supplied_move
from solver import test_cnf_affected_history as affected_tests


class MatchingHistoryTests(unittest.TestCase):
    def assert_state(self, h, version, source):
        affected_tests.AffectedHistoryTests.assert_state(self, h, version, source)
        if version not in h.matching_states:
            return
        lefts, rights, pins = h.matching_states[version]
        structure = h.matching_structures[h.checked[version][0]]
        model = h.witness(version)['model']
        expected_left, expected_right = {}, {}
        for var, (left, right) in structure['edges'].items():
            if model.get(var, False):
                expected_left.setdefault(left, []).append(var)
                expected_right.setdefault(right, []).append(var)
        if lefts is not None:
            for left in structure['adjacency']:
                self.assertEqual(expected_left.get(left, []), [map_get(lefts, left, Counter())])
            for _, right in structure['edges'].values():
                self.assertEqual(expected_right.get(right, []),
                                 [map_get(rights, right, Counter())] if map_get(rights, right, Counter()) else [])
        unit_vars = {abs(c[0]) for c in source if len(set(c)) == 1}
        for var in structure['edges']:
            self.assertEqual(bool(map_get(pins, var, Counter())), var in unit_vars)

    def test_disjoint_blocks_reuse_warm_state_and_older_branches(self):
        h = MatchingRepairHistory()
        source = source_for('matching', 4, 8)
        root = version = h.prepare(source)['version']
        old = [(root, source)]
        for block in range(8):
            clause, _ = supplied_move('matching', 4, block, h.witness(version)['model'])
            result = h.append_repair(version, clause)
            self.assertEqual(result['metrics']['matching_repairs'], 1)
            self.assertEqual(result['metrics'].get('matching_structure_builds', 0), int(block == 0))
            if block:
                self.assertEqual(result['metrics'].get('matching_model_entries', 0), 0)
                self.assertEqual(result['metrics'].get('matching_history_visits', 0), 0)
                self.assertEqual(result['metrics'].get('matching_source_literals', 0), 0)
            version, source = result['version'], source + (clause,)
            self.assert_state(h, version, source)
            old.append((version, source))
        branch = h.append_repair(root, [-1])['version']
        self.assert_state(h, branch, old[0][1] + ((-1,),))
        for v, s in old:
            self.assert_state(h, v, s)
        self.assertEqual(h.storage()['bases'], 1)
        h.close()

    def test_long_alternating_cycle_and_spare_resource(self):
        h = MatchingRepairHistory()
        n = 12
        source = domain_cnf([[i, (i+1) % n] for i in range(n)])
        parent = h.prepare(source)['version']
        model = h.witness(parent)['model']
        lit = next(v for v in (1, 2) if not model.get(v, False))
        result = h.append_repair(parent, [lit])
        self.assertEqual(result['metrics']['matching_path_choices'], n)
        self.assertEqual(result['metrics']['checked_joint_variables'], 2*n)
        self.assert_state(h, result['version'], source + [(lit,)])
        # A negative request vacates an edge and reaches a genuinely free right.
        source = domain_cnf([[0, 1], [1, 2]])
        parent = h.prepare(source)['version']
        model = h.witness(parent)['model']
        lit = -next(v for v in (1, 2) if model.get(v, False))
        result = h.append_repair(parent, [lit])
        self.assertEqual(result['metrics']['matching_repairs'], 1)
        self.assert_state(h, result['version'], source + [(lit,)])
        h.close()

    def test_unit_pins_guide_paths_and_nonunit_couplings_are_checked(self):
        h = MatchingRepairHistory()
        source = domain_cnf([range(3)]*3)
        root = h.prepare(source)['version']
        self.assertEqual(set(h.witness(root)['model']), {1, 5, 9})
        # Forbid the shortest swap. Unit guidance finds the longer 3-cycle.
        parent = h.append_repair(root, [-4, -4])['version']
        result = h.append_repair(parent, [2])
        self.assertEqual(result['metrics']['matching_path_choices'], 3)
        self.assert_state(h, result['version'], source + [(-4, -4), (2,)])
        pinned = h.append_repair(root, [5])['version']
        before = list(h.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(pinned, [2])
        self.assertEqual(before, list(h.db.iterdump()))
        # The equivalent conditional prohibition is not propagated by search.
        # The independent checker rejects the chosen swap; a longer path works.
        parent = h.append_repair(root, [-2, -4])['version']
        alternative = {2: True, 6: True, 7: True}
        self.assertTrue(holds(source + [(-2, -4), (2,)], alternative))
        before = list(h.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(parent, [2])
        self.assertEqual(h.counts['matching_rejected_paths'], 1)
        self.assertEqual(before, list(h.db.iterdump()))
        h.close()

    def test_unit_histories_against_all_permutation_models(self):
        rng = random.Random(9814)
        h = MatchingRepairHistory(repair_budget=100000)
        source = tuple(map(tuple, domain_cnf([range(3)]*3)))
        root = h.prepare(source)['version']
        versions = [(root, source)]
        models = [{1+row*3+col: True for row, col in enumerate(p)}
                  for p in itertools.permutations(range(3))]
        for _ in range(400):
            parent, old = rng.choice(versions)
            clause = (rng.choice((-1, 1))*rng.randint(1, 9),)
            new = old + (clause,)
            feasible = any(holds(new, model) for model in models)
            before = list(h.db.iterdump())
            try:
                result = h.append_repair(parent, clause)
            except UnsupportedExpansion:
                self.assertFalse(feasible)
                self.assertEqual(before, list(h.db.iterdump()))
                continue
            self.assertTrue(feasible)
            versions.append((result['version'], new))
            self.assert_state(h, result['version'], new)
            self.assert_state(h, parent, old)
        h.close()

    def test_budget_recognition_and_invalid_matching_views(self):
        h = MatchingRepairHistory(repair_budget=2)
        root = h.prepare(domain_cnf([range(4)]*4))['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(root, [2])
        h.close()
        h = MatchingRepairHistory()
        for source in ([(1, 2), (2, 3)], [(1, 2, 3), (-1, -2), (-2, -3)],
                       [(1, 2), (-1, -2)], [(1,), (-2, -3)]):
            version = h.prepare(source)['version']
            self.assertIsNone(h._matching_structure(h.checked[version][0]))
        # Duplicates and tautologies are normalized only for discovery.
        source = domain_cnf([range(3)]*3) + [(1, 2, 3), (99, -99)]
        root = h.prepare(source)['version']
        result = h.append_repair(root, [2])
        self.assert_state(h, result['version'], source + [(2,)])
        # With spare resources, valid SAT models need not be exact matchings.
        source = domain_cnf([[0, 1], [1, 2]])
        root = h.prepare(source)['version']
        structure = h._matching_structure(h.checked[root][0])
        h._matching_state(root, structure)
        child = h.append_repair(root, [1])['version']  # scalar adds a second true choice
        self.assertIsNone(h.matching_states[child][0])
        self.assert_state(h, child, source + [(1,)])
        # Keeping a pinned extra choice may require a model outside the
        # one-selected-edge view. It remains SAT, but this adapter rejects.
        self.assertTrue(holds(source + [(1,), (3,)], {1: True, 3: True, 4: True}))
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(child, [3])
        # A cold/lazy derivation can recover a later exact matching view.
        later = h.append_repair(child, [-2])['version']
        h.matching_states.clear()
        self.assertIsNotNone(h._matching_state(later, structure)[0])
        self.assert_state(h, later, source + [(1,), (-2,)])
        bad = h.prepare([()])['version']
        self.assertFalse(h.append_repair(bad, [])['answer'])
        h.close()

    def test_cold_replay_legacy_reader_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'matching.sqlite3'
            h = MatchingRepairHistory(path)
            source = source_for('matching', 4, 8)
            root = version = h.prepare(source)['version']
            versions = [(root, source)]
            for block in range(8):
                clause, _ = supplied_move('matching', 4, block, h.witness(version)['model'])
                version = h.append_repair(version, clause)['version']
                source += (clause,)
                versions.append((version, source))
            before = list(h.db.iterdump())
            h.close()
            # Same generic joint format: the preceding reader checks all moves.
            old = EquivalenceRepairHistory(path, repair_budget=0)
            self.assertTrue(old.query(version)['answer'])
            self.assertTrue(holds(source, old.witness(version)['model']))
            old.close()
            h = MatchingRepairHistory(path, repair_budget=0)
            for v, s in versions:
                self.assertTrue(h.query(v)['answer'])
                self.assert_state(h, v, s)
            self.assertFalse(h.matching_structures)
            self.assertEqual(before, list(h.db.iterdump()))
            h.close()
            h = MatchingRepairHistory(path)
            result = h.append_repair(versions[-2][0], source[-1])
            self.assertEqual(result['version'], version)
            self.assertEqual(result['metrics']['matching_structure_builds'], 1)
            self.assertEqual(result['solver_metrics'].get('expanded_nodes', 0), 0)
            self.assertEqual(before, list(h.db.iterdump()))
            h.close()


if __name__ == '__main__':
    unittest.main()
