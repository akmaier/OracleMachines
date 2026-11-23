from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random,unittest
from experiments.cnf_joint_backbone import discover,force_all,JointBackboneSolver,SingleFromJointSolver
from experiments.probe_cnf_joint_backbone import census
from experiments.cnf_residual_dag import normalize,token,restrict,holds,FORMAT
from experiments.cnf_probed_partition import acquire
from experiments.cnf_binary_backbone import check_path
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver

INDEPENDENT=((1,3),(1,-3),(2,4),(2,-4),(5,6,7))


def parts(cnf,literals):
    options={p['evidence']['literal']:p['evidence'] for p in census(cnf)['forced']}
    return [options[l] for l in literals]


def publish(s,cnf,evidence):
    model,proof=force_all(s,cnf,evidence);key=token(cnf,Counter())
    node=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=model is not None)
    if model is None:node['proof']=proof
    else:node['model']=[model.get(i,False) for i in range(1,max((abs(l) for c in cnf for l in c),default=0)+1)]
    s._store(key,node)
    return model,key


class JointBackboneTests(unittest.TestCase):
    def make(self,**kw):
        s=JointBackboneSolver(**kw);self.addCleanup(s.close);return s

    def test_two_independent_paths_share_graph_and_are_checked(self):
        cnf,_=normalize(INDEPENDENT);c=Counter();proof,cover,got=discover(cnf,c)
        self.assertIsNone(proof);self.assertIsNone(cover);self.assertEqual([p['literal'] for p in got],[-1,-2])
        for p in got:check_path(cnf,p,Counter())
        self.assertEqual(c['binary_cover_graph_edges'],8);self.assertEqual(c['joint_closure_roots'],1)

    def test_redundant_second_value_is_skipped_by_binary_closure(self):
        cnf,_=normalize([(1,3),(1,-3),(-1,2),(4,5,6)])
        c=Counter();got=discover(cnf,c)[2];self.assertEqual([p['literal'] for p in got],[-1])
        self.assertGreater(c['joint_redundant_candidates'],0)

    def test_target_bound_and_invalid_budgets(self):
        cnf,_=normalize(INDEPENDENT);c=Counter();self.assertEqual(len(discover(cnf,c,target_limit=1)[2]),1)
        for kw in ({'target_limit':0},{'target_limit':9},{'target_limit':True},{'root_limit':-1},{'width_limit':2}):
            with self.assertRaises(ValueError):discover(cnf,Counter(),**kw)
        cnf,_=normalize([(1,2),(1,-2),(-1,2),(-1,-2),(3,4,5)])
        self.assertIsNotNone(discover(cnf,Counter())[0])

    def test_context_transport_handles_satisfied_path_edges(self):
        cnf,_=normalize([(1,5),(1,-5),(2,4),(-4,1),(-1,-4),(6,),(-6,)])
        s=self.make();model,key=publish(s,cnf,parts(cnf,[-1,-2]))
        self.assertIsNone(model);self.assertFalse(s._read(key)['answer'])
        self.assertGreater(s.counts['joint_compiled_parents'],0)

    def test_conditioning_can_remove_later_variable(self):
        cnf,_=normalize([(-1,3),(-1,-3),(1,4),(1,-4),(1,2),(1,-2)])
        s=self.make();model,key=publish(s,cnf,parts(cnf,[-1,-2]))
        self.assertIsNone(model);self.assertGreater(s.counts['joint_irrelevant_variables'],0)

    def test_cached_sat_prefix_prevents_fresh_acquisition(self):
        cnf,_=normalize(INDEPENDENT);s=self.make();acquire(s,restrict(cnf,{1:True}),256)
        with patch.object(s,'_visit',side_effect=AssertionError('Fresh solve despite cached prefix')):
            model,key=publish(s,cnf,parts(cnf,[-1,-2]))
        self.assertTrue(holds(cnf,model));self.assertEqual(s.counts['joint_prefix_hits'],1)

    def test_cached_unsat_prefix_prevents_fresh_acquisition(self):
        cnf,_=normalize(list(INDEPENDENT)+[(5,),(-5,)])
        s=self.make();acquire(s,restrict(cnf,{1:True}),256)
        with patch.object(s,'_visit',side_effect=AssertionError('Fresh solve despite cached prefix')):
            model,key=publish(s,cnf,parts(cnf,[-1,-2]))
        self.assertIsNone(model);self.assertEqual(s.counts['joint_prefix_hits'],1)

    def test_malformed_and_duplicate_paths_are_rejected(self):
        cnf,_=normalize(INDEPENDENT);s=self.make();good=parts(cnf,[-1,-2])
        for evidence in ([],good*2,[good[0],good[0]],[dict(literal=-1,path=[[88,0]]),good[1]]):
            with self.assertRaises(ValueError):force_all(s,cnf,evidence)
        self.assertEqual(s.archive_storage()[0],0)

    def test_signed_sparse_models_and_cold_readers(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=JointBackboneSolver(path)
            try:
                for flip in range(8):
                    source=[[(100*abs(l)+17)*(1 if l>0 else -1)*(-1 if flip>>(abs(l)-1)&1 else 1) for l in c] for c in INDEPENDENT]
                    r=acquire(s,source,256);self.assertTrue(r['result']['answer']);self.assertTrue(holds(source,r['result']['model']))
                source=list(INDEPENDENT)+[(5,),(-5,)];r=acquire(s,source,256);self.assertFalse(r['result']['answer'])
                keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                rd=cls(path)
                try:
                    for key in keys:self.assertIsNotNone(rd._read(key))
                finally:rd.close()

    def test_random_context_compilation_matches_exhaustive_truth(self):
        rng=random.Random(202611230432);s=self.make();checked=0
        for _ in range(128):
            source=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,5),2)] for _ in range(rng.randrange(5,15))]
            cnf,_=normalize(source);available=census(cnf)['forced'];chosen=[]
            for row in available:
                if abs(row['evidence']['literal']) not in {abs(p['literal']) for p in chosen}:chosen.append(row['evidence'])
                if len(chosen)==2:break
            if len(chosen)<2:continue
            model,key=publish(s,cnf,chosen);checked+=1
            truth=any(holds(cnf,dict(zip(range(1,5),bits))) for bits in product((False,True),repeat=4))
            self.assertEqual(model is not None,truth)
            if model is not None:self.assertTrue(holds(cnf,model))
        self.assertGreater(checked,40)

    def test_native_random_mixtures_match_truth_with_both_batch_policies(self):
        rng=random.Random(432);a=self.make();b=SingleFromJointSolver();self.addCleanup(b.close)
        for _ in range(128):
            source=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,6),rng.choice((2,3)))] for _ in range(rng.randrange(3,22))]
            truth=any(holds(source,dict(zip(range(1,6),bits))) for bits in product((False,True),repeat=5))
            for s in (a,b):
                r=acquire(s,source,256);self.assertEqual(r['result']['answer'],truth)
                if truth:self.assertTrue(holds(source,r['result']['model']))

    def test_budget_stop_has_no_unfinished_root_and_recovers(self):
        s=self.make();source=list(INDEPENDENT)+[list(c) for c in product((-5,5),(-6,6),(-7,7))]
        r=acquire(s,source,1,retain_stop=True);self.assertIsNone(r['result']);self.assertIsNone(s._read(s._canonical(source)[2]))
        self.assertFalse(acquire(s,source,256)['result']['answer'])


if __name__=='__main__':unittest.main()
