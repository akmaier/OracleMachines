from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_resolution_learning as e

SQUARE=[[1,2],[1,-2],[-1,2],[-1,-2]]


class ResolutionLearningTests(TestCase):
    def proof(self,source=SQUARE):return e.solve(source)[0]
    def reject(self,source,proof):
        with self.assertRaises(ValueError):e.check_result(source,proof)
    def test_empty_true(self):self.assertTrue(e.check_result([],self.proof([]))['answer'])
    def test_empty_false(self):self.assertFalse(e.check_result([[]],self.proof([[]]))['answer'])
    def test_contradictory_units(self):self.assertFalse(e.check_result([[1],[-1]],self.proof([[1],[-1]]))['answer'])
    def test_square_refutation(self):self.assertFalse(e.check_result(SQUARE,self.proof())['answer'])
    def test_long_root_chain(self):
        source=[[1]]+[[-i,i+1] for i in range(1,1500)]+[[-1500]];p,d=e.solve(source)
        self.assertEqual(d['expanded'],1);self.assertFalse(e.check_result(source,p)['answer']);self.assertEqual(len(p['derivations'][-1][1]),1500)
    def test_sat_source_edit(self):self.reject([[1],[-1]],self.proof([[1]]))
    def test_sparse_names(self):
        source=[[57,901],[-57,901],[57,-901],[-57,-901],[8000,-8000]];self.assertFalse(e.check_result(source,self.proof(source))['answer'])
    def test_all_small_seeds(self):
        for source in (SQUARE,[[1,2],[-1,3],[-2,-3]],[[1],[3,-3]]):
            names=sorted({abs(v) for c in source for v in c});truth=any(all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source) for vs in product((False,True),repeat=len(names)))
            for vs in product((False,True),repeat=len(names)):
                seed=dict(format=e.prior.prior.previous.FORMAT,names=names,values=list(vs));p,d=e.search(source,seed);self.assertEqual(e.check_result(source,p)['answer'],truth)
    def test_zero_budget(self):p,d=e.solve(SQUARE,node_limit=0);self.assertIsNone(e.check_result(SQUARE,p)['answer']);self.assertEqual(d['expanded'],0)
    def test_invalid_policy_and_source(self):
        for n in (-1,True,0.5):
            with self.assertRaises(ValueError):e.solve(SQUARE,node_limit=n)
        for source in ([[0]],[[True]],[['x']]):
            with self.assertRaises(ValueError):e.solve(source)
    def test_checker_without_discovery(self):
        p=self.proof()
        with patch.object(e,'solve',side_effect=AssertionError),patch.object(e,'search',side_effect=AssertionError):self.assertFalse(e.check_result(SQUARE,p)['answer'])
    def test_invalid_parent(self):p=self.proof();p['derivations'][0][0]=-1;self.reject(SQUARE,p)
    def test_invalid_pivot(self):
        for pivot in (True,0,-1,777):
            p=self.proof();p['derivations'][0][1][0][0]=pivot;self.reject(SQUARE,p)
    def test_changed_lemma(self):p=self.proof();p['derivations'][0][2]=[];self.reject(SQUARE,p)
    def test_forward_parent(self):p=self.proof();p['derivations'][0][1][0][1]=len(SQUARE);self.reject(SQUARE,p)
    def test_nonempty_conclusion(self):p=self.proof();p['conclusion']=0;self.reject(SQUARE,p)
    def test_partial_knowledge_remains_unknown(self):
        p,d=e.solve(SQUARE,node_limit=2);self.assertEqual(p['kind'],'unknown');self.assertTrue(p['derivations']);self.assertIsNone(e.check_result(SQUARE,p)['answer'])
        p['kind']='unsat';p['conclusion']=len(SQUARE);self.reject(SQUARE,p)
    def test_changed_source_rejects_proof(self):self.reject(SQUARE[:-1],self.proof())
    def test_learned_clause_reused(self):
        c=Counter();p,d=e.solve(SQUARE,c);self.assertGreater(c['learned_clause_propagations'],0);self.assertGreater(c['learning_undo_occurrences'],0)
    def test_duplicate_and_tautological_source_reuse(self):
        p=self.proof();self.assertFalse(e.check_result(SQUARE+SQUARE+[[999,-999]],p)['answer'])

    def test_transport_addition_and_index_shift(self):
        p=self.proof();target=SQUARE+[[-999,1],[999]];m=e.transport_knowledge(SQUARE,p,target)
        self.assertFalse(e.check_result(target,m)['answer'])
    def test_transport_unused_clause_deletion(self):
        source=[[1],[-1],[2,3]];p=self.proof(source);m=e.transport_knowledge(source,p,[[1],[-1]])
        self.assertFalse(e.check_result([[1],[-1]],m)['answer'])
    def test_transport_missing_guard_rejected(self):
        with self.assertRaises(ValueError):e.transport_knowledge(SQUARE,self.proof(),SQUARE[:-1])
    def test_transport_does_not_preserve_sat_authority(self):
        p=self.proof([[1]]);m=e.transport_knowledge([[1]],p,[[1],[-1]])
        self.assertEqual(m['kind'],'unknown');self.assertIsNone(e.check_result([[1],[-1]],m)['answer'])
    def test_transport_partial_exclusion(self):
        p,_=e.solve(SQUARE,node_limit=2);m=e.transport_knowledge(SQUARE,p,SQUARE+[[999]])
        self.assertEqual(m['kind'],'unknown');self.assertTrue(m['derivations'])
    def test_transport_without_discovery(self):
        p=self.proof()
        with patch.object(e,'solve',side_effect=AssertionError),patch.object(e,'search',side_effect=AssertionError):
            m=e.transport_knowledge(SQUARE,p,SQUARE+[[77]])
            self.assertFalse(e.check_result(SQUARE+[[77]],m)['answer'])
