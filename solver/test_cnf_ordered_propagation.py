from collections import Counter
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_checked_probe_reuse import CheckedProbeReuseInventory
from experiments.cnf_ordered_propagation import (
    discovery_propagation, propagate_for_discovery, propagate_ordered)
from experiments.cnf_ordered_propagation_inventory import OrderedPropagationInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import propagate
from experiments.cnf_simplification import check_simplification, discover_simplification
from solver.test_cnf_implied_subsumption import implication_source


class OrderedPropagationTests(unittest.TestCase):
    def compare(self, cnf):
        expected = propagate(cnf, Counter())
        counts = Counter()
        actual = propagate_ordered(cnf, counts)
        self.assertEqual(actual, expected, cnf)
        self.assertEqual(list(actual[0].items()), list(expected[0].items()))
        literals = sum(map(len, cnf))
        self.assertLessEqual(counts['ordered_propagation_index_literals'], literals)
        self.assertLessEqual(counts['ordered_propagation_occurrence_updates'], literals)
        self.assertLessEqual(counts['ordered_propagation_events'], len(cnf))
        self.assertLessEqual(counts['ordered_propagation_peak_events'], len(cnf))
        certificate = dict(units=actual[1], conflict=actual[2], pure_rounds=[])
        check_simplification(cnf, certificate, Counter(), pure=False)
        return counts

    def test_exhaustive_ordered_small_formulas_with_repeated_literals(self):
        # All ordered sequences of up to three clauses of width <=2, including
        # duplicates, tautologies, competing unit reasons and empty clauses.
        literals = (-2, -1, 1, 2)
        clauses = [()] + [(a,) for a in literals] + list(itertools.product(literals, repeat=2))
        for size in range(4):
            for cnf in itertools.product(clauses, repeat=size):
                self.compare(cnf)

    def test_random_raw_and_edited_formulas(self):
        rng = random.Random(202611091230)
        for _ in range(1500):
            n = rng.randrange(1, 16)
            cnf = [tuple(rng.choice((-1, 1)) * rng.randrange(1, n+1)
                         for _ in range(rng.randrange(1, 7)))
                   for _ in range(rng.randrange(1, 45))]
            self.compare(cnf)
            rng.shuffle(cnf)
            self.compare(cnf + [(rng.choice((-1, 1)) * rng.randrange(1, n+1),)])

    def test_round_order_conflicts_and_stale_events(self):
        cases = [((-2, 3), (-1, 2), (1,)),
                 ((-2,), (-1, 2), (1,)),
                 ((1,), (-1,), (2,), ()),
                 ((1, 1, -2), (2,), (-1,)),
                 ((-1, 1), (1,), (-1,)),
                 ((-3,), (-2, 3), (-1, 2), (1,))]
        for cnf in cases:
            self.compare(cnf)
        self.assertEqual(propagate_ordered(cases[0], Counter())[1], [[1, 2], [2, 1], [3, 0]])

    def test_reverse_chain_work_and_unit_free_fast_path(self):
        n = 200
        cnf = tuple([(-i, i+1) for i in range(n-1, 0, -1)] + [(1,)])
        old = Counter(); propagate(cnf, old)
        new = self.compare(cnf)
        self.assertEqual(new['ordered_propagation_index_literals'], 2*n-1)
        self.assertEqual(new['ordered_propagation_occurrence_updates'], 2*n-1)
        self.assertEqual(new['ordered_propagation_events'], n)
        self.assertGreater(old['propagation_literal_visits'], n*n)
        counts = self.compare(((1, 2), (-1, 2), (-1, -2)))
        self.assertEqual(counts['ordered_propagation_no_units'], 1)
        self.assertEqual(counts['ordered_propagation_index_literals'], 0)

    def test_scoped_engine_restores_on_exception_and_nesting(self):
        cnf = ((-1, 2), (1,))
        counts = Counter()
        with self.assertRaises(RuntimeError):
            with discovery_propagation(propagate_ordered):
                discover_simplification(cnf, counts)
                with discovery_propagation(propagate):
                    propagate_for_discovery(cnf, counts)
                propagate_for_discovery(cnf, counts)
                raise RuntimeError('restore')
        self.assertEqual(counts['ordered_propagation_calls'], 2)
        propagate_for_discovery(cnf, counts)
        self.assertEqual(counts['ordered_propagation_calls'], 2)
        self.assertGreater(counts['propagation_literal_visits'], 0)

    def test_inventory_proofs_archive_and_cold_replay_unchanged(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        cases = [[c for i, c in enumerate(clauses) if mask >> i & 1] for mask in range(512)]
        rng = random.Random(202611091231)
        cases += [implication_source()] + [
            [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), 3))
             for _ in range(24)] for _ in range(20)]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = []
            for cls in (CheckedProbeReuseInventory, OrderedPropagationInventory):
                path = Path(tmp) / (cls.__name__ + '.db')
                h = cls(path, max_depth=1)
                for source in cases:
                    h.inspect(source)
                h.close(); snapshots.append(path.read_bytes())
            self.assertEqual(*snapshots)
            path = Path(tmp) / 'CheckedProbeReuseInventory.db'
            h = OrderedPropagationInventory(path, max_depth=1)
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
                h._load(key)
            self.assertGreater(h.counts['ordered_propagation_calls'], 0)
            self.assertEqual(h.counts['propagation_literal_visits'], 0)
            for source in cases:
                result = h.inspect(source)
                self.assertEqual(result['metrics'].get('inserted_nodes', 0), 0)
                self.assertEqual(result['metrics']['inserted_sources'], 0)
            h.close(); self.assertEqual(path.read_bytes(), snapshots[0])

    def test_saved_frontier_probe_discovery_identical(self):
        rows = json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        old = CheckedProbeReuseInventory(); new = OrderedPropagationInventory()
        for row in rows:
            self.assertEqual(encode(old._discover_probes(row['cnf'])),
                             encode(new._discover_probes(row['cnf'])))
        self.assertEqual(len(rows), 148)
        self.assertGreater(new.counts['ordered_propagation_calls'], 0)
        self.assertEqual(new.counts['propagation_literal_visits'], 0)
        old.close(); new.close()
