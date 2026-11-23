from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_conditional_recovery import proposal,recover
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_residual_dag import holds
from collections import Counter

# K implies not x without a unit clause; adding x yields a unit refutation.
T=dict(clauses=[[-2,-1],[-1,2],[1]],assumptions=[],trace=[[1,2],[-2,0]],conflict=1)
K=[[-2,-1],[-1,2]]


class ConditionalRecoveryTests(unittest.TestCase):
    def solver(self,**kwargs):
        s=ConsequencePrioritySolver(**kwargs);self.addCleanup(s.close);return s

    def run_case(self,source,template=T,context=None,budget=256):
        s=self.solver();context=[] if context is None else context
        from experiments.cnf_residual_dag import restrict
        screen=screen_branch(s,restrict(source,dict(context)),Counter())
        return s,recover(s,source,template,context,screen,budget)

    def test_positive_lift_checks_full_target(self):
        s,r=self.run_case(K);self.assertEqual(r['forced'],[[1,False]])
        self.assertTrue(r['result']['answer']);self.assertTrue(holds(K,r['result']['model']))
        self.assertTrue(s._read(r['result']['root'])['answer'])

    def test_negative_compiles_excluded_native_proof(self):
        other=list(product((-3,3),(-4,4),(-5,5)))
        s,r=self.run_case(K+other);self.assertFalse(r['result']['answer']);self.assertEqual(len(r['excluded']),1)
        with patch.object(s,'_expand',side_effect=AssertionError('Unexpected search')):
            self.assertFalse(s._read(r['result']['root'])['answer'])

    def test_guard_and_unit_prefix_lift(self):
        t=deepcopy(T);t['clauses']=[sorted(c+[7]) for c in t['clauses']];t['assumptions']=[[7,False]]
        check_template(t);source=[sorted(c+[7]) for c in K]+[[8],[-8,9]]
        s,r=self.run_case(source,t,[[7,False]]);self.assertTrue(r['result']['answer'])
        self.assertTrue(holds(source,{**r['result']['model'],7:False}));self.assertTrue(r['result']['model'][8])

    def test_budget_stop_never_publishes_unchecked_parent(self):
        s,r=self.run_case(K,budget=0);self.assertEqual(r['status'],'unresolved')
        self.assertIsNone(r['result']);self.assertIsNone(s._read(s._canonical(K)[2]))

    def test_no_change_when_force_already_known(self):
        s,r=self.run_case(K+[[-1]]);self.assertIsNone(r)

    def test_proposal_fails_closed_on_missing_and_outside_variables(self):
        self.assertIsNone(proposal([],T,[]));self.assertIsNone(proposal([[-2,-1]],T,[]))
        t=dict(clauses=[[1]],assumptions=[[1,False]],trace=[],conflict=0)
        self.assertIsNone(proposal([[2]],t,[[1,False]]))
        with self.assertRaises(ValueError):proposal(K,t,[])
        with self.assertRaises(ValueError):proposal(K,T,[],max_width=True)

    def test_bad_screen_rejected_before_publication(self):
        for changed in ('root','trace'):
            s=self.solver();screen=screen_branch(s,K,Counter())
            screen[changed]='wrong' if changed=='root' else [[2,0]]
            with self.assertRaises(ValueError):recover(s,K,T,[],screen,256)
            self.assertIsNone(s._read(s._canonical(K)[2]))

    def test_exhaustive_extra_clauses_agree_with_truth(self):
        extras=[[-1],[-2],[2],[1,2],[1,-2],[-1,2]]
        for mask in range(1<<len(extras)):
            source=K+[cl for i,cl in enumerate(extras) if mask>>i&1]
            s=self.solver();screen=screen_branch(s,source,Counter())
            if screen['conflict'] is not None:continue
            r=recover(s,source,T,[],screen,256)
            if r is None:continue
            expected=any(holds(source,dict(zip((1,2),bits))) for bits in product((False,True),repeat=2))
            self.assertEqual(r['result']['answer'],expected)

    def test_one_missing_clause_at_unit_fixpoint_has_at_most_one_new_literal(self):
        from experiments.cnf_residual_dag import propagate,restrict
        clauses=[list(c) for choices in product((-1,0,1),repeat=2) if any(choices)
                 for c in [[(i+1)*sign for i,sign in enumerate(choices) if sign]]]
        checked=0
        for mask in range(1<<len(clauses)):
            source=[cl for i,cl in enumerate(clauses) if mask>>i&1]
            fixed,_,conflict=propagate(source,Counter())
            if conflict is not None:continue
            for clause in clauses:
                if clause in source:continue
                if propagate(source+[clause],Counter())[2] is None:continue
                residual=restrict([clause],fixed)
                self.assertEqual(len(residual),1)
                self.assertLessEqual(len(residual[0]),1);checked+=1
        self.assertGreater(checked,0)
