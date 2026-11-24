from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random
import unittest

from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_census import closure
from experiments.cnf_probe_binary_lazy import lazy_closure
from experiments.cnf_probe_binary_closure import BinaryClosureSolver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_probe_lifetime import _UP
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.validate_cnf_ranked_binary_targets import TABLES


class LazyBinaryClosureTests(unittest.TestCase):
    def inputs(self, source):
        cnf, names = native.normalize(source)
        fixed, trace, conflict = native.propagate(cnf, Counter())
        return (cnf, names, native.token(cnf, Counter())), (fixed, trace, conflict, 0)

    def compare(self, source):
        canonical, up = self.inputs(source)
        before = deepcopy((canonical, up))
        old = closure(canonical, up, Counter())
        counts = Counter()
        new = lazy_closure(canonical, up, counts)
        self.assertEqual(new['status'], old['status'])
        self.assertEqual(new['nodes'], old['nodes'])
        self.assertEqual((canonical, up), before)
        return new, counts

    def test_misses_do_not_normalize_or_serialize_residual(self):
        for clauses in ([], [[3, 4]], [[3, 4], [-3, -4]], [[3, 4, 5]]):
            canonical, up = self.inputs([[1]] + [[-1] + c for c in clauses])
            with patch.object(native, 'normalize', side_effect=AssertionError('Normalization on miss')):
                with patch.object(native, 'token', side_effect=AssertionError('Key on miss')):
                    counts = Counter()
                    result = lazy_closure(canonical, up, counts)
            self.assertFalse(result['nodes'])
            self.assertNotIn('root', result)
            self.assertNotIn('residual', result)
            self.assertEqual(counts['lazy_normalizations_avoided'], 1)

    def test_duplicates_sparse_residual_labels_and_exact_proof(self):
        source = [[1], [17]] + [[-1, 29*a, 91*b] for a,b in product((-1,1), repeat=2)]
        source += [[-17, 29, 91], [29, 91, 50]]
        result, counts = self.compare(source)
        self.assertEqual(result['status'], 'binary-unsat')
        self.assertEqual(len(result['nodes']), 2)
        self.assertEqual(counts['lazy_raw_scc_calls'], 1)
        self.assertEqual(counts['lazy_certificate_scc_calls'], 1)
        self.assertEqual(counts['lazy_canonical_reconstructions'], 1)
        with TemporaryDirectory() as td:
            path = Path(td)/'db'
            writer = native.ResidualSolver(path)
            try:
                for item in result['nodes']: writer._store(item['key'], item['node'])
            finally: writer.close()
            for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
                reader = cls(path)
                try:
                    for item in result['nodes']:
                        self.assertEqual(reader._read(item['key']), item['node'])
                finally: reader.close()

    def test_already_canonical_path_has_no_extra_scc(self):
        for source in ([[a,b*2] for a,b in product((-1,1), repeat=2)], [[1,2],[-1,-2]]):
            new, counts = self.compare(source)
            self.assertEqual(counts['lazy_already_canonical_calls'], 1)
            self.assertEqual(counts['closure_scc_calls'], 1)
            self.assertEqual(counts['lazy_raw_calls'], 0)

    def test_exhaustive_conditioned_binary_and_mixed_cases(self):
        choices = [[2,3], [2,-3], [-2,3], [-2,-3], [2,3,4], [-2,-3,-4], [-1,2,3]]
        hits = 0
        for mask in range(1 << len(choices)):
            source = [[1]] + [[-1] + c for i,c in enumerate(choices) if mask >> i & 1]
            result, counts = self.compare(source)
            binary = [c for c in native.restrict_scan(self.inputs(source)[0][0], self.inputs(source)[1][0]) if len(c)==2]
            truth = any(native.holds(binary, dict(enumerate(bits,1))) for bits in product((False,True),repeat=4))
            self.assertEqual(bool(result['nodes']), not truth)
            hits += bool(result['nodes'])
        self.assertGreater(hits, 0)

    def test_binary_sat_does_not_decide_full_unsat_cnf(self):
        source = [[1]] + [[-1, a*2, b*3, c*4] for a,b,c in product((-1,1),repeat=3)]
        source += [[2,3], [-2,-3]]
        result, counts = self.compare(source)
        self.assertEqual(result['status'], 'binary-sat')
        self.assertFalse(result['nodes'])
        self.assertFalse(any(native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4)))

    def test_incomplete_units_fail_closed_and_conflicts_rejected(self):
        canonical, up = self.inputs([[1], [2,3]])
        for cnf in (((1,), (2,3)), ((), (2,3))):
            r = lazy_closure((cnf, (), ''), ({9: True}, [], None, 0), Counter())
            self.assertEqual(r['status'], 'not-unit-closed')
            self.assertFalse(r['nodes'])
        with self.assertRaises(ValueError): lazy_closure(canonical, ({},[],0,0), Counter())

    def test_corrupted_canonical_path_and_unit_lift_rejected(self):
        result, _ = self.compare([[1]] + [[-1,a*2,b*3] for a,b in product((-1,1),repeat=2)])
        for field in ('path', 'units', 'key'):
            bad = deepcopy(result)
            if field == 'path': bad['nodes'][0]['node']['proof']['forward'][0][1] = 9999
            elif field == 'units': bad['nodes'][1]['node']['proof']['trace'][0][1] = 9999
            else: bad['nodes'][1]['key'] = 'wrong'
            writer = native.ResidualSolver()
            try:
                with self.assertRaises(ValueError):
                    for item in bad['nodes']: writer._store(item['key'], item['node'])
            finally: writer.close()

    def test_random_search_exact_payloads_and_budget_stops(self):
        for limit in (0, 1, 16, 256):
            old = BinaryClosureSolver(node_limit=limit, affine_variables=1, handoff_bytes=131072)
            new = LazyBinaryClosureSolver(node_limit=limit, affine_variables=1, handoff_bytes=131072)
            try:
                for seed in range(30):
                    rng = random.Random(seed)
                    source = [[v if rng.randrange(2) else -v for v in rng.sample(range(1,9),3)] for _ in range(34)]
                    a, b = attempt(old,source), attempt(new,source)
                    self.assertEqual(a['status'], b['status'])
                    if a['result'] is not None:
                        self.assertEqual(a['result']['model'], b['result']['model'])
                    self.assertEqual(a['metrics'].get('expanded_nodes',0), b['metrics'].get('expanded_nodes',0))
                    self.assertLessEqual(b['metrics'].get('expanded_nodes',0), limit)
                    def stored(solver, table):
                        present = solver.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                        return dict(solver.db.execute(f'SELECT id,payload FROM {table}')) if present else {}
                    for table in TABLES:
                        self.assertEqual(stored(old,table), stored(new,table))
                    self.assertEqual((new._handoff_held,new._transferred_held), (0,0))
                    self.assertIsNone(_UP.get())
            finally:
                old.close(); new.close()


if __name__ == '__main__': unittest.main()
