from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_conditioning import ShortestClauseInventory, shortest_balanced_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_simplification import SimplifyingPatternInventory
from solver.test_cnf_simplification import check_simplified_tree


class ConditioningTests(unittest.TestCase):
    def test_both_polarities_short_clauses_and_budget(self):
        source = [(1, 2), (1, -2), (1, 3), (1, -3), (1, 4), (1, 5), (2, 6), (-2, 7)]
        h = SimplifyingPatternInventory(candidate_limit=1)
        self.assertEqual(h._choices(source), [1]); h.close()
        counts = Counter()
        self.assertEqual(shortest_balanced_choices(source, 1, counts), [2])
        self.assertEqual(counts['conditioning_rank_literal_visits'], 16)
        self.assertEqual(shortest_balanced_choices(source, 0, Counter()), [])
        self.assertEqual(shortest_balanced_choices([], 4, Counter()), [])
        # Extra occurrences in longer clauses cannot outrank a better balanced
        # shortest-clause score; they only enter the last structural tie-break.
        wide = [(1, 10+i, 100+i) for i in range(20)]
        self.assertEqual(shortest_balanced_choices(source+wide, 1, Counter()), [2])

    def test_exhaustive_two_variable_sources(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        h = ShortestClauseInventory(max_depth=2)
        for mask in range(1 << len(clauses)):
            r = h.inspect([c for i, c in enumerate(clauses) if mask >> i & 1])
            check_simplified_tree(h, r['root']['key'])
        h.close()

    def test_unlabelled_mixtures_renamings_and_all_branches(self):
        rng = random.Random(202611082300)
        h = ShortestClauseInventory(max_depth=2, simplify_pure=False)
        or_nodes = 0
        for _ in range(80):
            source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(2, 5)))
                      for _ in range(rng.randrange(8, 24))]
            names = list(range(1, 7)); rng.shuffle(names)
            mapping = dict(zip(range(1, 7), (v*101+7 for v in names)))
            variant = [tuple(mapping[abs(l)]*(1 if l > 0 else -1) for l in reversed(c)) for c in reversed(source)]
            for current in (source, variant+variant[:2]+[(9999, -9999)], source+[(1,)] ,source+[(-1,)]):
                r = h.inspect(current); check_simplified_tree(h, r['root']['key'])
                or_nodes += h._load(r['root']['key'])['kind'] == 'or'
        self.assertGreater(or_nodes, 0)
        h.close()

    def test_exact_policy_coexistence_replay_and_corrupt_order(self):
        source = [(1,2,3),(-1,-2,-3),(-1,-2,4),(-3,-4,5),(-1,3,-5),(2,-3,-5),(-2,4,5)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'
            old = SimplifyingPatternInventory(path, max_depth=2, simplify_pure=False)
            previous = old.inspect(source)
            old_rows = dict(old.db.execute('SELECT * FROM cnf_patterns_v1')); old.close()
            h = ShortestClauseInventory(path, max_depth=2, simplify_pure=False)
            r = h.inspect(source)
            self.assertNotEqual(previous['root']['key'], r['root']['key'])
            for k, v in old_rows.items():
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0], v)
            node = h._load(r['root']['key']); self.assertEqual(node['kind'], 'or')
            check_simplified_tree(h, r['root']['key']); h.close()
            before = path.read_bytes()
            h = ShortestClauseInventory(path, max_depth=2, simplify_pure=False)
            again = h.inspect(source)
            self.assertEqual(again['metrics'].get('inserted_nodes', 0), 0)
            self.assertEqual(again['metrics']['inserted_sources'], 0)
            h.close(); self.assertEqual(path.read_bytes(), before)
            h = ShortestClauseInventory(path, max_depth=2, simplify_pure=False)
            bad = copy.deepcopy(node); bad['alternatives'][0]['variable'] += 100
            with h.db:
                h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),r['root']['key']))
            h.close()
            h = ShortestClauseInventory(path, max_depth=2, simplify_pure=False)
            with self.assertRaises(ValueError): h.inspect(source)
            h.close()

    def test_same_source_different_caps_have_separate_identities(self):
        keys = []
        for cap in (0, 1, 4, 8):
            h = ShortestClauseInventory(max_depth=2, candidate_limit=cap)
            r = h.inspect([(1,2,3),(-1,-2,4),(-3,-4)])
            keys.append(r['root']['key']); check_simplified_tree(h, keys[-1]); h.close()
        self.assertEqual(len(keys), len(set(keys)))
