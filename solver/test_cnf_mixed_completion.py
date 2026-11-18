from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_mixed_completion import select
from experiments.cnf_inline_completion import select as previous
from experiments.cnf_positive_child import publish_model
from experiments.cnf_residual_dag import ResidualSolver, holds, two_cnf
from experiments.validate_cnf_mixed_completion import expected, validate_mixed_certificate

MIXED = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4], [3, 4], [-3, -4]]
NEGATIVE = [[1, 2], [-1, -2]] + [[1, a, b] for a in (-3, 3) for b in (-4, 4)]


class MixedCompletionTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def test_mixed_residual_replaces_acquisition_and_stops(self):
        s = self.solver(node_limit=0); counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Search')), patch.object(s, '_store', side_effect=AssertionError('Publication')):
            choice, trace = select(s, MIXED, counts=counts)
        self.assertEqual(trace['reason'], 'mixed-positive-model')
        self.assertEqual(counts['local_premise_probes'], 1)
        self.assertEqual(counts['mixed_scc_calls'], 1)
        self.assertEqual(counts['mixed_positive_models'], 1)
        self.assertEqual(counts['inline_completion_models'], 0)
        self.assertEqual((choice,trace),expected(s,MIXED,4,set(),trace))
        with patch.object(s, '_visit', side_effect=AssertionError('Acquisition')):
            result=publish_model(s,MIXED,choice)
        self.assertTrue(holds(MIXED,result['model']))
        self.assertEqual(result['metrics']['inserted_nodes'],1)

    def test_negative_condition_never_refutes_satisfiable_parent(self):
        s=self.solver(node_limit=0); counts=Counter(); choice,trace=select(s,NEGATIVE,counts=counts)
        self.assertEqual(trace['reason'],'inline-positive-model')
        self.assertEqual(counts['mixed_negative_conditions'],1)
        self.assertEqual(counts['local_premise_probes'],2)
        self.assertIsNone(trace['discovery']['completions'][0]['mixed']['model'])
        self.assertEqual((choice,trace),expected(s,NEGATIVE,4,set(),trace))
        self.assertTrue(publish_model(s,NEGATIVE,choice)['answer'])
        self.assertEqual(s.archive_storage()[0],1)

    def test_uniform_priority_and_width_rejection(self):
        uniform=[[1,2],[-1,-2],[1,3,4],[-1,-3,-4]]
        with patch('experiments.cnf_mixed_completion.two_cnf',side_effect=AssertionError('Unnecessary SCC')):
            self.assertEqual(select(self.solver(),uniform),previous(self.solver(),uniform))
        source=[[1,2],[-1,-2],[3,4,5],[-3,-4,-5]]
        counts=Counter();choice,trace=select(self.solver(),source,counts=counts)
        self.assertEqual(counts['mixed_scc_calls'],0)
        self.assertTrue(all(not c['two_cnf'] for c in trace['discovery']['completions']))
        self.assertIsNone(choice)

    def test_invalid_mixed_models_cannot_publish(self):
        for bad in ({3:False,4:False},{3:True},{1:False,3:False,4:True},{3:0,4:1}):
            s=self.solver()
            with patch('experiments.cnf_mixed_completion.two_cnf',return_value=(bad,None)):
                with self.assertRaises(ValueError):select(s,MIXED)
            self.assertEqual(s.archive_storage()[0],0)
        with patch('experiments.cnf_mixed_completion.holds',return_value=False):
            with self.assertRaises(ValueError):select(self.solver(),MIXED)

    def test_independent_reachability_rejects_false_status_and_paths(self):
        residual=((3,4),(3,-4),(-3,4),(-3,-4));counts=Counter();model,proof=two_cnf(residual,counts)
        item=dict(model=model,proof=proof,metrics=dict(counts));validate_mixed_certificate(residual,item)
        broken=deepcopy(item);broken['proof']['forward']=[]
        with self.assertRaises(AssertionError):validate_mixed_certificate(residual,broken)
        broken=deepcopy(item);broken['model']=[[3,False],[4,True]];broken['proof']=None
        with self.assertRaises(AssertionError):validate_mixed_certificate(residual,broken)
        broken=deepcopy(item);broken['metrics']['implication_edges']-=1
        with self.assertRaises(AssertionError):validate_mixed_certificate(residual,broken)

    def test_forced_prefix_transport_and_cold_replay(self):
        source=[[10]]+[[-10]+c for c in MIXED]
        for raw in (source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
            with TemporaryDirectory() as td:
                path=Path(td)/'proofs';s=ResidualSolver(path,node_limit=0,leaves=False)
                try:
                    choice,trace=select(s,raw);self.assertEqual(trace['reason'],'mixed-positive-model')
                    result=publish_model(s,raw,choice)
                finally:s.close()
                s=ResidualSolver(path)
                try:
                    s.db.execute('PRAGMA query_only=ON')
                    with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Cold publication')):
                        self.assertEqual(s.solve(raw)['model'],result['model'])
                        self.assertEqual(select(s,raw)[1]['reason'],'known-target')
                finally:s.close()

    def test_budget_and_native_inputs(self):
        for cap in (-1,True,1.5):
            with self.assertRaises(ValueError):select(self.solver(),MIXED,cap)
        self.assertEqual(select(self.solver(),MIXED,0)[1]['reason'],'disabled')
        for source in ([],[[]],[[1]],[[1],[-1]],[[1,2],[-1,-2]]):
            self.assertEqual(select(self.solver(),source),previous(self.solver(),source))

    def test_exhaustive_gated_binary_conditions_and_transports(self):
        pool=[[a,b] for x,y in ((3,4),(4,5)) for a in (-x,x) for b in (-y,y)]
        successes=negative=0
        for mask in range(256):
            source=[[1,2],[-1,-2]]+[[1]+c for i,c in enumerate(pool) if mask>>i&1]
            truth=any(all(any(bits[abs(l)-1]==(l>0) for l in c) for c in source) for bits in product((False,True),repeat=5))
            for raw in (source,[[-7*l for l in c[::-1]] for c in source[::-1]]):
                s=ResidualSolver()
                try:
                    choice,trace=select(s,raw)
                    self.assertEqual((choice,trace),expected(s,raw,4,set(),trace))
                    if choice and choice['kind']=='positive-model':
                        self.assertTrue(truth);self.assertTrue(holds(raw,publish_model(s,raw,choice)['model']))
                    successes+=trace['reason']=='mixed-positive-model'
                    d=trace['discovery']
                    negative+=sum('mixed' in c and c['mixed']['model'] is None for c in d['completions']) if d else 0
                finally:s.close()
        self.assertGreater(successes,0);self.assertGreater(negative,0)


if __name__=='__main__':unittest.main()
