from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_affine_projection import ProjectionPatternInventory
from experiments.cnf_simplification import SimplifyingPatternInventory, discover_simplification, check_simplification
from experiments.cnf_residual_dag import holds, normalize
from experiments.compare_cnf_matching import domain_cnf
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise


def check_simplified_tree(h, key, seen=None):
    seen = set() if seen is None else seen
    if key in seen:
        return
    seen.add(key);node = h._load(key)
    check_pointwise(h, key)
    edges = (node['edges'] if node['kind'] == 'and' else
             [e for a in node['alternatives'] for e in a['edges']] if node['kind'] == 'or' else
             [node['edge']] if node['kind'] in ('project', 'simplify') else [])
    for edge in edges:
        check_simplified_tree(h, edge['key'], seen)
    if node['kind'] not in ('project', 'simplify'):
        return
    edge = node['edge'];child = h._load(edge['key'])
    feasible = {tuple(model[v] for v in edge['names']) for model in assignments(node['cnf']) if holds(node['cnf'], model)}
    for child_model in assignments(child['cnf']):
        bits = tuple(child_model[i] for i in range(1, len(edge['names'])+1))
        assert holds(child['cnf'], child_model) == (bits in feasible)
        if holds(child['cnf'], child_model):
            lifted = h.lift(key, child_model)
            assert holds(node['cnf'], lifted)
            assert all(lifted[v] == child_model[i] for i, v in enumerate(edge['names'], 1))


def check_certificate_fibers(source, **options):
    cnf, _ = normalize(source, Counter())
    cert = discover_simplification(cnf, Counter(), **options)
    target, fixed = check_simplification(cnf, cert, Counter(), **options)
    names = sorted({abs(lit) for c in target for lit in c})
    feasible = {tuple(model[v] for v in names) for model in assignments(cnf) if holds(cnf, model)}
    for model in assignments(target):
        assert holds(target, model) == (tuple(model[v] for v in names) in feasible)
        if holds(target, model):
            lifted = {abs(lit): False for c in cnf for lit in c}
            lifted.update(fixed);lifted.update(model)
            assert holds(cnf, lifted)
    return cert, target


