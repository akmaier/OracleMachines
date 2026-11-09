from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_implied_subsumption import (
    ImpliedSubsumptionInventory, indexed_certificate, check_indexed_subsumption,
    original_implications)
from experiments.cnf_signed_subsumption import SignedSubsumptionInventory, subsumption_certificate
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_signed_subsumption import check_signed_tree, hidden_two_cnf


def implication_source():
    return [(-4,-1),(-3,-1,2),(1,2)]


class ImpliedSubsumptionTests(unittest.TestCase):
    def test_exhaustive_certificates_and_signed_model_equivalence(self):
        for n, limit in ((2,9),(3,3)):
            clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                     for signs in itertools.product((-1,0,1),repeat=n)]
            for size in range(limit+1):
                for source in itertools.combinations(clauses,size):
                    cert=indexed_certificate(source,Counter())
                    self.assertEqual(cert,subsumption_certificate(source,Counter()))
                    core=check_indexed_subsumption(source,cert,Counter())
                    for model in assignments(source):self.assertEqual(holds(source,model),holds(core,model))

    def test_equal_width_elision_duplicates_and_repeated_literal_fallback(self):
        source=list(itertools.combinations(range(1,11),3))
        old,new=Counter(),Counter()
        self.assertEqual(subsumption_certificate(source,old),indexed_certificate(source,new))
        self.assertEqual(old['subsumption_discovery_subset_tests'],120*119//2)
        self.assertEqual(new['subsumption_discovery_subset_tests'],0)
        for raw in (source+source[:5],[(1,),(1,),(1,-2),()],
                    [(1,1,1),(1,2),(1,)],[(1,2),(1,1),(2,2,3)],[]):
            counts=Counter();cert=indexed_certificate(raw,counts)
            self.assertEqual(cert,subsumption_certificate(raw,Counter()))
            check_indexed_subsumption(raw,cert,Counter())
            if any(len(set(c))!=len(c) for c in raw):self.assertEqual(counts['subset_index_fallbacks'],1)

    def test_saved_frontier_eight_exposures_without_fresh_probes(self):
        data=json.loads(Path('experiments/results/cnf-signed-subsumption/mechanisms.json').read_text())
        old=SignedSubsumptionInventory(max_depth=0,candidate_limit=0)
        new=ImpliedSubsumptionInventory(max_depth=0,candidate_limit=0)
        exposed=0
        for row in data['frontier']:
            a,b=old.inspect(row['cnf']),new.inspect(row['cnf'])
            self.assertEqual(a['profile'],b['profile'])
            self.assertFalse(a['summary']['closed'])
            self.assertEqual(b['summary']['closed'],bool(row['implied_subset_control']['recognized']))
            if b['summary']['closed']:
                exposed+=1;check_signed_tree(new,b['root']['key'])
        self.assertEqual(exposed,8);old.close();new.close()

    def test_initial_subset_exposure_keeps_priority(self):
        old=SignedSubsumptionInventory(max_depth=0)
        new=ImpliedSubsumptionInventory(max_depth=0)
        a,b=old.inspect(hidden_two_cnf()),new.inspect(hidden_two_cnf())
        oldnode,newnode=old._load(a['root']['key']),new._load(b['root']['key'])
        self.assertTrue(b['summary']['closed'])
        self.assertEqual(oldnode['subsumption'],newnode['subsumption'])
        self.assertNotIn('implied',newnode['subsumption']);check_signed_tree(new,b['root']['key'])
        old.close();new.close()

    def test_forged_implications_witnesses_and_origin_types(self):
        h=ImpliedSubsumptionInventory(max_depth=0);r=h.inspect(implication_source());key=r['root']['key']
        node=h._load(key);self.assertEqual(node['kind'],'subsumption')
        self.assertIn('implied',node['subsumption']);bads=[]
        bad=copy.deepcopy(node);bad['subsumption']['implied']['implications'][0]['clause'][0]*=-1;bads.append(bad)
        bad=copy.deepcopy(node);bad['subsumption']['implied']['implications'][0]['attempt']=999;bads.append(bad)
        bad=copy.deepcopy(node);bad['subsumption']['implied']['implications'][0]['unit']=False;bads.append(bad)
        bad=copy.deepcopy(node);bad['subsumption']['implied']['implications'].pop();bads.append(bad)
        bad=copy.deepcopy(node);bad['subsumption']['implied']['certificate']['removed'].pop();bads.append(bad)
        bad=copy.deepcopy(node);bad['edge']['names'].reverse();bads.append(bad)
        bad=copy.deepcopy(node);bad['subsumption'].pop('implied');bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):h._check(key,bad)
        h.close()

    def test_original_reasons_checked_before_implication_reuse(self):
        h=ImpliedSubsumptionInventory(max_depth=0);r=h.inspect(implication_source());key=r['root']['key']
        bad=copy.deepcopy(h._load(key))
        attempt=next(a for a in bad['profile']['probing']['attempts'] if a['certificate']['units'])
        attempt['certificate']['units'][0][1]=9999
        h.counts=Counter()
        with self.assertRaises(ValueError):h._check(key,bad)
        self.assertEqual(h.counts['implied_subset_unit_visits'],0);h.close()

    def test_signed_edits_random_fibers_and_tiny_inventory(self):
        h=ImpliedSubsumptionInventory(max_depth=1);rng=random.Random(202611091005)
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(1<<len(clauses)):
            r=h.inspect([c for i,c in enumerate(clauses) if mask>>i&1]);check_signed_tree(h,r['root']['key'])
        for source in [implication_source()]+[
            [tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(2,5)))
             for _ in range(rng.randrange(10,25))] for _ in range(40)]:
            names=sorted({abs(l) for c in source for l in c});shuffled=names[:];rng.shuffle(shuffled)
            mapping={v:(w*71+3)*rng.choice((-1,1)) for v,w in zip(names,shuffled)}
            variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source,variant,source[:-1],source+[(1,)],source+[(-1,2)]):
                r=h.inspect(changed);check_signed_tree(h,r['root']['key'])
            # Every emitted implication is true in every source model.
            cnf,_=normalize(source);profile=h._profile(cnf)
            implied=original_implications(cnf,profile['probing'].get('attempts',[]),Counter())
            for model in assignments(cnf):
                if holds(cnf,model):self.assertTrue(holds([i['clause'] for i in implied],model))
        h.close()
        with self.assertRaises(ValueError):ImpliedSubsumptionInventory(reuse_implications=1)

    def test_index_only_byte_identity_and_implied_cold_coexistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=SignedSubsumptionInventory(path,max_depth=0)
            for source in (implication_source(),hidden_two_cnf()):old.inspect(source)
            saved=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close();raw=path.read_bytes()
            indexed=ImpliedSubsumptionInventory(path,max_depth=0,reuse_implications=False)
            for source in (implication_source(),hidden_two_cnf()):
                r=indexed.inspect(source);self.assertEqual(r['metrics'].get('inserted_nodes',0),0)
            indexed.close();self.assertEqual(raw,path.read_bytes())
            h=ImpliedSubsumptionInventory(path,max_depth=0);r=h.inspect(implication_source());key=r['root']['key']
            for k,v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            bad=copy.deepcopy(h._load(key));h.close();raw=path.read_bytes()
            h=ImpliedSubsumptionInventory(path,max_depth=0)
            self.assertEqual(h.inspect(implication_source())['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            bad['edge']['key']=next(iter(saved));h=ImpliedSubsumptionInventory(path,max_depth=0)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
            h.close();h=ImpliedSubsumptionInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(implication_source())
            h.close()
