from copy import deepcopy
from itertools import product
import unittest
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_guard_chain import make_record,check_record
from experiments.cnf_premise_guard import PremiseGuardSelector


class PremiseGuardTests(unittest.TestCase):
    def solver(self):
        s=ResidualSolver();self.addCleanup(s.close);return s

    def hint(self,s,source):return dict(source=source,root=s._canonical(source)[2])

    def test_known_premise_needs_no_core_proof_or_publication(self):
        s=self.solver();source=[[1],[2,3]];core=[[1],[-1]];s.solve(source+[[-1]])
        hint=self.hint(s,core);self.assertIsNone(s._read(hint['root']));selector=PremiseGuardSelector([hint])
        with patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Publication')):
            choice,guard,target=selector.select(s,source)
        self.assertEqual(choice['path'],'known-premise');self.assertEqual(selector.counts['fallback_core_reads'],0)
        record=make_record(s,source,[guard],s.solve(target));self.assertTrue(check_record(s,record)['answer'])

    def test_missing_premise_uses_checked_subset(self):
        s=self.solver();source=[[1],[2,3]];core=[[1],[-1]];s.solve(core)
        selector=PremiseGuardSelector([self.hint(s,core)])
        with patch.object(s,'_expand',side_effect=AssertionError('Search')):choice,guard,target=selector.select(s,source)
        self.assertEqual(choice['path'],'checked-core');self.assertTrue(choice['inserted'])
        self.assertFalse(s._read(guard['stronger_root'])['answer']);self.assertTrue(s.solve(target)['answer'])

    def test_pending_does_not_supply_negative_evidence(self):
        s=self.solver();selector=PremiseGuardSelector([self.hint(s,[[1],[-1]])])
        with patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Publication')):
            self.assertIsNone(selector.select(s,[[1],[2,3]])[0])
        self.assertEqual(selector.counts['pending_fallbacks_skipped'],1)

    def test_positive_premise_skipped_and_bad_fallback_rejected(self):
        s=self.solver();source=[[1],[2,3]];core=[[1],[2]];s.solve(source+[[2]])
        selector=PremiseGuardSelector([self.hint(s,core)]);self.assertIsNone(selector.select(s,source)[0])
        self.assertEqual(selector.counts['positive_premises_skipped'],1)
        bad=self.hint(s,[[1],[-1]]);bad['root']='wrong'
        with self.assertRaises(ValueError):PremiseGuardSelector([bad]).select(s,source)

    def test_bank_is_copied_and_postings_match_bruteforce(self):
        s=self.solver();clauses=[tuple(sorted(sign*(i+1) for i,sign in enumerate(bits) if sign)) for bits in product((-1,0,1),repeat=2)]
        cores=[self.hint(s,[a,b]) for a in clauses for b in clauses if a!=b];original=deepcopy(cores);selector=PremiseGuardSelector(cores);cores.clear()
        from experiments.cnf_residual_dag import restrict
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];members=set(source);variables={abs(l) for c in source for l in c};expected=[]
            for i,core in enumerate(original):
                wanted=set(core['source']);missing=wanted-members
                if not wanted&members or len(missing)!=1:continue
                clause=next(iter(missing))
                if not clause or not {abs(l) for l in clause}<=variables:continue
                if set(map(tuple,restrict(source,{abs(l):l<0 for l in clause})))==members:continue
                expected.append((i,list(clause)))
            self.assertEqual(list(selector.candidates(source)),expected)

    def test_exhaustive_checked_outcomes_and_sat_control(self):
        clauses=[tuple(sorted(sign*(i+1) for i,sign in enumerate(bits) if sign)) for bits in product((-1,0,1),repeat=2)]
        models=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)];seen=set()
        for mask in range(1,512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];expected=any(holds(source,a) for a in models)
            # Each strengthened premise is solved independently before selection.
            s=ResidualSolver()
            try:
                hints=[]
                for clause in clauses:
                    if not clause or clause in source:continue
                    stronger=source+[clause];s.solve(stronger);hints.append(self.hint(s,stronger))
                with patch.object(s,'_expand',side_effect=AssertionError('Selection search')):choice,guard,target=PremiseGuardSelector(hints).select(s,source)
                if choice is None:continue
                record=make_record(s,source,[guard],s.solve(target));actual=check_record(s,record)
                self.assertEqual(actual['answer'],expected);seen.add(expected)
                if expected:self.assertTrue(holds(source,actual['model']))
            finally:s.close()
        self.assertEqual(seen,{False,True})


if __name__=='__main__':unittest.main()
