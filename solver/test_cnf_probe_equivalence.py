from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_common_consequence import CommonConsequenceInventory, discover_common_probes
from experiments.cnf_probe_equivalence import (
    ProbeEquivalenceInventory, discover_equivalence_probes, check_equivalence_probes)
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments, parity


def equivalence_source():
    # Smallest indirect equivalence on a selected unresolved archived path.
    return [(-4,-2,-1),(-3,1),(-2,4),(2,3)]


def check_fibers(cnf, result, limit):
    raw, fixed = check_equivalence_probes(cnf, result, limit, Counter())
    target, names = normalize(raw)
    feasible = {tuple(a[v] for v in names) for a in assignments(cnf) if holds(cnf,a)}
    for model in assignments(target):
        bits = tuple(model[i] for i in range(1,len(names)+1))
        assert holds(target,model) == (bits in feasible)
        if holds(target,model):
            lifted = {abs(l):False for c in cnf for l in c};lifted.update(fixed)
            lifted.update((v,model[i]) for i,v in enumerate(names,1))
            if result['status']=='equivalence':
                for v,rep in result['witness']['mapping']:
                    lifted[v] = lifted[abs(rep)] if rep>0 else not lifted[abs(rep)]
            assert holds(cnf,lifted)


class ProbeEquivalenceTests(unittest.TestCase):
    def test_exhaustive_two_variable_fibers(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        rewrites=0
        for mask in range(1<<len(clauses)):
            cnf,_=normalize([c for i,c in enumerate(clauses) if mask>>i&1])
            for limit in (1,4):
                r=discover_equivalence_probes(cnf,limit,Counter())
                rewrites+=r['status']=='equivalence';check_fibers(cnf,r,limit)
        self.assertGreater(rewrites,0)

    def test_indirect_block_reuses_all_attempts_and_closes(self):
        cnf,_=normalize(equivalence_source());a=Counter();b=Counter()
        old=discover_common_probes(cnf,4,a);new=discover_equivalence_probes(cnf,4,b)
        self.assertEqual(old['status'],'clear');self.assertEqual(new['status'],'equivalence')
        self.assertEqual(old['attempts'],new['attempts']);self.assertEqual(a['probe_attempts'],b['probe_attempts'])
        self.assertEqual(new['witness']['mapping'],[[1,1],[2,-1],[3,1]])
        check_fibers(cnf,new,4)
        old=CommonConsequenceInventory(max_depth=0);h=ProbeEquivalenceInventory(max_depth=0)
        self.assertFalse(old.inspect(cnf)['summary']['closed'])
        r=h.inspect(cnf);self.assertTrue(r['summary']['closed']);check_fused_tree(h,r['root']['key'])
        self.assertEqual(r['profile']['probing']['status'],'equivalence')
        old.close();h.close()

    def test_transitive_signed_blocks_vanishing_reps_and_couplings(self):
        sources=[[(1,2),(-1,-2)],
                 [(-1,2),(1,-2),(-2,-3),(2,3)],
                 [(-1,2),(1,-2),(-2,-3),(2,3),(1,3,4),(-1,-3,-4)],
                 equivalence_source()+[(1,2,4),(-1,-2,-4)]]
        for source in sources:
            cnf,_=normalize(source);r=discover_equivalence_probes(cnf,4,Counter());check_fibers(cnf,r,4)
        # Removing the binary reason invalidates the original equivalence.
        cnf,_=normalize(equivalence_source());r=discover_equivalence_probes(cnf,4,Counter())
        changed=tuple(c for c in cnf if c != (-3,1))
        self.assertTrue(holds(changed,{1:False,2:False,3:True,4:False}))
        with self.assertRaises(ValueError):check_equivalence_probes(changed,r,4,Counter())

    def test_random_mixtures_and_signed_renamings(self):
        rng=random.Random(2026110903);h=ProbeEquivalenceInventory(max_depth=2)
        for _ in range(80):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4))))
                    for _ in range(rng.randrange(8,24))]
            if rng.randrange(3)==0:source+=parity((2,3,4),1)
            perm=rng.sample(range(1,7),6);mapping={v:(perm[v-1]*31)*rng.choice((-1,1)) for v in range(1,7)}
            variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source,variant,source+[(1,)],source+[(-1,)]):
                cnf,_=normalize(changed);check_fibers(cnf,discover_equivalence_probes(cnf,4,Counter()),4)
                r=h.inspect(changed);check_fused_tree(h,r['root']['key'])
        h.close()

    def test_corruption_and_omitted_rewrite_rejected(self):
        cnf,_=normalize(equivalence_source());r=discover_equivalence_probes(cnf,4,Counter());bads=[]
        for witness in (dict(pair=False,mapping=r['witness']['mapping']),
                        dict(pair=1,mapping=r['witness']['mapping']),
                        dict(pair=0,mapping=[[1,1],[2,1],[3,1]]),
                        dict(pair=0,mapping=[[1,2],[2,2],[3,2]]),
                        dict(pair=0,mapping=[])):
            bad=copy.deepcopy(r);bad['witness']=witness;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][0]['certificate']['units'][0][1]=999;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][1]['value']=False;bads.append(bad)
        bad=dict(status='clear',attempts=r['attempts']);bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_equivalence_probes(cnf,bad,4,Counter())

    def test_cold_replay_policy_isolation_lifts_and_edge_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'archive.db';old=CommonConsequenceInventory(path,max_depth=0)
            old.inspect(equivalence_source());prior=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=ProbeEquivalenceInventory(path,max_depth=0);r=h.inspect(equivalence_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key));check_fused_tree(h,key)
            for bad_model in ({},{1:1},{1:False,2:False}):
                with self.assertRaises(ValueError):h.lift(key,bad_model)
            for k,v in prior.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            bad=copy.deepcopy(node);bad['edge']['names']=[999]
            with self.assertRaises(ValueError):h._check(key,bad)
            h.close();raw=path.read_bytes();h=ProbeEquivalenceInventory(path,max_depth=0)
            again=h.inspect(equivalence_source());self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            h=ProbeEquivalenceInventory(path,max_depth=0);node['profile']['probing']['witness']['mapping'][1][1]=1
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=ProbeEquivalenceInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(equivalence_source())
            h.close()

    def test_preserves_earlier_rules_and_inconclusive_status(self):
        h=ProbeEquivalenceInventory(max_depth=0)
        for source in (equivalence_source()+[(1,)],equivalence_source()+[(100,101)],parity((1,2,3),1)):
            self.assertEqual(h.inspect(source)['profile']['probing']['status'],'skipped')
        cnf,_=normalize(parity((1,2,3),0)+parity((1,2,3),1))
        self.assertEqual(discover_equivalence_probes(cnf,4,Counter()),dict(status='clear',attempts=[]))
        self.assertFalse(any(holds(cnf,a) for a in assignments(cnf)))
        h.close()
