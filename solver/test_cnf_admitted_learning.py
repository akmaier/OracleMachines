from collections import Counter
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_admitted_learning as e
from solver.test_cnf_selective_learning import independent,SQUARE


class AdmittedLearningTests(TestCase):
    def test_shortest_then_newest(self):
        source,p=independent();self.assertEqual(e.admit(source,p,clause_limit=1),[2]);self.assertEqual(e.admit(source,p,clause_limit=2),[2,1])
    def test_zero_admission(self):
        source,p=independent();self.assertEqual(e.admit(source,p,clause_limit=0),[])
    def test_source_duplicates_not_active(self):
        source,p=independent();base=e.prior.canonical(source,Counter());p['derivations'].append([0,[],list(base[0])]);self.assertEqual(e.admit(source,p,clause_limit=10),[2,1,0])
    def test_duplicate_derived_newest(self):
        source,p=independent();n=len(e.prior.canonical(source,Counter()));p['derivations'].append([n+2,[],[3]])
        self.assertEqual(e.admit(source,p,clause_limit=10),[3,1,0])
    def test_invalid_admission_budgets(self):
        source,p=independent()
        for b in (True,-1,.5):
            with self.assertRaises(ValueError):e.admit(source,p,clause_limit=b)
    def test_invalid_expansion_budgets(self):
        source,p=independent()
        for b in (True,-1,.5):
            with self.assertRaises(ValueError):e.expand(source,p,node_limit=b)
            with self.assertRaises(ValueError):e.solve(source,p,source,clause_limit=b)
    def test_inactive_corruption_rejected(self):
        source,p=independent();p['derivations'][0][2]=[]
        with self.assertRaises(ValueError):e.admit(source,p,clause_limit=0)
    def test_selection_without_search(self):
        source,p=independent()
        with patch.object(e.prior.prior,'search',side_effect=AssertionError):self.assertEqual(e.admit(source,p,clause_limit=1),[2])
    def test_inactive_evidence_preserved(self):
        source,p=independent();r,d=e.expand(source,p,node_limit=0,clause_limit=1);self.assertEqual(r['derivations'],p['derivations']);self.assertEqual(d['admitted'],[2]);self.assertIsNone(e.prior.prior.check_result(source,r)['answer'])
    def test_all_admitted_matches_prior_certificate(self):
        source,p=independent();target=source+[[-3,99],[-99]];p,_=e.prior.transport(source,p,target);a,da=e.prior.expand(target,p);b,db=e.expand(target,p,clause_limit=999)
        self.assertEqual(a,b);self.assertEqual(da['expanded'],db['expanded'])
    def test_zero_admission_still_solves(self):
        source,p=independent();target=source+[[-3]];p,_=e.prior.transport(source,p,target);r,d=e.expand(target,p,clause_limit=0);self.assertFalse(e.prior.prior.check_result(target,r)['answer'])
    def test_composed_proof_uses_retained_evidence(self):
        source,p=independent();target=source+[[-3]];p,_=e.prior.transport(source,p,target);r,d=e.expand(target,p,clause_limit=1);self.assertFalse(e.prior.prior.check_result(target,r)['answer']);self.assertEqual(r['derivations'][:3],p['derivations'])
    def test_retained_refutation_needs_no_expansion(self):
        p,_=e.prior.prior.solve(SQUARE)
        with patch.object(e.prior.prior,'search',side_effect=AssertionError):r,d=e.expand(SQUARE,p,node_limit=0,clause_limit=0)
        self.assertFalse(e.prior.prior.check_result(SQUARE,r)['answer']);self.assertEqual(d['expanded'],0)
    def test_edits_drop_invalid_ancestors(self):
        source,p=independent();target=source[1:]+[[-3]];r,d=e.solve(source,p,target);self.assertFalse(e.prior.prior.check_result(target,r)['answer']);self.assertEqual(d['survival']['retained_indices'],[2])
    def test_sat_complete_target_check(self):
        source,p=independent();target=source[1:]+[[777,-777],[666]];r,d=e.solve(source,p,target);self.assertTrue(e.prior.prior.check_result(target,r)['answer'])
    def test_checker_independent(self):
        source,p=independent();target=source+[[-3]];p,_=e.prior.transport(source,p,target);r,d=e.expand(target,p)
        with patch.object(e,'expand',side_effect=AssertionError),patch.object(e.prior.prior,'search',side_effect=AssertionError):self.assertFalse(e.prior.prior.check_result(target,r)['answer'])
    def test_does_not_mutate_input(self):
        source,p=independent();old=deepcopy((source,p));e.expand(source,p);self.assertEqual(old,(source,p))
    def test_default_cap_128(self):
        source=[]
        for i in range(1,131):source += [[i,1000+i],[i,-1000-i]]
        base=e.prior.canonical(source,Counter());index={c:i for i,c in enumerate(base)};records=[]
        for i in range(1,131):records.append([index[(i,1000+i)],[[1000+i,index[(-1000-i,i)]]],[i]])
        p=dict(format=e.prior.prior.FORMAT,kind='unknown',witness=None,derivations=records,conclusion=None);counts=Counter();chosen=e.admit(source,p,counts)
        self.assertEqual(len(chosen),128);self.assertEqual(chosen,list(range(129,1,-1)));self.assertEqual(counts['admission_active_literals'],128)

    def test_unremapped_old_indices_rejected(self):
        source,p=independent()
        with self.assertRaises(ValueError):e.expand(source+[[-3]],p)
