from copy import deepcopy
from itertools import combinations, product
from unittest.mock import patch
import json, random, unittest
from experiments import cnf_capacity_core as c


def pigeonhole(demands, capacity):
    source = [[1 + d * capacity + g for g in range(capacity)] for d in range(demands)]
    source += [[-(1 + a * capacity + g), -(1 + b * capacity + g)]
               for g in range(capacity) for a, b in combinations(range(demands), 2)]
    return source


def truth(source):
    names = sorted({abs(v) for clause in source for v in clause})
    return any(all(any(assignment[abs(v)] == (v > 0) for v in clause) for clause in source)
               for bits in product((False, True), repeat=len(names))
               for assignment in [dict(zip(names, bits))])


class CapacityCoreTests(unittest.TestCase):
    def proof(self):
        source = pigeonhole(4, 3)
        proof, _ = c.discover(source)
        self.assertIsNotNone(proof)
        return source, proof

    def test_unsat_capacity(self):
        source, proof = self.proof()
        self.assertEqual((len(proof['demands']), len(proof['groups'])), (4, 3))
        self.assertFalse(c.check(source, proof)['answer'])

    def test_sat_capacity_is_only_unknown(self):
        for d, n in ((1, 3), (3, 3), (2, 4)):
            self.assertIsNone(c.discover(pigeonhole(d, n))[0])

    def test_empty_clause_and_empty_formula(self):
        proof, _ = c.discover([[]], work_limit=0)
        self.assertFalse(c.check([[]], proof)['answer'])
        self.assertIsNone(c.discover([])[0])

    def test_signed_sparse_permutation(self):
        source, _ = self.proof(); rng = random.Random(47)
        mapping = dict(zip(range(1, 13), rng.sample(range(101, 10000), 12)))
        signs = {v: rng.choice((-1, 1)) for v in mapping}
        renamed = [[mapping[abs(v)] * signs[abs(v)] * (1 if v > 0 else -1)
                    for v in reversed(clause)] for clause in reversed(source)]
        proof, _ = c.discover(renamed)
        self.assertFalse(c.check(renamed, proof)['answer'])

    def test_added_mixed_constraints_and_duplicate_noise(self):
        source, proof = self.proof()
        mixed = source + [[100, -101, 102], [-102, 103], [104, -104], source[0] * 2]
        self.assertFalse(c.check(mixed, proof)['answer'])
        found, _ = c.discover(mixed)
        self.assertFalse(c.check(mixed, found)['answer'])

    def test_dropped_exclusion_rejects_old_proof(self):
        source, proof = self.proof()
        with self.assertRaises(ValueError): c.check(source[:-1], proof)

    def test_dropped_demand_can_be_sat(self):
        source, proof = self.proof(); edited = source[1:]
        self.assertTrue(truth(edited))
        with self.assertRaises(ValueError): c.check(edited, proof)
        self.assertIsNone(c.discover(edited)[0])

    def test_changed_exclusion_sign_rejects(self):
        source, proof = self.proof(); edited = deepcopy(source); edited[-1][0] *= -1
        with self.assertRaises(ValueError): c.check(edited, proof)

    def test_overlapping_demands_rejected(self):
        proof = dict(format=c.FORMAT, demands=[[1], [1, 2]], groups=[[1, 2]])
        with self.assertRaises(ValueError): c.check([[1], [1, 2], [-1, -2]], proof)

    def test_duplicate_demand_rejected(self):
        proof = dict(format=c.FORMAT, demands=[[1], [1]], groups=[[1]])
        with self.assertRaises(ValueError): c.check([[1]], proof)

    def test_missing_or_duplicate_partition_vertex_rejected(self):
        source, proof = self.proof()
        for op in (lambda p: p['groups'][0].pop(), lambda p: p['groups'][0].append(p['groups'][1][0])):
            bad = deepcopy(proof); op(bad)
            with self.assertRaises(ValueError): c.check(source, bad)

    def test_no_strict_deficiency_rejected(self):
        proof = dict(format=c.FORMAT, demands=[[1, 2]], groups=[[1, 2]])
        with self.assertRaises(ValueError): c.check([[1, 2], [-1, -2]], proof)

    def test_complement_conflict_needs_no_clause(self):
        proof = dict(format=c.FORMAT, demands=[[-8], [8]], groups=[[-8, 8]])
        self.assertFalse(c.check([[-8], [8]], proof)['answer'])

    def test_hall_subset_with_spare_global_capacity(self):
        source = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        source += [[-a, -b] for a, b in combinations(range(1, 7), 2)]
        proof, _ = c.discover(source)
        self.assertEqual((len(proof['demands']), len(proof['groups'])), (2, 1))
        self.assertFalse(c.check(source, proof)['answer'])

    def test_budget_stop_is_not_a_verdict(self):
        proof, diagnostic = c.discover(pigeonhole(4, 3), work_limit=0)
        self.assertIsNone(proof); self.assertEqual(diagnostic['reason'], 'work-limit')

    def test_reject_malformed_source_and_proof(self):
        for source in ([[True]], [[0]], [[1.0]], [1], 'cnf'):
            with self.assertRaises(ValueError): c.discover(source)
        source, proof = self.proof()
        for field, value in (('format', 'wrong'), ('demands', {}), ('groups', [True])):
            bad = deepcopy(proof); bad[field] = value
            with self.assertRaises(ValueError): c.check(source, bad)
        with self.assertRaises(ValueError): c.discover(source, work_limit=True)

    def test_cold_check_without_search(self):
        source, proof = self.proof()
        with patch.object(c, 'discover', side_effect=AssertionError('search')):
            self.assertFalse(c.check(source, json.loads(json.dumps(proof)))['answer'])

    def test_pipeline_short_circuit_and_fallback(self):
        from experiments import cnf_external_cutsets as e
        with patch.object(e, 'discover', side_effect=AssertionError('old search')):
            proof, _ = c.pipeline(pigeonhole(4, 3))
            self.assertFalse(c.check_pipeline(pigeonhole(4, 3), proof)['answer'])
        proof, _ = c.pipeline([[1, 2]])
        self.assertEqual(proof['kind'], 'external')
        self.assertTrue(c.check_pipeline([[1, 2]], proof)['answer'])

    def test_exhaustive_two_variable_soundness(self):
        clauses = [[s*v for v, s in enumerate(signs, 1) if s]
                   for signs in product((-1, 0, 1), repeat=2)]
        for mask in range(512):
            source = [clause for i, clause in enumerate(clauses) if mask >> i & 1]
            proof, _ = c.discover(source)
            if proof is not None:
                self.assertFalse(truth(source)); self.assertFalse(c.check(source, proof)['answer'])

    def test_satisfiable_adversarial_mixtures(self):
        rng = random.Random(277)
        for _ in range(100):
            source = [[rng.choice((-1, 1))*v for v in rng.sample(range(1, 6), rng.randrange(1, 5))]
                      for _ in range(10)]
            source = [clause for clause in source if any(v > 0 for v in clause)]
            self.assertIsNone(c.discover(source)[0])


if __name__ == '__main__': unittest.main()
