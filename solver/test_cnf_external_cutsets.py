from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,unittest
from experiments import cnf_external_cutsets as e


class ExternalCutsetTests(unittest.TestCase):
    def test_multiline_and_multiple_clauses(self):
        source,header=e.parse_dimacs('c header\np cnf 3 3\n1 -2\nc middle\n3 0 -1 0\n0\n')
        self.assertEqual(source,[[1,-2,3],[-1],[]]);self.assertEqual(header,dict(variables=3,clauses=3))

    def test_legacy_terminator(self):
        for tail in ('%\n','%\n0\n','%\nc trailing\n0\n'):
            self.assertEqual(e.parse_dimacs('p cnf 1 1\n1 0\n'+tail)[0],[[1]])

    def test_empty_and_false(self):
        self.assertEqual(e.parse_dimacs('p cnf 0 0')[0],[])
        self.assertEqual(e.parse_dimacs('p cnf 0 1\n0')[0],[[]])

    def test_reject_bad_headers(self):
        for text in ('1 0','p cnf 1 -1','p dnf 1 1\n1 0','p cnf 1 1 extra','p cnf 1 1\np cnf 1 1\n1 0','p cnf 1000001 0'):
            with self.assertRaises(ValueError):e.parse_dimacs(text)

    def test_reject_clause_and_variable_mismatch(self):
        for text in ('p cnf 1 1\n2 0','p cnf 1 1\n-2 0','p cnf 1 1\n1','p cnf 1 2\n1 0','p cnf 1 1\n1 0 0','p cnf 1 1\n1.0 0'):
            with self.assertRaises(ValueError):e.parse_dimacs(text)

    def test_reject_unchecked_trailer(self):
        for text in ('p cnf 1 1\n%\n','p cnf 1 1\n1 0\n%\n1 0','p cnf 1 1\n1 0\n%\n0\n0','p cnf 1 1\n1 0\n%\n%'):
            with self.assertRaises(ValueError):e.parse_dimacs(text)

    def test_preserve_duplicate_and_tautological_raw_clauses(self):
        self.assertEqual(e.parse_dimacs('p cnf 9 3\n9 9 -9 0\n9 0\n9 0')[0],[[9,9,-9],[9],[9]])

    def test_reader_roundtrip_all_two_variable_formulas(self):
        clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(512):
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            text='p cnf 2 '+str(len(source))+'\n'+'\n'.join(' '.join(map(str,c+[0])) for c in source)
            self.assertEqual(e.parse_dimacs(text)[0],source)

    def test_baseline_sat_unsat(self):
        for source,answer in (([[1,2]],True),([[1],[-1]],False),([],True),([[]],False)):
            for expand in (False,True):
                proof,_=e.discover(source,expand=expand);got=e.check(source,proof)
                self.assertEqual(got['answer'],answer);self.assertEqual(proof['attempts'],[])

    def test_cold_without_discovery(self):
        source=[[11,99],[-11,27]];proof,_=e.discover(source,expand=True)
        with patch.object(e.previous,'discover',side_effect=AssertionError('discovery')):
            self.assertTrue(e.check(source,json.loads(json.dumps(proof)))['answer'])

    def test_changed_fixed_policy(self):
        source=[[1,2]];proof,_=e.discover(source)
        for change in (lambda p:p.__setitem__('expand',1),lambda p:p['context'].__setitem__('mode','one'),lambda p:p['context']['limits'].__setitem__('depth_limit',3)):
            bad=deepcopy(proof);change(bad)
            with self.assertRaises(ValueError):e.check(source,bad)

    def test_changed_source_and_witness(self):
        source=[[1,2]];proof,_=e.discover(source)
        with self.assertRaises(ValueError):e.check(source+[[]],proof)
        proof['model']=[False,False]
        with self.assertRaises(ValueError):e.check(source,proof)

    def fixture(self):
        root=Path(__file__).resolve().parents[1];case=json.loads((root/'experiments/results/cnf-selective-width-buckets/remaining.json').read_text())['cases'][0]
        context=json.loads((root/case['proof']['path']).read_text())
        return case['source'],context

    def test_existing_open_root_and_exact_recomposition(self):
        source,context=self.fixture()
        with patch.object(e.previous,'discover',return_value=(context,{})):proof,_=e.discover(source,expand=True)
        got=e.check(source,proof);self.assertTrue(got['answer']);self.assertTrue(e.native.holds(source,got['model']))
        with patch.object(e.factors,'discover',side_effect=AssertionError('factor discovery')),patch.object(e.previous,'discover',side_effect=AssertionError('old discovery')):self.assertEqual(e.check(source,json.loads(json.dumps(proof))),got)

    def test_missing_or_reordered_target(self):
        source,context=self.fixture()
        with patch.object(e.previous,'discover',return_value=(context,{})):proof,_=e.discover(source,expand=True)
        bad=deepcopy(proof);bad['attempts'].clear()
        with self.assertRaises(ValueError):e.check(source,bad)
        bad=deepcopy(proof);bad['attempts'][0]['target']=True
        with self.assertRaises(ValueError):e.check(source,bad)

    def test_expansion_requires_requested_policy(self):
        source,context=self.fixture()
        with patch.object(e.previous,'discover',return_value=(context,{})):proof,_=e.discover(source,expand=True)
        proof['expand']=False
        with self.assertRaises(ValueError):e.check(source,proof)

    def test_wide_frontier_admission_before_materialization(self):
        self.assertFalse(e.admitted([[1,2,3,4]],dict(limits=dict(bag_limit=3))))
        self.assertTrue(e.admitted([[1,-1,2,3,4]],dict(limits=dict(bag_limit=3))))


if __name__=='__main__':unittest.main()
