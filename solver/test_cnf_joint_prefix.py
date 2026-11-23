from collections import Counter
from itertools import product
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import random,unittest
from experiments.cnf_joint_prefix import reuse_prefix,reused_joint_prefix
from experiments.cnf_joint_backbone import force_all
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_residual_dag import normalize,restrict,token,FORMAT,holds
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from solver.test_cnf_joint_backbone import INDEPENDENT,parts
from experiments.probe_cnf_joint_backbone import census


class JointPrefixTests(unittest.TestCase):
    def compare(self,source,literals,seed=None):
        cnf,_=normalize(source);evidence=parts(cnf,literals);outputs=[];counts=[]
        for fn in (force_all,reuse_prefix):
            s=ConsequencePrioritySolver()
            try:
                if seed is not None:acquire(s,restrict(cnf,seed),256)
                s.counts=Counter();model,proof=fn(s,cnf,evidence);key=token(cnf,Counter())
                node=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=model is not None)
                if model is None:node['proof']=proof
                else:
                    self.assertTrue(holds(cnf,model));node['model']=[model.get(v,False) for v in range(1,max((abs(l) for c in cnf for l in c),default=0)+1)]
                s._store(key,node);outputs.append((model,proof,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY rowid'))));counts.append(dict(s.counts))
            finally:s.close()
        self.assertEqual(outputs[0],outputs[1]);return outputs[1],counts

    def test_negative_prefix_reuses_exact_construction_and_proof(self):
        _,c=self.compare(list(INDEPENDENT)+[(5,),(-5,)],[-1,-2])
        self.assertEqual(c[1]['joint_prefix_construction_reuses'],1)
        self.assertLess(c[1]['normalization_literal_visits'],c[0]['normalization_literal_visits'])
        self.assertLess(c[1]['restriction_literal_visits'],c[0]['restriction_literal_visits'])
        self.assertEqual(c[0]['verified_nodes'],c[1]['verified_nodes'])

    def test_positive_exit_and_single_consequence_match(self):
        _,c=self.compare(INDEPENDENT,[-1,-2]);self.assertNotIn('joint_prefix_construction_reuses',c[1])
        self.compare(list(INDEPENDENT)+[(5,),(-5,)],[-1])

    def test_cached_prefix_keeps_priority(self):
        for source in (INDEPENDENT,list(INDEPENDENT)+[(5,),(-5,)]):
            _,c=self.compare(source,[-1,-2],seed={1:True});self.assertEqual(c[1]['joint_prefix_hits'],1)
            self.assertNotIn('joint_prefix_construction_reuses',c[1])

    def test_disappearing_variable_and_satisfied_reason(self):
        self.compare([(-1,3),(-1,-3),(1,4),(1,-4),(1,2),(1,-2)],[-1,-2])
        self.compare([(1,5),(1,-5),(2,4),(-4,1),(-1,-4),(6,),(-6,)],[-1,-2])

    def test_bad_paths_and_larger_batches_remain_rejected(self):
        cnf,_=normalize(INDEPENDENT);evidence=parts(cnf,[-1,-2]);s=ConsequencePrioritySolver()
        try:
            for e in ([],evidence*2,[evidence[0],evidence[0]],[dict(literal=-1,path=[[88,0]]),evidence[1]]):
                with self.assertRaises(ValueError):reuse_prefix(s,cnf,e)
            self.assertEqual(s.archive_storage()[0],0)
        finally:s.close()

    def test_random_signed_mixtures_match_truth_and_bytes(self):
        rng=random.Random(737);checked=0
        for _ in range(96):
            source=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,5),2)] for _ in range(rng.randrange(5,15))]
            cnf,_=normalize(source);chosen=[]
            for row in census(cnf)['forced']:
                l=row['evidence']['literal']
                if abs(l) not in {abs(x) for x in chosen}:chosen.append(l)
                if len(chosen)==2:break
            if len(chosen)!=2:continue
            output,_=self.compare(cnf,chosen);checked+=1
            self.assertEqual(output[0] is not None,any(holds(cnf,dict(zip(range(1,5),bits))) for bits in product((False,True),repeat=4)))
        self.assertGreater(checked,30)

    def test_exception_restores_scoped_override(self):
        from experiments import cnf_consequence_priority as p,cnf_joint_backbone as j
        original=p.force_all
        with self.assertRaisesRegex(RuntimeError,'test'):
            with reused_joint_prefix():
                self.assertIs(p.force_all,reuse_prefix);self.assertIs(j.force_all,reuse_prefix)
                raise RuntimeError('test')
        self.assertIs(p.force_all,original);self.assertIs(j.force_all,original)

    def test_cold_checkers_reject_tampered_compiled_parent(self):
        source=list(INDEPENDENT)+[(5,),(-5,)];out,_=self.compare(source,[-1,-2])
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ConsequencePrioritySolver(path)
            try:
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1(id,payload) VALUES (?,?)',out[2])
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path)
                try:
                    for k,_ in out[2]:self.assertIsNotNone(r._read(k))
                finally:r.close()
            import json
            split=next((k,json.loads(v)) for k,v in out[2] if json.loads(v).get('proof',{}).get('kind')=='split')
            split[1]['proof']['low']='absent-child'
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path)
                try:
                    with self.assertRaises(ValueError):r._verify(split[0],split[1])
                finally:r.close()


if __name__=='__main__':unittest.main()
