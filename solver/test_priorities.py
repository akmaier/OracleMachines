"""Regression tests for final outcomes, live retention and semantic provenance."""
import random
import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded
from solver.test_interfaces import xor,neg,chain,var


class PriorityTests(unittest.TestCase):
    def test_polarity_baseline_needs_no_training_and_is_checked(self):
        from experiments.run_priorities import PolaritySolver,encoding_size
        from experiments.run_expanded import dimacs,encode_dimacs
        clauses=[[i if i%2 else -i] for i in range(1,25)]
        bits=encode_dimacs(dimacs(clauses))
        self.assertEqual(encoding_size(clauses),len(bits))
        with tempfile.TemporaryDirectory() as d,PolaritySolver(Path(d)/'s.db') as s:
            result=s.solve(bits)
            self.assertTrue(result['answer'])
            self.assertEqual(result['source'],'verified_witness')
            self.assertEqual(s.db.execute('SELECT count(*) FROM models').fetchone()[0],0)

    def test_direct_reference_normalizes_satlib_delimiters(self):
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        from experiments.run_priorities import worker
        case=dict(stage=0,name='satlib-format',phase='test',expected=True,encoding_bytes=3,
                  dimacs='c comment\np cnf 1 1\n1 0\n%\n0\n')
        out=StringIO()
        with redirect_stdout(out):worker('direct',[case],64*1024**2,3)
        self.assertEqual(json.loads(out.getvalue())['status'],'ok')

    def test_preallocation_failure_does_not_borrow_previous_ledger(self):
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        from experiments.run_priorities import worker
        case=dict(stage=0,name='first',phase='test',expected=True,encoding_bytes=3,dimacs='p cnf 1 1\n1 0\n')
        out=StringIO()
        with redirect_stdout(out):worker('checked',[case,case|{'stage':1,'encoding_bytes':9*1024**2}],64*1024**2,3)
        rows=[json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(rows[0]['status'],'ok');self.assertEqual(rows[1]['status'],'error')
        self.assertEqual(rows[1]['failure_metrics'],{})

    def test_checked_cnf_compilation_matches_exhaustive_source(self):
        rng=random.Random(1781)
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            for width in (1,2):
                layers=[list(range(i*width+1,(i+1)*width+1)) for i in range(4)]
                for _ in range(25):
                    clauses=[]
                    for _ in range(12):
                        edge=rng.randrange(3);scope=layers[edge]+layers[edge+1]
                        clauses.append([rng.choice(scope)*rng.choice([-1,1]) for _ in range(rng.randrange(1,4))])
                    expected=any(all(any(values[abs(lit)-1]==(lit>0) for lit in c) for c in clauses)
                        for values in itertools.product([False,True],repeat=4*width))
                    result=s.layered_cnf(width,clauses,layers,witness=True)
                    self.assertEqual(result['answer'],expected)
                    self.assertEqual(result['compilation']['passes'],2)
                    if expected:
                        values={v:bool(result['witness'][i]&(1<<j)) for i,b in enumerate(layers) for j,v in enumerate(b)}
                        self.assertTrue(all(any(values[abs(lit)]==(lit>0) for lit in c) for c in clauses))
            self.assertFalse(s.layered_cnf(1,[[]],[[1],[]])['answer'])
            self.assertTrue(s.layered_cnf(1,[],[[],[]])['answer'])
            for clauses,layers in [([[1,3]],[[1],[2],[3]]),([[2]],[[1],[]]),([[1]],[[1],[1]]),([[0]],[[1],[]])]:
                with self.assertRaises(ValueError):s.layered_cnf(1,clauses,layers)

    def test_source_binding_and_logical_length_reject_forgery(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            result=s.layered(1,append=[15,0])
            with self.assertRaisesRegex(ValueError,'identity suffix'):
                s._request(dict(mode='layered_query',root=result['root'],size=1,left=3,right=3,witness=False))
            with self.assertRaisesRegex(ValueError,'differs'):
                s._request(dict(mode='layered_source_query',root=result['root'],width=1,
                    clauses=[],layers=[[1],[2],[3]],witness=False))

    def test_semantic_rebinding_keeps_current_provenance_across_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path,interfaces=True) as s:
                first=s.expand(add={f'e{i}':xor(i,i+1) for i in range(16)})
                edit=s.expand(first['state'],add={'e0':neg(xor(0,1))})
                self.assertTrue(edit['answer'])
                self.assertEqual(edit['interfaces']['semantic_stops'],1)
                self.assertEqual(edit['interfaces']['provenance_rebinds'],16)
                self.assertEqual(edit['interfaces']['affected_buckets'],17)
                self.assertEqual(edit['interfaces']['combination_rows'],2)
            with PersistentSolver(path,interfaces=True) as s:
                self.assertTrue(s.expand(edit['state'])['answer'])
                negative=s.expand(edit['state'],add={'left':var(0),'right':var(16)})
                self.assertFalse(negative['answer'])
                self.assertTrue(s.expand(negative['state'],remove=['e0'])['answer'])
                self.assertTrue(s.expand(first['state'],add={'left':var(0),'right':var(16)})['answer'])

    def test_iterative_lazy_evaluation_beyond_previous_depth_cap(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',interfaces=True) as s:
            result=s.expand(add={'chain':chain(320),'left':var(0),'right':neg(var(320))})
            self.assertFalse(result['answer']);self.assertIsNone(result['fallback_reason'])
            self.assertGreater(result['interfaces']['evaluation_stack_peak'],256)

    def test_proposal_timeout_reserves_checked_fallback(self):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',reuse_exact=False) as s:
            s.solve(var(0));original=s._request
            def request(value):
                if value['mode']=='propose':raise BudgetExceeded('injected speculative timeout')
                return original(value)
            with patch.object(s,'_request',side_effect=request):result=s.solve(var(0))
            self.assertTrue(result['answer'])
            self.assertEqual(result['proposals']['attempts'][0]['outcome'],'budget')
            self.assertEqual(result['proposals']['budget_seconds'],0.25)

    def test_final_route_outcome_and_telemetry_failure(self):
        with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db',adaptive=True,reuse_exact=False) as s:
            with patch.object(s,'archive_usage',side_effect=RuntimeError('late failure')):
                with self.assertRaisesRegex(RuntimeError,'late failure'):s.solve('010',learn=False)
            self.assertEqual([r[0] for r in s.db.execute('SELECT success FROM route_observations')],[0])
            self.assertTrue(s.solve('010',learn=False)['answer'])
            self.assertEqual([r[0] for r in s.db.execute('SELECT success FROM route_observations')],[0,1])
            with patch.object(s.router,'observe',side_effect=RuntimeError('telemetry unavailable')) as observe:
                result=s.solve('010',learn=False)
            self.assertTrue(result['answer']);self.assertEqual(observe.call_count,1)
            self.assertEqual(result['routing']['observation_error'],'telemetry unavailable')

    def test_distinct_layers_retention_and_explicit_refusal(self):
        rng=random.Random(1709);edges=[rng.getrandbits(256)|1 for _ in range(256)]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'s.db'
            with PersistentSolver(path,native_layer_cells=511*256) as s:
                first=s.layered(4,append=edges,left=1,right=1)
                second=s.layered(4,first['state'],replace={127:rng.getrandbits(256)|1},left=1,right=1)
                third=s.layered(4,second['state'],left=1,right=1)
                self.assertEqual(first['layered']['native_definitions'],511)
                self.assertEqual(second['layered']['native_definitions'],9)
                self.assertEqual(second['layered']['native_evictions'],9)
                self.assertEqual(third['layered']['native_definitions'],0)
                self.assertEqual(third['layered']['retention_visits'],0)
                self.assertLessEqual(third['layered']['native_cells'],511*256)
                self.assertTrue(s.layered(4,first['state'],left=1,right=1)['answer'])
            with PersistentSolver(path,native_layer_cells=510*256) as s:
                with self.assertRaisesRegex(BudgetExceeded,'working set'):s.layered(4,first['state'])
                self.assertEqual(s.db.execute('SELECT count(*) FROM layered_states').fetchone()[0],2)
            with PersistentSolver(path) as s:
                self.assertTrue(s.layered(4,second['state'],left=1,right=1)['answer'])
