from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_variable_elimination import (
    VariableEliminationInventory, discover_elimination, check_elimination, lift_elimination)
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds, ResidualSolver


def assignments(variables):
    return (dict(zip(variables, values)) for values in itertools.product((False, True), repeat=len(variables)))


def projection_check(test, source, variable):
    proof = dict(variable=variable)
    try:
        target = check_elimination(source, proof, Counter())
    except ValueError:
        return False  # Growth is a deliberate refusal, not a satisfiability claim.
    rest = sorted({abs(lit) for clause in source for lit in clause} - {variable})
    for model in assignments(rest):
        expected = any(holds(source, model | {variable: value}) for value in (False, True))
        test.assertEqual(holds(target, model), expected, (source, variable, model))
        if expected:
            lifted = lift_elimination(source, proof, model, Counter())
            test.assertTrue(holds(source, lifted))
            for v in {abs(lit) for clause in target for lit in clause}:
                test.assertEqual(lifted[v], model[v])
    return True


class VariableEliminationTests(unittest.TestCase):
    def test_exhaustive_projection_and_constructive_lift(self):
        clauses = [tuple(s * (i + 1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        accepted = 0
        for mask in range(512):
            source = tuple(c for i, c in enumerate(clauses) if mask >> i & 1)
            support = {abs(lit) for c in source for lit in c}
            for v in support:
                accepted += projection_check(self, source, v)
            proof = discover_elimination(source, Counter())
            if proof['variable'] is not None:
                self.assertTrue(projection_check(self, source, proof['variable']))
        self.assertGreater(accepted, 900)

    def test_random_unlabelled_edits_and_colliding_large_names(self):
        rng = random.Random(202611121405)
        for _ in range(200):
            cnf, _ = normalize([tuple(rng.choice((-1, 1)) * v for v in rng.sample(range(1, 7), rng.randrange(1, 5)))
                                for _ in range(rng.randrange(1, 20))])
            # Non-contiguous identifiers and sign changes must not affect exactness.
            names = {v: ((1 << 130) + v * 64) * rng.choice((-1, 1)) for v in range(1, 7)}
            cnf = tuple(tuple(names[abs(l)] * (1 if l > 0 else -1) for l in c) for c in cnf)
            for v in sorted({abs(lit) for c in cnf for lit in c}):
                projection_check(self, cnf, v)
            edited = tuple(dict.fromkeys(cnf + ((abs(names[1]),),)))
            proof = discover_elimination(edited, Counter())
            if proof['variable'] is not None:
                self.assertTrue(projection_check(self, edited, proof['variable']))

    def test_all_pairs_tautologies_duplicates_growth_and_caps(self):
        source = ((1, 2), (1, 3), (-1, 4), (-1, 5))
        proof = dict(variable=1)
        self.assertEqual(check_elimination(source, proof, Counter()), ((2, 4), (2, 5), (3, 4), (3, 5)))
        with self.assertRaises(ValueError): check_elimination(source, proof, Counter(), pair_limit=3)
        # Omitting even one pair admits a model with neither extension to x.
        model = {2: False, 3: True, 4: False, 5: True}
        self.assertTrue(holds(((2, 5), (3, 4), (3, 5)), model))
        self.assertFalse(any(holds(source, model | {1: b}) for b in (False, True)))
        for source in [((1, 2), (-1, -2)), ((1, 2), (-1, 2), (2,)), ((1,), (-1,)), ((1, 2), (1, 3))]:
            self.assertTrue(projection_check(self, source, 1))
        growing = ((1, 2, 3), (1, 4, 5), (-1, 6, 7), (-1, 8, 9))
        with self.assertRaises(ValueError): check_elimination(growing, proof, Counter())
        self.assertIsNone(discover_elimination(source, Counter(), candidate_limit=0)['variable'])
        self.assertIsNone(check_elimination(source, {'variable': None}, Counter()))

    def test_invalid_certificates_sources_models_and_independent_check(self):
        source = ((1, 2), (-1, 3))
        for certificate in ({}, {'variable': 1, 'target': []}, {'variable': True}, {'variable': 0},
                            {'variable': -1}, {'variable': 4}, {'variable': '1'}, []):
            with self.assertRaises(ValueError): check_elimination(source, certificate, Counter())
        for source in (((0,),), ((True,),), ((1, 1),), ((1, -1),), ((1,), (1,))):
            with self.assertRaises(ValueError): discover_elimination(source, Counter())
            with self.assertRaises(ValueError): check_elimination(source, {'variable': None}, Counter())
        source = ((1, 2), (-1, 3))
        for limit in (-1, True, 1.2, '3'):
            with self.assertRaises(ValueError): discover_elimination(source, Counter(), pair_limit=limit)
            with self.assertRaises(ValueError): VariableEliminationInventory(elimination_candidate_limit=limit)
        for model in ({}, {2: False, 3: False}, {2: 1, 3: True}, {2: True, 3: True, -2: False}):
            with self.assertRaises(ValueError): lift_elimination(source, {'variable': 1}, model, Counter())
        with patch('experiments.cnf_variable_elimination.discover_elimination', side_effect=AssertionError('discovery called')):
            self.assertEqual(check_elimination(source, {'variable': 1}, Counter()), ((2, 3),))

    def test_integrated_frontier_persistence_lifts_and_corruption(self):
        frontier = json.loads(Path('experiments/results/cnf-variable-elimination-probe/raw-opportunity.json').read_text())['rows']
        cases = [r['cnf'] for r in frontier[:18]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive.db'; old = PreparedProbeInventory(path, max_depth=0)
            before_rows = []
            for source in cases: old.inspect(source)
            for table in ('cnf_patterns_v1', 'cnf_pattern_sources_v1'):
                before_rows.append((table, old.db.execute(f'SELECT id,payload FROM {table}').fetchall()))
            old.close(); h = VariableEliminationInventory(path, max_depth=0); solver = ResidualSolver(path)
            for source in cases: h.inspect(source)
            nodes = [(key, json.loads(payload)) for key, payload in h.db.execute('SELECT id,payload FROM cnf_patterns_v1')
                     if json.loads(payload)['kind'] == 'eliminate']
            self.assertGreater(len(nodes), 10)
            for key, node in nodes:
                child = h._load(node['edge']['key']); solved = solver.solve(child['cnf'])
                if solved['answer']:
                    self.assertTrue(holds(node['cnf'], h.lift(key, solved['model'])))
            for table, rows in before_rows:
                for key, payload in rows:
                    self.assertEqual(h.db.execute(f'SELECT payload FROM {table} WHERE id=?', (key,)).fetchone(), (payload,))
            h.close(); solver.close(); snapshot = path.read_bytes()
            h = VariableEliminationInventory(path, max_depth=0)
            with patch('experiments.cnf_variable_elimination.discover_elimination', side_effect=AssertionError('cold discovery called')):
                for key, _ in nodes: self.assertIsNotNone(h._load(key))
                for source in cases: self.assertFalse(h.inspect(source)['metrics'].get('inserted_nodes', 0))
            h.close(); self.assertEqual(path.read_bytes(), snapshot)
            key, original = nodes[0]
            for mutation in ('variable', 'edge', 'summary', 'source'):
                bad = copy.deepcopy(original)
                if mutation == 'variable': bad['elimination']['variable'] = 100000
                elif mutation == 'edge': bad['edge']['names'] = []
                elif mutation == 'summary': bad['summary']['unresolved_literals'] += 1
                else: bad['cnf'] = []
                h = VariableEliminationInventory(path, max_depth=0)
                with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(bad), key))
                with self.assertRaises(ValueError): h._load(key)
                with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(original), key))
                h.close()


if __name__ == '__main__': unittest.main()
