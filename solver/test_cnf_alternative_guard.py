from copy import deepcopy
from collections import Counter
from unittest.mock import patch
import unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_proof_choice import ProofChoiceBank
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard,lift
from experiments.cnf_alternative_guard import AlternativeGuardSelector


class AlternativeGuardTests(unittest.TestCase):
    def make(self):
        s=ResidualSolver();self.addCleanup(s.close);return s
    def bank(self,s,cores=()):return ProofChoiceBank(s,dict(cores=[]),dict(cores=list(cores),deferred=True,causal_unit_slicing=True))
    def fixture(self,s,source=None,clauses=None):
        source=source or [[1],[-1],[2,3],[-2,4]];clauses=clauses or [[2],[3]]
        entries=[]
        for c in clauses:
            stronger=source+[c];r=s.solve(stronger);entries.append(dict(source=stronger,root=r['root']))
        bank=ExtensionBank(entries);guards=list(bank.candidates(source,Counter()))
        return source,bank,guards
    def test_ready_alternative_publishes_only_through_normal_subset_path(self):
        s=self.make();source,extensions,guards=self.fixture(s);core=[[1],[-1],[-2,4]];r=s.solve(core);bank=self.bank(s,[dict(source=core,root=r['root'],origin=r['root'])]);before=s.archive_storage()
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')),patch.object(s,'_store',side_effect=AssertionError('Selection publication')):
            selected,trace=AlternativeGuardSelector().select(s,extensions,source,guards[0],bank)
        self.assertEqual(selected,guards[1]);self.assertEqual(trace['attempts'][0]['status'],'ready');self.assertEqual(before,s.archive_storage())
        fixed,target=check_guard(s,source,selected)
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            self.assertTrue(bank.reuse(target)['inserted']);self.assertFalse(s.solve(target)['answer'])
    def test_known_positive_alternative_lifts_to_whole_query(self):
        s=self.make();source,extensions,guards=self.fixture(s,[[1],[2,3],[-2,3]],[[-1],[-3]]);s.solve([[1]])
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            chosen,trace=AlternativeGuardSelector().select(s,extensions,source,guards[0],self.bank(s));fixed,target=check_guard(s,source,chosen);child=s.solve(target);lift(source,fixed,child['model'])
        self.assertEqual(chosen,guards[1]);self.assertTrue(trace['attempts'][0]['answer'])
    def test_known_negative_alternative_uses_ordinary_proof(self):
        s=self.make();source,extensions,guards=self.fixture(s);_,target=check_guard(s,source,guards[1]);s.solve(target)
        chosen,trace=AlternativeGuardSelector().select(s,extensions,source,guards[0],self.bank(s))
        self.assertEqual(chosen,guards[1]);self.assertEqual(trace['attempts'][0]['status'],'known');self.assertFalse(trace['attempts'][0]['answer'])
    def test_pending_match_is_not_materialized_by_selection(self):
        s=self.make();source,extensions,guards=self.fixture(s);core=[[1],[-1],[-2,4]];key=s._canonical(core)[2];self.assertIsNone(s._read(key))
        bank=self.bank(s,[dict(source=core,root=key,origin='unavailable')]);selector=AlternativeGuardSelector()
        with patch.object(s,'_store',side_effect=AssertionError('Pending publication')),patch.object(s,'_expand',side_effect=AssertionError('Search')):
            chosen,trace=selector.select(s,extensions,source,guards[0],bank)
        self.assertIsNone(chosen);self.assertFalse(trace['selected']);self.assertEqual(selector.counts['pending_hints_skipped'],1)
    def test_candidate_budget_counts_nonnegative_guard_hints(self):
        s=self.make();source,extensions,guards=self.fixture(s,[[1],[2,3],[-2,3]],[[-1],[2],[-3]]);s.solve([[1]])
        chosen,trace=AlternativeGuardSelector(1).select(s,extensions,source,guards[0],self.bank(s));self.assertIsNone(chosen);self.assertEqual(len(trace['attempts']),1)
        chosen,trace=AlternativeGuardSelector(2).select(s,extensions,source,guards[0],self.bank(s));self.assertEqual(chosen,guards[2]);self.assertEqual(len(trace['attempts']),2)
    def test_zero_budget_and_invalid_budget(self):
        s=self.make();source,extensions,guards=self.fixture(s)
        chosen,trace=AlternativeGuardSelector(0).select(s,extensions,source,guards[0],self.bank(s));self.assertIsNone(chosen);self.assertEqual(trace['attempts'],[])
        for value in (-1,True,1.5):
            with self.assertRaises(ValueError):AlternativeGuardSelector(value)
    def test_forged_guard_and_support_reject(self):
        s=self.make();source,extensions,guards=self.fixture(s);bad=deepcopy(guards[0]);bad['stronger_root']='foreign'
        with self.assertRaises(ValueError):AlternativeGuardSelector().select(s,extensions,source,bad,self.bank(s))
        core=[[1],[-1],[-2,4]];bank=self.bank(s,[dict(source=core,root='foreign',origin='foreign')])
        with self.assertRaises(ValueError):AlternativeGuardSelector().select(s,extensions,source,guards[0],bank)
    def test_miss_preserves_archive_and_original_guard(self):
        s=self.make();source,extensions,guards=self.fixture(s);original=deepcopy(guards[0]);before=s.archive_storage()
        with patch.object(s,'_expand',side_effect=AssertionError('Search')):chosen,trace=AlternativeGuardSelector().select(s,extensions,source,original,self.bank(s))
        self.assertIsNone(chosen);self.assertEqual(trace['original_guard'],original);self.assertEqual(before,s.archive_storage())


if __name__=='__main__':unittest.main()
