from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sqlite3,unittest
from experiments import cnf_live_fallback as live
from experiments.cnf_probed_partition import acquire
from experiments.cnf_partition_preparation import run as restart
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_transported_partition import native_query
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_clause_partition import check_record


def candidate(source):
    cnf,names=normalize(source)
    return dict(target=[list(c) for c in cnf],target_names=list(names))

def cube(n):return [list(c) for c in product(*[(-i,i) for i in range(1,n+1)])]
def rows(s):return list(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))

def short_probe(s,source,budget,**kw):
    return acquire(s,source,min(budget,1) if s._budget_hook is not None else budget,**kw)


class LiveFallbackTests(unittest.TestCase):
    def make(self,cls=live.ContinuationSolver,**kw):
        s=cls(**kw);self.addCleanup(s.close);return s
    def slow(self,**kw):return self.make(leaves=False,decompose=False,matching=False,positive_subsumption=False,**kw)
    def with_origin(self,s,source):
        core=cube(3);root=native_query(s,core,256)['root'];c=candidate(source)
        c.update(origin=root,origin_names=[1,2,3]);return c

    def test_native_visitor_matches_all_two_variable_truths_and_payloads(self):
        a=self.make(InputSafeAffineProbeSolver);b=self.make()
        clauses=[[i*sign for i,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1]
            x=acquire(a,source,256);y=acquire(b,source,256)
            truth=any(holds(source,dict(zip((1,2),bits))) for bits in product((False,True),repeat=2))
            self.assertEqual(y['result']['answer'],truth);self.assertEqual(x['metrics'],y['metrics'])
        self.assertEqual(rows(a),rows(b))

    def test_resume_preserves_direct_trace_for_both_verdicts(self):
        for source in (cube(11),cube(11)[1:]):
            a=self.slow();b=self.slow();observed=[]
            direct=acquire(a,source,256)
            r=live.run(b,candidate(source),'probe-native',256,observe=lambda s,e:observed.append((s.counts.copy(),e)))
            self.assertEqual(r['route'],'resumed');self.assertEqual(len(observed),1)
            self.assertEqual(r['expanded_nodes'],direct['metrics']['expanded_nodes'])
            self.assertEqual(r['result']['model'],direct['result']['model']);self.assertEqual(rows(a),rows(b))
            self.assertEqual(r['probe']['metrics']['expanded_nodes'],8)
            self.assertIsNone(b._budget_hook);self.assertFalse(b._continuation_active);self.assertFalse(b.db.active)

    def test_total_budget_stop_has_no_root_authority_and_keeps_checked_prefix(self):
        source=[[-22,-21,-20]]+cube(11)
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=live.ContinuationSolver(path,positive_subsumption=False)
            try:
                r=live.run(s,candidate(source),'probe-native',9)
                self.assertEqual(r['expanded_nodes'],9);self.assertIsNone(r['result'])
                self.assertIsNone(s._read(s._canonical(source)[2]));keys=[k for k,v in rows(s)];self.assertTrue(keys)
                self.assertFalse(s.db.active);self.assertFalse(s.db.pending)
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                rd=cls(path)
                try:
                    for k in keys:self.assertIsNotNone(rd._read(k))
                finally:rd.close()

    def test_eligible_partition_discards_stack_and_matches_old_composition(self):
        source=[[-3,-2,-1],[1,2,3]];a=self.make();b=self.make()
        ca=self.with_origin(a,source);cb=self.with_origin(b,source)
        expected=restart(a,ca,'reverse6')
        with patch.object(live,'acquire',side_effect=short_probe):r=live.run(b,cb,'probe6')
        self.assertEqual(r['route'],'partition');self.assertEqual(r['partition'],expected['partition'])
        check_record(b,r['partition']);self.assertIsNone(b._budget_hook)

    def test_ineligible_preparation_is_once_and_continues_in_place(self):
        source=[[-3,-2,-1],[1,2,3]];s=self.make();c=self.with_origin(s,source)
        with patch.object(live,'acquire',side_effect=short_probe),patch.object(live,'prepare_support',side_effect=live.SupportBudget('stop')) as prep:
            r=live.run(s,c,'probe6')
        self.assertEqual(prep.call_count,1);self.assertEqual(r['route'],'resumed')
        self.assertTrue(holds(source,r['result']['model']));self.assertEqual(r['expanded_nodes'],2)

    def test_control_failure_unwinds_and_solver_recovers(self):
        source=cube(11);s=self.slow()
        def fail(s,e):raise ValueError('control failure')
        with self.assertRaisesRegex(ValueError,'control failure'):live.run(s,candidate(source),'probe-native',256,observe=fail)
        self.assertFalse(s.db.active);self.assertIsNone(s._budget_hook);self.assertFalse(s._continuation_active)
        self.assertIsNone(s._read(s._canonical(source)[2]))
        self.assertFalse(live.run(s,candidate(source),'probe-native',256)['result']['answer'])

    def test_nested_search_during_control_is_rejected(self):
        source=cube(11);s=self.slow()
        with self.assertRaisesRegex(RuntimeError,'Search inside continuation routing'):
            live.run(s,candidate(source),'probe-native',256,observe=lambda solver,e:solver._visit([[1]]))
        self.assertFalse(s.db.active);self.assertFalse(s._continuation_deciding)

    def test_failed_boundary_commit_rolls_back_and_clears_hook(self):
        s=self.slow();source=cube(11)
        with patch.object(s.db,'finish',side_effect=sqlite3.OperationalError('commit failure')):
            with self.assertRaises(sqlite3.OperationalError):live.run(s,candidate(source),'probe-native',256)
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending);self.assertIsNone(s._budget_hook)

    def test_edited_and_signed_sources_do_not_reuse_unfinished_frames(self):
        s=self.slow();source=cube(10);r=live.run(s,candidate(source),'probe-native',9)
        self.assertIsNone(s._budget_hook)
        changed=[[(-1 if l>0 else 1)*(abs(l)*100+7) for l in c] for c in source[1:]]
        r=live.run(s,candidate(changed),'probe-native',256)
        self.assertTrue(r['result']['answer']);self.assertTrue(holds(changed,r['result']['model']))

    def test_zero_budget_cached_root_and_invalid_configuration(self):
        s=self.make();c=candidate([[1]])
        self.assertIsNone(live.run(s,c,'probe6',0)['result'])
        self.assertTrue(live.run(s,c,'probe6')['result']['answer'])
        self.assertTrue(live.run(s,c,'probe6',0)['result']['answer'])
        for n in (-1,True,0.5):
            with self.assertRaises(ValueError):live.run(s,c,'probe6',n)
        with self.assertRaises(ValueError):live.run(s,c,'wrong')
        with self.assertRaises(TypeError):live.run(self.make(InputSafeAffineProbeSolver),c,'probe6')


if __name__=='__main__':unittest.main()
