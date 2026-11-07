from pathlib import Path
import itertools
import json
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.persistent import PersistentSolver
from solver.incremental_proof import dimacs_clauses
from solver.test_fast import HARD_UNSAT,MIXED,cnf_bits,neg,conj,var


class ProofIncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'cache.db'

    def test_component_wrapper_uses_a_compatible_checked_certificate(self):
        with PersistentSolver(self.path,backend='cadical',components=True,incremental_proofs=True) as s:
            with patch.object(s.incremental,'propose',side_effect=AssertionError('Unsupported wrapper format')):
                result=s.solve(conj(HARD_UNSAT,var(20)),learn=False)
            self.assertFalse(result['answer'])
            self.assertEqual(result['backend'],'components')
            self.assertEqual(s.audit()['checked'],1)

    def test_general_unsat_uses_checked_live_trace_and_restarts(self):
        for bits in [HARD_UNSAT,neg(neg(HARD_UNSAT))]:
            with PersistentSolver(self.path,backend='cadical',incremental_proofs=True) as s:
                # This assertion excludes a successful fresh standalone solver
                # disguising an unsupported incremental proof as a success.
                with patch('solver.persistent.bounded_run',side_effect=AssertionError('Fresh solve')):
                    result=s.solve(bits,learn=False)
                self.assertFalse(result['answer'])
                self.assertEqual(result['backend'],'incremental_lrat')
                self.assertTrue(result['incremental']['proof_accepted'])
                if bits!=HARD_UNSAT:self.assertGreater(result['incremental']['restored_clauses'],0)
        with PersistentSolver(self.path) as s:self.assertEqual(s.audit()['checked'],2)

    def test_failed_assumption_does_not_become_permanent_constraint(self):
        with PersistentSolver(self.path,backend='cadical',incremental_proofs=True) as s:
            self.assertFalse(s.solve(HARD_UNSAT,learn=False)['answer'])
            self.assertTrue(s.solve(MIXED,learn=False)['answer'])
            self.assertTrue(s.solve(neg(MIXED),learn=False)['answer'])
            self.assertIsNone(s.incremental.process.poll())

    def test_saved_false_clause_cannot_forge_negative_answer(self):
        with PersistentSolver(self.path,backend='cadical',incremental_proofs=True) as s:
            self.assertTrue(s.solve(MIXED,learn=False)['answer'])
            native=s._request(dict(mode='incremental_prepare',bits=MIXED))
            root=dimacs_clauses(native['dimacs'])[0][0]
            s.incremental.store.append([], [dict(clause=[-root],parents=[])])
        with PersistentSolver(self.path,backend='cadical',incremental_proofs=True) as s:
            result=s.solve(neg(neg(MIXED)),learn=False)
            self.assertTrue(result['answer'])
            self.assertEqual(result['incremental']['verdict'],20)
            self.assertFalse(result['incremental'].get('proof_accepted',False))
            self.assertEqual(result['backend'],'cadical')

    def test_certificate_is_bound_to_original_formula_and_hints(self):
        with PersistentSolver(self.path,backend='cadical',incremental_proofs=True) as s:
            s.solve(HARD_UNSAT,learn=False)
            certificate=json.loads(s.db.execute('SELECT certificate FROM proofs').fetchone()[0])
            self.assertTrue(s._verify_certificate(HARD_UNSAT,certificate))
            self.assertFalse(s._verify_certificate(MIXED,certificate))
            certificate['text']='100000 0 0\n'
            self.assertFalse(s._verify_certificate(HARD_UNSAT,certificate))

    def test_random_contexts_agree_with_truth_tables(self):
        rng=random.Random(911)
        with PersistentSolver(self.path,backend='cadical',incremental_proofs=True,reuse_exact=False) as s:
            for _ in range(35):
                clauses=[[(i,bool(rng.randrange(2))) for i in rng.sample(range(5),3)] for _ in range(25)]
                expected=any(all(any(a[i]==b for i,b in c) for c in clauses) for a in itertools.product((False,True),repeat=5))
                result=s.solve(cnf_bits(clauses),learn=False)
                self.assertEqual(result['answer'],expected)

if __name__=='__main__':unittest.main()
