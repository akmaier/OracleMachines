from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize, restriction_engine
from experiments.cnf_shared_clause_check import SharedClauseReconstruction
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.cnf_single_pass_inventory import SinglePassCheckInventory
from experiments.cnf_simplification import (check_simplification, discover_simplification,
    reconstruct_simplification_scan, simplification_reconstruction)
from solver.test_cnf_implied_subsumption import implication_source


def outcome(engine, cnf, assigned, units):
    try:
        return ('ok', engine(cnf, assigned, Counter(), units=units))
    except (ValueError, TypeError) as error:
        return (type(error).__name__, str(error))


class SinglePassCheckTests(unittest.TestCase):
    def test_exhaustive_reconstruction_including_rejected_fixed_points(self):
        literals = (-2, -1, 1, 2)
        clauses = [()] + [(a,) for a in literals] + list(itertools.product(literals, repeat=2))
        assignments = [{i+1: v for i, v in enumerate(values) if v is not None}
                       for values in itertools.product((None, False, True), repeat=2)]
        cached = SharedClauseReconstruction(256)
        for size in range(4):
            for cnf in itertools.product(clauses, repeat=size):
                for assigned in assignments:
                    for units in (False, True):
                        expected = outcome(reconstruct_simplification_scan, cnf, assigned, units)
                        for engine in (reconstruct_single_pass, cached):
                            self.assertEqual(outcome(engine, cnf, assigned, units), expected)
                        if not units:
                            for a, b in itertools.product((False, True), repeat=2):
                                complete = {1: a, 2: b}
                                if all(complete[v] == value for v, value in assigned.items()):
                                    self.assertEqual(holds(expected[1], complete), holds(cnf, complete))
        self.assertLessEqual(cached.state()['peak_units'], 256)

    def test_whole_checker_all_policies_and_forged_certificates(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        for mask in range(512):
            cnf, _ = normalize([c for i, c in enumerate(clauses) if mask >> i & 1])
            for units, pure in itertools.product((False, True), repeat=2):
                options = dict(units=units, pure=pure)
                cert = discover_simplification(cnf, Counter(), **options)
                expected = check_simplification(cnf, cert, Counter(), **options)
                with simplification_reconstruction(reconstruct_single_pass):
                    self.assertEqual(check_simplification(cnf, cert, Counter(), **options), expected)
        for cnf, cert in (
            (((1,), (-1, 2)), dict(units=[], conflict=None, pure_rounds=[])),
            (((1,), (-1, 2)), dict(units=[[1, 0]], conflict=None, pure_rounds=[])),
            (((1, 2), (-1, 3)), dict(units=[[1, 0]], conflict=None, pure_rounds=[])),
            (((1, 2), (-1, 3)), dict(units=[], conflict=0, pure_rounds=[])),
            (((1, 2), (-1, 3)), dict(units=[], conflict=None, pure_rounds=[[1]])),
        ):
            with simplification_reconstruction(reconstruct_single_pass):
                with self.assertRaises(ValueError):check_simplification(cnf, cert, Counter())

    def test_sharing_lazy_copy_and_mutable_edits(self):
        cnf = ((1, -2, 3), (-1, 4), (5, 6), ())
        counts = Counter()
        result = reconstruct_single_pass(cnf, {1: True}, counts, units=False)
        self.assertEqual(result, [(4,), (5, 6), ()])
        self.assertIs(result[1], cnf[2]); self.assertIs(result[2], cnf[3])
        self.assertEqual(counts['single_check_shared_clauses'], 2)
        self.assertEqual(counts['single_check_copied_literals'], 1)
        mutable = [[1, 2, 3], [-1, 4]]
        first = reconstruct_single_pass(mutable, {}, Counter(), units=False)
        mutable[0][0] = -1
        self.assertEqual(first, [(1, 2, 3), (-1, 4)])
        self.assertEqual(reconstruct_single_pass(mutable, {1: True}, Counter(), units=False), [(2, 3), (4,)])
        # A first falsification may allocate a prefix before a later satisfaction.
        self.assertEqual(reconstruct_single_pass(((2, -1, 3, 4),), {1: True, 4: True}, Counter(), units=False), [])

    def test_unusual_input_fallbacks_and_cache_invalidation(self):
        class Int(int):pass
        class Tuple(tuple):pass
        sources = [((True, 2),), ((0, 2),), ((Int(1), 2),), (Tuple((1, 2)),), (('x', 2),)]
        for cnf in sources:
            for assigned in ({}, {1: True}, {1: 1}, {True: False}, {-1: True}, {0: True}):
                for units in (False, True):
                    expected = outcome(reconstruct_simplification_scan, cnf, assigned, units)
                    self.assertEqual(outcome(reconstruct_single_pass, cnf, assigned, units), expected)
        cached = SharedClauseReconstruction(5); counts = Counter(); clause = (1, 2)
        cached((clause,), {}, counts, units=False)
        cached((clause,), {}, counts, units=False)
        equal = tuple(list(clause)); cached((equal,), {}, counts, units=False)
        self.assertEqual(counts['clause_check_hits'], 1)
        self.assertEqual(counts['clause_check_evictions'], 1)
        mutable = [1, 2]; cached((mutable,), {}, counts, units=False); mutable[0] = -1
        self.assertEqual(cached((mutable,), {1: True}, counts, units=False), [(2,)])
        for limit in (0, 1):
            engine = SharedClauseReconstruction(limit)
            self.assertEqual(engine((clause,), {}, Counter(), units=False), [clause])
            self.assertEqual(engine.state()['entries'], 0)
        cached.clear(); self.assertEqual(cached.state()['units'], 0)
        for invalid in (-1, True, 1.5, '5'):
            with self.assertRaises(ValueError):SharedClauseReconstruction(invalid)

    def test_random_edits_large_identifiers_and_order(self):
        rng = random.Random(202611091420)
        for _ in range(1000):
            n = rng.randrange(1, 20); base = 1 << 1024 if rng.randrange(5) == 0 else 0
            cnf = tuple(tuple(rng.choice((-1, 1))*(base+rng.randrange(1, n+1))
                              for _ in range(rng.randrange(6))) for _ in range(rng.randrange(40)))
            for _ in range(3):
                assigned = {base+i: rng.choice((True, False)) for i in rng.sample(range(1, n+3), rng.randrange(n+2))}
                for units in (False, True):
                    self.assertEqual(outcome(reconstruct_single_pass, cnf, assigned, units),
                                     outcome(reconstruct_simplification_scan, cnf, assigned, units))
            edited = cnf+((base+1,),)
            for units in (False, True):
                self.assertEqual(outcome(reconstruct_single_pass, edited, assigned, units),
                                 outcome(reconstruct_simplification_scan, edited, assigned, units))

    def test_scope_restoration_and_discovery_independence(self):
        cnf = ((1,), (-1, 2)); cert = dict(units=[[1, 0], [2, 1]], conflict=None, pure_rounds=[])
        counts = Counter()
        def forbidden(*args, **kwargs):raise AssertionError('used discovery reconstruction')
        with self.assertRaises(RuntimeError):
            with restriction_engine(forbidden), simplification_reconstruction(reconstruct_single_pass):
                self.assertEqual(check_simplification(cnf, cert, counts, pure=False), ((), {1: True, 2: True}))
                with simplification_reconstruction(None):check_simplification(cnf, cert, counts, pure=False)
                raise RuntimeError('restore')
        check_simplification(cnf, cert, counts, pure=False)
        self.assertEqual(counts['single_check_calls'], 1)
        self.assertEqual(counts['simplification_reconstruction_literals'], 6)

    def test_archive_identity_cold_replay_and_corruption(self):
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        cases = [[c for i, c in enumerate(clauses) if mask >> i & 1] for mask in range(512)]
        rng = random.Random(202611091421)
        cases += [implication_source()]+[[tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), 3))
                                         for _ in range(24)] for _ in range(20)]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = []
            for cls in (IndexedRestrictionInventory, SinglePassCheckInventory):
                path = Path(tmp)/(cls.__name__+'.db'); h = cls(path, max_depth=1)
                for source in cases:h.inspect(source)
                h.close(); snapshots.append(path.read_bytes())
            self.assertEqual(*snapshots)
            path = Path(tmp)/'IndexedRestrictionInventory.db'; h = SinglePassCheckInventory(path, max_depth=1)
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):h._load(key)
            for source in cases:
                result = h.inspect(source)
                self.assertEqual(result['metrics'].get('inserted_nodes', 0), 0)
                self.assertEqual(result['metrics']['inserted_sources'], 0)
            result = h.inspect(implication_source()); key = result['root']['key']; bad = copy.deepcopy(h._load(key))
            h.close(); self.assertEqual(path.read_bytes(), snapshots[0])
            attempt = next(a for a in bad['profile']['probing']['attempts'] if a['certificate']['units'])
            attempt['certificate']['units'][0][1] = 9999
            h = SinglePassCheckInventory(path, max_depth=1)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(bad), key))
            h.close(); h = SinglePassCheckInventory(path, max_depth=1)
            with self.assertRaises(ValueError):h.inspect(implication_source())
            h.close()

    def test_saved_frontier_proofs(self):
        rows = json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        old = IndexedRestrictionInventory(); new = SinglePassCheckInventory()
        for row in rows:
            self.assertEqual(encode(old._check_probes(row['cnf'], row['probing'])),
                             encode(new._check_probes(row['cnf'], row['probing'])))
        old.close(); new.close(); self.assertEqual(len(rows), 148)
