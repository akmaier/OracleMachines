import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_pattern_inventory import FAMILIES, PatternInventory, classify, encode
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_matching import domain_cnf


def assignments(cnf):
    names = sorted({abs(lit) for c in cnf for lit in c})
    return (dict(zip(names, bits)) for bits in itertools.product((False, True), repeat=len(names)))


def parity(variables, rhs):
    return [tuple(-v if bit else v for v, bit in zip(variables, bits))
            for bits in itertools.product((False, True), repeat=len(variables)) if sum(bits) % 2 != rhs]


def check_pointwise(h, key, seen=None):
    """Check assignment equivalence, not just satisfiability of one result."""
    seen = set() if seen is None else seen
    if key in seen:
        return
    seen.add(key)
    node = h._load(key)
    cnf = node['cnf']
    edge_groups = ([node['edges']] if node['kind'] == 'and' else
                   [a['edges'] for a in node['alternatives']] if node['kind'] == 'or' else [])
    for edges in edge_groups:
        for edge in edges:
            check_pointwise(h, edge['key'], seen)
    for model in assignments(cnf):
        def child(edge):
            local = {i: model[var] for i, var in enumerate(edge['names'], 1)}
            return holds(h._load(edge['key'])['cnf'], local)
        if node['kind'] == 'and':
            assert holds(cnf, model) == all(child(edge) for edge in node['edges'])
            supports = [set(edge['names']) for edge in node['edges']]
            assert sum(map(len, supports)) == len(set().union(*supports))
        elif node['kind'] == 'or':
            for attempt in node['alternatives']:
                assert holds(cnf, model) == child(attempt['edges'][int(model[attempt['variable']])])
        if node['profile']['outcomes']['single_parity'] == 'recognized':
            certificate = node['profile']['evidence']['single_parity']
            assert holds(cnf, model) == (sum(model[v] for v in certificate['variables']) % 2 == certificate['rhs'])


