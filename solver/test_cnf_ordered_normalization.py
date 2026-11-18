from collections import Counter
from itertools import product,combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random,sqlite3,unittest
from experiments.cnf_ordered_normalization import normalize_ordered,OrderedNormalizationSolver
from experiments.cnf_residual_dag import normalize,restrict_scan
from experiments.cnf_publication_batches import BatchedPublicationSolver,NATIVE,V2,V3
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_publication_batches import blocking,replay
from solver.test_cnf_multiblock_equivalence import two_blocks,table


class OrderedNormalizationTests(unittest.TestCase):
    def equal(self,source):
        a=Counter();b=Counter()
        self.assertEqual(normalize(source,a),normalize_ordered(source,b))
        self.assertEqual(a['normalization_literal_visits'],b['normalization_literal_visits'])

    def test_exhaustive_literal_sequences_and_clause_pairs(self):
        clauses=[p for n in range(5) for p in product((-2,-1,1,2),repeat=n)]
        for clause in clauses:self.equal([clause])
        for a in clauses[:21]:
            for b in clauses[:21]:self.equal([a,b])

    def test_exhaustive_three_variable_formulas(self):
        clauses=[tuple(sorted(s*(i+1) for i,s in enumerate(signs) if s))
                 for signs in product((-1,0,1),repeat=3)]
        for n in range(4):
            for source in combinations(clauses,n):self.equal(source)

    def test_invalid_literals_not_hidden_by_empty_or_tautology(self):
        for bad in (True,False,0,1.0,'1',None):
            for source in ([[],[bad]],[[1,-1,bad]],[[-2,1,bad]]):
                with self.assertRaises(ValueError):normalize_ordered(source)
                with self.assertRaises(ValueError):normalize(source)

    def test_sparse_signed_names_duplicates_and_huge_integers(self):
        for source in ([[-999,-7,2,13]], [[7,-7],[999]],[[7,2,2],[-999,-7]],
                       [[-(2**10000),3,2**9999]],[[7,2],[-999,-7],[2,7]],[] ):self.equal(source)
        a,names=normalize_ordered([[-999,-7,2,13]])
        self.assertEqual(a,((-4,-2,1,3),));self.assertEqual(names,(2,7,13,999))

    def test_restriction_preserves_only_local_order(self):
        # Removing literals can reverse lexicographic clause order and create duplicates.
        cnf=((1,2),(1,3),(2,3))
        raw=restrict_scan(cnf,{1:False})
        self.assertEqual(raw,((2,),(3,),(2,3)));self.assertNotEqual(tuple(sorted(raw)),raw)
        self.equal(raw);self.equal(restrict_scan(((1,2),(2,)),{1:False}))
        for source in (blocking(3),[[-1,2,3],[-2,3],[-3,-1,2]]):
            cnf,_=normalize(source)
            for assignment in ({1:False},{2:True},{1:False,3:True}):self.equal(restrict_scan(cnf,assignment))

    def test_random_mixtures_and_mutations(self):
        rng=random.Random(810271)
        for _ in range(500):
            source=[[rng.choice((-100,-9,-2,2,9,100)) for _ in range(rng.randrange(7))]
                    for _ in range(rng.randrange(8))]
            self.equal(source);self.equal([list(reversed(c)) for c in reversed(source)])

    def test_stream_proofs_models_counters_and_warm_reuse(self):
        a=BatchedPublicationSolver();b=OrderedNormalizationSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        sources=[blocking(4),two_blocks(True),two_blocks()]+[generate(f,12,i,840)
                 for f in ('random-three','coupled-parity','gated-horn','graph-colouring') for i in (0,1)]
        for source in sources:
            x=a.solve(source);y=b.solve(source)
            for key in ('answer','model','root','authority','quotient_choice'):self.assertEqual(x[key],y[key])
            self.assertEqual(x['metrics'],{k:v for k,v in y['metrics'].items() if not k.startswith('ordered_')})
            self.assertEqual(y['answer'],truth_table(source)['answer'])
            self.assertIsNone(b._verification_canonical)
        for t in (NATIVE,V2,V3):self.assertEqual(table(a,t),table(b,t))
        with patch.object(b,'_expand',side_effect=AssertionError('Warm expansion')):
            self.assertFalse(b.solve(blocking(4))['answer'])

    def test_failure_rollback_retry_and_cold_proof_read(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=OrderedNormalizationSolver(path,leaves=False)
            try:
                s.solve([]);before=table(s,NATIVE)
                with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
                    with self.assertRaises(sqlite3.OperationalError):s.solve(blocking(4))
                self.assertEqual(table(s,NATIVE),before);self.assertFalse(s.db.pending)
                self.assertEqual(set(s.checked),set(before));self.assertIsNone(s._verification_canonical)
                self.assertFalse(s.solve(blocking(4))['answer'])
            finally:s.close()
            self.assertEqual(len(replay(path)),5)


if __name__=='__main__':unittest.main()
