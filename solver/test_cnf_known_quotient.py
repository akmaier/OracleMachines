from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,unittest
from experiments.cnf_known_quotient import KnownQuotientSolver
from experiments.cnf_multiblock_equivalence import MultiEquivalenceSolver,discover_all,check_blocks,MultiEquivalenceStore
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_cross_family import truth_table,generate
from solver.test_cnf_multiblock_equivalence import two_blocks,table,V2


def prepare(s,source,kind):
    cnf,_=normalize(source);e=discover_all(cnf,Counter());target,_=check_blocks(cnf,e if kind=='all' else e[:1],Counter())
    model,key=s._visit(target);return key,model


class KnownQuotientTests(unittest.TestCase):
    def test_first_negative_hit_avoids_acquisition(self):
        s=KnownQuotientSolver();self.addCleanup(s.close);source=two_blocks(True);key,_=prepare(s,source,'first');before=table(s,'cnf_residual_v1')
        with patch.object(s,'_visit',side_effect=AssertionError('Fresh child')):r=s.solve(source)
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['quotient_choice_first_hits'],1)
        self.assertEqual(r['quotient_choice']['selected'],'first');self.assertEqual(r['quotient_choice']['candidates'][-1]['key'],key)
        self.assertEqual(table(s,'cnf_residual_v1'),before);self.assertEqual(r['metrics']['multi_applied_blocks'],1)
        self.assertEqual(r['authority'],'binary-equivalence-negative-v2')

    def test_known_all_preferred_and_single_alternative_not_constructed(self):
        for unsat in (False,True):
            s=KnownQuotientSolver();self.addCleanup(s.close);raw=two_blocks(unsat);prepare(s,raw,'first');key,_=prepare(s,raw,'all')
            with patch.object(s,'_visit',side_effect=AssertionError('Known all')):r=s.solve(raw)
            self.assertEqual(r['answer'],not unsat);self.assertEqual(r['metrics']['quotient_choice_all_hits'],1)
            self.assertEqual(len(r['quotient_choice']['candidates']),1);self.assertEqual(r['quotient_choice']['candidates'][0]['key'],key)
            self.assertNotIn('quotient_choice_alternates_built',r['metrics'])

    def test_known_positive_first_model_coordinate_transport(self):
        source=two_blocks();names={1:-101,2:17,3:-8,4:900,5:42}
        renamed=[[(1 if l>0 else -1)*names[abs(l)] for l in c] for c in source]
        for raw in (source,renamed):
            s=KnownQuotientSolver();self.addCleanup(s.close);prepare(s,raw,'first')
            with patch.object(s,'_visit',side_effect=AssertionError('Fresh positive')):r=s.solve(raw)
            self.assertTrue(r['answer']);self.assertTrue(holds(raw,r['model']));self.assertEqual(r['metrics']['quotient_choice_first_hits'],1)

    def test_both_miss_keeps_complete_reduction_and_proofs(self):
        a=KnownQuotientSolver();b=MultiEquivalenceSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        for raw in (two_blocks(True),two_blocks()):
            x=a.solve(raw);y=b.solve(raw);self.assertEqual(x['answer'],y['answer'])
            if x['quotient_choice'] is not None:
                self.assertEqual(x['quotient_choice']['selected'],'all')
        for t in ('cnf_residual_v1','cnf_binary_equivalence_v2','cnf_binary_equivalence_v3'):self.assertEqual(table(a,t),table(b,t))

    def test_cold_positive_and_negative_children_and_old_reader(self):
        for unsat in (False,True):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=KnownQuotientSolver(path);prepare(s,two_blocks(unsat),'first');s.close();s=KnownQuotientSolver(path)
                try:
                    with patch.object(s,'_visit',side_effect=AssertionError('Cold acquisition')):r=s.solve(two_blocks(unsat))
                    self.assertEqual(r['answer'],not unsat);self.assertEqual(r['metrics']['quotient_choice_first_hits'],1)
                    if unsat:self.assertIsNotNone(MultiEquivalenceStore(s).read(r['root']))
                finally:s.close()

    def test_corrupt_native_child_is_not_treated_as_known(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=KnownQuotientSolver(path);key,_=prepare(s,two_blocks(),'first')
            with s.db:s.db.execute('UPDATE cnf_residual_v1 SET payload=? WHERE id=?',(json.dumps(dict(format='forged',answer=True)),key))
            s.close();s=KnownQuotientSolver(path)
            try:
                with self.assertRaises(ValueError):s.solve(two_blocks())
            finally:s.close()

    def test_disabled_reuse_and_warm_source_skip_choice(self):
        s=KnownQuotientSolver(reuse=False);self.addCleanup(s.close);r=s.solve(two_blocks(True));self.assertIsNone(r['quotient_choice'])
        s=KnownQuotientSolver();self.addCleanup(s.close);s.solve(two_blocks(True))
        with patch.object(s,'choose_quotient',side_effect=AssertionError('Warm choice')):self.assertFalse(s.solve(two_blocks(True))['answer'])

    def test_exhaustive_signed_mixtures_and_edited_sources(self):
        wide=[list(c) for c in product((1,-1),(3,-3),(5,-5))]
        for sign in (1,-1):
            s=KnownQuotientSolver();self.addCleanup(s.close)
            for mask in range(1,256):
                raw=[[-1,2],[1,-2],[-3,sign*4],[3,-sign*4]]+[c for i,c in enumerate(wide) if mask>>i&1]
                r=s.solve(raw);self.assertEqual(r['answer'],truth_table(raw)['answer'])
                if r['answer']:self.assertTrue(holds(raw,r['model']))
            for raw in (two_blocks(True)[1:],two_blocks()+[[1,-3,5]],generate('random-three',12,2,724)):
                r=s.solve(raw);self.assertEqual(r['answer'],truth_table(raw)['answer'])


if __name__=='__main__':unittest.main()
