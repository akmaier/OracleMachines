from collections import Counter
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_selective_learning as e

SQUARE=[[1,2],[1,-2],[-1,2],[-1,-2]]


def independent():
    source=[[1,2],[1,-2],[3,4],[3,-4],[-1,5]]
    base=e.canonical(source,Counter());i={c:n for n,c in enumerate(base)};n=len(base)
    records=[[i[(1,2)],[[2,i[(-2,1)]]],[1]],
             [n,[[1,i[(-1,5)]]],[5]],
             [i[(3,4)],[[4,i[(-4,3)]]],[3]]]
    proof=dict(format=e.prior.FORMAT,kind='unknown',witness=None,derivations=records,conclusion=None)
    e.prior.check_result(source,proof)
    return source,proof


class SelectiveLearningTests(TestCase):
    def test_independent_survives(self):
        source,p=independent();target=source[1:];k,d=e.transport(source,p,target)
        self.assertEqual(d['retained_indices'],[2]);self.assertEqual(d['discarded_indices'],[0,1]);self.assertEqual(k['derivations'][0][2],[3]);self.assertIsNone(e.prior.check_result(target,k)['answer'])
    def test_descendant_can_survive_parent_of_other_component_deleted(self):
        source,p=independent();k,d=e.transport(source,p,source[:2]+source[4:]);self.assertEqual(d['retained_indices'],[0,1]);self.assertEqual(k['derivations'][-1][2],[5])
    def test_all_survive_index_shift(self):
        source,p=independent();k,d=e.transport(source,p,source+[[-999,1]])
        self.assertEqual(d['retained_indices'],[0,1,2]);self.assertIsNone(e.prior.check_result(source+[[-999,1]],k)['answer'])
    def test_empty_target(self):
        source,p=independent();k,d=e.transport(source,p,[]);self.assertEqual(k['derivations'],[]);self.assertIsNone(e.prior.check_result([],k)['answer'])
    def test_empty_clause_target(self):
        source,p=independent();k,d=e.transport(source,p,[[]]);self.assertFalse(e.prior.check_result([[]],k)['answer'])
    def test_refutation_survives(self):
        p,_=e.prior.solve(SQUARE);k,d=e.transport(SQUARE,p,SQUARE+[[90]]);self.assertFalse(e.prior.check_result(SQUARE+[[90]],k)['answer'])
    def test_refutation_lost_is_unknown(self):
        p,_=e.prior.solve(SQUARE);k,d=e.transport(SQUARE,p,SQUARE[:-1]);self.assertIsNone(e.prior.check_result(SQUARE[:-1],k)['answer'])
    def test_old_sat_never_authorizes_target(self):
        p,_=e.prior.solve([[1]]);k,d=e.transport([[1]],p,[[1],[-1]]);self.assertIsNone(e.prior.check_result([[1],[-1]],k)['answer'])
    def test_invalid_removed_derivation_rejected(self):
        source,p=independent();p['derivations'][0][2]=[]
        with self.assertRaises(ValueError):e.transport(source,p,[])
    def test_invalid_target(self):
        source,p=independent()
        for target in ([[0]],[[True]],['x']):
            with self.assertRaises(ValueError):e.transport(source,p,target)
    def test_tautologies_and_duplicates(self):
        source,p=independent();k,d=e.transport(source,p,source+source+[[99,-99]]);self.assertEqual(len(k['derivations']),3)
    def test_transport_without_search(self):
        source,p=independent()
        with patch.object(e.prior,'search',side_effect=AssertionError),patch.object(e.prior,'solve',side_effect=AssertionError):e.transport(source,p,source[1:])
    def test_expand_sat_after_deletion(self):
        p,_=e.prior.solve(SQUARE);target=SQUARE[:-1];result,d=e.solve(SQUARE,p,target);self.assertTrue(e.prior.check_result(target,result)['answer'])
    def test_expand_substitutes_derived_premise(self):
        source,p=independent();target=source[1:]+[[-3]];result,d=e.solve(source,p,target)
        self.assertFalse(e.prior.check_result(target,result)['answer']);self.assertEqual(d['expansion']['reused'],1)
    def test_expand_shared_variable_mixture(self):
        source,p=independent();target=source[1:]+[[-3,700],[-700]];result,d=e.solve(source,p,target)
        self.assertFalse(e.prior.check_result(target,result)['answer'])
    def test_expand_new_variables_and_tautologies(self):
        source,p=independent();target=source[1:]+[[999,-999],[800]];r,d=e.solve(source,p,target);self.assertTrue(e.prior.check_result(target,r)['answer'])
    def test_partial_budget_remains_unknown(self):
        source,p=independent();r,d=e.solve(source,p,source,node_limit=0);self.assertIsNone(e.prior.check_result(source,r)['answer']);self.assertEqual(len(r['derivations']),3)
    def test_retained_refutation_requires_no_search(self):
        p,_=e.prior.solve(SQUARE)
        with patch.object(e.prior,'search',side_effect=AssertionError):r,d=e.solve(SQUARE,p,SQUARE,node_limit=0)
        self.assertFalse(e.prior.check_result(SQUARE,r)['answer']);self.assertEqual(d['expansion']['expanded'],0)
    def test_invalid_budget(self):
        source,p=independent()
        for budget in (True,-1,.2):
            with self.assertRaises(ValueError):e.solve(source,p,source,node_limit=budget)
    def test_forged_knowledge_rejected(self):
        source,p=independent();p['derivations'][1][0]=999
        with self.assertRaises(ValueError):e.expand(source,p)
    def test_output_checks_without_any_search(self):
        source,p=independent();target=source[1:]+[[-3]];r,d=e.solve(source,p,target)
        with patch.object(e,'solve',side_effect=AssertionError),patch.object(e.prior,'search',side_effect=AssertionError):self.assertFalse(e.prior.check_result(target,r)['answer'])
    def test_inputs_not_mutated(self):
        source,p=independent();before=deepcopy((source,p));e.solve(source,p,source[1:]);self.assertEqual((source,p),before)
