from copy import deepcopy
from itertools import combinations, product
from unittest.mock import patch
import json, random, unittest
from experiments import cnf_choice_witness as e


def choices(n):
    source = [[1+3*i+j for j in range(3)] for i in range(n)]
    # Each row can choose its own private resource, plus two shared resources.
    for j in (1,2):
        source += [[-(1+3*a+j),-(1+3*b+j)] for a,b in combinations(range(n),2)]
    return source


class ChoiceWitnessTests(unittest.TestCase):
    def test_strict_matching_model(self):
        source=choices(5); proof,diag=e.discover(source)
        self.assertTrue(e.check(source,proof)['answer'])
        self.assertTrue(diag['attempts'][0]['strict_choice_class'])

    def test_signed_sparse_renaming(self):
        source=choices(5);rng=random.Random(59)
        mapping={v:rng.choice((-1,1))*w for v,w in zip(range(1,16),rng.sample(range(101,10000),15))}
        renamed=[[mapping[abs(v)]*(1 if v>0 else -1) for v in reversed(c)] for c in reversed(source)]
        proof,_=e.discover(renamed);self.assertTrue(e.check(renamed,proof)['answer'])

    def test_empty_formula_and_tautological_support(self):
        for source in ([],[[71,-71]],[[1,1,-1],[2,-2]]):
            proof,_=e.discover(source);self.assertTrue(e.check(source,proof)['answer'])
            self.assertEqual(proof['names'],sorted({abs(v) for c in source for v in c}))

    def test_empty_clause_returns_no_sat_proof(self):
        self.assertIsNone(e.discover([[]])[0])

    def test_matching_is_not_sat_authority(self):
        source=[[1,2,3],[-1],[-2],[-3]]
        proof,diag=e.discover(source);self.assertIsNone(proof)
        self.assertIn('source-rejects-model',[r['reason'] for r in diag['attempts']])

    def test_nonclique_component_can_hide_sat(self):
        source=[[1,2,3],[4,5,6]]+[[-i,-(i+1)] for i in range(1,6)]
        proof,diag=e.discover(source);self.assertIsNone(proof)
        self.assertEqual(diag['attempts'][0]['reason'],'no-conservative-matching')
        self.assertFalse(diag['attempts'][0]['clique_components'])
        witness=dict(format=e.FORMAT,names=list(range(1,7)),values=[True,False,False,True,False,False])
        self.assertTrue(e.check(source,witness)['answer'])

    def test_uncovered_satisfied_constraints_are_checked(self):
        source=choices(4)+[[100,-101]]
        proof,_=e.discover(source);self.assertTrue(e.check(source,proof)['answer'])

    def test_missing_name_or_value_rejected(self):
        source=choices(3);proof,_=e.discover(source)
        for field in ('names','values'):
            bad=deepcopy(proof);bad[field].pop()
            with self.assertRaises(ValueError):e.check(source,bad)

    def test_changed_witness_rejected(self):
        source=choices(3);proof,_=e.discover(source);proof['values']=[False]*9
        with self.assertRaises(ValueError):e.check(source,proof)

    def test_changed_source_rechecked(self):
        source=choices(3);proof,_=e.discover(source);model=e.check(source,proof)['model']
        v=next(v for v,b in model.items() if b)
        with self.assertRaises(ValueError):e.check(source+[[-v]],proof)

    def test_satisfied_addition_reuses_witness(self):
        source=choices(3);proof,_=e.discover(source);model=e.check(source,proof)['model']
        v=next(v for v,b in model.items() if b)
        self.assertTrue(e.check(source+[[v]],proof)['answer'])

    def test_reject_malformed_values_and_input(self):
        source=choices(3);proof,_=e.discover(source)
        for field,value in (('format','wrong'),('names',[True]),('values',[1]*9)):
            bad=deepcopy(proof);bad[field]=value
            with self.assertRaises(ValueError):e.check(source,bad)
        for source in ([[0]],[[True]],[[1.0]],'cnf'):
            with self.assertRaises(ValueError):e.discover(source)
        with self.assertRaises(ValueError):e.discover([],matching_allowance=True)

    def test_matching_budget_admission(self):
        proof,diag=e.discover(choices(4),matching_allowance=0)
        self.assertIsNone(proof);self.assertEqual(diag['reserved'],0)
        self.assertTrue(all(r['reason']=='matching-admission' for r in diag['attempts']))

    def test_cold_check_without_matching(self):
        source=choices(4);proof,_=e.discover(source)
        with patch.object(e.native,'solve_matching',side_effect=AssertionError('search')):
            self.assertTrue(e.check(source,json.loads(json.dumps(proof)))['answer'])

    def test_pipeline_short_circuit(self):
        with patch.object(e.capacity,'pipeline',side_effect=AssertionError('fallback')):
            proof,_=e.pipeline(choices(4));self.assertTrue(e.check_pipeline(choices(4),proof)['answer'])

    def test_pipeline_falls_back_on_failed_proposal(self):
        source=[[1],[-1]];proof,_=e.pipeline(source)
        self.assertEqual(proof['kind'],'previous');self.assertFalse(e.check_pipeline(source,proof)['answer'])

    def test_two_variable_truth_agreement(self):
        clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(512):
            source=[c for i,c in enumerate(clauses) if bits>>i&1];proof,_=e.discover(source)
            if proof is not None:
                self.assertTrue(any(all(any(values[abs(v)-1]==(v>0) for v in c) for c in source) for values in product((False,True),repeat=2)))

    def test_external_edited_capacity_model(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        row=json.loads((root/'experiments/results/cnf-external-cutsets/panel.json').read_text())[36]
        proof,diag=e.discover(row['source']);self.assertTrue(e.check(row['source'],proof)['answer'])
        self.assertFalse(diag['attempts'][0]['strict_choice_class'])
        self.assertEqual(diag['attempts'][0]['unclassified_clauses'],10)


if __name__=='__main__':unittest.main()
