"""Truth-table checks for the proposed missing-clause restriction, not a solver."""
from itertools import product
from unittest import TestCase,main
from experiments.cnf_residual_dag import holds,restrict


class MissingClauseConditionTests(TestCase):
    def test_all_two_variable_formulas_and_missing_clauses(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(s) if sign) for s in product((-1,0,1),repeat=2)]
        models=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        checked=positive=0
        for mask in range(512):
            target=[c for i,c in enumerate(clauses) if mask>>i&1]
            for clause in clauses:
                if not clause or clause in target:continue
                if any(holds(target+[clause],a) for a in models):continue
                fixed={abs(l):l<0 for l in clause};residual=restrict(target,fixed)
                self.assertEqual(any(holds(target,a) for a in models),any(holds(residual,a) for a in models))
                for a in models:
                    if holds(target,a):self.assertTrue(all(a[v]==b for v,b in fixed.items()))
                checked+=1;positive+=any(holds(target,a) for a in models)
        self.assertGreater(checked,0);self.assertGreater(positive,0)

    def test_dropping_missing_clause_does_not_establish_unsat(self):
        target=[[1]];missing=[-1];models=[{1:False},{1:True}]
        self.assertFalse(any(holds(target+[missing],a) for a in models))
        self.assertTrue(any(holds(target,a) for a in models))
        self.assertEqual(restrict(target,{1:True}),())


if __name__=='__main__':main()
