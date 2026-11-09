from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_signed_subsumption import (
    SignedSubsumptionInventory, subsumption_certificate, check_subsumption)
from experiments.cnf_learning_activity import ActivityLearningInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_fused_conditioning import check_fused_tree


def hidden_two_cnf():
    return [(-8,-6),(-7,-6),(-7,-1,3),(-7,3),(-3,7,9),
            (-3,8),(-3,9),(-2,8),(4,6),(5,8)]


def check_signed_tree(h, key, seen=None):
    seen = set() if seen is None else seen
    if key in seen: return
    seen.add(key); node = h._load(key)
    edges = (node['edges'] if node['kind'] == 'and' else
             [e for a in node['alternatives'] for e in a['edges']] if node['kind'] == 'or' else
             [node['edge']] if node['kind'] in ('project','simplify','probe','subsumption') else [])
    if node['kind'] == 'subsumption':
        edge = node['edge']; child = h._load(edge['key'])
        for model in assignments(node['cnf']):
            local = {i: model[v] for i,v in enumerate(edge['names'],1)}
            assert holds(node['cnf'],model) == holds(child['cnf'],local)
        for model in assignments(child['cnf']):
            if holds(child['cnf'],model):
                lifted = h.lift(key,model)
                assert holds(node['cnf'],lifted)
                assert all(lifted[v] == model[i] for i,v in enumerate(edge['names'],1))
    else:
        check_fused_tree(h,key,{e['key'] for e in edges})
    for edge in edges: check_signed_tree(h,edge['key'],seen)