class PatternInventoryTests(unittest.TestCase):
    def test_exhaustive_two_variable_coverage_and_overlaps(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        h = PatternInventory()
        cells = {}
        for mask in range(1 << len(clauses)):
            source = [c for i, c in enumerate(clauses) if mask >> i & 1]
            r = h.inspect(source)
            self.assertEqual(set(r['profile']['outcomes']), set(FAMILIES))
            self.assertTrue(r['summary']['closed'])
            self.assertEqual(r['profile']['outcomes']['two_cnf'], 'recognized')
            cells.setdefault(r['profile']['cell'], []).append(mask)
            check_pointwise(h, r['root']['key'])
            self.assertEqual(any(holds(source, a) for a in assignments(source)),
                             any(holds(h._load(r['root']['key'])['cnf'], a)
                                 for a in assignments(h._load(r['root']['key'])['cnf'])))
        self.assertEqual(sum(map(len, cells.values())), 512)
        self.assertGreater(len(cells), 1)
        r = h.inspect([(1,)])
        self.assertGreater(sum(v == 'recognized' for v in r['profile']['outcomes'].values()), 3)
        self.assertEqual(h.storage()['sources'], 512)
        h.close()

    def test_single_parity_certificates_and_cap(self):
        for n in range(1, 7):
            for rhs in (0, 1):
                h = PatternInventory()
                r = h.inspect(parity(range(1, n+1), rhs))
                self.assertEqual(r['profile']['outcomes']['single_parity'], 'recognized')
                self.assertEqual(r['profile']['evidence']['single_parity']['rhs'], rhs)
                check_pointwise(h, r['root']['key'])
                h.close()
        h = PatternInventory(parity_width=3, max_depth=0)
        r = h.inspect(parity(range(1, 5), 1))
        self.assertEqual(r['profile']['outcomes']['single_parity'], 'unresolved')
        self.assertFalse(r['summary']['closed'])
        h.close()
        h = PatternInventory(max_depth=0)
        source = parity(range(1, 5), 1)
        self.assertEqual(h.inspect(source[:-1])['profile']['outcomes']['single_parity'], 'excluded')
        mixed = parity((1, 2, 3, 4), 1) + parity((3, 4, 5, 6), 1)
        self.assertEqual(h.inspect(mixed)['profile']['outcomes']['single_parity'], 'excluded')
        self.assertFalse(h.inspect(mixed)['summary']['closed'])
        h.close()

    def test_components_conditioning_and_unknown_are_distinct(self):
        source = parity((1, 2, 3, 4), 1) + parity((5, 6, 7, 8), 1)
        h = PatternInventory(max_depth=0, decompose=False)
        self.assertFalse(h.inspect(source)['summary']['closed'])
        h.close()
        h = PatternInventory(max_depth=0)
        r = h.inspect(source)
        self.assertTrue(r['summary']['closed'])
        self.assertEqual(h._load(r['root']['key'])['kind'], 'and')
        check_pointwise(h, r['root']['key'])
        h.close()
        # All assignments forbidden. One split leaves unrecognized full 3-CNF;
        # two levels reach 2-CNF. Closed does not mean satisfiable.
        source = parity((1, 2, 3, 4), 0) + parity((1, 2, 3, 4), 1)
        for depth, closed in ((0, False), (1, False), (2, True)):
            h = PatternInventory(max_depth=depth, candidate_limit=2)
            r = h.inspect(source)
            self.assertEqual(r['summary']['closed'], closed)
            self.assertFalse(any(holds(source, a) for a in assignments(source)))
            check_pointwise(h, r['root']['key'])
            h.close()

    def test_random_conditioned_recomposition_and_renamings(self):
        rng = random.Random(71108)
        h = PatternInventory(max_depth=2, candidate_limit=3)
        for _ in range(80):
            source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 6), rng.randrange(1, 5)))
                      for _ in range(rng.randrange(2, 12))]
            r = h.inspect(source)
            check_pointwise(h, r['root']['key'])
            renamed = [tuple((abs(lit)*17+100)*(1 if lit > 0 else -1) for lit in reversed(c))
                       for c in reversed(source)]
            r2 = h.inspect(renamed + renamed[:1] + [(999, -999)])
            self.assertEqual(r['root']['key'], r2['root']['key'])
            self.assertEqual(r['profile'], r2['profile'])
        h.close()

    def test_cold_persistence_all_alternatives_and_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'patterns.sqlite3'
            h = PatternInventory(path)
            source = parity((1, 2, 3, 4), 0) + parity((1, 2, 3, 4), 1)
            first = h.inspect(source)
            storage = h.storage()
            self.assertGreater(storage['nodes'], 1)
            h.close()
            raw = path.read_bytes()
            h = PatternInventory(path)
            second = h.inspect(source)
            self.assertEqual(first['root'], second['root'])
            self.assertEqual(second['metrics'].get('inserted_nodes', 0), 0)
            self.assertEqual(second['metrics']['inserted_sources'], 0)
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
                self.assertIsNotNone(h._load(key))
            self.assertEqual(storage, h.storage())
            h.close()
            self.assertEqual(raw, path.read_bytes())

    def test_forged_profiles_branches_and_partitions_fail(self):
        h = PatternInventory(max_depth=1)
        source = parity((1, 2, 3, 4), 0) + parity((1, 2, 3, 4), 1)
        r = h.inspect(source)
        key = r['root']['key']
        node = h._load(key)
        mutations = []
        bad = copy.deepcopy(node);bad['profile']['outcomes']['single_parity'] = 'recognized';mutations.append(bad)
        bad = copy.deepcopy(node);bad['alternatives'][0]['edges'][1] = bad['alternatives'][0]['edges'][0];mutations.append(bad)
        # The full cube restrictions normalize identically; corrupt the binding
        # separately so the checker still rejects an identity-preserving forgery.
        mutations.pop()
        bad = copy.deepcopy(node);bad['alternatives'][0]['edges'][1]['names'] = [1];mutations.append(bad)
        bad = copy.deepcopy(node);bad['summary']['closed'] = True;mutations.append(bad)
        bad = copy.deepcopy(node);bad['alternatives'].pop();mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):
                h._check(key, bad)
        source = parity((1, 2, 3, 4), 1) + parity((5, 6, 7, 8), 1)
        r = h.inspect(source);key = r['root']['key'];bad = copy.deepcopy(h._load(key))
        bad['edges'][1]['names'] = bad['edges'][0]['names']
        with self.assertRaises(ValueError):
            h._check(key, bad)
        h.close()

    def test_configuration_and_invalid_input(self):
        for options in (dict(max_depth=-1), dict(max_depth=4), dict(max_depth=True),
                        dict(candidate_limit=65), dict(parity_width=-1), dict(decompose=1)):
            with self.assertRaises(ValueError):
                PatternInventory(**options)
        h = PatternInventory()
        for source in ([(0,)], [(True,)], [(), ('x',)]):
            with self.assertRaises(ValueError):
                h.inspect(source)
        self.assertEqual(h.storage()['nodes'], 0)
        h.close()


if __name__ == '__main__':
    unittest.main()
