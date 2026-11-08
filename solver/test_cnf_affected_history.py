"""Soundness, exact single-flip coverage, persistence and forged repair rejection."""
from collections import Counter
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_repair_history import RepairHistory, map_get
from experiments.cnf_residual_dag import holds


class AffectedHistoryTests(unittest.TestCase):
    def assert_state(self, history, version, source):
        self.assertEqual(history.materialize(version)['cnf'], tuple(map(tuple, source)))
        model = history.witness(version)['model']
        if model is None:
            return
        self.assertTrue(holds(source, model))
        postings, counts, next_id = history.clause_states[version]
        self.assertEqual(next_id, len(source) + 1)
        expected = {}
        for cid, clause in enumerate(source, 1):
            unique = set(clause)
            self.assertEqual(map_get(counts, cid, Counter()),
                             sum(model.get(abs(lit), False) == (lit > 0) for lit in unique))
            for var in {abs(lit) for lit in unique}:
                mask = (1 if var in unique else 0) | (2 if -var in unique else 0)
                expected.setdefault(var, []).insert(0, (cid, mask))
        for var, wanted in expected.items():
            entry, actual = map_get(postings, var, Counter()), []
            while entry:
                cid, mask, entry = entry
                actual.append((cid, mask))
            self.assertEqual(actual, wanted)

    def test_blocked_but_sat_and_older_branches(self):
        h = AffectedRepairHistory()
        root = h.prepare([(1,)])['version']
        parent = h.append_repair(root, [-2, 1])['version']
        version = h.append_repair(parent, [2])['version']
        self.assert_state(h, version, [(1,), (-2, 1), (2,)])
        self.assert_state(h, parent, [(1,), (-2, 1)])
        self.assertFalse(h.witness(parent)['model'].get(2, False))
        other = h.append_repair(parent, [-2])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(other, [2])
        self.assertEqual(h.storage()['bases'], 1)
        h.close()

    def test_duplicates_tautologies_both_signs_and_negative_flip(self):
        h = AffectedRepairHistory()
        root = h.prepare([(1,), (-2, -2, 1), (2, -2, -2)])['version']
        child = h.append_repair(root, [2, 2])['version']
        self.assert_state(h, child, [(1,), (-2, -2, 1), (2, -2, -2), (2, 2)])
        # Duplicate true literals must not hide destruction of a unit clause.
        bad = h.prepare([(-3, -3)])['version']
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(bad, [3])
        # The solver's pure default supplies x=true here; protected old x can flip.
        parent = h.prepare([(1, 2), (-1, 2)])['version']
        model = h.witness(parent)['model']
        lit = -1 if model.get(1, False) else 1
        changed = h.append_repair(parent, [lit])['version']
        self.assert_state(h, changed, [(1, 2), (-1, 2), (lit,)])
        h.close()

    def test_budget_rejection_has_no_persistent_mutation(self):
        h = AffectedRepairHistory(repair_budget=0)
        parent = h.prepare([(1,), (-2, 1)])['version']
        before = list(h.db.iterdump())
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(parent, [2])
        self.assertEqual(before, list(h.db.iterdump()))
        # A fresh variable has no affected clauses, even with a zero budget.
        child = h.append_repair(parent, [3])['version']
        self.assert_state(h, child, [(1,), (-2, 1), (3,)])
        h.close()
        for budget in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                AffectedRepairHistory(repair_budget=budget)

    def test_exhaustive_single_flip_coverage_and_random_branches(self):
        literals = (1, -1, 2, -2, 3, -3)
        clauses = [c for n in range(4) for c in itertools.combinations(literals, n)]
        bases = [[], [(1, 2)], [(1,), (-1,)], [(1, -1)],
                 [(1,), (-2, 1)], [(1, 2), (-1, -2)], [(-2, -2, 1), (1,)]]
        h = AffectedRepairHistory()
        versions = [h.prepare(base)['version'] for base in bases]
        rng = random.Random(734)
        proposals = [(v, c) for v in versions for c in clauses]
        for i in range(len(proposals) + 400):
            parent, clause = proposals[i] if i < len(proposals) else (rng.choice(versions), rng.choice(clauses))
            source = h.materialize(parent)['cnf']
            model = h.witness(parent)['model']
            can_accept = model is None or holds([clause], model) or any(
                holds(source + (clause,), {**model, abs(lit): lit > 0}) for lit in clause)
            before = list(h.db.iterdump())
            try:
                result = h.append_repair(parent, clause)
            except UnsupportedExpansion:
                self.assertFalse(can_accept)
                self.assertEqual(before, list(h.db.iterdump()))
                continue
            self.assertTrue(can_accept)
            version = result['version']
            versions.append(version)
            self.assert_state(h, version, source + (clause,))
            self.assert_state(h, parent, source)
            if model is None:
                self.assertFalse(any(holds(source + (clause,), dict(zip((1, 2, 3), vals)))
                                     for vals in itertools.product((False, True), repeat=3)))
        h.close()

    def test_cold_chain_and_mixed_legacy_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.sqlite3'
            old = RepairHistory(path)
            root = old.prepare([(1,)])['version']
            version = old.append_repair(root, [10])['version']
            old.close()
            h = AffectedRepairHistory(path)
            source = [(1,), (10,)]
            for i in range(32):
                for clause in ((-100-i, 1), (100+i,)):
                    version = h.append_repair(version, clause)['version']
                    source.append(clause)
            legacy = h.append(version, [1, 9])['version']
            source.append((1, 9))
            version = h.append_decision(legacy, [10])['version']
            source.append((10,))
            self.assert_state(h, version, source)
            with self.assertRaises(UnsupportedExpansion):
                h.append_decision(version, [-100])
            before = list(h.db.iterdump())
            h.close()
            h = AffectedRepairHistory(path, repair_budget=0)
            self.assertTrue(h.query(version)['answer'])
            self.assert_state(h, version, source)
            self.assertEqual(before, list(h.db.iterdump()))
            h.close()
            old = RepairHistory(path)
            self.assertTrue(old.query(root)['answer'])
            with self.assertRaises(ValueError):
                old.query(version)
            old.close()

    def test_forged_repairs_fail_cold(self):
        for mutation in ('opposite_parent', 'missing_literal', 'bool', 'unchanged', 'invalid_tail', 'base', 'cycle'):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'history.sqlite3'
                h = AffectedRepairHistory(path)
                root = h.prepare([(1,), (-2, 1)])['version']
                blocked = h.append_repair(root, [-2])['version']
                child = h.append_repair(root, [2])['version']
                payload = dict(kind='append-affected', clause=[2], repair=2)
                with h.db:
                    if mutation == 'opposite_parent':
                        h.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (blocked, child))
                    elif mutation == 'base':
                        base_id = h.checked[root][0]
                        base = json.loads(h.db.execute('SELECT payload FROM cnf_positive_bases_v1 WHERE id=?', (base_id,)).fetchone()[0])
                        base['source'].append([-2, -2])
                        h.db.execute('UPDATE cnf_positive_bases_v1 SET payload=? WHERE id=?', (json.dumps(base), base_id))
                    elif mutation == 'cycle':
                        h.db.execute('UPDATE cnf_positive_versions_v1 SET parent=? WHERE id=?', (child, child))
                    else:
                        if mutation == 'missing_literal': payload['repair'] = 3
                        if mutation == 'bool': payload['repair'] = True
                        if mutation == 'unchanged': payload.update(clause=[1], repair=1)
                        if mutation == 'invalid_tail': payload['clause'] = [2, 0]
                        h.db.execute('UPDATE cnf_positive_versions_v1 SET payload=? WHERE id=?', (json.dumps(payload), child))
                h.close()
                h = AffectedRepairHistory(path)
                with self.assertRaises(ValueError, msg=mutation):
                    h.query(child)
                h.close()

    def test_joint_flip_limit_and_unsat_additions(self):
        h = AffectedRepairHistory()
        # Implication cycle forces x=y; changing either one alone is invalid.
        parent = h.prepare([(-1, 2), (1, -2)])['version']
        model = h.witness(parent)['model']
        lit = -1 if model.get(1, False) else 1
        with self.assertRaises(UnsupportedExpansion):
            h.append_repair(parent, [lit])
        self.assertTrue(h.prepare([(-1, 2), (1, -2), (lit,)])['answer'])
        bad = h.prepare([()])['version']
        result = h.append_repair(bad, [])
        self.assertFalse(result['answer'])
        self.assertIsNone(h.clause_states[result['version']])
        h.close()


if __name__ == '__main__':
    unittest.main()
