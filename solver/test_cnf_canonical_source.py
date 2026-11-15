from collections import Counter
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_canonical_source import canonical_source, CanonicalSourceInventory
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_residual_dag import normalize
from solver.test_cnf_source_local import OPTIONS


class CanonicalSourceTests(unittest.TestCase):
    def same(self, source):
        self.assertEqual(canonical_source(source, Counter()), normalize(source, Counter()))

    def test_all_two_variable_clause_sets_and_reorderings(self):
        clauses = [tuple(sorted(l for l in row if l)) for row in itertools.product((0, -1, 1), (0, -2, 2))]
        for mask in range(1 << len(clauses)):
            cnf = [clauses[i] for i in range(len(clauses)) if mask & (1 << i)]
            variants = [cnf, list(reversed(cnf)), [tuple(reversed(c)) for c in cnf],
                        [[3*l for l in c] for c in cnf]]
            for source in variants:
                self.same(source)
                normal, _ = normalize(source)
                counts = Counter()
                self.assertEqual(canonical_source(normal, counts), normalize(normal))
                self.assertEqual(counts['canonical_order_reuses'], 1)

    def test_seeded_mixtures_duplicates_tautologies_and_large_names(self):
        rng = random.Random(1190)
        for _ in range(1000):
            cnf = [tuple(rng.choice((-1, 1))*rng.randint(1, 12) for _ in range(rng.randrange(6)))
                   for _ in range(rng.randrange(16))]
            self.same(cnf)
        self.same([(-10**80, 10**80 + 7), (10**80,)])

    def test_invalid_values_retain_original_rejections(self):
        for source in [[(0,)], [(True,)], [(1.0,)], [(1, 'x')], [(), (0,)], [(), (True,)]]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    normalize(source)
                with self.assertRaises(ValueError):
                    canonical_source(source, Counter())

    def test_iterators_and_unusual_containers_use_full_fallback(self):
        for factory in (lambda: iter([(2,), (-1, 2)]), lambda: [set([1, 2]), (-2,) ]):
            expected = normalize(factory()); counts = Counter()
            self.assertEqual(canonical_source(factory(), counts), expected)
            self.assertEqual(counts['canonical_fallback_calls'], 1)

    def test_returned_lists_cannot_mutate_or_reuse_future_inputs(self):
        cnf = [[-2, 1], [2]]; counts = Counter()
        first = canonical_source(cnf, counts)
        cnf[0][0] = -3
        self.assertEqual(first, (((-2, 1), (2,)), (1, 2)))
        self.assertEqual(canonical_source(cnf, counts), normalize(cnf))

    def test_both_verifier_views_keep_exact_keys_and_names(self):
        with tempfile.TemporaryDirectory() as td:
            old = BudgetedInventory(Path(td)/'old', **OPTIONS)
            new = CanonicalSourceInventory(Path(td)/'new', **OPTIONS)
            try:
                self.assertEqual(old.config, new.config)
                self.assertEqual(old.prepared.config, new.prepared.config)
                for source in [[], [[]], [[-2, 1], [2]], [[7, -2], [2]], [[-2, 2], [1, 1]]]:
                    for depth in range(3):
                        self.assertEqual(old._canonical(source, depth), new._canonical(source, depth))
                        self.assertEqual(old.prepared._canonical(source, depth), new.prepared._canonical(source, depth))
            finally:
                old.close(); new.close()

    def test_fresh_acquisition_and_cold_replay_keep_identical_records(self):
        source = json.loads(Path('solver/fixtures/trace-split.json').read_text())
        records = []
        with tempfile.TemporaryDirectory() as td:
            for name, cls in [('old', BudgetedInventory), ('new', CanonicalSourceInventory)]:
                path = Path(td)/name
                h = cls(path, **OPTIONS); h.set_admission_budget(32)
                try:
                    key = h._edge(source, 0)['key']
                    records.append((key, list(h.db.execute('SELECT id,payload FROM cnf_patterns_v1 ORDER BY id')), set(h.admitted)))
                finally:
                    h.close()
                h = CanonicalSourceInventory(path, **OPTIONS); h.set_admission_budget(0)
                try:
                    with patch.object(h, '_discover', side_effect=AssertionError('fresh discovery')):
                        self.assertIsNotNone(h._load(key))
                    self.assertFalse(h.admitted)
                finally:
                    h.close()
        self.assertEqual(records[0], records[1])

    def test_canonical_input_still_rejects_forged_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'history'
            h = CanonicalSourceInventory(path, **OPTIONS); h.set_admission_budget(32)
            key = h._edge([[1]], 0)['key']
            node = json.loads(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()[0])
            node['summary']['closed'] = False
            with h.db:
                h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (json.dumps(node), key))
            h.close()
            h = CanonicalSourceInventory(path, **OPTIONS); h.set_admission_budget(0)
            try:
                with self.assertRaises(ValueError):
                    h._load(key)
                self.assertNotIn(key, h.checked)
            finally:
                h.close()


if __name__ == '__main__':
    unittest.main()
