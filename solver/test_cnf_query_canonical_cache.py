from collections import Counter
from itertools import product
from unittest.mock import patch
import sys,unittest
from experiments.cnf_query_canonical_cache import QueryCanonicalSolver
from experiments.cnf_known_quotient import KnownQuotientSolver
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_cross_family import truth_table,generate
from solver.test_cnf_multiblock_equivalence import two_blocks,table


class QueryCanonicalCacheTests(unittest.TestCase):
    def test_exact_immutable_triple_and_input_snapshot(self):
        s=QueryCanonicalSolver();self.addCleanup(s.close);raw=[[12,-51,12],[51,12]]
        with s.canonical_session():
            a=s._canonical(raw);self.assertEqual(a,ResidualSolver._canonical(s,raw))
            with patch.object(KnownQuotientSolver,'_canonical',side_effect=AssertionError('Repeated normalization')):
                self.assertIs(s._canonical(raw),a)
            raw[0][0]=-12;b=s._canonical(raw);self.assertNotEqual(a,b)
            self.assertIsInstance(a[0],tuple);self.assertIsInstance(a[1],tuple);self.assertIsInstance(a[2],str)
        self.assertIsNone(s.canonical_cache);self.assertEqual(s.canonical_payload,0)

    def test_rejects_equal_hash_invalid_literals_before_hit(self):
        s=QueryCanonicalSolver();self.addCleanup(s.close)
        with s.canonical_session():
            s._canonical([[1,2]])
            for raw in ([[True,2]],[[1.0,2]],[[0,2]],[[1,'2']]):
                with self.assertRaises(ValueError):s._canonical(raw)
            self.assertEqual(s.counts['canonical_cache_hits'],0)
            s._canonical([[1,2]]);self.assertEqual(s.counts['canonical_cache_hits'],1)

    def test_result_names_not_confused_by_same_normalized_formula(self):
        s=QueryCanonicalSolver();self.addCleanup(s.close)
        with s.canonical_session():
            a=s._canonical([[10,40]]);b=s._canonical([[2,7]])
            self.assertEqual(a[0],b[0]);self.assertEqual(a[2],b[2]);self.assertNotEqual(a[1],b[1])
            self.assertEqual(s._canonical([[10,40]])[1],(10,40))

    def test_capacity_eviction_and_oversized_skip(self):
        s=QueryCanonicalSolver(canonical_cache_bytes=4096);self.addCleanup(s.close)
        with s.canonical_session():
            for i in range(60):
                raw=[[i+1,-(i+2),i+3]];self.assertEqual(s._canonical(raw),ResidualSolver._canonical(s,raw))
                self.assertLessEqual(s.canonical_payload+sys.getsizeof(s.canonical_cache),4096)
            self.assertGreater(s.counts['canonical_cache_evictions'],0)
            s._canonical([list(range(1,1000))]);self.assertGreater(s.counts['canonical_cache_oversized_skips'],0)
            self.assertLessEqual(s.canonical_payload+sys.getsizeof(s.canonical_cache),4096)
        self.assertEqual(s.canonical_payload,0)

    def test_charged_bound_covers_reachable_python_objects(self):
        s=QueryCanonicalSolver(canonical_cache_bytes=1024*1024);self.addCleanup(s.close)
        def size(value,seen):
            if id(value) in seen:return 0
            seen.add(id(value));n=sys.getsizeof(value)
            if isinstance(value,dict):n+=sum(size(k,seen)+size(v,seen) for k,v in value.items())
            elif isinstance(value,tuple):n+=sum(size(v,seen) for v in value)
            return n
        with s.canonical_session():
            for raw in ([[1,2],[2,-3]],[[2**200,-3],[4]],[[1,-1],[]],[],[[3,3,3]]):
                s._canonical(raw)
                self.assertLessEqual(size(s.canonical_cache,set()),s.canonical_payload+sys.getsizeof(s.canonical_cache))

    def test_clear_on_success_failure_and_between_queries(self):
        s=QueryCanonicalSolver();self.addCleanup(s.close)
        for raw in (two_blocks(True),two_blocks(),[[True]]):
            try:s.solve(raw)
            except ValueError:pass
            self.assertIsNone(s.canonical_cache);self.assertEqual(s.canonical_payload,0)
        with self.assertRaises(RuntimeError):
            with s.canonical_session():
                s._canonical([[1]])
                with s.canonical_session():pass
        self.assertIsNone(s.canonical_cache)
        with s.canonical_session():
            before=s.counts['canonical_cache_misses'];s._canonical([[1]])
            self.assertEqual(s.counts['canonical_cache_misses'],before+1)

    def test_disabled_cache_is_original_normalization(self):
        s=QueryCanonicalSolver(canonical_cache_bytes=0);self.addCleanup(s.close)
        with s.canonical_session():
            s._canonical([[1]]);s._canonical([[1]])
        self.assertEqual(s.counts['normalization_literal_visits'],2)
        self.assertFalse(any(k.startswith('canonical_cache_') for k in s.counts))
        for bad in (True,-1,1,3.14):
            with self.assertRaises(ValueError):QueryCanonicalSolver(canonical_cache_bytes=bad)

    def test_all_small_inputs_match_reference_normalization(self):
        s=QueryCanonicalSolver();self.addCleanup(s.close)
        clauses=[(),(1,),(2,),(-1,),(-2,),(1,-1),(1,1),(1,2),(-1,2),(-2,1)]
        with s.canonical_session():
            for parts in product(clauses,repeat=3):
                expected=ResidualSolver._canonical(s,parts)
                self.assertEqual(s._canonical(parts),expected);self.assertEqual(s._canonical(parts),expected)

    def test_stream_truth_models_proofs_and_choices_unchanged(self):
        a=KnownQuotientSolver();b=QueryCanonicalSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        sources=[two_blocks(True),two_blocks()]+[generate(f,12,i,820) for f in ('random-three','coupled-parity','gated-horn','graph-colouring') for i in (0,1)]
        for raw in sources:
            for source in (raw,raw+[[10,-20,30]]):
                x=a.solve(source);y=b.solve(source)
                for field in ('answer','model','root','authority','quotient_choice'):self.assertEqual(x[field],y[field])
                self.assertEqual(y['answer'],truth_table(source)['answer'])
                if y['answer']:self.assertTrue(holds(source,y['model']))
                self.assertLessEqual(y['metrics'].get('canonical_cache_peak_bytes',0),128*1024)
                self.assertIsNone(b.canonical_cache)
        for t in ('cnf_residual_v1','cnf_binary_equivalence_v2','cnf_binary_equivalence_v3'):self.assertEqual(table(a,t),table(b,t))


if __name__=='__main__':unittest.main()
