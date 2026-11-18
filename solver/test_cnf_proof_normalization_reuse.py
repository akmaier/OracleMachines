from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,sqlite3,unittest
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver,NATIVE,V2,V3
from experiments.cnf_residual_dag import ResidualSolver,normalize,token
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_publication_batches import blocking,replay
from solver.test_cnf_multiblock_equivalence import two_blocks,table


class ProofNormalizationTests(unittest.TestCase):
    def session(self,s):
        # Exercise private producer/consumer hooks without solving a whole query.
        s._proof_memo={};self.addCleanup(setattr,s,'_proof_memo',None)

    def test_hit_reuses_triple_but_checks_child_key_and_answer(self):
        s=ProofNormalizationSolver(leaves=False);self.addCleanup(s.close);self.session(s)
        source=blocking(2);model,key=s._visit(source);self.assertIsNone(model)
        with patch.object(BatchedPublicationSolver,'_canonical',side_effect=AssertionError('Repeated normalization')):
            s._negative_child(key,source)
            with self.assertRaises(ValueError):s._negative_child('wrong',source)
        positive=[[1]];_,key=s._visit(positive)
        with self.assertRaisesRegex(ValueError,'UNSAT child'):s._negative_child(key,positive)

    def test_invalid_equal_hash_literals_rejected_before_lookup(self):
        s=ProofNormalizationSolver();self.addCleanup(s.close);self.session(s)
        _,key=s._visit([[-1],[1]])
        for bad in ([[-1],[True]],[[-1],[1.0]],[[-1],[0]],[[-1],['1']]):
            with self.assertRaises(ValueError):s._negative_child(key,bad)

    def test_missing_child_not_authenticated_by_pure_result(self):
        s=ProofNormalizationSolver();self.addCleanup(s.close);self.session(s)
        raw=((-1,),(1,));s._producer_input=raw;result=s._canonical(raw)
        self.assertIn(raw,s._proof_memo)
        with self.assertRaisesRegex(ValueError,'Missing checked'):s._negative_child(result[2],raw)

    def test_name_maps_and_mutable_input_snapshots_remain_bound(self):
        s=ProofNormalizationSolver();self.addCleanup(s.close);self.session(s)
        a=[[7,-11]];s._producer_input=a;x=s._canonical(a)
        b=[[2,-3]];s._producer_input=b;y=s._canonical(b)
        self.assertEqual(x[0],y[0]);self.assertNotEqual(x[1],y[1]);a[0][0]=9
        self.assertEqual(s._proof_memo[((7,-11),)][0][1],(7,11))

    def test_strict_cap_eviction_oversize_and_object_charge(self):
        s=ProofNormalizationSolver(proof_memo_bytes=4096);self.addCleanup(s.close);self.session(s)
        def size(value,seen):
            if id(value) in seen:return 0
            seen.add(id(value));n=sys.getsizeof(value)
            if isinstance(value,dict):n+=sum(size(k,seen)+size(v,seen) for k,v in value.items())
            elif isinstance(value,tuple):n+=sum(size(v,seen) for v in value)
            return n
        for raw in ([[i,-(i+1)]] for i in range(1,60)):
            s._producer_input=raw;s._canonical(raw)
            self.assertLessEqual(size(s._proof_memo,set()),sys.getsizeof(s._proof_memo)+s._proof_payload)
            self.assertLessEqual(sys.getsizeof(s._proof_memo)+s._proof_payload,4096)
        self.assertGreater(s.counts['proof_memo_evictions'],0)
        for raw in ([[2**200,-(2**200)],[]],[list(range(1,1000))]):
            s._producer_input=raw;s._canonical(raw)
            self.assertLessEqual(size(s._proof_memo,set()),sys.getsizeof(s._proof_memo)+s._proof_payload)
        self.assertGreater(s.counts['proof_memo_oversized_skips'],0)

    def test_only_visitation_admits_and_scope_clears_on_failure(self):
        s=ProofNormalizationSolver();self.addCleanup(s.close);self.session(s)
        s._canonical([[1]]);self.assertFalse(s._proof_memo)
        with self.assertRaises(RuntimeError):s.solve([[1]])
        s._proof_memo=None
        for source in ([[True]],blocking(3)):
            s.node_limit=0
            with self.assertRaises((ValueError,RuntimeError)):s.solve(source)
            self.assertIsNone(s._proof_memo);self.assertEqual(s._proof_payload,0)
            self.assertIsNone(s._producer_input);self.assertIsNone(s._consumer_input)

    def test_failed_commit_clears_memo_and_pending_proof_checks(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ProofNormalizationSolver(path,leaves=False)
            try:
                s.solve([]);before=table(s,NATIVE)
                with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
                    with self.assertRaises(sqlite3.OperationalError):s.solve(blocking(4))
                self.assertIsNone(s._proof_memo);self.assertFalse(s.db.pending);self.assertEqual(table(s,NATIVE),before)
                self.assertEqual(set(s.checked),set(before));self.assertFalse(s.solve(blocking(4))['answer'])
            finally:s.close()
            self.assertEqual(len(replay(path)),5)

    def test_stream_and_warm_reuse_match_prior(self):
        a=BatchedPublicationSolver();b=ProofNormalizationSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        for source in [blocking(4),two_blocks(True),two_blocks()]+[generate(f,12,i,840) for f in ('random-three','coupled-parity','gated-horn','graph-colouring') for i in (0,1)]:
            x=a.solve(source);y=b.solve(source)
            for f in ('answer','model','root','authority','quotient_choice'):self.assertEqual(x[f],y[f])
            self.assertEqual(y['answer'],truth_table(source)['answer']);self.assertIsNone(b._proof_memo)
        for t in (NATIVE,V2,V3):self.assertEqual(table(a,t),table(b,t))
        with patch.object(b,'_expand',side_effect=AssertionError('Warm expansion')):r=b.solve(blocking(4))
        self.assertFalse(r['metrics'].get('proof_memo_producers',0));self.assertFalse(r['metrics'].get('proof_memo_lookups',0))

    def test_invalid_cap_fails_before_opening(self):
        for cap in (True,0,-1,1,3.14):
            with self.assertRaises(ValueError):ProofNormalizationSolver(proof_memo_bytes=cap)


if __name__=='__main__':unittest.main()
