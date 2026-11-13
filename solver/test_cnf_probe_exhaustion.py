from collections import Counter
from itertools import combinations, product
import unittest

from experiments.cnf_probe_exhaustion import no_unit_triggers, check_clear_attempts, certify_exhaustion
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import discover_simplification


class ProbeExhaustionTests(unittest.TestCase):
    def test_full_coverage_requires_both_values_of_every_binary_variable(self):
        cnf = ((1,2),(-1,3),(1,2,4))
        attempts = [dict(variable=v,value=value,certificate=discover_simplification(
            restrict(cnf,{v:value},Counter()),Counter(),pure=False)) for v in (1,2,3) for value in (False,True)]
        self.assertEqual(certify_exhaustion(cnf,attempts,Counter()),([1,2,3],[4]))
        with self.assertRaises(ValueError): certify_exhaustion(cnf,attempts[:-1],Counter())
        with self.assertRaises(ValueError): certify_exhaustion(cnf,attempts[:-2],Counter())

    def test_augmented_learning_trace_is_not_an_original_source_trace(self):
        cnf = ((1,2),(-1,2),(2,3,4))
        attempts = [dict(variable=1,value=value,certificate=discover_simplification(
            restrict(cnf,{1:value},Counter()),Counter(),pure=False)) for value in (False,True)]
        counts = Counter(); check_clear_attempts(cnf,attempts,counts)
        self.assertEqual(counts['exhaustion_checked_attempts'],2)
        # Clause (2) is logically implied, but it cannot be silently used as an
        # initial unit when analysing plain propagation on the original source.
        augmented = cnf + ((2,),)
        nested = dict(variable=3,value=False,certificate=discover_simplification(
            restrict(augmented,{3:False},Counter()),Counter(),pure=False))
        with self.assertRaises(ValueError): check_clear_attempts(cnf,[nested],Counter())

    def test_all_small_normalized_formulas_agree_with_propagation(self):
        clauses = [tuple(v*s for v,s in zip(vs,signs))
            for width in (2,3) for vs in combinations((1,2,3),width)
            for signs in product((-1,1),repeat=width)]
        checked = 0
        for size in range(1,4):
            for cnf in combinations(clauses,size):
                support = {abs(l) for c in cnf for l in c}
                binary = {abs(l) for c in cnf if len(c)==2 for l in c}
                outside = sorted(support-binary)
                self.assertTrue(no_unit_triggers(cnf,outside,Counter()))
                for v in outside:
                    for value in (False,True):
                        residual = restrict(cnf,{v:value},Counter())
                        self.assertTrue(all(len(c)>=2 for c in residual))
                        result = discover_simplification(residual,Counter(),pure=False)
                        self.assertEqual(result,dict(units=[],conflict=None,pure_rounds=[]))
                        checked += 1
        self.assertGreater(checked,500)

    def test_normalization_and_no_existing_units_are_required(self):
        for cnf in (((1,), (2,3,4)), ((),), ((1,1,2),), ((1,-1,2),), ((True,2,3),)):
            with self.assertRaises(ValueError): no_unit_triggers(cnf,[],Counter())
        with self.assertRaises(ValueError): no_unit_triggers(((1,2),(1,3,4)),[1],Counter())
        with self.assertRaises(ValueError): no_unit_triggers(((1,2,3),),[4],Counter())

    def test_no_unit_trigger_does_not_mean_satisfiable(self):
        # Forbid all eight assignments of three variables: UNSAT, but every
        # single-assumption residual has width two and no initial unit.
        cnf = tuple(tuple(v*s for v,s in zip((1,2,3),signs)) for signs in product((-1,1),repeat=3))
        self.assertTrue(no_unit_triggers(cnf,[1,2,3],Counter()))
        for values in product((False,True),repeat=3):
            self.assertFalse(all(any(values[abs(l)-1] == (l>0) for l in clause) for clause in cnf))


if __name__ == '__main__': unittest.main()
