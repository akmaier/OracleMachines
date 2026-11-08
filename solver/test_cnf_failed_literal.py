from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_failed_literal import FailedLiteralInventory, discover_probes, check_probes
from experiments.cnf_fused_conditioning import FusedShortestClauseInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments, parity


def forced_source():
    return [(1,2),(1,-2),(-1,3,4),(-3,-4,5),(-1,-3,-5),(2,4,-5)]


class FailedLiteralTests(unittest.TestCase):
    def test_exhaustive_small_probe_fibers(self):
        # All 512 CNFs over two variables, including constants and units.
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1,0,1), repeat=2)]
        for mask in range(1 << len(clauses)):
            cnf,_ = normalize([c for i,c in enumerate(clauses) if mask >> i & 1])
            certificate = discover_probes(cnf, 4, Counter())
            target,fixed = check_probes(cnf, certificate, 4, Counter())
            remaining = sorted({abs(l) for c in target for l in c})
            feasible = {tuple(a[v] for v in remaining) for a in assignments(cnf) if holds(cnf,a)}
            for model in assignments(target):
                self.assertEqual(holds(target,model), tuple(model[v] for v in remaining) in feasible)
                if holds(target,model):
                    lifted={abs(l):False for c in cnf for l in c};lifted.update(fixed);lifted.update(model)
                    self.assertTrue(holds(cnf,lifted))

    def test_random_tree_fibers_and_edits(self):
        rng=random.Random(2026110901);h=FailedLiteralInventory(max_depth=2)
        probes=0
        for _ in range(80):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,3,4))))
                    for _ in range(rng.randrange(10,26))]
            if rng.randrange(3)==0:source+=parity((2,3,4),1)
            for variant in (source, source+[(1,)], source+[(-1,)],
                            [tuple(l*17 for l in reversed(c)) for c in reversed(source)]):
                r=h.inspect(variant);check_fused_tree(h,r['root']['key'])
                probes+=r['metrics'].get('probe_attempts',0)
        self.assertGreater(probes,0)
        self.assertTrue(any(n['kind']=='probe' for n in h.checked.values()));h.close()

    def test_forced_value_and_gate_priority(self):
        h=FailedLiteralInventory(max_depth=0)
        r=h.inspect(forced_source());node=h._load(r['root']['key'])
        self.assertEqual(node['kind'],'probe');self.assertEqual(node['depth'],0)
        check_fused_tree(h,r['root']['key'])
        for source in ([(1,2),(-1,-2)],forced_source()+[(1,)],
                       forced_source()+[(100,101)], parity((1,2,3),1)):
            r=h.inspect(source);node=h._load(r['root']['key'])
            self.assertEqual(node['profile']['probing']['status'],'skipped')
        h.close()

    def test_no_binary_clause_and_unsuccessful_not_sat(self):
        # Four clauses on each of two overlapping parity equations can be
        # globally UNSAT without unit conflicts under any single assumption.
        source=parity((1,2,3),0)+parity((1,2,3),1)
        cnf,_=normalize(source);r=discover_probes(cnf,4,Counter())
        self.assertEqual(r,dict(status='clear',attempts=[]))
        self.assertFalse(any(holds(cnf,a) for a in assignments(cnf)))
        self.assertEqual(check_probes(cnf,r,4,Counter()),(cnf,{}))

    def test_corrupt_reasons_assumptions_missing_failures_and_transport(self):
        cnf,_=normalize(forced_source());r=discover_probes(cnf,4,Counter())
        self.assertEqual(r['status'],'forced')
        bads=[]
        bad=copy.deepcopy(r);bad['attempts'][-1]['certificate']['conflict']=99999;bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][-1]['value']=int(bad['attempts'][-1]['value']);bads.append(bad)
        bad=copy.deepcopy(r);bad['attempts'][-1]['certificate']['units'][0][0]*=-1;bads.append(bad)
        bad=copy.deepcopy(r);bad['closure']['units'].append([999,0]);bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_probes(cnf,bad,4,Counter())
        clear=discover_probes(((1,2),(-1,-2)),4,Counter());clear['attempts'].pop()
        with self.assertRaisesRegex(ValueError,'Omitted'):check_probes(((1,2),(-1,-2)),clear,4,Counter())
        h=FailedLiteralInventory(max_depth=0);r=h.inspect(forced_source());node=h._load(r['root']['key'])
        bad=copy.deepcopy(node);bad['edge']['names'].append(999)
        with self.assertRaises(ValueError):h._check(r['root']['key'],bad)
        with self.assertRaises(ValueError):h.lift(r['root']['key'],{})
        h.close()

    def test_cold_persistence_policy_isolation_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'archive.db';old=FusedShortestClauseInventory(path,max_depth=0)
            old.inspect(forced_source());prior=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=FailedLiteralInventory(path,max_depth=0);r=h.inspect(forced_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key))
            for k,v in prior.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close();raw=path.read_bytes();h=FailedLiteralInventory(path,max_depth=0)
            again=h.inspect(forced_source());self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            h=FailedLiteralInventory(path,max_depth=0)
            node['profile']['probing']['attempts'][-1]['certificate']['conflict']=99999
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=FailedLiteralInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(forced_source())
            h.close()

    def test_zero_budget_retains_baseline(self):
        old=FusedShortestClauseInventory(max_depth=2);new=FailedLiteralInventory(max_depth=2,probe_limit=0)
        for source in (forced_source(),parity((1,2,3),0),forced_source()+[(1,)]):
            a,b=old.inspect(source),new.inspect(source)
            self.assertEqual(a['summary'],b['summary']);self.assertEqual(b['metrics'].get('probe_attempts',0),0)
            check_fused_tree(new,b['root']['key'])
        old.close();new.close()
        for budget in (-1,65,True,1.5):
            with self.assertRaises(ValueError):FailedLiteralInventory(probe_limit=budget)
