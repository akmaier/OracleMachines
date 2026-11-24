from itertools import combinations,product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,random,unittest
from experiments.cnf_probe_handoff import ProbeHandoffSolver,prepare
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments.cnf_residual_dag import normalize,restrict,holds,restriction_engine
from experiments import cnf_residual_dag as native
from experiments import cnf_cofactor_handoff as prior
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from collections import Counter


class ProbeHandoffTests(unittest.TestCase):
    def solver(self,cls=ProbeHandoffSolver,**kw):
        s=cls(affine_variables=1,**kw);self.addCleanup(s.close);return s

    def rows(self,s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))

    def source(self,seed,n=8):
        rng=random.Random(seed)
        return [[v if rng.randrange(2) else -v for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]

    def test_preparation_matches_full_normalizer(self):
        for seed in range(30):
            cnf,_=normalize(self.source(seed));n=max(abs(l) for c in cnf for l in c)
            for v in range(1,n+1):
                for b in (False,True):
                    raw,got=prepare(cnf,v,b,Counter());expected,names=normalize(restrict(cnf,{v:b}))
                    self.assertEqual((expected,names),got[:2]);self.assertEqual(raw,restrict(cnf,{v:b}))

    def test_random_truth_and_identical_native_payloads(self):
        consumed=propagations=0
        for seed in range(40):
            src=self.source(seed,6)
            a=self.solver(WholePoolPrioritySolver,node_limit=256);b=self.solver(node_limit=256)
            x,y=a.solve(src),b.solve(src)
            truth=any(holds(src,dict(enumerate(bits,1))) for bits in product((False,True),repeat=6))
            self.assertEqual(x['answer'],truth);self.assertEqual(y['answer'],truth)
            self.assertEqual(self.rows(a),self.rows(b))
            self.assertEqual(x['metrics'].get('expanded_nodes',0),y['metrics'].get('expanded_nodes',0))
            consumed+=y['metrics'].get('handoff_selected',0);propagations+=y['metrics'].get('handoff_propagation_reuses',0)
        self.assertGreater(consumed,0);self.assertGreater(propagations,0)

    def test_zero_and_tiny_caps_preserve_outputs(self):
        src=self.source(17);a=self.solver(WholePoolPrioritySolver,node_limit=256);x=a.solve(src)
        for cap in (0,1,128,256*1024):
            b=self.solver(node_limit=256,handoff_bytes=cap);y=b.solve(src)
            self.assertEqual(x['answer'],y['answer']);self.assertEqual(self.rows(a),self.rows(b))
            self.assertLessEqual(y['metrics']['whole_handoff_peak_bytes'],cap)
            if cap<128:self.assertEqual(y['metrics']['whole_handoff_consumed'],0)

    def test_stopped_prefixes_and_cleanup_match(self):
        src=self.source(11)
        for cap in range(9):
            a=self.solver(WholePoolPrioritySolver,node_limit=cap);b=self.solver(node_limit=cap)
            x,y=attempt(a,src),attempt(b,src)
            self.assertEqual(x['status'],y['status']);self.assertEqual(self.rows(a),self.rows(b))
            self.assertLessEqual(y['metrics'].get('expanded_nodes',0),cap)
            self.assertEqual(b._handoff_held,0);self.assertIsNone(b._waiting_offer)
            self.assertIsNone(b._handoff_canonical);self.assertFalse(b._handoff_active)
            self.assertIsNone(native._restriction_engine.get());self.assertIsNone(prior._PROPAGATION.get())

    def test_verification_disables_hints_and_restores_on_exception(self):
        s=self.solver();marker=prior._PROPAGATION.set(('untrusted',s.counts,()))
        def check(*args):
            self.assertIsNone(prior._PROPAGATION.get())
            self.assertEqual(s._handoff_verifying,1)
            raise ValueError('malformed certificate')
        try:
            with patch.object(WholePoolPrioritySolver,'_verify',side_effect=check):
                with self.assertRaisesRegex(ValueError,'malformed'):s._verify('x',{})
            self.assertEqual(prior._PROPAGATION.get(),('untrusted',s.counts,()))
            self.assertEqual(s._handoff_verifying,0)
        finally:prior._PROPAGATION.reset(marker)

    def test_existing_pool_priority_survives_handoff_insertion(self):
        a=self.solver(WholePoolPrioritySolver);b=self.solver()
        witnesses=negative=0
        for seed in range(12):
            x=a.solve(self.source(seed));y=b.solve(self.source(seed))
            self.assertEqual(x['model'],y['model']);self.assertEqual(self.rows(a),self.rows(b))
            for key in ('witness_probes','witness_hits','negative_target_literals','expanded_nodes'):
                self.assertEqual(x['metrics'].get(key,0),y['metrics'].get(key,0))
            witnesses+=y['metrics'].get('witness_probes',0)
            negative+=y['metrics'].get('negative_target_literals',0)
        self.assertGreater(witnesses,0);self.assertGreater(negative,0)

    def test_offer_requires_exact_parent_counter_and_child_and_is_one_use(self):
        s=self.solver();parent,_=normalize(self.source(1))
        s.handoff_summary=dict(peak_bytes=0,admissions=0,oversized=0,consumed=0,discarded=0)
        raw,canonical=prepare(parent,1,False,s.counts);offer=s._offer(raw,canonical,None)
        self.assertIsNotNone(offer)
        with s._continuation(parent,1,{False:offer}):
            with patch.object(native,'restrict_scan',return_value=('ordinary',)):
                equal_parent=tuple(list(parent));self.assertIsNot(parent,equal_parent)
                self.assertEqual(native.restrict(equal_parent,{1:False},s.counts),('ordinary',))
                self.assertEqual(native.restrict(parent,{1:False},Counter()),('ordinary',))
                self.assertEqual(native.restrict(parent,{1:True},s.counts),('ordinary',))
                got=native.restrict(parent,{1:False},s.counts);self.assertIs(got,raw)
                self.assertEqual(native.restrict(parent,{1:False},s.counts),('ordinary',))
            with patch.object(WholePoolPrioritySolver,'_visit',return_value=(None,'unrelated')):
                self.assertEqual(s._visit(tuple(list(raw))),(None,'unrelated'))
                self.assertIs(s._waiting_offer,offer)
        self.assertEqual(s._handoff_held,0);self.assertIsNone(s._waiting_offer)
        self.assertEqual(s.handoff_summary['discarded'],1)

    def test_foreign_engine_rejected_before_query(self):
        s=self.solver()
        with restriction_engine(lambda *args:()):
            with self.assertRaises(RuntimeError):s.solve(self.source(1))
        self.assertEqual(self.rows(s),{})
        for cap in (-1,True,1.5):
            with self.assertRaises(ValueError):ProbeHandoffSolver(handoff_bytes=cap)

    def test_cold_replay_and_sparse_witnesses(self):
        source=[[l*19 for l in c] for c in self.source(2)]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ProbeHandoffSolver(path,affine_variables=1,node_limit=256)
            try:
                r=s.solve((iter(c) for c in source));rows=self.rows(s)
                if r['answer']:self.assertTrue(holds(source,r['model']))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for k,v in rows.items():self.assertEqual(reader._read(k),json.loads(v))
                finally:reader.close()
            reader=ProbeHandoffSolver(path,affine_variables=1,node_limit=0)
            try:
                with patch.object(reader,'_expand',side_effect=AssertionError('fresh search')):
                    self.assertEqual(reader.solve(source)['answer'],r['answer'])
            finally:reader.close()


if __name__=='__main__':unittest.main()
