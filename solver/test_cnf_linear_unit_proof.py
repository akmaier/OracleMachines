from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_linear_unit_proof as e

SQUARE=[[1,2],[1,-2],[-1,2],[-1,-2]]


class LinearUnitTests(TestCase):
    def proof(self,source=SQUARE):return e.pack(source,e.prior.discover(source)['exclusion'])
    def reject(self,source,p):
        with self.assertRaises(ValueError):e.check_exclusion(source,p)
    def test_square(self):self.assertFalse(e.check_exclusion(SQUARE,self.proof())['answer'])
    def test_empty_clause(self):self.assertFalse(e.check_exclusion([[]],self.proof([[]]))['answer'])
    def test_sat_and_empty(self):
        for source in ([],[[1]],[[999,-999]],[[2,4],[-2,-4]]):self.assertTrue(e.check_result(source,e.solve(source)[0])['answer'])
    def test_order_independent_packing(self):
        p=e.prior.discover(SQUARE)['exclusion'];q=deepcopy(p);q['nodes']=dict(reversed(list(q['nodes'].items())))
        self.assertEqual(e.pack(SQUARE,p),e.pack(SQUARE,q))
    def test_check_without_search_pack_or_old_checker(self):
        p=self.proof()
        with patch.object(e,'pack',side_effect=AssertionError),patch.object(e.prior,'discover',side_effect=AssertionError),patch.object(e.prior,'check_exclusion',side_effect=AssertionError):
            self.assertFalse(e.check_exclusion(SQUARE,p)['answer'])
    def test_missing_child(self):p=self.proof();p['nodes'].pop();self.reject(SQUARE,p)
    def test_trailing_node(self):p=self.proof();p['nodes'].append(p['nodes'][-1]);self.reject(SQUARE,p)
    def test_nonunit(self):p=self.proof();p['nodes'][0][0]=[0];self.reject(SQUARE,p)
    def test_missing_units(self):p=self.proof([[1],[-1]]);p['nodes'][0][0]=[];self.reject([[1],[-1]],p)
    def test_branch_omission(self):p=self.proof();p['nodes'][0][2].pop();self.reject(SQUARE,p)
    def test_branch_duplicate(self):p=self.proof();p['nodes'][0][2]=[1,1];self.reject(SQUARE,p)
    def test_wrong_clause(self):p=self.proof();p['nodes'][-1][1]=999;self.reject(SQUARE,p)
    def test_changed_source(self):self.reject([[1,2]],self.proof())
    def test_bad_shape(self):
        for p in (None,{},dict(format=e.FORMAT,seed={},nodes=[])):self.reject(SQUARE,p)
    def test_bad_node(self):
        for node in (None,{},[],[[],True],[[],0,[]],[[],0,[True,2]]):
            p=self.proof();p['nodes'][0]=node;self.reject(SQUARE,p)
    def test_missing_root(self):p=self.proof();p['nodes']=[];self.reject(SQUARE,p)
    def test_sparse_taut_and_duplicates(self):
        source=[[57],[-57,1024],[-1024],[57],[9000,-9000]];self.assertFalse(e.check_exclusion(source,self.proof(source))['answer'])
    def test_long_unit_chain(self):
        source=[[1]]+[[-i,i+1] for i in range(1,1500)]+[[-1500]];self.assertFalse(e.check_exclusion(source,self.proof(source))['answer'])
    def test_search_unchanged(self):
        for source in (SQUARE,[[1]],[[1,2],[-1,3],[-2,-3]]):
            a,da=e.prior.solve(source);b,db=e.solve(source);self.assertEqual(da,db);self.assertEqual(a['kind'],b['kind'])
            if a['kind']=='sat':self.assertEqual(a['certificate'],b['certificate'])
    def test_unknown_is_not_refutation(self):
        p=dict(format=e.RESULT,kind='unknown',certificate=None);self.assertIsNone(e.check_result(SQUARE,p)['answer']);p['kind']='unsat';self.reject(SQUARE,p)
