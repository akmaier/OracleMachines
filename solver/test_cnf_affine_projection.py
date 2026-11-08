from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_affine_patterns import AffinePatternInventory
from experiments.cnf_affine_projection import (ProjectionPatternInventory, project_equations,
    check_projection, encode_boundary, check_boundary, lift_projection)
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_matching import domain_cnf
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise


def check_projected_tree(h, key, seen=None):
    seen = set() if seen is None else seen
    if key in seen:
        return
    seen.add(key);node = h._load(key)
    check_pointwise(h, key)
    edges = (node['edges'] if node['kind'] == 'and' else
             [e for a in node['alternatives'] for e in a['edges']] if node['kind'] == 'or' else
             [node['edge']] if node['kind'] == 'project' else [])
    for edge in edges:
        check_projected_tree(h, edge['key'], seen)
    if node['kind'] != 'project':
        return
    # Compare existential fibers, not pointwise equivalence on eliminated vars.
    feasible = set()
    edge = node['edge'];child = h._load(edge['key'])
    for model in assignments(node['cnf']):
        if holds(node['cnf'], model):
            feasible.add(tuple(model[v] for v in edge['names']))
    for child_model in assignments(child['cnf']):
        bits = tuple(child_model[i] for i in range(1, len(edge['names'])+1))
        assert holds(child['cnf'], child_model) == (bits in feasible)
        if holds(child['cnf'], child_model):
            lifted = h.lift(key, child_model)
            assert holds(node['cnf'], lifted)
            assert all(lifted[v] == child_model[i] for i, v in enumerate(edge['names'], 1))


