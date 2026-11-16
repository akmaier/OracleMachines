from itertools import product
from unittest.mock import patch
import random,tempfile,unittest
from pathlib import Path
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_unsat_support import CoreBank,checked_subset
from experiments.cnf_causal_support import CausalSupportExtractor as SupportExtractor
from experiments.cnf_unsat_support import SupportExtractor as OldExtractor
from experiments.cnf_causal_support import slice_trace
from collections import Counter


class CausalSupportTests(unittest.TestCase):
    def make(self,**kw):
        s=ResidualSolver(**kw);self.addCleanup(s.close);return s
    def test_unused_unit_removed_from_conflict_support(self):
        s=self.make();f=[[-9],[1],[-1]];s.solve(f)
        old=OldExtractor(s).source_core(f);e=SupportExtractor(s);new=e.source_core(f)
        self.assertEqual(len(old['source']),3);self.assertEqual(new['source'],[[-1],[1]])
        self.assertEqual(e.counts['unit_trace_steps_removed'],1)
    def test_reason_dependencies_are_transitive_and_ordered(self):
        cnf=[[9],[1],[-1,2],[-2,3],[-3]];trace=[[9,0],[1,1],[2,2],[3,3]]
        self.assertEqual(slice_trace(cnf,trace,{3},Counter()),trace[1:])
        with self.assertRaises(ValueError):slice_trace(cnf,trace,{20},Counter())
    def test_irrelevant_units_before_negative_child_disappear(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False)
        f=[list(c) for c in product(*[(-i,i) for i in (1,2,3)])]+[[-9]];s.solve(f)
        old=OldExtractor(s).source_core(f);new=SupportExtractor(s).source_core(f)
        self.assertEqual(len(old['source']),9);self.assertEqual(len(new['source']),8)
        self.assertTrue(all(abs(l)!=9 for c in new['source'] for l in c))
    def test_index_mode_does_not_publish_and_materialization_matches(self):
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False)
        f=[list(c) for c in product(*[(-i,i) for i in (1,2,3)])]+[[-9]];s.solve(f);before=s.archive_storage()
        with patch.object(s,'_store',side_effect=AssertionError('Index-only publication')),patch.object(s,'_expand',side_effect=AssertionError('Fresh extraction search')):
            proposal=SupportExtractor(s,materialize=False).source_core(f)
        self.assertEqual(s.archive_storage(),before)
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh materialization search')):
            actual=SupportExtractor(s).source_core(f);self.assertEqual(actual,proposal);self.assertFalse(s.solve(actual['source'])['answer'])
    def check_core(self,s,source):
        before=s.solve(source);self.assertFalse(before['answer'])
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh extraction search')):
            e=SupportExtractor(s);core=e.source_core(source)
            self.assertLessEqual({tuple(sorted(c)) for c in core['source']},{tuple(sorted(c)) for c in source})
            self.assertFalse(s.solve(core['source'])['answer'])
        return e,core
    def test_all_two_variable_formulas(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2)]
        assignments=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        for mask in range(512):
            f=[c for i,c in enumerate(clauses) if mask>>i&1]
            if any(holds(f,a) for a in assignments):continue
            s=ResidualSolver()
            try:
                _,core=self.check_core(s,f)
                self.assertFalse(any(holds(core['source'],a) for a in assignments))
            finally:s.close()
    def test_split_and_unit_child_proofs(self):
        f=[list(c) for c in product(*[(-i,i) for i in (1,2,3)])]
        s=self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False)
        e,core=self.check_core(s,f+[[9],[9,10]])
        self.assertGreater(e.counts['support_kind_split'],0);self.assertGreater(e.counts['support_kind_units'],0)
        self.assertLess(len(core['source']),len(f)+2)
    def test_implication_paths_and_component(self):
        s=self.make();f=[[1,2],[1,-2],[-1,2],[-1,-2],[3,4]]
        e,core=self.check_core(s,f);self.assertGreater(e.counts['support_kind_implications'],0);self.assertLess(len(core['source']),len(f))
        f=[list(c) for c in product(*[(-i,i) for i in (1,2,3)])]+[[4,5,6]]
        e,core=self.check_core(s,f);self.assertGreater(e.counts['support_kind_component'],0);self.assertEqual(len(core['source']),8)
    def test_hall_and_subsumption_supports(self):
        f=[[3*i+1,3*i+2,3*i+3] for i in range(4)]
        f += [[-(3*i+h),-(3*j+h)] for h in (1,2,3) for i in range(4) for j in range(i+1,4)]
        s=self.make();e,core=self.check_core(s,f+[[13,14,15]])
        self.assertGreater(e.counts['support_kind_hall-v1'],0);self.assertEqual(len(core['source']),len(f))
        e,core=self.check_core(s,f+[[1,2,3,13]])
        self.assertGreater(e.counts['support_kind_positive-subsumption-v1'],0);self.assertEqual(len(core['source']),len(f))
    def test_raw_coordinate_transport_and_checked_weakening(self):
        s=self.make();source=[[10],[-10],[20,30]];_,core=self.check_core(s,source)
        query=core['source']+[[-40,50,60]]
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh publication search')):
            hit=CoreBank(s,[core]).reuse(query);self.assertTrue(hit['inserted']);self.assertFalse(s.solve(query)['answer'])
            self.assertIsNone(CoreBank(s,[core]).reuse([[1],[-1]]))
        self.assertFalse(s.solve([[1],[-1]])['answer'])
    def test_missing_sat_and_wrong_subset_reject(self):
        s=self.make();key=s._canonical([[1],[-1]])[2]
        with self.assertRaises(ValueError):SupportExtractor(s).extract(key)
        sat=s.solve([[1]])
        with self.assertRaises(ValueError):SupportExtractor(s).extract(sat['root'])
        with self.assertRaises(ValueError):checked_subset(s,[[1],[2]],[[1]])
        self.check_core(s,[[1],[-1]])
        with self.assertRaises(ValueError):checked_subset(s,[[1],[2]],[[1],[-1]])
        with self.assertRaises(ValueError):CoreBank(s,[dict(source=[[1],[-1]],root='foreign')])
    def test_empty_clause_query_and_duplicate_input(self):
        s=self.make();_,core=self.check_core(s,[[10],[-10],[-10]])
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            checked_subset(s,[[],[10],[-10]],core['source']);self.assertFalse(s.solve([[]])['answer'])
    def test_persistent_cold_derived_proofs(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'proofs';s=ResidualSolver(path)
            _,core=self.check_core(s,[[10],[-10],[20,30]])
            checked_subset(s,core['source']+[[40,50]],core['source']);s.close()
            cold=ResidualSolver(path)
            try:
                with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):
                    for key, in cold.db.execute('SELECT id FROM cnf_residual_v1'):cold._read(key)
                    self.assertFalse(cold.solve(core['source']+[[40,50]])['answer'])
            finally:cold.close()
    def test_random_three_variable_cores_against_truth_tables(self):
        rng=random.Random(20261116);clauses=[tuple(sign*(i+1) for i,sign in enumerate(s) if sign) for s in product((-1,0,1),repeat=3) if any(s)]
        assignments=[dict(zip((1,2,3),b)) for b in product((False,True),repeat=3)]
        for _ in range(100):
            source=rng.sample(clauses,rng.randrange(4,20))
            if any(holds(source,a) for a in assignments):continue
            s=ResidualSolver(leaves=False,decompose=False,positive_subsumption=False)
            try:
                _,core=self.check_core(s,source);self.assertFalse(any(holds(core['source'],a) for a in assignments))
            finally:s.close()


if __name__=='__main__':unittest.main()