class SignedSubsumptionTests(unittest.TestCase):
    def test_exhaustive_signed_semantics_and_empty_clauses(self):
        for n, limit in ((2,9),(3,3)):
            clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                       for signs in itertools.product((-1,0,1),repeat=n)]
            for size in range(limit+1):
                for source in itertools.combinations(clauses,size):
                    certificate = subsumption_certificate(source,Counter())
                    target = check_subsumption(source,certificate,Counter())
                    for model in assignments(source):
                        self.assertEqual(holds(source,model),holds(target,model))
        source = [(1,), (1,), (1,-2), ()]
        certificate = subsumption_certificate(source,Counter())
        self.assertEqual(check_subsumption(source,certificate,Counter()),((),))

    def test_polarity_coverage_retained_witness_and_policy_corruption(self):
        source = [(-1,2),(-1,2,3),(1,2),(-1,2,4)]
        certificate = subsumption_certificate(source,Counter())
        self.assertEqual(certificate,dict(kept=[0,2],removed=[[1,0],[3,0]]))
        bads = [dict(kept=[0,2],removed=[[1,2],[3,0]]),
                dict(kept=[0,2],removed=[[1,0]]),
                dict(kept=[0,2],removed=[[1,3],[3,0]]),
                dict(kept=[0,2,2],removed=[[1,0],[3,0]]),
                dict(kept=[False,2],removed=[[1,0],[3,0]]),
                dict(kept=[0,2],removed=[[1,0],[3,99]]),
                dict(kept=[0,1,2,3],removed=[])]
        for bad in bads:
            with self.assertRaises(ValueError): check_subsumption(source,bad,Counter())

    def test_hidden_family_and_disappearing_variable_lifts(self):
        h = SignedSubsumptionInventory(max_depth=0)
        old = ActivityLearningInventory(max_depth=0)
        self.assertFalse(old.inspect(hidden_two_cnf())['summary']['closed'])
        result = h.inspect(hidden_two_cnf()); node = h._load(result['root']['key'])
        self.assertEqual(node['kind'],'subsumption');self.assertTrue(result['summary']['closed'])
        self.assertEqual(node['subsumption']['core_profile']['outcomes']['two_cnf'],'recognized')
        self.assertNotIn(1,node['edge']['names'])
        check_signed_tree(h,result['root']['key'])
        with self.assertRaises(ValueError): h.lift(result['root']['key'],{})
        old.close();h.close()

    def test_exhaustive_inventory_and_random_edits_all_branches(self):
        h = SignedSubsumptionInventory(max_depth=1)
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            result = h.inspect([c for i,c in enumerate(clauses) if mask>>i&1])
            check_signed_tree(h,result['root']['key'])
        rng = random.Random(2026110910)
        for _ in range(40):
            source = [tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(2,5)))
                      for _ in range(rng.randrange(10,25))]
            for changed in (source,source+[source[0]+(7,)],source[:-1],source+[(1,)]):
                result=h.inspect(changed);check_signed_tree(h,result['root']['key'])
        h.close()

    def test_frontier_witnesses_and_failed_searches_persist(self):
        data=json.loads(Path('experiments/results/cnf-activity/frontier-subsumption.json').read_text())
        h=SignedSubsumptionInventory(max_depth=0,candidate_limit=0)
        exposures=failures=0
        for record in data['records']:
            r=h.inspect(record['source']);node=h._load(r['root']['key'])
            self.assertEqual(r['summary']['closed'],bool(record['recognized']))
            if record['recognized']:exposures+=1
            else:
                failures+=1;self.assertEqual(node['kind'],'unresolved')
            self.assertEqual(node['subsumption']['certificate'],
                dict(kept=record['kept'],removed=record['removed']))
        self.assertEqual((exposures,failures),(7,140));h.close()

    def test_signed_renaming_priorities_and_adversarial_edit(self):
        h=SignedSubsumptionInventory(max_depth=0)
        rng=random.Random(4110);names=list(range(1,10));rng.shuffle(names)
        mapping={i+1:(v*71+3)*rng.choice((-1,1)) for i,v in enumerate(names)}
        variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c))
                 for c in reversed(hidden_two_cnf())]
        for source in (hidden_two_cnf(),variant):
            r=h.inspect(source);self.assertTrue(r['summary']['closed']);check_signed_tree(h,r['root']['key'])
        # Replacing a subset witness with opposite polarity is not a deletion license.
        cnf,_=normalize(hidden_two_cnf());cert=subsumption_certificate(cnf,Counter())
        j,k=cert['removed'][0];edited=list(cnf);edited[k]=tuple(-l for l in cnf[k])
        with self.assertRaises(ValueError):check_subsumption(edited,cert,Counter())
        for source in ([(1,2),(-1,3)],[(1,)],[(1,2,3),(4,5,6)],hidden_two_cnf()+[(1,)]):
            r=h.inspect(source);self.assertNotIn('subsumption',h._load(r['root']['key']))
        h.close()

    def test_cold_replay_policy_binding_and_forged_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=ActivityLearningInventory(path,max_depth=0)
            old.inspect(hidden_two_cnf());saved=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=SignedSubsumptionInventory(path,max_depth=0);r=h.inspect(hidden_two_cnf());key=r['root']['key']
            node=copy.deepcopy(h._load(key));self.assertNotIn(key,saved)
            for k,v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close();raw=path.read_bytes();h=SignedSubsumptionInventory(path,max_depth=0)
            again=h.inspect(hidden_two_cnf());self.assertEqual(again['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            bads=[]
            bad=copy.deepcopy(node);bad['edge']['names'].append(1);bads.append(bad)
            bad=copy.deepcopy(node);bad['edge']['key']=next(iter(saved));bads.append(bad)
            bad=copy.deepcopy(node);del bad['subsumption'];bads.append(bad)
            bad=copy.deepcopy(node);bad['subsumption']['core_profile']['outcomes']['horn']='recognized';bads.append(bad)
            bad=copy.deepcopy(node);bad['summary']['closed']=False;bads.append(bad)
            for bad in bads:
                path.write_bytes(raw);h=SignedSubsumptionInventory(path,max_depth=0)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
                h.close();h=SignedSubsumptionInventory(path,max_depth=0)
                with self.assertRaises(ValueError):h.inspect(hidden_two_cnf())
                h.close()
