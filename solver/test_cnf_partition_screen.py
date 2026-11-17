from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_partition_screen import PartitionScreen,screen_branch,publish_screened_branch
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record,check_record


class PartitionScreenTests(unittest.TestCase):
    def solver(self):
        s=native.ResidualSolver();self.addCleanup(s.close);return s

    def test_conflict_trace_publishes_without_expand_or_propagation(self):
        s=self.solver();source=[[1],[-1]];screen=screen_branch(s,source,Counter())
        with patch.object(s,'_expand',side_effect=AssertionError('Expansion')),patch.object(native,'propagate',side_effect=AssertionError('Repeated propagation')):
            r=publish_screened_branch(s,source,screen)
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['screen_trace_publications'],1);self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
        with patch.object(s,'_store',side_effect=AssertionError('Repeated publication')):self.assertFalse(publish_screened_branch(s,source,screen)['answer'])

    def test_partial_trace_preserves_native_proofs(self):
        source=[[10],[-10,20,30],[-10,-20,30],[-10,20,-30],[-10,-20,-30]];s=self.solver();baseline=self.solver();old=baseline.solve(source);screen=screen_branch(s,source,Counter());root_cnf=s._canonical(source)[0];original=native.propagate
        def guarded(cnf,counts):
            self.assertNotEqual(cnf,root_cnf);return original(cnf,counts)
        with patch.object(native,'propagate',side_effect=guarded):r=publish_screened_branch(s,source,screen)
        self.assertFalse(r['answer']);self.assertEqual(s._read(r['root']),baseline._read(old['root']));self.assertEqual(r['metrics']['screen_trace_publications'],1)

    def test_partial_trace_lifts_sat_and_unforced_fallback(self):
        for source in ([[10],[-10,20,30]],[[10,20],[-10,20]],[]):
            s=self.solver();screen=screen_branch(s,source,Counter());r=publish_screened_branch(s,source,screen)
            self.assertTrue(r['answer']);self.assertTrue(native.holds(source,r['model']))

    def test_tampered_trace_or_conflict_cannot_publish_unsat(self):
        for field in ('root','trace','conflict'):
            s=self.solver();source=[[1],[-1]];bad=screen_branch(s,source,Counter())
            if field=='root':bad[field]='wrong'
            elif field=='trace':bad[field]=[[1,0]]
            else:bad[field]=999
            with self.assertRaises(ValueError):publish_screened_branch(s,source,bad)
            self.assertEqual(s.archive_storage()[0],0)

    def test_all_two_variable_cnfs_against_truth_tables(self):
        clauses=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            expected=any(native.holds(source,dict(zip((1,2),values))) for values in product((False,True),repeat=2))
            s=native.ResidualSolver()
            try:
                screen=screen_branch(s,source,Counter());r=publish_screened_branch(s,source,screen)
                self.assertEqual(r['answer'],expected)
                if r['answer']:self.assertTrue(native.holds(source,r['model']))
            finally:s.close()

    def test_screening_bounds_and_pending_skip(self):
        s=self.solver();target=[[1,2,3],[-1,2],[-2,3]];cores=[]
        for extra in ([[1],[-3]],[[2],[-3]],[[1],[-2],[3]]):
            source=target+extra;cores.append(dict(source=source,root=s._canonical(source)[2]))
        selector=PartitionScreen(cores,plan_limit=1,core_read_limit=1)
        with patch.object(s,'_expand',side_effect=AssertionError('Screen search')),patch.object(s,'_store',side_effect=AssertionError('Screen publication')):choice,trace=selector.select(s,target)
        self.assertIsNone(choice);self.assertLessEqual(len(trace['core_checks']),1);self.assertEqual(trace['attempts'],[])
        self.assertIsNone(PartitionScreen(cores,plan_limit=0).select(s,target)[0])
        with self.assertRaises(ValueError):PartitionScreen(cores,plan_limit=-1)

    def test_all_terminal_cover_and_nonterminal_two_branch_rejection(self):
        # Four binary clauses are UNSAT without initial units. Missing units
        # create two terminal branches whose traces become reusable proofs.
        s=self.solver();target=[[1,2],[-1,2],[1,-2],[-1,-2]];extra=[[1],[-1]];core=target+extra;hint=dict(source=core,root=s.solve(core)['root']);selector=PartitionScreen([hint])
        with patch.object(s,'_expand',side_effect=AssertionError('Screen search')):choice,trace=selector.select(s,target)
        self.assertIsNotNone(choice);self.assertEqual(choice['remaining'],0);self.assertLessEqual(len(trace['attempts']),4)
        _,root=publish_premise(s,target,hint,choice['missing']);children=[]
        for (_,_,child),screen in zip(branch_sources(target,choice['missing'])[1],choice['branches']):children.append(publish_screened_branch(s,child,screen))
        r=make_record(s,target,[],choice['missing'],root,children);self.assertFalse(check_record(s,r)['answer'])
        # A satisfiable target cannot have an all-terminal covering partition.
        s=self.solver();target=[[1,2],[-1,2],[-2,-3]];core=target+[[2],[3]];hint=dict(source=core,root=s.solve(core)['root'])
        self.assertIsNone(PartitionScreen([hint]).select(s,target)[0])


if __name__=='__main__':unittest.main()