class AffineProjectionTests(unittest.TestCase):
    def test_all_two_variable_equation_systems_and_all_boundaries(self):
        equations = [dict(variables=[i+1 for i in range(2) if mask >> i & 1], rhs=rhs)
                     for mask in range(4) for rhs in (0, 1)]
        for subset in range(1 << len(equations)):
            selected = [e for i, e in enumerate(equations) if subset >> i & 1]
            for keep_bits in range(4):
                keep = [v for v in (1, 2) if keep_bits >> (v-1) & 1]
                cert = project_equations(selected, keep, Counter())
                check_projection(selected, keep, cert, Counter())
                blocks = encode_boundary(cert, 100, Counter());check_boundary(cert, blocks, Counter())
                target = [c for block in blocks for c in block]
                for bits in itertools.product((False, True), repeat=len(keep)):
                    model = dict(zip(keep, bits))
                    extensions = [dict(zip((1, 2), values)) for values in itertools.product((False, True), repeat=2)]
                    feasible = any(all(sum(a[v] for v in e['variables']) % 2 == e['rhs'] for e in selected)
                                   for a in extensions if all(a[v] == model[v] for v in keep))
                    self.assertEqual(holds(target, model), feasible)
                    if feasible:
                        lifted = lift_projection(selected, keep, cert, model, Counter())
                        self.assertTrue(all(sum(lifted[v] for v in e['variables']) % 2 == e['rhs'] for e in selected))
                    else:
                        with self.assertRaises(ValueError):
                            lift_projection(selected, keep, cert, model, Counter())

    def test_free_interface_nontrivial_relation_and_infeasible_coupling(self):
        sources = [parity((1, 2, 3, 4), 1)+parity((3, 4, 5, 6), 1)+[(1, 6)],
                   parity((1, 2, 3), 0)+parity((1, 2, 4), 1)+[(3, 4)],
                   parity((1, 2, 3), 0)+parity((1, 2, 4), 1)+[(3, 4), (-3, 4), (3, -4)],
                   parity((1, 2, 3, 4), 1)+[(1, 5, 6), (-5, -6)]]
        h = ProjectionPatternInventory(max_depth=0)
        kinds = []
        for source in sources:
            r = h.inspect(source)
            kinds.append(h._load(r['root']['key'])['kind'])
            check_projected_tree(h, r['root']['key'])
        self.assertIn('project', kinds)
        h.close()

    def test_connected_matching_parity_and_growing_coupled_cases(self):
        for count in (4, 8, 16, 32):
            source = [c for i in range(count) for c in parity(range(2*i+1, 2*i+5), 1)] + [(1, 2*count+2)]
            h = ProjectionPatternInventory(max_depth=0)
            r = h.inspect(source);node = h._load(r['root']['key'])
            self.assertTrue(r['summary']['closed'])
            self.assertEqual(node['kind'], 'project')
            self.assertEqual(len(node['edge']['names']), 2)
            child_model = {1: True, 2: False}
            self.assertTrue(holds(node['cnf'], h.lift(r['root']['key'], child_model)))
            h.close()
        h = ProjectionPatternInventory(max_depth=2)
        source = domain_cnf([range(3)]*3)+parity((10, 11, 12, 13), 1)+[(1, 10)]
        r = h.inspect(source)
        # Projection removes the affine interior, but the mixed leftover still
        # escapes the strict matching recognizer and frequency-first splitting.
        self.assertFalse(r['summary']['closed'])
        self.assertEqual(h._load(r['root']['key'])['kind'], 'project')
        h.close()

    def test_exhaustive_two_variable_sources_and_seeded_mixtures(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        h = ProjectionPatternInventory(max_depth=2)
        for mask in range(1 << len(clauses)):
            r = h.inspect([c for i, c in enumerate(clauses) if mask >> i & 1])
            check_projected_tree(h, r['root']['key'])
        rng = random.Random(2026110822)
        for _ in range(80):
            source = parity(rng.sample(range(1, 7), 3), rng.randrange(2))
            source += parity(rng.sample(range(1, 7), 3), rng.randrange(2))
            source += [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(2, 5)))
                       for _ in range(rng.randrange(1, 6))]
            r = h.inspect(source);check_projected_tree(h, r['root']['key'])
        h.close()

    def test_encoding_budget_checked_before_enumeration(self):
        equations = [dict(variables=[1]+list(range(2, 14)), rhs=0),
                     dict(variables=[1]+list(range(14, 26)), rhs=1)]
        cert = project_equations(equations, list(range(2, 26)), Counter())
        check_projection(equations, list(range(2, 26)), cert, Counter())
        with patch('experiments.cnf_affine_projection.itertools.product', side_effect=AssertionError('enumerated')):
            self.assertIsNone(encode_boundary(cert, 4096, Counter()))
        # Two small source equations can create a wider projected equation.
        source = parity((1, 2, 3), 0)+parity((1, 4, 5), 1)+[(2, 3, 4, 5)]
        h = ProjectionPatternInventory(max_depth=0, projection_budget=4)
        r = h.inspect(source)
        self.assertEqual(r['profile']['projection']['status'], 'encoding_cap')
        self.assertFalse(r['summary']['closed'])
        check_projected_tree(h, r['root']['key']);h.close()

    def test_false_elimination_missing_boundary_and_invalid_encoding_rejected(self):
        equations = [dict(variables=[1, 2], rhs=0), dict(variables=[1, 3], rhs=1)]
        keep = [2, 3];cert = project_equations(equations, keep, Counter())
        mutations = []
        bad = copy.deepcopy(cert);bad['boundary'] = [];mutations.append(bad)
        bad = copy.deepcopy(cert);bad['rows'][-1]['using'] = [];mutations.append(bad)
        bad = copy.deepcopy(cert);bad['rows'][-1]['rhs'] ^= 1;mutations.append(bad)
        bad = copy.deepcopy(cert);bad['internal'] = [];mutations.append(bad)
        bad = copy.deepcopy(cert);bad['rows'][0]['using'] = [1];mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):
                check_projection(equations, keep, bad, Counter())
        blocks = encode_boundary(cert, 100, Counter())
        bad = copy.deepcopy(blocks);bad[0][0][0] *= -1
        for bad_blocks in ([], bad, [blocks[0][:1]], [[blocks[0][0]]*2]):
            with self.assertRaises(ValueError):
                check_boundary(cert, bad_blocks, Counter())
        source = parity((1, 2, 3), 0)+parity((1, 2, 4), 1)+[(3, 4)]
        h = ProjectionPatternInventory(max_depth=0)
        with patch('experiments.cnf_affine_projection.encode_boundary', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'Missing projected'):
                h.inspect(source)
        h.close()

    def test_cold_source_lifting_and_corruption(self):
        source = parity((1, 2, 3), 0)+parity((1, 2, 4), 1)+[(3, 4)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'projection.sqlite3'
            old = AffinePatternInventory(path, max_depth=0);before = old.inspect(source)
            saved = list(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h = ProjectionPatternInventory(path, max_depth=0);first = h.inspect(source)
            self.assertNotEqual(before['root']['key'], first['root']['key'])
            for key, payload in saved:
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()[0], payload)
            h.close();raw = path.read_bytes()
            h = ProjectionPatternInventory(path, max_depth=0);second = h.inspect(source)
            self.assertEqual(first['root'], second['root'])
            self.assertEqual(second['metrics'].get('inserted_nodes', 0), 0)
            self.assertEqual(second['metrics']['inserted_sources'], 0)
            check_projected_tree(h, second['root']['key']);h.close()
            self.assertEqual(raw, path.read_bytes())
            h = ProjectionPatternInventory(path, max_depth=0);key = first['root']['key']
            bad = copy.deepcopy(h._load(key));bad['edge']['names'] = [1, 2]
            with self.assertRaises(ValueError): h._check(key, bad)
            bad = copy.deepcopy(h._load(key));bad['profile']['projection']['certificate']['boundary'] = []
            h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (json.dumps(bad), key));h.db.commit();h.close()
            h = ProjectionPatternInventory(path, max_depth=0)
            with self.assertRaises(ValueError): h.inspect(source)
            h.close()

    def test_configuration(self):
        for budget in (-1, True, 65537, 1.5):
            with self.assertRaises(ValueError): ProjectionPatternInventory(projection_budget=budget)


if __name__ == '__main__':
    unittest.main()
