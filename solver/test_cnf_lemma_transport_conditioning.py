from collections import Counter
import unittest

from experiments.cnf_lemma_transport import check_certificate
from experiments.cnf_residual_dag import restrict, holds
from experiments.cnf_simplification import check_simplification
from solver.test_cnf_lemma_transport import certificate, trace, step


class TransportConditioningTests(unittest.TestCase):
    def test_conditioning_can_shorten_a_lemma_to_a_new_unit(self):
        # x implies a,b, and together a,b imply y. Setting y=false does not
        # itself start UP, but the retained implication x -> y gives not x.
        cnf = [[-1, 2], [-1, 3], [-2, -3, 4]]
        cert = certificate(cnf, trace(cnf, 1, True)); a = trace(cnf, 4, False)
        raw, _ = check_simplification(restrict(cnf, {4: False}, Counter()), a['certificate'], Counter(), pure=False)
        self.assertEqual(a['certificate']['units'], [])
        cert['steps'] = [step('condition', raw, attempt=a)]
        result = check_certificate(cert)
        self.assertEqual(result['additions'], [[-1]])
        self.assertTrue(holds(result['target'], {1: False, 2: False, 3: True}))
        for a in (False, True):
            for b in (False, True):
                self.assertFalse(holds(result['target'], {1: True, 2: a, 3: b}))


if __name__ == '__main__': unittest.main()
