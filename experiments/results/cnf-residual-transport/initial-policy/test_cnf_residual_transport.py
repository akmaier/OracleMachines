from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,random,sqlite3,unittest
from experiments.cnf_residual_transport import ResidualTransportSolver,TABLE,charge
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_cross_family import truth_table


def cube(offset=3):
    return [[(1 if v>0 else -1)*(abs(v)+offset) for v in c]
            for c in product((-1,1),(-2,2),(-3,3))]


class ResidualTransportTests(unittest.TestCase):
    def make(self,*args,**kwargs):
        s=ResidualTransportSolver(*args,**kwargs);self.addCleanup(s.close);return s

    def test_automatic_map_crosses_compact_coordinate_shift(self):
        s=self.make(affine_variables=1,leaves=False,decompose=False)
        self.assertFalse(s.solve(cube())['answer'])
        target=cube()+[[1,4,7],[2,5,8],[3,6,9]]
        with patch.object(ResidualSolver,'_expand',side_effect=AssertionError('Fresh native search')):
            r=s.solve((iter(c) for c in target))
        self.assertFalse(r['answer']);self.assertEqual(r['metrics']['transport_hits'],1)
        self.assertFalse(s._transport_stack);self.assertEqual(s._map_charge,0)

    def test_compact_ablation_misses_the_same_transfer(self):
        s=self.make(transport=False,affine_variables=1,leaves=False,decompose=False)
        s.solve(cube());r=s.solve(cube()+[[1,4,7],[2,5,8],[3,6,9]])
        self.assertFalse(r['answer']);self.assertEqual(r['metrics'].get('transport_hits',0),0)

    def test_cold_hints_retain_maps_and_native_authority(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ResidualTransportSolver(path,affine_variables=1,leaves=False)
            try:s.solve(cube());keys=list(s.transport_pool)
            finally:s.close()
            s=ResidualTransportSolver(path,affine_variables=1,leaves=False)
            try:
                self.assertEqual(list(s.transport_pool),keys)
                with patch.object(ResidualSolver,'_expand',side_effect=AssertionError('Fresh native search')):
                    r=s.solve(cube()+[[1,4,7],[2,5,8],[3,6,9]])
                self.assertEqual(r['metrics']['transport_hits'],1)
            finally:s.close()
            s=CanonicalVerifySnapshot(path)
            try:
                for key, in s.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(s._read(key))
            finally:s.close()

    def test_conditional_negative_does_not_refute_sat_source(self):
        source=[[1]+c for c in cube()]+[[-1,10]]
        s=self.make(affine_variables=1,leaves=False,decompose=False)
        r=s.solve(source);self.assertTrue(r['answer']);self.assertTrue(holds(source,r['model']))
        self.assertTrue(any(e['names']==(4,5,6) for e in s.transport_pool.values()))
        r=s.solve(source+[[2,4,11]]);self.assertTrue(r['answer']);self.assertTrue(holds(source,r['model']))

    def test_budget_stop_retains_only_committed_maps(self):
        source=[[1]+c for c in cube()]+[[-1,10]]
        s=self.make(affine_variables=1,leaves=False,decompose=False,batch_rows=1,node_limit=5)
        with self.assertRaisesRegex(RuntimeError,'no verdict'):s.solve(source)
        self.assertTrue(s.transport_pool)
        self.assertFalse(s._transport_stage);self.assertFalse(s._transport_stack)
        self.assertEqual(s._map_charge,0)
        for e in s.transport_pool.values():
            self.assertIsNotNone(s.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(e['origin'],)).fetchone())
        s.node_limit=100;self.assertTrue(s.solve(source)['answer'])

    def test_failed_native_or_metadata_commit_is_not_hint_authority(self):
        s=self.make(affine_variables=1,leaves=False,batch_rows=32)
        def native_fail(event,table,key):
            if event=='after_insert':raise RuntimeError('native failure')
        s.publication_hook=native_fail
        with self.assertRaisesRegex(RuntimeError,'native failure'):s.solve(cube())
        self.assertFalse(s.transport_pool);self.assertFalse(s._transport_stage)
        s.publication_hook=None
        def metadata_fail(event):raise RuntimeError('metadata failure')
        s.transport_publication_hook=metadata_fail
        with self.assertRaisesRegex(RuntimeError,'metadata failure'):s.solve(cube())
        self.assertFalse(s.transport_pool);self.assertFalse(s._transport_stage);self.assertFalse(s.db.in_transaction)
        self.assertEqual(s.db.execute(f'SELECT count(*) FROM {TABLE}').fetchone()[0],0)
        self.assertGreater(s.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0],0)
        s.transport_publication_hook=None;self.assertFalse(s.solve(cube())['answer'])

    def test_deleted_premise_and_changed_identity_miss(self):
        s=self.make(affine_variables=1,leaves=False);s.solve(cube())
        target=cube()[:-1]+[[1,4,7],[2,5,8],[3,6,9]]
        r=s.solve(target);self.assertTrue(r['answer']);self.assertTrue(holds(target,r['model']))
        self.assertEqual(r['metrics'].get('transport_hits',0),0)

    def test_untrusted_positive_and_malformed_cold_hints(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ResidualTransportSolver(path,affine_variables=1)
            try:
                origin=s.solve([[4,5,6]])['root']
                for names in ([4,5,6],[4,4,6]):
                    payload=json.dumps(dict(origin=origin,names=names),sort_keys=True,separators=(',',':'))
                    key=hashlib.sha256(payload.encode()).hexdigest()
                    with s.db:s.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)',(key,payload))
            finally:s.close()
            s=ResidualTransportSolver(path,affine_variables=1)
            try:
                self.assertEqual(s.transport_setup_counts['transport_invalid_hints'],1)
                r=s.solve([[4,5,6],[1,4,7],[2,5,8],[3,6,9]])
                self.assertTrue(r['answer']);self.assertEqual(r['metrics']['transport_positive_hints'],1)
                self.assertEqual(r['metrics'].get('transport_hits',0),0)
            finally:s.close()

    def test_limits_and_order_preserving_map_invariants(self):
        s=self.make(transport_capacity=2,transport_stage_limit=3,transport_probes=2,transport_candidates=1,
                    transport_bytes=16000,transport_map_bytes=4096,transport_depth=2,affine_variables=1,leaves=False)
        for off in range(3,8):
            r=s.solve(cube(off));m=r['metrics']
            self.assertLessEqual(m.get('transport_probes',0),2);self.assertLessEqual(m.get('transport_staged',0),3)
            self.assertLessEqual(m['transport_retained_entries'],2)
            self.assertLessEqual(m['transport_retained_bytes'],16000)
            self.assertLessEqual(m['transport_map_peak_bytes'],4096)
            if s.transport_pool:self.assertGreaterEqual(m['transport_retained_bytes'],charge(s.transport_pool))
        for kwargs in (dict(transport_capacity=False),dict(transport_bytes=0),dict(transport='yes')):
            with self.assertRaises(ValueError):ResidualTransportSolver(**kwargs)
        huge=1<<100;r=s.solve([[huge,huge+1]])
        self.assertTrue(r['answer']);self.assertEqual(r['metrics'].get('transport_composed_variables',0),0)

    def test_exhaustive_and_seeded_mixed_quotient_inputs(self):
        s=self.make();control=InputSafeAffineProbeSolver();self.addCleanup(control.close)
        clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        sources=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(943)
        sources += [[[v if rng.randrange(2) else -v for v in rng.sample(range(1,7),rng.randint(1,3))] for _ in range(22)] for _ in range(100)]
        sources += [[[-1,2],[1,-2],[-3,4],[3,-4],[1,3,5],[-2,-4,6]],
                    [[-1,2],[1,-2],[-3,4],[3,-4],[1,3],[-1,-3]]]
        for source in sources:
            r=s.solve(source);self.assertEqual(r['answer'],truth_table(source)['answer'])
            self.assertEqual(r['answer'],control.solve(source)['answer'])
            if r['answer']:self.assertTrue(holds(source,r['model']))


if __name__=='__main__':unittest.main()