class SimplificationTests(unittest.TestCase):
    def test_exhaustive_two_variable_fibers_all_policies(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        h = SimplifyingPatternInventory(max_depth=2)
        for mask in range(1 << len(clauses)):
            source = [c for i, c in enumerate(clauses) if mask >> i & 1]
            for units, pure in ((True, True), (True, False), (False, True)):
                check_certificate_fibers(source, units=units, pure=pure)
            r = h.inspect(source);check_simplified_tree(h, r['root']['key'])
        h.close()

    def test_unit_implication_conflict_and_pure_cascade(self):
        for source in ([(-1,), (1, 2), (-2, 3), (-3,)],
                       [(-1,), (1, 2), (-2, 3)],
                       [(1, 2), (-2, 3), (-3, 4)]):
            check_certificate_fibers(source)
        cert, target = check_certificate_fibers([(1, 2), (-2, 3), (-3, 4)], units=False)
        self.assertGreater(len(cert['pure_rounds']), 1)
        self.assertEqual(target, ())

    def test_all_couplings_participate_in_purity(self):
        # Looking only at the first clause would incorrectly choose x=true.
        source = [(1, 2, 3), (-1, 4, 5), (-2, -4), (-3, -5)]
        cert, target = check_certificate_fibers(source)
        self.assertEqual(cert['pure_rounds'], [])
        cnf, _ = normalize(source, Counter())
        bad = dict(units=[], conflict=None, pure_rounds=[[1]])
        with self.assertRaisesRegex(ValueError, 'impure'):
            check_simplification(cnf, bad, Counter())
        self.assertEqual(target, cnf)

    def test_matching_parity_exposed_and_opposite_bridge_retained(self):
        core = domain_cnf([range(3)]*3)
        source = core+parity((10, 11, 12, 13), 1)+[(1, 10)]
        h = SimplifyingPatternInventory(max_depth=0)
        result = h.inspect(source)
        self.assertTrue(result['summary']['closed'])
        root = h._load(result['root']['key']);self.assertEqual(root['kind'], 'project')
        child = h._load(root['edge']['key']);self.assertEqual(child['kind'], 'simplify')
        final = h._load(child['edge']['key'])
        self.assertEqual(final['profile']['outcomes']['matching'], 'recognized')
        edited = h.inspect(source+[(-10, 2)])
        child = h._load(h._load(edited['root']['key'])['edge']['key'])
        self.assertEqual(child['profile']['simplification']['status'], 'fixed_point')
        self.assertFalse(edited['summary']['closed'])
        h.close()
        # This larger case is checked by full lifted witnesses in the benchmark;
        # a smaller matching-plus-parity instance also checks every fiber here.
        h = SimplifyingPatternInventory(max_depth=0)
        source = domain_cnf([range(2)]*2)+parity((5, 6, 7, 8), 1)+[(1, 5)]
        r = h.inspect(source);check_simplified_tree(h, r['root']['key']);h.close()

    def test_random_mixtures_full_recomposition_and_renamings(self):
        rng = random.Random(202611082219)
        h = SimplifyingPatternInventory(max_depth=2)
        for _ in range(100):
            source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(1, 5)))
                      for _ in range(rng.randrange(3, 20))]
            if rng.randrange(2): source += parity(rng.sample(range(1, 7), 3), rng.randrange(2))
            check_certificate_fibers(source)
            r = h.inspect(source);check_simplified_tree(h, r['root']['key'])
            shuffled = list(range(1, 7));rng.shuffle(shuffled)
            rename = dict(zip(range(1, 7), (v*37+11 for v in shuffled)))
            variant = [tuple(rename[abs(lit)]*(1 if lit > 0 else -1) for lit in reversed(c)) for c in reversed(source)]
            r2 = h.inspect(variant+variant[:1]+[(999, -999)])
            check_simplified_tree(h, r2['root']['key'])
            self.assertEqual(r['profile']['cell'], r2['profile']['cell'])
        h.close()

    def test_forged_reasons_conflicts_and_omitted_rounds(self):
        cnf, _ = normalize([(-1,), (1, 2), (-2, 3), (-3,)], Counter())
        cert = discover_simplification(cnf, Counter())
        mutations = []
        bad = copy.deepcopy(cert);bad['units'][0][0] *= -1;mutations.append(bad)
        bad = copy.deepcopy(cert);bad['conflict'] = 100;mutations.append(bad)
        bad = copy.deepcopy(cert);bad['units'].pop();mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError): check_simplification(cnf, bad, Counter())
        cnf, _ = normalize([(1, 2), (-2, 3), (-3, 4)], Counter())
        cert = discover_simplification(cnf, Counter());cert['pure_rounds'].pop()
        with self.assertRaisesRegex(ValueError, 'fixed point'):
            check_simplification(cnf, cert, Counter())

    def test_checker_does_not_trust_discovery(self):
        source = domain_cnf([range(3)]*3)+[(1, 10), (-10, 2)]
        h = SimplifyingPatternInventory(max_depth=0)
        fake = dict(units=[], conflict=None, pure_rounds=[[10]])
        with patch('experiments.cnf_simplification.discover_simplification', return_value=fake):
            with self.assertRaisesRegex(ValueError, 'impure'): h.inspect(source)
        h.close()

    def test_old_rows_cold_lifting_and_corruption(self):
        source = domain_cnf([range(3)]*3)+[(1, 10)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'simplify.sqlite3'
            old = ProjectionPatternInventory(path, max_depth=0);before = old.inspect(source)
            saved = list(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h = SimplifyingPatternInventory(path, max_depth=0);first = h.inspect(source)
            self.assertNotEqual(first['root']['key'], before['root']['key'])
            for key, value in saved:
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()[0], value)
            h.close();raw = path.read_bytes()
            h = SimplifyingPatternInventory(path, max_depth=0);second = h.inspect(source)
            self.assertEqual(first['root'], second['root'])
            self.assertEqual(second['metrics'].get('inserted_nodes', 0), 0)
            self.assertEqual(second['metrics']['inserted_sources'], 0)
            key = second['root']['key'];node = h._load(key)
            model = {i: i in (1, 5, 9) for i in range(1, 10)}
            self.assertTrue(holds(source, h.lift(key, model)))
            h.close();self.assertEqual(raw, path.read_bytes())
            h = SimplifyingPatternInventory(path, max_depth=0)
            bad = copy.deepcopy(node);bad['profile']['simplification']['certificate']['pure_rounds'][0][0] *= -1
            h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (json.dumps(bad), key));h.db.commit();h.close()
            h = SimplifyingPatternInventory(path, max_depth=0)
            with self.assertRaises(ValueError): h.inspect(source)
            h.close()

    def test_configuration(self):
        for options in (dict(simplify_units=1), dict(simplify_pure=None)):
            with self.assertRaises(ValueError): SimplifyingPatternInventory(**options)


if __name__ == '__main__':
    unittest.main()
