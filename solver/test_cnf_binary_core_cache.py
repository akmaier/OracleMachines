from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,unittest
from experiments.cnf_binary_core_cache import BinaryCoreCache,CachedBinaryEquivalenceSolver,parse_key,core_key,TABLE,encode
from experiments.cnf_binary_equivalence import discover,check_substitution
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,TABLE as EXT
from experiments.cnf_residual_dag import ResidualSolver,normalize,holds
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_cross_family import truth_table,generate
from solver.test_cnf_binary_equivalence import negative


def rows(s,table):return dict(s.db.execute(f'SELECT id,payload FROM {table}'))


class BinaryCoreCacheTests(unittest.TestCase):
    def test_transports_indices_after_wide_insertions(self):
        s=CachedBinaryEquivalenceSolver();self.addCleanup(s.close)
        source=normalize(negative())[0];a=s.binary_cores.find(source)
        edit=tuple(sorted(set(source+((-6,-5,-4),(2,3,6)))))
        with patch('experiments.cnf_binary_core_cache.compute',side_effect=AssertionError('Repeated SCC')):
            b=s.binary_cores.find(edit)
        self.assertEqual(b,discover(edit,Counter()));check_substitution(edit,b,Counter())
        self.assertNotEqual(a,b);self.assertEqual(s.counts['equiv_cache_memory_hits'],1)
        # Returned mutable evidence cannot poison the retained local-coordinate trees.
        b['forward'][0][2]=-1
        self.assertEqual(s.binary_cores.find(edit),discover(edit,Counter()))

    def test_binary_edits_and_coordinate_changes_miss(self):
        s=CachedBinaryEquivalenceSolver();self.addCleanup(s.close);source=normalize(negative())[0]
        s.binary_cores.find(source);binary=next(c for c in source if len(c)==2)
        for edited in (tuple(c for c in source if c!=binary),tuple(sorted(source+((-9,8),))),tuple(tuple(l*2 for l in c) for c in source)):
            self.assertEqual(s.binary_cores.find(edited),discover(edited,Counter()))
        self.assertEqual(s.counts['equiv_cache_misses'],4);self.assertEqual(s.counts['equiv_cache_memory_hits'],0)

    def test_null_cache_is_discovery_only_and_checks_eligibility(self):
        s=CachedBinaryEquivalenceSolver();self.addCleanup(s.close)
        source=((-3,2),(1,2,3));self.assertIsNone(s.binary_cores.find(source))
        with patch('experiments.cnf_binary_core_cache.compute',side_effect=AssertionError('Repeated miss')):
            self.assertIsNone(s.binary_cores.find(tuple(sorted(source+((-3,-2,-1),)))))
            for formula in ((),((),),((1,),),((1,2),),((1,2,3),)):
                self.assertIsNone(s.binary_cores.find(formula))
        self.assertEqual(s.counts['equiv_cache_memory_hits'],1)
        self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],1)

    def test_cold_cache_recomputes_once_and_preserves_database(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=CachedBinaryEquivalenceSolver(path);source=normalize(negative())[0]
            try:expected=s.binary_cores.find(source);before=rows(s,TABLE)
            finally:s.close()
            s=SnapshotResidualSolver(path);cache=BinaryCoreCache(s)
            try:
                self.assertEqual(cache.find(source),expected)
                self.assertEqual(s.counts['equiv_cache_validated_entries'],1)
                with patch('experiments.cnf_binary_core_cache.compute',side_effect=AssertionError('Twice')):
                    self.assertEqual(cache.find(source),expected)
                self.assertEqual(rows(s,TABLE),before)
            finally:s.close()

    def test_cold_outcome_corruption_and_key_corruption_rejected(self):
        s=CachedBinaryEquivalenceSolver();self.addCleanup(s.close);source=normalize(negative())[0]
        s.binary_cores.find(source);key,payload=next(iter(rows(s,TABLE).items()))
        with self.assertRaises(ValueError):s.binary_cores.verify(key,'null')
        for bad in (key+' ',key.replace(':[',': [',1),core_key(((1,1),)),core_key(((1,-1),)),core_key(((True,2),)),core_key(((0,2),)),core_key(((1,2),(1,2))),core_key(())):
            with self.assertRaises(ValueError):parse_key(bad)
        with s.db:s.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?',('null',key))
        cache=BinaryCoreCache(s)
        with self.assertRaises(ValueError):cache.find(source)
        # A false positive on a no-block core is also rejected.
        empty=core_key(((-3,2),))
        with self.assertRaises(ValueError):cache.verify(empty,payload)

    def test_all_small_binary_cores_match_and_reuse(self):
        binary=[tuple(sorted(c)) for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        s=CachedBinaryEquivalenceSolver(persistent_cache=False);self.addCleanup(s.close)
        for mask in range(1<<len(binary)):
            core=tuple(sorted(c for i,c in enumerate(binary) if mask>>i&1))
            a=tuple(sorted(core+((1,2,3),)));b=tuple(sorted(core+((-3,-2,-1),)))
            self.assertEqual(s.binary_cores.find(a),discover(a,Counter()))
            self.assertEqual(s.binary_cores.find(b),discover(b,Counter()))
        self.assertEqual(len(s.binary_cores.checked),4095)
        self.assertEqual(s.counts['equiv_cache_memory_hits'],4095)

    def test_full_solver_payloads_and_truth_match_on_edits(self):
        for persistent in (False,True):
            a=CompactBinaryEquivalenceSolver();b=CachedBinaryEquivalenceSolver(persistent_cache=persistent)
            try:
                sources=[negative()]+[generate(f,12,i,36) for f in ('random-three','coupled-parity','gated-horn','graph-colouring') for i in range(2)]
                for source in sources:
                    for raw in (source,source+[[1,-2,3]],source[:-1]):
                        x=a.solve(raw);y=b.solve(raw)
                        self.assertEqual(x['answer'],truth_table(raw)['answer']);self.assertEqual(x['answer'],y['answer']);self.assertEqual(x['model'],y['model'])
                        self.assertEqual(x['root'],y['root']);self.assertEqual(x['authority'],y['authority'])
                for table in ('cnf_residual_v1',EXT):self.assertEqual(rows(a,table),rows(b,table))
            finally:a.close();b.close()

    def test_warm_source_and_disabled_discovery_do_no_cache_work(self):
        s=CachedBinaryEquivalenceSolver();self.addCleanup(s.close);r=s.solve(negative())
        with patch.object(s.binary_cores,'find',side_effect=AssertionError('Warm discovery')),patch.object(s,'_expand',side_effect=AssertionError('Warm search')):
            self.assertEqual(s.solve(negative())['answer'],r['answer'])
        t=CachedBinaryEquivalenceSolver(leaves=False);self.addCleanup(t.close)
        with patch.object(t.binary_cores,'find',side_effect=AssertionError('Disabled')):self.assertFalse(t.solve(negative())['answer'])


if __name__=='__main__':unittest.main()
