from collections import Counter
from itertools import product
from unittest.mock import patch
import unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_partition_screen import PartitionScreen,publish_screened_branch
from experiments.cnf_terminal_first_screen import TerminalFirstScreen


class TerminalFirstScreenTests(unittest.TestCase):
    def solver(self):
        s=native.ResidualSolver();self.addCleanup(s.close);return s

    def test_terminal_target_skips_postings_and_core_reads(self):
        s=self.solver();source=[[1],[-1]];screen=TerminalFirstScreen([dict(source=source,root=s._canonical(source)[2])])
        with patch.dict(screen.index.__dict__,{'postings':None}),patch.object(s,'_read',side_effect=AssertionError('Core read')),patch.object(s,'_expand',side_effect=AssertionError('Search')):
            plan,trace=screen.select(s,source)
        self.assertIsNone(plan);self.assertTrue(trace['terminal']);self.assertEqual(trace['attempts'],[]);self.assertEqual(trace['core_checks'],[])
        with patch.object(native,'propagate',side_effect=AssertionError('Repeated propagation')),patch.object(s,'_expand',side_effect=AssertionError('Expansion')):got=publish_screened_branch(s,source,trace['baseline'])
        self.assertFalse(got['answer']);self.assertEqual(got['metrics']['inserted_nodes'],1);self.assertEqual(got['metrics'].get('expanded_nodes',0),0)

    def test_nonterminal_plan_matches_frozen_policy(self):
        s=self.solver();target=[[1,2],[-1,2],[1,-2],[-1,-2]];core=target+[[1],[-1]];hint=dict(source=core,root=s.solve(core)['root'])
        old=PartitionScreen([hint]);new=TerminalFirstScreen([hint]);a,ta=old.select(s,target);b,tb=new.select(s,target)
        self.assertFalse(tb.pop('terminal'));self.assertEqual((a,ta),(b,tb));self.assertEqual(old.counts,new.counts)

    def test_zero_budget_is_noop_and_pending_core_does_not_certify(self):
        s=self.solver();target=[[1,2],[-1,2],[1,-2],[-1,-2]];core=target+[[1],[-1]];hint=dict(source=core,root=s._canonical(core)[2])
        for kwargs in ({'plan_limit':0},{'core_read_limit':0}):
            with patch('experiments.cnf_terminal_first_screen.screen_branch',side_effect=AssertionError('Disabled probe')):
                self.assertEqual(TerminalFirstScreen([hint],**kwargs).select(s,target),(None,dict(attempts=[],selected=None,core_checks=[])))
        plan,trace=TerminalFirstScreen([hint]).select(s,target);self.assertIsNone(plan);self.assertFalse(trace['terminal']);self.assertEqual(trace['core_checks'],[dict(core=0,ready=False)])

    def test_trace_tampering_rejected_before_publication(self):
        s=self.solver();source=[[1],[-1]];_,trace=TerminalFirstScreen([]).select(s,source);trace['baseline']['conflict']=999
        with self.assertRaises(ValueError):publish_screened_branch(s,source,trace['baseline'])
        self.assertEqual(s.archive_storage()[0],0)

    def test_all_two_variable_cnfs_terminal_truth_and_fallback(self):
        clauses=[[i*sign for i,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];expected=any(native.holds(source,dict(zip((1,2),values))) for values in product((False,True),repeat=2));s=native.ResidualSolver()
            try:
                plan,trace=TerminalFirstScreen([]).select(s,source);self.assertIsNone(plan)
                if trace['terminal']:self.assertFalse(expected);result=publish_screened_branch(s,source,trace['baseline'])
                else:result=s.solve(source)
                self.assertEqual(result['answer'],expected)
                if expected:self.assertTrue(native.holds(source,result['model']))
            finally:s.close()


if __name__=='__main__':unittest.main()
