from collections import Counter
from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy,unittest
from experiments.cnf_binary_clause_cover import BinaryClauseCoverSolver,inspect,compile_cover
from experiments.cnf_binary_subset import BinarySubsetSolver
from experiments.cnf_residual_dag import ResidualSolver,normalize,holds,two_cnf
from experiments.cnf_cross_family import generate,truth_table


def fixture(width=3):
    return [[i for i in range(1,width+1)]]+[[a,b] for i in range(1,width+1) for a,b in ((-i,width+i),(-i,-width-i))]


class BinaryClauseCoverTests(unittest.TestCase):
    def test_satisfiable_binary_core_refutes_wide_clause(self):
        for width in (3,4):
            source=fixture(width);cnf,_=normalize(source);counts=Counter()
            self.assertIsNotNone(two_cnf([c for c in cnf if len(c)==2],Counter())[0])
            proof,cover=inspect(cnf,counts)
            self.assertIsNone(proof);self.assertIsNotNone(cover)
            s=BinaryClauseCoverSolver();self.addCleanup(s.close);r=s.solve(source)
            self.assertFalse(r['answer']);self.assertEqual(r['metrics']['binary_cover_found'],1)
            self.assertEqual(r['metrics']['binary_cover_pair_reuses'],1)
            self.assertLessEqual(r['archive_nodes'],2*width-3)

    def test_corrupt_or_incomplete_paths_are_rejected(self):
        cnf,_=normalize(fixture());_,cover=inspect(cnf,Counter());s=ResidualSolver();self.addCleanup(s.close)
        bad=copy.deepcopy(cover);bad['paths'][0]=[]
        with self.assertRaises(ValueError):compile_cover(s,cnf,bad)
        bad=copy.deepcopy(cover);bad['paths'][0][0][1]=cover['clause_index']
        with self.assertRaises(ValueError):compile_cover(s,cnf,bad)
        self.assertEqual(s.archive_storage()[0],0)

    def test_budget_and_missing_binary_variable_are_inconclusive(self):
        cnf,_=normalize(fixture());counts=Counter()
        self.assertIsNone(inspect(cnf,counts,root_limit=2)[1])
        self.assertEqual(counts['binary_cover_reach_roots'],2)
        self.assertGreater(counts['binary_cover_budget_skips'],0)
        source=fixture();source[0].append(99);cnf,_=normalize(source)
        self.assertIsNone(inspect(cnf,Counter())[1])
        s=BinaryClauseCoverSolver();self.addCleanup(s.close);self.assertTrue(s.solve(source)['answer'])
        for limit in (-1,True):
            with self.assertRaises(ValueError):inspect(cnf,Counter(),root_limit=limit)

    def test_exhaustive_binary_subsets_with_wide_clause(self):
        binary=[c for vs in combinations((1,2,3),2) for c in product(*[(v,-v) for v in vs])]
        s=BinaryClauseCoverSolver();self.addCleanup(s.close)
        for mask in range(1<<len(binary)):
            source=[c for i,c in enumerate(binary) if mask>>i&1]+[(1 if mask&1 else -1,2,-3)]
            expected=any(holds(source,dict(zip((1,2,3),bits))) for bits in product((False,True),repeat=3))
            self.assertEqual(s.solve(source)['answer'],expected,source)

    def test_signed_renaming_cold_reader_and_prior_payloads(self):
        source=fixture(4);names={i:(-1 if i%2 else 1)*(31+17*i) for i in range(1,9)}
        source=[[(1 if l>0 else -1)*names[abs(l)] for l in c] for c in reversed(source)]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BinaryClauseCoverSolver(path)
            try:
                s.solve([[999]]);old=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                r=s.solve(source);self.assertFalse(r['answer']);self.assertTrue(old.items()<=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')).items())
                final=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            s=ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Cold write')):
                    self.assertFalse(s.solve(source)['answer'])
                self.assertEqual(final,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()

    def test_disabled_leaves_and_existing_subsets(self):
        source=fixture();s=BinaryClauseCoverSolver(leaves=False);self.addCleanup(s.close)
        with patch('experiments.cnf_binary_clause_cover.inspect',side_effect=AssertionError('Disabled')):
            self.assertFalse(s.solve(source)['answer'])
        for f in ([],[[]],[[1],[-1]],[[1,2],[-1,2],[1,-2],[-1,-2],[1,3,4]]):
            a=BinarySubsetSolver();b=BinaryClauseCoverSolver()
            try:self.assertEqual(a.solve(f)['answer'],b.solve(f)['answer'])
            finally:a.close();b.close()

    def test_shared_reachability_and_known_root(self):
        rename={1:1,2:2,3:4,4:3,5:5,6:6}
        source=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in fixture()]
        source += [[1,2,3]];cnf,_=normalize(source);counts=Counter()
        _,cover=inspect(cnf,counts);self.assertIsNotNone(cover)
        # Source clauses can share literal queries; a completed search is reused.
        self.assertGreater(counts['binary_cover_reach_hits'],0)
        s=BinaryClauseCoverSolver();self.addCleanup(s.close);s.solve(source)
        with patch.object(s,'_expand',side_effect=AssertionError('Known source')):
            self.assertFalse(s.solve(source)['answer'])

    def test_cross_family_truth(self):
        for family in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for sample in range(4):
                source=generate(family,12,sample,35);s=BinaryClauseCoverSolver()
                try:self.assertEqual(s.solve(source)['answer'],truth_table(source)['answer'])
                finally:s.close()


if __name__=='__main__':unittest.main()
