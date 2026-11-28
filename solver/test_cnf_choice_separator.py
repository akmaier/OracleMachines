from collections import Counter
from copy import deepcopy
from itertools import combinations
from unittest.mock import patch
import json
import unittest
from experiments import cnf_choice_separator as e
from solver.test_cnf_choice_forest import coloring


class ChoiceSeparatorTests(unittest.TestCase):
    def test_cyclic_graphs_beyond_two_cutsets(self):
        source = coloring(5, combinations(range(5),2))
        self.assertIsNone(e.prior.discover(source)[0])
        proof, diag = e.discover(source)
        self.assertIs(e.check(source,proof)['answer'], False)
        self.assertEqual(diag['attempts'][0]['maximum_separator_size'],4)

    def test_cycle_model(self):
        source = coloring(8,[(i,(i+1)%8) for i in range(8)])
        proof, _ = e.discover(source)
        self.assertTrue(e.check(source,proof)['answer'])

    def test_early_empty_message_refutes_whole_source(self):
        source = coloring(4,combinations(range(4),2)) + [[100,101,102]]
        proof, _ = e.discover(source)
        self.assertLess(len(proof['tables']),len(proof['order']))
        self.assertIs(e.check(source,proof)['answer'],False)
        proof['tables'].pop()
        self.assertIsNone(e.check(source,proof)['answer'])

    def test_positive_prefix_not_full_sat(self):
        source = coloring(4,[(0,1),(1,2),(2,3)])
        proof, _ = e.discover(source); proof['tables'].pop()
        self.assertIsNone(e.check(source,proof)['answer'])

    def test_disconnected_and_isolated(self):
        source = coloring(6,[(0,1),(2,3)])
        proof, _ = e.discover(source)
        self.assertTrue(e.check(source,proof)['answer'])

    def test_empty_and_tautology(self):
        for source, answer in (([],True),([[71,-71]],True),([[]],False)):
            proof,_=e.discover(source)
            self.assertIs(e.check(source,proof)['answer'],answer)

    def test_sparse_signed_and_duplicate_sources(self):
        source=coloring(4,[(0,1),(1,2),(2,3),(3,0)])
        mapping={i:(-1 if i%2 else 1)*(17*i+101) for i in range(1,13)}
        source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source]
        proof,_=e.discover(source)
        self.assertTrue(e.check(source[::-1]+source[:1]+[[9999,-9999]],proof)['answer'])

    def test_budget_prefix(self):
        source=coloring(4,[(0,1),(1,2),(2,3)])
        for kwargs in ({'state_limit':0},{'bag_limit':0},{'state_limit':9}):
            proof,diag=e.discover(source,**kwargs)
            self.assertIsNone(e.check(source,proof)['answer'])
            self.assertEqual(diag['reason'],'incomplete')

    def test_order_budget(self):
        source=coloring(4,combinations(range(4),2))
        proof,diag=e.discover(source,order_limit=0)
        self.assertIsNone(proof); self.assertEqual(diag['attempts'][0]['reason'],'order-limit')

    def test_inexact_and_noncanonical_relation(self):
        source=coloring(3,combinations(range(3),2));proof,_=e.discover(source)
        for rows in ([], [[True,2]], [[999,1000]], proof['tables'][0]*2, proof['tables'][0][::-1]):
            bad=deepcopy(proof);bad['tables'][0]=rows
            with self.assertRaises(ValueError):e.check(source,bad)

    def test_invalid_order_or_schema(self):
        source=coloring(3,combinations(range(3),2));proof,_=e.discover(source)
        for key,value in (('order',[0,1]),('order',[0,0,1]),('order',[True,1,2]),('empty',1),('tables',{}),('format','bad')):
            bad=deepcopy(proof);bad[key]=value
            with self.assertRaises(ValueError):e.check(source,bad)

    def test_changed_source_rechecked(self):
        source=coloring(4,combinations(range(4),2));proof,_=e.discover(source)
        with self.assertRaises(ValueError):e.check(source[:-1],proof)
        with self.assertRaises(ValueError):e.check(source+[[-1,-4,-7]],proof)

    def test_unclassified_clause_remains_unknown(self):
        source=coloring(4,[(0,1),(1,2),(2,3)])+[[-1,-4,-7]]
        self.assertIsNone(e.discover(source)[0])

    def test_raw_invalid_inputs_and_limits(self):
        for source in ([[0]],[[True]],[[1.0]],'cnf'):
            with self.assertRaises(ValueError):e.discover(source)
        for kwargs in ({'bag_limit':True},{'state_limit':-1},{'order_limit':1.0}):
            with self.assertRaises(ValueError):e.discover([],**kwargs)

    def test_cold_replay_without_ordering_or_tables(self):
        source=coloring(5,combinations(range(5),2));proof,_=e.discover(source)
        with patch.object(e,'discover',side_effect=AssertionError),patch.object(e,'min_fill',side_effect=AssertionError),patch.object(e,'make_table',side_effect=AssertionError):
            self.assertIs(e.check(source,json.loads(json.dumps(proof)))['answer'],False)

    def test_plan_message_scope_and_edge_coverage(self):
        graph={0:{1,3},1:{0,2},2:{1,3},3:{0,2}}
        order=[0,2,1,3];seps,children=e.plan(graph,order,Counter())
        for i,v in enumerate(order):
            bag={v,*seps[i]}
            for c in children[i]:self.assertLess(c,i);self.assertTrue(set(seps[c])<=bag)
        for a,ns in graph.items():
            for b in ns:self.assertTrue(any({a,b}<={v,*seps[i]} for i,v in enumerate(order)))


if __name__=='__main__':unittest.main()
