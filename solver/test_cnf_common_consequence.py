from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_common_consequence import (
    CommonConsequenceInventory, discover_common_probes, check_common_probes)
from experiments.cnf_failed_literal import FailedLiteralInventory, discover_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments, parity


def common_source():
    # Smallest common-consequence opportunity in the prior archived study.
    return [(-4,3),(-3,-1),(-3,2),(-2,-1),(-1,2,5),(1,5)]


def check_fibers(cnf, result, limit):
    target,fixed=check_common_probes(cnf,result,limit,Counter())
    remaining=sorted({abs(l) for c in target for l in c})
    feasible={tuple(a[v] for v in remaining) for a in assignments(cnf) if holds(cnf,a)}
    for model in assignments(target):
        assert holds(target,model)==(tuple(model[v] for v in remaining) in feasible)
        if holds(target,model):
            lifted={abs(l):False for c in cnf for l in c};lifted.update(fixed);lifted.update(model)
            assert holds(cnf,lifted)


class CommonConsequenceTests(unittest.TestCase):
    def test_exhaustive_two_variable_fibers(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            cnf,_=normalize([c for i,c in enumerate(clauses) if mask>>i&1])
            for limit in (1,4):
                check_fibers(cnf,discover_common_probes(cnf,limit,Counter()),limit)

    def test_reuses_attempts_and_all_common_literals_of_first_pair(self):
        for source,limit,expected in ((common_source(),4,[5]),
                                      ([(1,2),(-1,2),(1,3),(-1,3)],1,[2,3])):
            cnf,_=normalize(source);a=Counter();b=Counter()
            old=discover_probes(cnf,limit,a);new=discover_common_probes(cnf,limit,b)
            self.assertEqual(old['status'],'clear');self.assertEqual(new['status'],'common')
            self.assertEqual(old['attempts'],new['attempts']);self.assertEqual(a['probe_attempts'],b['probe_attempts'])
            self.assertEqual(new['witness'],dict(pair=0,literals=expected));check_fibers(cnf,new,limit)
        old=FailedLiteralInventory(max_depth=0);new=CommonConsequenceInventory(max_depth=0)
        self.assertFalse(old.inspect(common_source())['summary']['closed'])
        r=new.inspect(common_source());self.assertTrue(r['summary']['closed']);check_fused_tree(new,r['root']['key'])
        old.close();new.close()

    def test_random_mixtures_renamings_and_source_invalidation(self):
        rng=random.Random(2026110902);h=CommonConsequenceInventory(max_depth=2)
        for _ in range(80):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,3,4))))
                    for _ in range(rng.randrange(10,25))]
            if rng.randrange(3)==0:source+=parity((2,3,4),1)
            for variant in (source,source+[(1,)],source+[(-1,)],
                            [tuple(l*31 for l in reversed(c)) for c in reversed(source)]):
                r=h.inspect(variant);check_fused_tree(h,r['root']['key'])
        for variant in (common_source(),common_source()[:4]+common_source()[5:],common_source()+[(-5,)]):
            r=h.inspect(variant);check_fused_tree(h,r['root']['key'])
        self.assertTrue(holds(common_source()[:4]+common_source()[5:],{1:True,2:False,3:False,4:False,5:False}))
        h.close()

    def test_no_conflict_is_not_common_or_sat(self):
        cnf,_=normalize(parity((1,2,3),0)+parity((1,2,3),1))
        result=discover_common_probes(cnf,4,Counter())
        self.assertEqual(result,dict(status='clear',attempts=[]))
        self.assertFalse(any(holds(cnf,a) for a in assignments(cnf)))
        check_fibers(cnf,result,4)

    def test_corrupt_or_omitted_common_proof_rejected(self):
        cnf,_=normalize(common_source());r=discover_common_probes(cnf,4,Counter());bads=[]
        for witness in (dict(pair=1,literals=[5]),dict(pair=False,literals=[5]),
                        dict(pair=0,literals=[-3]),dict(pair=0,literals=[-5]),dict(pair=0,literals=[])):
            bad=copy.deepcopy(r);bad['witness']=witness;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][1]['value']=False;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][0]['certificate']['units'][0][1]=999;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts']=bad['attempts'][:2];bads.append(bad)
        bad=copy.deepcopy(r);bad['closure']['units']=[[999,0]];bads.append(bad)
        bad=dict(status='clear',attempts=r['attempts']);bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_common_probes(cnf,bad,4,Counter())

    def test_cold_replay_policy_isolation_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'archive.db';old=FailedLiteralInventory(path,max_depth=0)
            old.inspect(common_source());prior=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=CommonConsequenceInventory(path,max_depth=0);r=h.inspect(common_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key))
            for k,v in prior.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close();raw=path.read_bytes();h=CommonConsequenceInventory(path,max_depth=0)
            again=h.inspect(common_source());self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            h=CommonConsequenceInventory(path,max_depth=0)
            node['profile']['probing']['witness']['literals']=[-5]
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=CommonConsequenceInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(common_source())
            h.close()

    def test_invalid_lift_and_earlier_priorities(self):
        h=CommonConsequenceInventory(max_depth=0);r=h.inspect(common_source());key=r['root']['key']
        with self.assertRaises(ValueError):h.lift(key,{})
        for source in (common_source()+[(5,)],common_source()+[(100,101)],parity((1,2,3),1)):
            r=h.inspect(source);self.assertEqual(r['profile']['probing']['status'],'skipped')
        h.close()
