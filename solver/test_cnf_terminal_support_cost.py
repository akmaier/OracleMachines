"""Publication bound for slicing a checked terminal unit-conflict proof."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_unsat_support import checked_subset


class TerminalSupportCostTests(TestCase):
    def test_unit_conflict_chains_publish_at_most_core_and_target(self):
        # Vary proof length and irrelevant assignments. The bound concerns
        # rows, not clause/literal size, checking time, or arbitrary proof DAGs.
        for length in (1,2,3,5,8,13,21,34):
            for irrelevant in (1,4):
                with self.subTest(length=length,irrelevant=irrelevant),TemporaryDirectory() as td:
                    path=Path(td)/'proofs';s=ResidualSolver(path)
                    try:
                        source=[[1]]+[[-i,i+1] for i in range(1,length)]+[[-length]]
                        source += [[100+i] for i in range(irrelevant)]
                        solved=s.solve(source);node=s._read(solved['root'])
                        self.assertEqual(node['proof']['kind'],'units')
                        self.assertIsNotNone(node['proof'].get('conflict'))
                        before=s.archive_storage()[0]
                        with patch.object(s,'_expand',side_effect=AssertionError('Fresh derivation search')):
                            extractor=CausalSupportExtractor(s);core=extractor.source_core(source)
                            self.assertEqual(extractor.counts['support_nodes'],1)
                            self.assertLessEqual(s.archive_storage()[0]-before,1)
                            target=core['source']+[[200,201,202]]
                            checked_subset(s,target,core['source'])
                            self.assertLessEqual(s.archive_storage()[0]-before,2)
                            self.assertFalse(s.solve(target)['answer'])
                    finally:s.close()
                    cold=ResidualSolver(path)
                    try:
                        with patch.object(cold,'_expand',side_effect=AssertionError('Fresh cold search')):
                            for key, in cold.db.execute('SELECT id FROM cnf_residual_v1'):
                                self.assertIsNotNone(cold._read(key))
                            self.assertFalse(cold.solve(target)['answer'])
                    finally:cold.close()


if __name__=='__main__':main()
