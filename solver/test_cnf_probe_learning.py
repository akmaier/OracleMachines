from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_equivalence import ProbeEquivalenceInventory, discover_equivalence_probes
from experiments.cnf_probe_learning import (
    ProbeLearningInventory, augment, learning_batch, discover_learning_probes, check_learning_probes)
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments, parity


def learning_source():
    # Two learned constraint resolvents make the previously unranked x=7 fail
    # under its false assumption (march_eq's Figure 1 local-learning pattern).
    source=[(1,-2),(2,-3),(2,3,7),(4,-5),(4,-6),(5,6,7),(-1,-4,7)]
    # Flip variable 2 to avoid the earlier all-true family recognizing the
    # unmodified example before probing. The logical learning pattern is intact.
    return [tuple(-l if abs(l)==2 else l for l in c) for c in source]


def equivalence_source():
    return [(-7,-1,4),(-5,4),(-5,6),(-4,-2),(-4,1,3),(-4,8),
            (-3,2),(-2,7),(-2,7,8),(-1,7),(3,8)]


def check_fibers(cnf, result, probe_limit, learn_limit):
    raw,fixed=check_learning_probes(cnf,result,probe_limit,learn_limit,Counter())
    if result['status'] in ('learned','learning_clear'):
        expanded=augment(cnf,result['batch'])
        for a in assignments(cnf):assert holds(cnf,a)==holds(expanded,a)
    target,names=normalize(raw)
    feasible={tuple(a[v] for v in names) for a in assignments(cnf) if holds(cnf,a)}
    reduction=result['continuation'] if result['status']=='learned' else result
    for model in assignments(target):
        bits=tuple(model[i] for i in range(1,len(names)+1))
        assert holds(target,model)==(bits in feasible)
        if holds(target,model):
            lifted={abs(l):False for c in cnf for l in c};lifted.update(fixed)
            lifted.update((v,model[i]) for i,v in enumerate(names,1))
            if reduction['status']=='equivalence':
                for v,rep in reduction['witness']['mapping']:
                    lifted[v]=lifted[abs(rep)] if rep>0 else not lifted[abs(rep)]
            assert holds(cnf,lifted)


