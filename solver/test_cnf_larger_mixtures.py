from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from experiments.cnf_larger_mixtures import FAMILIES,SIZES,catalog,generate,attempt
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_cross_family import truth_table
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_ordered_normalization import OrderedNormalizationSolver
from solver.test_cnf_publication_batches import blocking,replay


class LargerMixtureTests(unittest.TestCase):
    def test_catalog_is_deterministic_and_complete(self):
        cases=catalog();self.assertEqual(cases,catalog());self.assertEqual(len(cases),108)
        self.assertEqual({c['size'] for c in cases},set(SIZES))
        self.assertEqual({c['family'] for c in cases},set(FAMILIES))
        for i,c in enumerate(cases):
            self.assertEqual(c['case'],i)
            self.assertTrue(all(type(l) is int and l for cl in c['source'] for l in cl))

    def test_repeated_keys_and_original_names(self):
        for family in FAMILIES:
            source,edited,repeated=generate(family,24,0)
            a,names=normalize(source);b,newnames=normalize(repeated)
            self.assertEqual(a,b);self.assertEqual(newnames,tuple(2*v+1 for v in names))
            self.assertNotEqual(source,edited)

    def test_small_unlabelled_mixtures_match_exhaustive_truth(self):
        solvers=[cls() for cls in (BatchedPublicationSolver,ProofNormalizationSolver,OrderedNormalizationSolver)]
        for s in solvers:self.addCleanup(s.close)
        for family in FAMILIES:
            for sample in (0,1):
                for source in generate(family,12,sample):
                    truth=truth_table(source)['answer'];results=[attempt(s,source) for s in solvers]
                    self.assertTrue(all(r['status']==('sat' if truth else 'unsat') for r in results))
                    for r in results[1:]:
                        for field in ('answer','model','root','authority','quotient_choice'):
                            self.assertEqual(r['result'][field],results[0]['result'][field])

    def test_budget_is_unknown_and_committed_prefix_survives(self):
        for cls in (BatchedPublicationSolver,ProofNormalizationSolver,OrderedNormalizationSolver):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=cls(path,node_limit=3,batch_rows=1,leaves=False)
                try:
                    r=attempt(s,blocking(5));self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['result'])
                    self.assertEqual(r['metrics']['expanded_nodes'],3)
                    self.assertFalse(s.db.in_transaction);self.assertFalse(s.db.pending)
                    self.assertIsNone(getattr(s,'_proof_memo',None))
                    rows=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                    s.node_limit=1000;self.assertEqual(attempt(s,blocking(5))['status'],'unsat')
                    self.assertLessEqual(rows.items(),dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')).items())
                finally:s.close()
                self.assertTrue(replay(path))

    def test_other_runtime_errors_are_not_silenced(self):
        class Broken:
            def solve(self,source):raise RuntimeError('Unexpected defect')
        with self.assertRaisesRegex(RuntimeError,'Unexpected defect'):attempt(Broken(),[])


if __name__=='__main__':unittest.main()
