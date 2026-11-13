from collections import Counter
import copy
from itertools import product
import json
import unittest
from unittest.mock import patch

from experiments.cnf_exhaustion_certificate import make_certificate,check_certificate
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import discover_simplification


class ExhaustionCertificateTests(unittest.TestCase):
    def fixture(self):
        cnf=((1,2),(-1,3),(1,2,4))
        attempts=[dict(variable=v,value=b,certificate=discover_simplification(
            restrict(cnf,{v:b},Counter()),Counter(),pure=False)) for v in (1,2,3,4) for b in (False,True)]
        return cnf,attempts

    def test_standalone_replay_needs_only_binary_traces(self):
        cnf,attempts=self.fixture();certificate=make_certificate(cnf,attempts+attempts)
        self.assertEqual(len(certificate['attempts']),6)
        counts=Counter()
        with patch('experiments.cnf_simplification.discover_simplification',side_effect=AssertionError('new search')):
            result=check_certificate(json.loads(json.dumps(certificate)),expected_cnf=cnf,counts=counts)
        self.assertEqual(result['binary'],[1,2,3]);self.assertEqual(result['outside'],[4])
        self.assertEqual(counts['exhaustion_checked_attempts'],6)
        attempts[0]['certificate']['units'].clear()
        self.assertEqual(check_certificate(certificate),result)

    def test_exact_formula_binding_includes_clause_order(self):
        cnf,attempts=self.fixture();certificate=make_certificate(cnf,attempts)
        for other in (cnf[::-1],cnf+((2,3),)):
            with self.assertRaises(ValueError):check_certificate(certificate,expected_cnf=other)

    def test_missing_duplicate_and_forged_reasons_are_rejected(self):
        cnf,attempts=self.fixture();certificate=make_certificate(cnf,attempts)
        missing=copy.deepcopy(certificate);missing['attempts'].pop()
        duplicate=copy.deepcopy(certificate);duplicate['attempts'][1]=duplicate['attempts'][0]
        forged=copy.deepcopy(certificate);forged['attempts'][0]['certificate']['units'][0][1]=999
        for bad in (missing,duplicate,forged):
            with self.assertRaises(ValueError):check_certificate(bad)
        with self.assertRaises(ValueError):make_certificate(cnf,attempts[:5])

    def test_exhaustion_can_hold_for_an_unsatisfiable_formula(self):
        cnf=tuple(tuple(v*s for v,s in zip((1,2,3),signs)) for signs in product((-1,1),repeat=3))
        certificate=make_certificate(cnf,[]);result=check_certificate(certificate)
        self.assertEqual(result['outside'],[1,2,3]);self.assertEqual(result['checked_attempts'],0)
        for values in product((False,True),repeat=3):
            self.assertFalse(all(any(values[abs(l)-1]==(l>0) for l in clause) for clause in cnf))

    def test_normalized_formula_and_certificate_shape_are_required(self):
        for cnf in (((1,),),((),),((1,-1,2),),((True,2,3),)):
            with self.assertRaises(ValueError):make_certificate(cnf,[])
        cnf,attempts=self.fixture();certificate=make_certificate(cnf,attempts)
        certificate['answer']=True
        with self.assertRaises(ValueError):check_certificate(certificate)


if __name__=='__main__':unittest.main()
