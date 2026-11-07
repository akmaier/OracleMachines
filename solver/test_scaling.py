"""Independent semantic and persistence checks for structural optimizations."""
import itertools
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solver.persistent import PersistentSolver
from solver.resources import Deadline, BudgetExceeded
from solver.symbolic import BDD
from solver.test_fast import cnf_bits
from solver.test_interfaces import var, neg, disj, xor, chain
from solver.test_fast import HARD_UNSAT, MIXED, conj


class SymbolicTests(unittest.TestCase):
    def test_apply_restrict_project_against_truth_tables(self):
        from solver.incremental import parse_postfix
        rng = random.Random(619)
        for _ in range(45):
            clauses = [[(v, bool(rng.randrange(2))) for v in rng.sample(range(5), 3)]
                       for _ in range(12)]
            manager = BDD()
            manager.begin(Deadline(3))
            root = manager.formula(parse_postfix(cnf_bits(clauses), Deadline(3))[0])
            restored = BDD()
            imported = restored.restore(manager.dump(root))
            for values in itertools.product((False, True), repeat=5):
                assignment = dict(enumerate(values))
                expected = all(any(values[v] == b for v, b in c) for c in clauses)
                self.assertEqual(manager.evaluate(root, assignment), expected)
                self.assertEqual(restored.evaluate(imported, assignment), expected)
                for v in range(5):
                    projected = manager.exists(root, v)
                    possible = any(all(any((b if u == v else values[u]) == sign for u, sign in c)
                                       for c in clauses) for b in (False, True))
                    self.assertEqual(manager.evaluate(projected, assignment), possible)

    def test_large_parity_is_built_without_rows(self):
        b = BDD()
        root = 0
        for v in range(80):
            atom = b.node(v, 0, 1)
            root = b.apply('or', b.apply('and', root, b.negate(atom)),
                           b.apply('and', b.negate(root), atom))
        self.assertLess(len(b.dump(root)['nodes']), 160)
        self.assertEqual(b.exists(root, 30), 1)
        self.assertTrue(b.evaluate(root, {v: v == 50 for v in range(80)}))

    def test_caps_and_forged_order_are_rejected(self):
        b = BDD(max_nodes=1)
        b.node(0, 0, 1)
        with self.assertRaises(BudgetExceeded):b.node(1, 0, 1)
        with self.assertRaises(ValueError):
            BDD().restore(dict(version=1, root=3, nodes=[[0, 0, 1], [1, 0, 2]]))


class ScalingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'results.sqlite3'

    def tearDown(self):
        self.temp.cleanup()

    def test_local_planning_and_restart_branch_history(self):
        with PersistentSolver(self.path, interfaces=True) as s:
            first = s.expand(add={'chain':chain(24), 'start':var(0), 'end':var(24)})
            edited = s.expand(first['state'], add={'end':neg(var(24))})
            self.assertFalse(edited['answer'])
            self.assertLessEqual(edited['interfaces']['affected_buckets'], 2)
            self.assertGreaterEqual(edited['interfaces']['reused_buckets'], 23)
            self.assertEqual(edited['interfaces']['planned_buckets'], 0)
        with PersistentSolver(self.path, interfaces=True) as s:
            branch = s.expand(first['state'], add={'extension':xor(24, 25)})
            self.assertTrue(branch['answer'])
            self.assertTrue(s.expand(first['state'])['answer'])
            self.assertFalse(s.expand(edited['state'])['answer'])

    def test_random_edits_and_new_variables_match_exhaustive(self):
        rng = random.Random(207)
        with PersistentSolver(self.path, symbolic=True, max_interface=5) as s:
            active = {}
            state = None
            for _ in range(65):
                key = str(rng.randrange(9))
                add, remove = {}, []
                if key in active and rng.randrange(3) == 0:
                    del active[key]
                    remove = [key]
                else:
                    clause = [(v, bool(rng.randrange(2))) for v in rng.sample(range(5), 3)]
                    active[key] = clause
                    add[key] = cnf_bits([clause])
                expected = any(all(any(a[v] == b for v, b in c) for c in active.values())
                               for a in itertools.product((False, True), repeat=5))
                result = s.expand(state, add=add, remove=remove)
                self.assertEqual(result['answer'], expected)
                state = result['state']

    def test_symbolic_proposals_are_checked_and_archived(self):
        with PersistentSolver(self.path, symbolic=True) as s:
            first = s.expand(add={'chain':chain(10), 'start':var(0), 'end':neg(var(10))})
            self.assertFalse(first['answer'])
            self.assertGreater(first['interfaces']['symbolic_rows'], 0)
            self.assertEqual(first['interfaces']['leaf_rows'], 0)
            self.assertGreater(first['interfaces']['native_row_acquisitions'], 0)
        with PersistentSolver(self.path, symbolic=True) as s:
            second = s.expand(first['state'], remove=['end'])
            self.assertTrue(second['answer'])
            self.assertGreater(second['interfaces']['symbolic_replays'], 0)

    def test_poisoned_symbolic_proposal_cannot_change_verdict(self):
        with PersistentSolver(self.path, symbolic=True) as s:
            first = s.expand(add={'x':var(0)})
            with s.db:
                wrong = s.interfaces.store.put('symbolic_relation',dict(version=1,root=0,nodes=[]))[0]
                s.db.execute('UPDATE interface_symbolic SET object_id=?',(wrong,))
                s.db.execute('DELETE FROM interface_rows')
                # The original known rows remain checked evidence. Force a new
                # factor that depends on the poisoned symbolic leaf instead.
        with PersistentSolver(self.path, symbolic=True) as s:
            with self.assertRaises(ValueError):
                s.expand(first['state'], add={'new':disj(var(0),var(1))})

    def test_symbolic_node_cap_uses_checked_lazy_fallback(self):
        with PersistentSolver(self.path, symbolic=True) as s:
            s.interfaces.bdd.max_nodes = 1
            result = s.expand(add={'c':disj(var(0),var(1))})
            self.assertTrue(result['answer'])
            self.assertGreater(result['interfaces']['symbolic_fallbacks'],0)

    def test_verified_core_reuses_live_state_and_revalidates_after_restart(self):
        with PersistentSolver(self.path, backend='cadical', incremental_proofs=True) as s:
            first = s.solve(HARD_UNSAT, learn=False)
            self.assertEqual(first['incremental']['history_recompiled'], 0)
            with patch.object(s.incremental, 'propose', side_effect=AssertionError('Fresh proposal')):
                second = s.solve(conj(HARD_UNSAT, MIXED), learn=False)
            self.assertFalse(second['answer'])
            self.assertEqual(second['backend'], 'incremental_core')
            self.assertFalse(second['incremental']['core_revalidated'])
        with PersistentSolver(self.path, backend='cadical', incremental_proofs=True) as s:
            with patch.object(s.incremental, 'propose', side_effect=AssertionError('Fresh proposal')):
                third = s.solve(conj(HARD_UNSAT, var(8)), learn=False)
            self.assertFalse(third['answer'])
            self.assertTrue(third['incremental']['core_revalidated'])
            self.assertTrue(s.solve(MIXED, learn=False)['answer'])
            self.assertEqual(s.audit()['checked'], 4)

    def test_adaptive_routing_persists_measurements_and_charges_overhead(self):
        with PersistentSolver(self.path, adaptive=True, reuse_exact=False) as s:
            routes = []
            for _ in range(5):
                result = s.solve(MIXED, learn=False)
                self.assertTrue(result['answer'])
                self.assertEqual(sum(result['phase_ns'].values()), result['wall_ns'])
                self.assertIn('routing_selection', result['phase_ns'])
                self.assertIn('routing_observation', result['phase_ns'])
                routes.append(result['routing']['route'])
            self.assertEqual(routes[:2], ['checked', 'interfaces'])
        with PersistentSolver(self.path, adaptive=True, reuse_exact=False) as s:
            result = s.solve(MIXED, learn=False)
            self.assertEqual(result['routing']['observations'], 5)
            self.assertEqual(s.db.execute('SELECT count(*) FROM route_observations').fetchone()[0],6)

    def test_archive_cap_preserves_history_and_never_means_unsat(self):
        with PersistentSolver(self.path) as s:
            s.solve(MIXED, learn=False)
            before = [tuple(r) for r in s.db.execute('SELECT * FROM results')]
            cap = s.archive_usage()['logical_database_bytes'] + 4096
        with PersistentSolver(self.path, max_archive_bytes=cap) as s:
            with self.assertRaises(BudgetExceeded):s.solve(var(12000), learn=False)
            self.assertEqual([tuple(r) for r in s.db.execute('SELECT * FROM results')], before)
            self.assertTrue(s.solve(MIXED, learn=False)['answer'])
            self.assertLessEqual(s.archive_usage()['logical_database_bytes'], cap)
            self.assertFalse(s.archive_usage()['physical_storage_hard_bound'])
        with self.assertRaises(ValueError):PersistentSolver(self.path, max_archive_bytes=4096)
        with PersistentSolver(self.path) as s:self.assertEqual(s.audit()['checked'],1)


if __name__ == '__main__':unittest.main()
