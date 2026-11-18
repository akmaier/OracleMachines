from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_affine_session import TerminalStore,NegativeChainBank,evaluate
from experiments.cnf_affine_negative import NegativeStore,compose,check_composed
from experiments.cnf_affine_completion import complete
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_affine_negative import exhausted


class AffineSessionTests(unittest.TestCase):
    def test_terminal_replay_avoids_native_alternative(self):
        s=ResidualSolver();self.addCleanup(s.close);source=exhausted()
        native=s.solve(source);_,e=complete(s,source);store=TerminalStore(s,create=True)
        child=store.publish(source,e);record=compose(store,source,[],child)
        s.checked.clear();store.checked.clear()
        with patch.object(s,'_read',side_effect=AssertionError('Unnecessary native alternative')):
            check_composed(store,record)
        self.assertEqual(len(s.checked),0)
        self.assertEqual(store.read(native['root'])['answer'],False)

    def test_persistent_lookup_precedes_discovery_and_search(self):
        with TemporaryDirectory() as td:
            p=Path(td)/'s'
            # Use a guaranteed negative target without native pre-solving.
            source=exhausted();s=ResidualSolver(p);TerminalStore(s,create=True)
            try:
                _,e=complete(s,source);store=TerminalStore(s);child=store.publish(source,e)
                before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            s=ResidualSolver(p)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch('experiments.compare_cnf_affine_negative.select',side_effect=AssertionError('Repeated discovery')),patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Write')):
                    r=evaluate(s,source,source,[])
                self.assertTrue(r['extension_lookup_hit']);self.assertFalse(r['record']['answer'])
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()

    def test_unknown_sources_match_exhaustive_truth_and_warm_bank(self):
        for family in ('random-three','coupled-parity','gated-horn','graph-colouring'):
            for sample in range(4):
                source=generate(family,12,sample,33);s=ResidualSolver();store=TerminalStore(s,create=True)
                try:
                    r=evaluate(s,source,source,[])
                    self.assertEqual(r['record']['answer'],truth_table(source)['answer'])
                    if r['extension']:
                        bank=NegativeChainBank(store,[r['record']]);self.assertFalse(bank.lookup(source)['answer'])
                        self.assertIsNone(bank.lookup([[9999]]))
                finally:s.close()

    def test_known_native_and_nonnegative_fallback(self):
        s=ResidualSolver();self.addCleanup(s.close);TerminalStore(s,create=True)
        for source in ([[1]],[[1],[-1]],[[1,2],[2,3]]):
            expected=s.solve(source)['answer'];before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            with patch.object(s,'_expand',side_effect=AssertionError('Known native search')):
                r=evaluate(s,source,source,[],eligible=False)
            self.assertEqual(r['record']['answer'],expected);self.assertFalse(r['extension'])
            self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))


if __name__=='__main__':unittest.main()
