from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,random,unittest
from experiments.cnf_probe_handoff import ProbeHandoffSolver,prepare
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver,_UP,propagate
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments import cnf_residual_dag as native
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class ProbeLifetimeTests(unittest.TestCase):
    def solver(self,cls=ProbeLifetimeSolver,**kw):
        s=cls(affine_variables=1,**kw);self.addCleanup(s.close);return s

    def source(self,seed,n=8):
        rng=random.Random(seed)
        return [[v if rng.randrange(2) else -v for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]

    def rows(self,s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))

    def init_summary(self,s):
        s.handoff_summary=dict(peak_bytes=0,admissions=0,oversized=0,consumed=0,discarded=0)
        s.lifetime_summary=dict(transferred_peak_bytes=0,full_visit_envelope_peak_bytes=0,
            canonical_retirements=0,propagation_retirements=0,visit_retirements=0,discard_retirements=0)

    def test_truth_and_exact_chronological_pool_priority(self):
        old=self.solver(ProbeHandoffSolver,handoff_bytes=2*1024*1024)
        new=[self.solver(handoff_bytes=2*1024*1024,release_early=b) for b in (False,True)]
        uses=0
        for seed in range(40):
            src=self.source(seed,6);x=old.solve(src)
            truth=any(native.holds(src,dict(enumerate(bits,1))) for bits in product((False,True),repeat=6))
            self.assertEqual(x['answer'],truth)
            for s in new:
                y=s.solve(src);self.assertEqual(y['model'],x['model']);self.assertEqual(self.rows(s),self.rows(old))
                for k in ('expanded_nodes','witness_probes','witness_hits','negative_target_literals'):
                    self.assertEqual(y['metrics'].get(k,0),x['metrics'].get(k,0))
                uses+=y['metrics'].get('whole_lifetime_propagation_retirements',0)
        self.assertGreater(uses,0)

    def test_retirement_clears_references_before_descendant_admission(self):
        s=self.solver();self.init_summary(s)
        parent,_=native.normalize(self.source(1));raw,canonical=prepare(parent,1,False,s.counts)
        fixed,trace,conflict=native.propagate(canonical[0],Counter())
        lease=s._offer(raw,canonical,(fixed,trace,conflict,0));charge=lease.charge
        s._handoff_canonical=lease;self.assertEqual(s._canonical(raw),canonical)
        self.assertIsNone(lease.raw);self.assertIsNone(lease.canonical)
        token=_UP.set((canonical[0],s.counts,s,lease))
        try:
            got=propagate(canonical[0],s.counts);self.assertEqual(got,(fixed,trace,conflict))
            self.assertTrue(lease.retired);self.assertIsNone(lease.propagation);self.assertIsNone(_UP.get())
            self.assertEqual(s._handoff_held,0);self.assertEqual(s._transferred_held,charge)
            again=propagate(canonical[0],s.counts);self.assertEqual(again,got)
            self.assertEqual(s.counts['handoff_propagation_reuses'],1)
            # A new admission has its own payload; the old conservative charge
            # remains observable instead of disappearing from the comparison.
            other=s._offer(raw,canonical,None)
            self.assertGreater(s.lifetime_summary['full_visit_envelope_peak_bytes'],charge)
            s._discard(other)
        finally:_UP.reset(token);s._transferred_held=0

    def test_clear_only_control_keeps_original_charge(self):
        s=self.solver(release_early=False);self.init_summary(s)
        parent,_=native.normalize(self.source(2));raw,canonical=prepare(parent,1,False,s.counts)
        lease=s._offer(raw,canonical,None);charge=lease.charge;s._handoff_canonical=lease
        self.assertEqual(s._canonical(raw),canonical)
        self.assertTrue(lease.retired);self.assertIsNone(lease.raw);self.assertIsNone(lease.canonical)
        self.assertEqual(s._handoff_held,charge);self.assertEqual(s._transferred_held,0)
        # This unit test does not enter a native visit to perform its final release.
        s._handoff_held-=lease.charge;lease.charge=0

    def test_caps_stops_and_all_cleanup_paths(self):
        for capacity in (0,128,256*1024,2*1024*1024):
            for limit in range(9):
                for policy in (False,True):
                    old=self.solver(ProbeHandoffSolver,node_limit=limit,handoff_bytes=capacity)
                    s=self.solver(node_limit=limit,handoff_bytes=capacity,release_early=policy)
                    a=attempt(old,self.source(11));b=attempt(s,self.source(11))
                    self.assertEqual(a['status'],b['status']);self.assertEqual(self.rows(old),self.rows(s))
                    self.assertEqual((s._handoff_held,s._transferred_held),(0,0))
                    self.assertIsNone(_UP.get());self.assertIsNone(native._restriction_engine.get())
                    self.assertLessEqual(b['metrics']['whole_handoff_peak_bytes'],capacity)
                    self.assertEqual(sum(s.lifetime_summary[k] for k in ('canonical_retirements','propagation_retirements','visit_retirements','discard_retirements')),s.handoff_summary['admissions'])

    def test_foreign_identity_and_verification_do_not_consume(self):
        s=self.solver();self.init_summary(s);cnf,_=native.normalize(self.source(3))
        raw,canonical=prepare(cnf,1,False,s.counts)
        fixed,trace,conflict=native.propagate(canonical[0],Counter())
        lease=s._offer(raw,canonical,(fixed,trace,conflict,0));token=_UP.set((canonical[0],s.counts,s,lease))
        try:
            propagate(tuple(list(canonical[0])),s.counts)
            propagate(canonical[0],Counter())
            self.assertFalse(lease.retired)
            def check(*args):
                self.assertIsNone(_UP.get());raise ValueError('invalid proof')
            with patch.object(WholePoolPrioritySolver,'_verify',side_effect=check):
                with self.assertRaisesRegex(ValueError,'invalid'):s._verify('x',{})
            self.assertFalse(lease.retired);self.assertEqual(s._handoff_verifying,0)
        finally:_UP.reset(token);s._discard(lease)

    def test_sparse_iterables_cold_replay_and_exact_roots(self):
        src=[[l*17 for l in c] for c in self.source(2)]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ProbeLifetimeSolver(path,affine_variables=1,node_limit=256)
            try:
                r=s.solve((iter(c) for c in src));rows=self.rows(s)
                if r['answer']:self.assertTrue(native.holds(src,r['model']))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key,payload in rows.items():self.assertEqual(reader._read(key),json.loads(payload))
                finally:reader.close()
            reader=ProbeLifetimeSolver(path,node_limit=0)
            try:
                with patch.object(reader,'_expand',side_effect=AssertionError('new search')):
                    self.assertEqual(reader.solve(src)['answer'],r['answer'])
            finally:reader.close()

    def test_foreign_context_and_invalid_policy_rejected(self):
        s=self.solver();token=_UP.set(('foreign',))
        try:
            with self.assertRaises(RuntimeError):s.solve(self.source(0))
        finally:_UP.reset(token)
        with self.assertRaises(ValueError):ProbeLifetimeSolver(release_early=1)


if __name__=='__main__':unittest.main()