class ProbeLearningTests(unittest.TestCase):
    def test_exhaustive_small_fibers(self):
        for variables,max_clauses in ((2,9),(3,3)):
            clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                     for signs in itertools.product((-1,0,1),repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses,count):
                    cnf,_=normalize(source)
                    for cap in (0,1,4):
                        check_fibers(cnf,discover_learning_probes(cnf,4,cap,Counter()),4,cap)

    def test_saved_reasons_force_new_literal_and_signed_equivalence(self):
        for source,kind in ((learning_source(),'forced'),(equivalence_source(),'equivalence')):
            cnf,_=normalize(source);before=Counter();after=Counter()
            old=discover_equivalence_probes(cnf,4,before);new=discover_learning_probes(cnf,4,4,after)
            self.assertEqual(old['status'],'clear');self.assertEqual(new['status'],'learned')
            self.assertEqual(old['attempts'],new['attempts']);self.assertEqual(new['continuation']['status'],kind)
            self.assertLessEqual(len(new['batch']),4);check_fibers(cnf,new,4,4)
            h=ProbeLearningInventory(max_depth=0);r=h.inspect(source);check_fused_tree(h,r['root']['key'])
            self.assertEqual(r['profile']['probing']['status'],'learned');h.close()

    def test_inconclusive_learning_does_not_recurse(self):
        source=[(-4,-1),(-3,-1,2),(1,2)];cnf,_=normalize(source)
        r=discover_learning_probes(cnf,4,4,Counter());self.assertEqual(r['status'],'learning_clear')
        target,fixed=check_learning_probes(cnf,r,4,4,Counter());self.assertEqual(target,cnf);self.assertEqual(fixed,{})
        h=ProbeLearningInventory(max_depth=0);r=h.inspect(source)
        self.assertEqual(h._load(r['root']['key'])['kind'],'unresolved');self.assertEqual(h.storage()['nodes'],1)
        h.close()

    def test_budget_and_binary_redundancy(self):
        for bad in (-1,17,True,1.5):
            with self.assertRaises(ValueError):ProbeLearningInventory(learn_limit=bad)
        cnf,_=normalize(learning_source());attempts=discover_equivalence_probes(cnf,4,Counter())['attempts']
        for cap in (0,1,4):self.assertLessEqual(len(learning_batch(cnf,attempts,cap,Counter())),cap)
        cnf,_=normalize([(-1,2),(-2,3),(-3,4)])
        attempts=discover_equivalence_probes(cnf,4,Counter())['attempts'];counts=Counter()
        self.assertEqual(learning_batch(cnf,attempts,4,counts),[])
        self.assertGreater(counts['learning_binary_redundant'],0)

    def test_preserves_earlier_recognition_and_disabled_policy(self):
        unflipped=[tuple(-l if abs(l)==2 else l for l in c) for c in learning_source()]
        h=ProbeLearningInventory(max_depth=0)
        self.assertEqual(h.inspect(unflipped)['profile']['probing']['status'],'skipped');h.close()
        h=ProbeLearningInventory(max_depth=0,learn_limit=0);old=ProbeEquivalenceInventory(max_depth=0)
        for source in (learning_source(),equivalence_source(),learning_source()+[(7,)]):
            a=h.inspect(source);b=old.inspect(source)
            self.assertEqual(a['profile'],b['profile']);self.assertEqual(a['summary'],b['summary'])
        h.close();old.close()

    def test_random_signed_mixtures_and_edits(self):
        rng=random.Random(20261109023245);h=ProbeLearningInventory(max_depth=2)
        sources=[learning_source(),equivalence_source()]
        for _ in range(60):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4))))
                    for _ in range(rng.randrange(8,24))]
            if rng.randrange(3)==0:source+=parity((2,3,4),1)
            sources.append(source)
        for source in sources:
            variables=sorted({abs(l) for c in source for l in c});perm=rng.sample(variables,len(variables))
            mapping={v:p*31*rng.choice((-1,1)) for v,p in zip(variables,perm)}
            variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source,variant,source+[(1,)],source[:-1]):
                cnf,_=normalize(changed);check_fibers(cnf,discover_learning_probes(cnf,4,4,Counter()),4,4)
                r=h.inspect(changed);check_fused_tree(h,r['root']['key'])
        h.close()

    def test_corrupt_circular_or_omitted_proofs_rejected(self):
        cnf,_=normalize(learning_source());r=discover_learning_probes(cnf,4,4,Counter());bads=[]
        for field,value in (('attempt',False),('unit',999),('clause',[1,-7])):
            bad=copy.deepcopy(r);bad['batch'][0][field]=value;bads.append(bad)
        bad=copy.deepcopy(r);bad['batch']=bad['batch'][:1];bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][0]['certificate']['units'][0][1]=len(cnf);bads.append(bad)
        bad=copy.deepcopy(r);bad['continuation']['attempts'][0]['certificate']['units'][0][1]=999;bads.append(bad)
        bad=copy.deepcopy(r);bad['status']='learning_clear';bads.append(bad)
        bad=dict(status='clear',attempts=r['attempts']);bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_learning_probes(cnf,bad,4,4,Counter())
        with self.assertRaises(ValueError):check_learning_probes(cnf[:-1],r,4,4,Counter())

    def test_cold_coexistence_transport_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'archive.db';old=ProbeEquivalenceInventory(path,max_depth=0)
            old.inspect(equivalence_source());prior=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=ProbeLearningInventory(path,max_depth=0);r=h.inspect(equivalence_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key));check_fused_tree(h,key)
            for model in ({},{1:1}):
                with self.assertRaises(ValueError):h.lift(key,model)
            for k,v in prior.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close();raw=path.read_bytes();h=ProbeLearningInventory(path,max_depth=0)
            again=h.inspect(equivalence_source());self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            h=ProbeLearningInventory(path,max_depth=0);node['profile']['probing']['batch'][0]['clause'][0]*=-1
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=ProbeLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(equivalence_source())
            h.close()
