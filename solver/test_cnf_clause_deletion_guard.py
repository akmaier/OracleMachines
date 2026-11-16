from collections import Counter
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard,propose,removed_clause,lift,replay
from experiments.cnf_residual_dag import ResidualSolver,holds,restrict


class ClauseDeletionGuardTests(unittest.TestCase):
    def test_all_two_variable_formulas_obey_the_conditional_identity(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2)]
        assignments=[dict(zip((1,2),bits)) for bits in product((False,True),repeat=2)]
        for mask in range(1<<len(clauses)):
            strong=[c for i,c in enumerate(clauses) if mask>>i&1]
            if any(holds(strong,a) for a in assignments):continue
            for clause in strong:
                weak=[c for c in strong if c!=clause];deleted=removed_clause(strong,weak)
                fixed={abs(l):l<0 for l in deleted};target=restrict(weak,fixed)
                for a in assignments:
                    self.assertEqual(holds(weak,a),all(a[v]==b for v,b in fixed.items()) and holds(target,a))
    def test_checked_unsat_guard_and_lift(self):
        solver=ResidualSolver();self.addCleanup(solver.close)
        strong=[[1],[-1,2],[-2]];weak=[[-1,2],[-2]];old=solver.solve(strong)
        bank=ExtensionBank([dict(source=strong,root=old['root'])]);cert=propose(solver,bank,weak)
        fixed,target=check_guard(solver,weak,cert);self.assertEqual(fixed,{1:False})
        child=solver.solve(target);model=lift(weak,fixed,child['model']);self.assertTrue(holds(weak,model))
        with patch.object(solver,'_expand',side_effect=AssertionError('fresh solving')):
            self.assertTrue(replay(solver,weak,cert,child)['answer'])
    def test_satisfiable_premise_declines_and_forged_guard_rejects(self):
        solver=ResidualSolver();self.addCleanup(solver.close);strong=[[1],[2]];old=solver.solve(strong)
        bank=ExtensionBank([dict(source=strong,root=old['root'])]);self.assertIsNone(propose(solver,bank,[[2]]))
        cert=next(bank.candidates([[2]],Counter()))
        with self.assertRaises(ValueError):check_guard(solver,[[2]],cert)
    def test_missing_or_foreign_proof_is_not_an_unsat_premise(self):
        solver=ResidualSolver();self.addCleanup(solver.close);strong=[[1],[-1]]
        root=solver._canonical(strong)[2];bank=ExtensionBank([dict(source=strong,root=root)])
        self.assertIsNone(propose(solver,bank,[[-1]]));cert=next(bank.candidates([[-1]],Counter()))
        with self.assertRaises(ValueError):check_guard(solver,[[-1]],cert)
        solver.solve(strong);cert['stronger_root']='foreign'
        with self.assertRaises(ValueError):check_guard(solver,[[-1]],cert)
    def test_multiple_deletions_or_changed_signs_reject(self):
        with self.assertRaises(ValueError):removed_clause([[1],[2],[-1]],[[2]])
        with self.assertRaises(ValueError):removed_clause([[1],[2]],[[1],[-2]])
        with self.assertRaises(ValueError):removed_clause([[1,-1],[2]],[[2]])
    def test_tampered_clause_and_conflicting_model_reject(self):
        solver=ResidualSolver();self.addCleanup(solver.close);strong=[[1],[-1]];old=solver.solve(strong)
        cert=propose(solver,ExtensionBank([dict(source=strong,root=old['root'])]),[[-1]])
        cert['removed_clause']=[-1]
        with self.assertRaises(ValueError):check_guard(solver,[[-1]],cert)
        with self.assertRaises(ValueError):lift([[-1]],{1:False},{1:True})


if __name__=='__main__':unittest.main()
