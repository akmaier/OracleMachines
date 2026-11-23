from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,unittest
from experiments.cnf_whole_proof_reuse import WholeProofReuseSolver
from experiments.cnf_partial_proof_plan import extract_partial,make_plan,check_plan,survival,recompose
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import holds
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

CUBE=list(product((-1,1),(-2,2),(-3,3)))


class WholeProofReuseTests(unittest.TestCase):
    def solver(self,**kw):
        s=WholeProofReuseSolver(leaves=False,**kw);self.addCleanup(s.close);return s

    @classmethod
    def setUpClass(cls):
        s=WholeProofReuseSolver(leaves=False)
        try:
            acquire(s,CUBE,256)
            cls.plan=make_plan(extract_partial(s,CUBE)[0])
        finally:s.close()

    def test_all_cube_deletions_agree_with_exhaustive_truth(self):
        for mask in range(256):
            target=[c for i,c in enumerate(CUBE) if mask>>i&1]
            s=self.solver();r=recompose(s,target,self.plan,256)
            node=s._read(r['root']);truth=any(holds(target,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
            self.assertEqual(node['answer'],truth)

    def test_budget_frontier_retains_a_complete_plan(self):
        s=self.solver();acquire(s,CUBE,256)
        for nodes,literals in ((1,65536),(64,1),(4,65536)):
            bundle,c=extract_partial(s,CUBE,node_limit=nodes,literal_limit=literals);plan=make_plan(bundle)
            check_plan(plan);self.assertGreater(c['partial_plan_open_leaves'],0)
            self.assertLessEqual(c.get('conditional_node_visits',0),nodes)
            self.assertLessEqual(c.get('conditional_node_literals',0),literals)

    def test_open_leaf_never_provides_authority(self):
        plan=dict(format=self.plan['format'],tree=dict(leaf=0),templates=[dict(open=True,clauses=[])])
        s=self.solver();r=recompose(s,CUBE,plan,0)
        self.assertTrue(r['stopped']);self.assertIsNone(s._read(r['root']))
        self.assertEqual(s.counts.get('expanded_nodes',0),0);self.assertFalse(s.db.active)

    def test_tampering_is_rejected_before_publication(self):
        for mode in ('leaf','assumptions','open','unused'):
            p=deepcopy(self.plan)
            if mode=='leaf':p['tree']=dict(leaf=999)
            elif mode=='assumptions':p['templates'][0]['assumptions'].append([100,True])
            elif mode=='open':p['templates'][0]=dict(open=True,clauses=[[1]])
            else:p['templates'].append(dict(open=True,clauses=[]))
            s=self.solver()
            with self.assertRaises(ValueError):recompose(s,CUBE,p,256)
            self.assertEqual(s.archive_storage()[0],0);self.assertFalse(s.db.active)

    def test_automatic_near_match_and_raw_positive_witness(self):
        s=self.solver(node_limit=256);acquire(s,CUBE,256)
        src=[[x*19 for x in c] for c in CUBE[1:]]
        r=s.solve((iter(c) for c in src));self.assertTrue(r['answer']);self.assertTrue(holds(src,r['model']))
        self.assertEqual(r['metrics']['whole_plan_attempts'],1)
        self.assertGreater(r['metrics']['whole_plan_selected_intact'],0)
        self.assertEqual(r['authority'],'native')

    def test_shared_native_budget_and_reusable_stopped_prefix(self):
        target=CUBE[1:-1]+[(-1,-2,-3,4),(-1,-2,-3,-4),
            (1,2,3,5,6),(1,2,3,5,-6),(1,2,3,-5,6),(1,2,3,-5,-6)]
        for budget in range(7):
            s=self.solver();r=recompose(s,target,self.plan,budget)
            self.assertLessEqual(s.counts.get('expanded_nodes',0),budget)
            self.assertFalse(s.db.active);self.assertFalse(s.db.in_transaction)
            self.assertIsNone(s._support_plan);self.assertIsNone(s._verification_canonical)
            for key, in s.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(s._read(key))

    def test_known_roots_skip_extraction_and_preserve_payloads(self):
        s=self.solver(node_limit=256);acquire(s,CUBE,256);first=s.solve(CUBE[1:])
        stored=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
        with patch('experiments.cnf_whole_proof_reuse.extract_partial',side_effect=AssertionError('fresh extraction')):
            again=s.solve(CUBE[1:]);self.assertEqual(first['answer'],again['answer'])
        self.assertEqual(stored,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id')))

    def test_cold_native_replay_needs_no_plan(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=WholeProofReuseSolver(path,leaves=False,node_limit=256)
            try:acquire(s,CUBE,256);r=s.solve(CUBE[1:]);rows=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key,payload in rows.items():self.assertEqual(reader._read(key),json.loads(payload))
                finally:reader.close()
            s=WholeProofReuseSolver(path,leaves=False,node_limit=0)
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('search')):
                    self.assertEqual(s.solve(CUBE[1:])['answer'],r['answer'])
            finally:s.close()

    def test_source_and_limit_validation(self):
        for option in (dict(whole_plan_nodes=0),dict(whole_plan_nodes=65),dict(whole_plan_literals=True)):
            with self.assertRaises(ValueError):WholeProofReuseSolver(**option)
        s=self.solver()
        for bad in (True,0,1.5):
            with self.assertRaises(ValueError):s.solve([[bad]])

    def test_no_origin_does_not_invent_a_plan(self):
        s=self.solver(node_limit=256);r=attempt(s,CUBE[1:])
        self.assertEqual(r['status'],'sat');self.assertEqual(r['metrics'].get('whole_plan_extractions',0),0)


if __name__=='__main__':unittest.main()
