"""Persistent pure-literal repair: source support, branching and independent replay."""
from collections import Counter
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_positive_history import PositiveHistory, UnsupportedExpansion
from experiments.cnf_repair_history import RepairHistory, map_get, map_set
from experiments.cnf_residual_dag import holds


class RepairHistoryTests(unittest.TestCase):
    def test_persistent_trie_sparse_keys_and_unchanged_roots(self):
        counts, root, saved = Counter(), None, []
        keys = [1, 2, 3, 4, 5, 2**1200 + 123, 10**20, 99999]
        for i, key in enumerate(keys):
            saved.append(root)
            root = map_set(root, key, i + 1, counts)
            self.assertEqual(map_get(root, key, counts), i + 1)
            self.assertEqual(map_get(saved[-1], key, counts), 0)
            self.assertIs(map_set(root, key, i + 1, counts), root)
        for i, key in enumerate(keys):
            self.assertEqual(map_get(root, key, counts), i + 1)
        self.assertEqual(map_get(root, 100000, counts), 0)

    def test_fresh_units_and_cold_repair_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'repair.sqlite3'
            history = RepairHistory(path)
            root = history.prepare([(1, 2)])['version']
            version, source = root, [(1, 2)]
            for i in range(128):
                clause = (10000 + i,)
                result = history.append_repair(version, clause)
                self.assertEqual(result['metrics']['verified_repairs'], 1)
                self.assertEqual(result['metrics']['support_literal_visits'], 1)
                self.assertEqual(result['solver_metrics'], {})
                version = result['version']
                source.append(clause)
            self.assertEqual(history.storage()['bases'], 1)
            self.assertEqual(history.materialize(version)['cnf'], tuple(source))
            self.assertTrue(holds(source, history.witness(version)['model']))
            self.assertFalse(history.witness(root)['model'].get(10000, False))
            before = list(history.db.iterdump())
            history.close()
            history = RepairHistory(path)
            result = history.query(version)
            self.assertTrue(result['answer'])
            self.assertEqual(result['metrics']['verified_repairs'], 128)
            self.assertTrue(holds(source, history.witness(version)['model']))
            self.assertEqual(before, list(history.db.iterdump()))
            history.close()

    def test_prior_deltas_and_tautologies_prevent_false_freshness(self):
        history = RepairHistory()
        root = history.prepare([(1,)])['version']
        parent = history.append_repair(root, [-10])['version']
        before = list(history.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            history.append_repair(parent, [10])
        self.assertEqual(before, list(history.db.iterdump()))
        # Same edit on a different branch is safe; no support leaks between forks.
        child = history.append_repair(root, [10])['version']
        self.assertTrue(history.witness(child)['model'][10])
        self.assertFalse(history.witness(parent)['model'].get(10, False))
        taut = history.append_repair(root, [11, -11])['version']
        with self.assertRaises(UnsupportedExpansion):
            history.append_repair(taut, [11])
        # Conservative purity rejection can miss a valid SAT repair.
        self.assertTrue(history.prepare([(1,), (11, -11), (11,)])['answer'])
        history.close()

    def test_pure_existing_literal_and_mixed_operations(self):
        history = RepairHistory()
        root = history.prepare([(1,), (1, 2)])['version']
        # Force a pure but currently false variable; use current witness if solver
        # happens to choose true for an unconstrained variable in a future engine.
        model = history.witness(root)['model']
        if not model.get(2, False):
            changed = history.append_repair(root, [2])
            self.assertEqual(changed['metrics']['verified_repairs'], 1)
        else:
            changed = history.append_repair(root, [3])
        version = changed['version']
        legacy = history.append(version, [1, 9])['version']
        same = history.append_repair(legacy, [9])['version']
        self.assertEqual(same, history.append_repair(legacy, [9])['version'])
        self.assertTrue(holds(history.materialize(same)['cnf'], history.witness(same)['model']))
        with self.assertRaises(UnsupportedExpansion):
            history.append_decision(same, [-9])
        self.assertTrue(history.query(root)['answer'])
        history.close()

    def test_exhaustive_small_repair_answers_and_forks(self):
        literals = (1, -1, 2, -2, 3, -3)
        clauses = [c for n in range(4) for c in itertools.combinations(literals, n)]
        history = RepairHistory()
        roots = [history.prepare(b)['version'] for b in ([], [(1, 2)], [(1,), (-1,)], [(1, -1)])]
        for parent in roots:
            for clause in clauses:
                source = history.materialize(parent)['cnf'] + (clause,)
                try:
                    result = history.append_repair(parent, clause)
                except UnsupportedExpansion:
                    continue
                actual = any(holds(source, dict(zip((1, 2, 3), values)))
                             for values in itertools.product((False, True), repeat=3))
                self.assertEqual(result['answer'], actual)
                if actual:
                    self.assertTrue(holds(source, history.witness(result['version'])['model']))
        # Long randomized branches test support/assignment sharing and SAT failures.
        rng = random.Random(451)
        for _ in range(300):
            parent = rng.choice(roots)
            clause = rng.choice(clauses)
            source = history.materialize(parent)['cnf'] + (clause,)
            try:
                result = history.append_repair(parent, clause)
            except UnsupportedExpansion:
                continue
            roots.append(result['version'])
            if result['answer']:
                self.assertTrue(holds(source, history.witness(result['version'])['model']))
            else:
                self.assertFalse(any(holds(source, dict(zip((1, 2, 3), values)))
                                     for values in itertools.product((False, True), repeat=3)))
        history.close()

    def test_bad_inputs_and_cold_repair_forgery(self):
        for mutation in ('opposite', 'missing_literal', 'invalid_tail', 'bool_repair', 'cross_base', 'cycle', 'base_tautology'):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'repair.sqlite3'
                history = RepairHistory(path)
                root = history.prepare([(1,)])['version']
                opposite = history.append_repair(root, [-10])['version']
                other = history.prepare([(2,)])['version']
                version = history.append_repair(root, [10])['version']
                for clause in ([10, 0], [10, True], [10, 1.5], None):
                    before = list(history.db.iterdump())
                    with self.assertRaises(ValueError):
                        history.append_repair(version, clause)
                    self.assertEqual(before, list(history.db.iterdump()))
                payload = json.loads(history.db.execute('SELECT payload FROM cnf_positive_versions_v1 WHERE id=?', (version,)).fetchone()[0])
                with history.db:
                    if mutation == 'opposite':
                        history.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (opposite, version))
                    elif mutation == 'cross_base':
                        history.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (other, version))
                    elif mutation == 'cycle':
                        history.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (version, version))
                    elif mutation == 'base_tautology':
                        base_id = history.checked[root][0]
                        base = json.loads(history.db.execute('SELECT payload FROM cnf_positive_bases_v1 WHERE id=?', (base_id,)).fetchone()[0])
                        base['source'].append([10, -10])  # canonical root unchanged, but exact support changes
                        history.db.execute('UPDATE cnf_positive_bases_v1 SET payload=? WHERE id=?', (json.dumps(base), base_id))
                    else:
                        if mutation == 'missing_literal':
                            payload['repair'] = 11
                        elif mutation == 'invalid_tail':
                            payload['clause'] = [10, 0]
                        else:
                            payload['repair'] = True
                        history.db.execute('UPDATE cnf_positive_versions_v1 SET payload=? WHERE id=?', (json.dumps(payload), version))
                history.close()
                history = RepairHistory(path)
                with self.assertRaises(ValueError, msg=mutation):
                    history.query(version)
                history.close()

    def test_old_history_can_be_extended_without_modifying_old_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'repair.sqlite3'
            old = PositiveHistory(path)
            root = old.prepare([(1, 2), (-1, -2)])['version']
            first = old.append(root, [1, 2, 5])['version']
            last = old.append_decision(first, [-9])['version']
            rows = list(old.db.execute('SELECT * FROM cnf_positive_versions_v1 ORDER BY id'))
            old.close()
            history = RepairHistory(path)
            version = history.append_repair(last, [10])['version']
            self.assertTrue(holds(history.materialize(version)['cnf'], history.witness(version)['model']))
            self.assertEqual(rows, list(history.db.execute('SELECT * FROM cnf_positive_versions_v1 WHERE id<=? ORDER BY id', (last,))))
            with self.assertRaises(UnsupportedExpansion):
                history.append_repair(version, [9])
            history.close()


if __name__ == '__main__':
    unittest.main()
