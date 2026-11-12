from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_clause_mask import ClauseMaskReconstruction, ClauseMaskInventory
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import restriction_engine
from experiments.cnf_simplification import check_simplification, reconstruct_simplification_scan, simplification_reconstruction
from solver.test_cnf_single_pass_check import outcome
from solver.test_cnf_prepared_probes import hard_source


class ClauseMaskTests(unittest.TestCase):
    def test_exhaustive_reconstruction_and_fixed_point_rejection(self):
        lits=(-2,-1,1,2);clauses=[()]+[(v,) for v in lits]+list(itertools.product(lits,repeat=2))
        assignments=[{i+1:v for i,v in enumerate(values) if v is not None}
                     for values in itertools.product((None,False,True),repeat=2)]
        engine=ClauseMaskReconstruction(256)
        for size in range(4):
            for cnf in itertools.product(clauses,repeat=size):
                for assigned in assignments:
                    for units in (False,True):
                        self.assertEqual(outcome(engine,cnf,assigned,units),
                                         outcome(reconstruct_simplification_scan,cnf,assigned,units))
                self.assertLessEqual(engine.state()['units'],256)

    def test_collisions_huge_ids_and_no_cached_verdict(self):
        engine=ClauseMaskReconstruction();counts=Counter();clause=(65,-66)
        self.assertEqual(engine((clause,),{1:True,2:False},counts,units=True),[clause])
        self.assertEqual(counts['clause_mask_false_positives'],1)
        self.assertEqual(engine((clause,),{65:False},counts,units=False),[(-66,)])
        with self.assertRaises(ValueError):engine((clause,),{65:False},counts,units=True)
        self.assertEqual(engine((clause,),{65:True},counts,units=True),[])
        huge=1<<2048
        for cnf in (((huge+1,-huge-2),(huge+65,huge+66)),((1,),()),((0,65),)):
            for assigned in ({},{huge+1:True},{1:False},{65:True}):
                for units in (False,True):
                    self.assertEqual(outcome(engine,cnf,assigned,units),
                                     outcome(reconstruct_simplification_scan,cnf,assigned,units))
        def forbidden(*args,**kwargs):raise AssertionError('discovery state used')
        source=((1,),(-1,2));cert=dict(units=[[1,0],[2,1]],conflict=None,pure_rounds=[])
        with restriction_engine(forbidden),simplification_reconstruction(engine):
            self.assertEqual(check_simplification(source,cert,counts,pure=False),((),{1:True,2:True}))
            bad=copy.deepcopy(cert);bad['units'][1][1]=0
            with self.assertRaises(ValueError):check_simplification(source,bad,counts,pure=False)

    def test_identity_mutability_types_and_fifo_budget(self):
        engine=ClauseMaskReconstruction(256);counts=Counter();clause=(1,2,3)
        first=engine((clause,),{},counts,units=True);self.assertIs(first[0],clause)
        engine((clause,),{10:True},counts,units=True);self.assertEqual(counts['clause_mask_hits'],1)
        new=tuple(list(clause));engine((new,),{},counts,units=True)
        self.assertEqual(counts['clause_mask_admissions'],2)
        mutable=[[1,2],[-1,3]];engine(mutable,{1:True},counts,units=False);mutable[0][0]=-1
        self.assertEqual(engine(mutable,{1:True},counts,units=False),[(2,),(3,)])
        class Int(int):pass
        class Tuple(tuple):pass
        for cnf in (((True,2),),((0,2),),((Int(1),2),),(Tuple((1,2)),),(('x',2),)):
            for assigned in ({},{1:True},{1:1},{True:False},{-1:True},{0:True}):
                for units in (False,True):
                    self.assertEqual(outcome(engine,cnf,assigned,units),
                                     outcome(reconstruct_simplification_scan,cnf,assigned,units))
        for limit in (0,1,5,6):
            small=ClauseMaskReconstruction(limit);c=Counter()
            for _ in range(2):small((clause,),{},c,units=True)
            self.assertEqual(c['clause_mask_hits'],int(limit==6))
            self.assertLessEqual(small.state()['peak_units'],limit)
        small=ClauseMaskReconstruction(6);c=Counter()
        for clause in ((1,2,3),(2,3,4),(1,2,3)):small((clause,),{},c,units=True)
        self.assertEqual(c['clause_mask_evictions'],2);small.clear();self.assertEqual(small.state()['units'],0)
        for bad in (-1,True,1.5,'5'):
            with self.assertRaises(ValueError):ClauseMaskReconstruction(bad)
            with self.assertRaises(ValueError):ClauseMaskInventory(clause_mask_units=bad)

    def test_random_mutations_and_colliding_identifiers(self):
        rng=random.Random(202611121300);engine=ClauseMaskReconstruction(2048)
        for _ in range(500):
            names=[64*rng.randrange(10)+i for i in range(1,rng.randrange(2,20))]
            cnf=tuple(tuple(rng.choice((-1,1))*rng.choice(names) for _ in range(rng.randrange(6)))
                      for _ in range(rng.randrange(40)))
            for _ in range(3):
                assigned={v:rng.choice((True,False)) for v in rng.sample(names,rng.randrange(len(names)+1))}
                for units in (False,True):
                    self.assertEqual(outcome(engine,cnf,assigned,units),
                                     outcome(reconstruct_simplification_scan,cnf,assigned,units))
            edited=cnf+((names[0],),)
            for units in (False,True):
                self.assertEqual(outcome(engine,edited,assigned,units),
                                 outcome(reconstruct_simplification_scan,edited,assigned,units))

    def test_integrated_archive_identity_cold_replay_and_corruption(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        cases=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(202611121301)
        cases += [[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3)) for _ in range(24)] for _ in range(20)]+[hard_source()]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots=[];results=[]
            for cls in (PreparedProbeInventory,ClauseMaskInventory):
                path=Path(tmp)/cls.__name__;old=PolarityHornInventory(path,max_depth=1)
                for source in cases:old.inspect(source)
                old.close();h=cls(path,max_depth=1);current=[]
                for source in cases:
                    r=h.inspect(source);current.append((r['root'],r['profile'],r['summary']))
                results.append(encode(current));h.close();snapshots.append(path.read_bytes())
                h=cls(path,max_depth=1)
                for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
                    reader=h.prepared if json.loads(key)[1]==h.prepared.config else h
                    reader._load(key)
                for source in cases:
                    r=h.inspect(source);self.assertFalse(r['metrics'].get('inserted_nodes',0))
                if cls is ClauseMaskInventory:
                    self.assertIs(h._checked_reconstruction,h.prepared._checked_reconstruction)
                    self.assertLessEqual(h.reconstruction_state()['peak_units'],32768)
                h.close();self.assertEqual(path.read_bytes(),snapshots[-1])
            self.assertEqual(*snapshots);self.assertEqual(*results)
            # Persisted nodes still need their exact source binding checked cold.
            path=Path(tmp)/'ClauseMaskInventory';h=ClauseMaskInventory(path,max_depth=1)
            key=h.inspect(hard_source())['root']['key'];node=copy.deepcopy(h._load(key));h.close()
            node['cnf']=[]
            h=ClauseMaskInventory(path,max_depth=1)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=ClauseMaskInventory(path,max_depth=1)
            with self.assertRaises(ValueError):h.inspect(hard_source())
            h.close()

    def test_saved_frontier_proofs(self):
        rows=json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        a,b=PreparedProbeInventory(),ClauseMaskInventory()
        try:
            for row in rows:
                cnf=tuple(tuple(c) for c in row['cnf'])
                self.assertEqual(encode(a._check_probes(cnf,row['probing'])),encode(b._check_probes(cnf,row['probing'])))
        finally:a.close();b.close()


if __name__=='__main__':unittest.main()
