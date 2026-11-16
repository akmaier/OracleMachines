from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_witness_signatures import WitnessSignatures
from experiments.cnf_residual_dag import ResidualSolver,holds


class WitnessSignatureTests(unittest.TestCase):
    def bank(self,limit=64):
        b=WitnessSignatures([dict(source=[[1],[-1,2],[-2]])],attempt_limit=limit)
        b.observe([[-1,2],[-2]],{1:False,2:False},dict(kind='seed',case=0));return b

    def test_exact_lookup_and_checked_publication(self):
        b=self.bank();b.drain();s=ResidualSolver();self.addCleanup(s.close)
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            for removed in b.templates[0]['source']:
                q=[c for c in b.templates[0]['source'] if c!=removed]
                hit=b.reuse(s,q);self.assertIsNotNone(hit);r=s.solve(q)
                self.assertTrue(r['answer']);self.assertTrue(holds(q,r['model']))

    def test_budget_is_per_template_and_never_resets(self):
        b=self.bank(1);b.drain();saved=b.state();b.drain();self.assertEqual(saved,b.state())
        r=WitnessSignatures.restore(saved);r.drain();self.assertEqual(saved,r.state())
        self.assertEqual(len(b.templates[0]['attempts']),1)

    def test_exhausted_queue_roundtrip_with_unused_budget(self):
        b=self.bank();b.drain();self.assertLess(len(b.templates[0]['attempts']),b.limit)
        self.assertEqual(WitnessSignatures.restore(b.state()).state(),b.state())

    def test_seed_phase_and_zero_budget_roundtrip(self):
        b=self.bank(0);self.assertEqual(WitnessSignatures.restore(b.state()).state(),b.state())
        b.drain();self.assertEqual(WitnessSignatures.restore(b.state()).state(),b.state())
        self.assertFalse(b.templates[0]['attempts'])
        with self.assertRaises(ValueError):b.observe([],{},dict(kind='seed'))

    def test_same_signature_is_not_a_transition_congruence(self):
        b=WitnessSignatures([dict(source=[[-1,-2],[2]])])
        for x in (False,True):b.observe([[-1,-2]],{1:x,2:False},dict(kind='seed',x=x))
        self.assertEqual(len(b.templates[0]['states']),2)
        self.assertEqual(len(b.compiled[0]['representatives']),1)
        b.drain();states=b.templates[0]['states'];attempts=b.templates[0]['attempts']
        self.assertEqual(states[0]['bad'],states[1]['bad'])
        self.assertNotEqual(attempts[0]['bad'],attempts[1]['bad'])
        self.assertEqual(attempts[0]['bad'],0)

    def test_unknown_query_and_unsat_template_miss(self):
        b=self.bank();b.drain();s=ResidualSolver();self.addCleanup(s.close)
        self.assertIsNone(b.reuse(s,[[3]]));self.assertIsNone(b.reuse(s,[[1],[-1,2],[-2]]))
        self.assertEqual(s.archive_storage()[0],0)

    def test_empty_clauses_and_empty_templates(self):
        for source in ([],[[]]):
            b=WitnessSignatures([dict(source=source)]);b.observe([],{},dict(kind='seed'));b.drain()
            self.assertEqual(WitnessSignatures.restore(b.state()).state(),b.state())
            s=ResidualSolver();self.addCleanup(s.close)
            self.assertIsNotNone(b.reuse(s,[]))
            if source:self.assertIsNone(b.reuse(s,source))

    def test_invalid_model_and_template_coordinates_reject(self):
        b=self.bank()
        for q,m in (([[1]],{1:False}),([[1]],{1:1}),([[1]],{1:True,2:'false'})):
            with self.assertRaises(ValueError):b.observe(q,m,dict(kind='seed'))
        with self.assertRaises(ValueError):b.observe([],{},dict(kind='flip'))

    def test_invalid_budget_and_unsupported_tautology_reject(self):
        for v in (-1,True,1.5):
            with self.assertRaises(ValueError):WitnessSignatures([],attempt_limit=v)
            with self.assertRaises(ValueError):WitnessSignatures([],max_bad=v)
        with self.assertRaises(ValueError):WitnessSignatures([dict(source=[[1,-1]])])

    def test_tampered_state_and_transcript_reject(self):
        b=self.bank();b.drain();original=b.state()
        changes=[lambda s:s['templates'][0]['states'][0].update(bad=0),
                 lambda s:s['templates'][0]['states'][0].update(bits=True),
                 lambda s:s['templates'][0]['attempts'][0].update(accepted=False),
                 lambda s:s['templates'][0].update(cursor=0),
                 lambda s:s.update(attempt_limit=0),
                 lambda s:s['templates'][0]['names'].reverse()]
        for change in changes:
            saved=deepcopy(original);change(saved)
            with self.assertRaises(ValueError):WitnessSignatures.restore(saved)

    def test_publication_checks_full_model_even_with_corrupt_index(self):
        b=self.bank(0);b.compiled[0]['representatives']={0:0};s=ResidualSolver();self.addCleanup(s.close)
        with self.assertRaises(ValueError):b.reuse(s,[[1]])
        self.assertEqual(s.archive_storage()[0],0)

    def test_exhaustive_two_variable_signatures_and_flip_updates(self):
        clauses=[tuple((i+1)*a for i,a in enumerate(signs) if a) for signs in product((-1,0,1),repeat=2) if any(signs)]
        for subset in range(1<<len(clauses)):
            f=[c for i,c in enumerate(clauses) if subset>>i&1]
            b=WitnessSignatures([dict(source=f)],attempt_limit=32,max_bad=8)
            for bits in product((False,True),repeat=2):
                m=dict(zip((1,2),bits));q=[c for c in f if holds([c],m)]
                b.observe(q,m,dict(kind='seed',bits=bits))
            b.drain();t=b.templates[0]
            for state in t['states']:
                model={v:bool(state['bits']>>i&1) for i,v in enumerate(t['names'])}
                for present in range(1<<len(f)):
                    query=[c for i,c in enumerate(t['source']) if present>>i&1]
                    self.assertEqual(state['bad']&present==0,holds(query,model))
            for a in t['attempts']:
                bits=t['states'][a['parent']]['bits']^(1<<a['variable'])
                self.assertEqual(a['bad'],b._bad(0,bits))
            self.assertEqual(WitnessSignatures.restore(b.state()).templates,b.templates)


if __name__=='__main__':unittest.main()
