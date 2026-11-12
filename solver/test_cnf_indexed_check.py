from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_indexed_check import CheckedReconstruction, IndexedCheckInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import restriction_engine
from experiments.cnf_simplification import (check_simplification, reconstruct_simplification_scan,
                                            simplification_reconstruction)
from solver.test_cnf_single_pass_check import outcome
from solver.test_cnf_prepared_probes import hard_source


class IndexedCheckTests(unittest.TestCase):
    def test_exhaustive_ordered_sources_partial_assignments_and_fixed_points(self):
        lits = (-2, -1, 1, 2)
        clauses = [()] + [(v,) for v in lits] + list(itertools.product(lits, repeat=2))
        assignments = [{i+1:v for i,v in enumerate(values) if v is not None}
                       for values in itertools.product((None, False, True), repeat=2)]
        engine = CheckedReconstruction(256)
        for size in range(4):
            for cnf in itertools.product(clauses, repeat=size):
                for assigned in assignments:
                    for units in (False, True):
                        self.assertEqual(outcome(engine, cnf, assigned, units),
                                         outcome(reconstruct_simplification_scan, cnf, assigned, units))
                self.assertLessEqual(engine.state()['units'], 256)

    def test_untouched_identity_short_clauses_and_independent_discovery(self):
        cnf = ((1, -2, 3), (-1, 4, 7), (5, 6))
        engine = CheckedReconstruction(); counts = Counter()
        self.assertEqual(engine(cnf, {1:True}, counts, units=True), [(4,7), (5,6)])
        result = engine(cnf, {1:False}, counts, units=True)
        self.assertIs(result[-1], cnf[-1]); self.assertEqual(counts['indexed_check_hits'], 1)
        equal = tuple(tuple(list(c)) for c in cnf)
        engine(equal, {}, counts, units=True)
        self.assertEqual(counts['indexed_check_admissions'], 2)
        short = ((1,), (-1,2))
        # A source index is not a cached fixed-point verdict.
        engine(short, {}, counts, units=False)
        with self.assertRaises(ValueError): engine(short, {}, counts, units=True)
        def forbidden(*args, **kwargs): raise AssertionError('used discovery state')
        cert = dict(units=[[1,0],[2,1]], conflict=None, pure_rounds=[])
        with restriction_engine(forbidden), simplification_reconstruction(engine):
            self.assertEqual(check_simplification(short,cert,counts,pure=False),((),{1:True,2:True}))
            bad = copy.deepcopy(cert);bad['units'][1][1]=0
            with self.assertRaises(ValueError):check_simplification(short,bad,counts,pure=False)
        self.assertGreater(counts['indexed_check_hits'], 1)

    def test_edits_mutability_unusual_types_and_limits(self):
        class Int(int): pass
        class Tuple(tuple): pass
        engine=CheckedReconstruction(64); counts=Counter()
        mutable=[[1,2],[-1,3]]
        before=engine(mutable,{1:True},counts,units=False); mutable[0][0]=-1
        self.assertEqual(before,[(3,)])
        for cnf in (mutable, ((True,2),), ((0,2),), ((Int(1),2),),
                    (Tuple((1,2)),), Tuple(((1,2),)), (('x',2),)):
            for assigned in ({}, {1:True}, {1:1}, {True:False}, {-1:True}, {0:True}):
                for units in (False,True):
                    self.assertEqual(outcome(engine,cnf,assigned,units),
                                     outcome(reconstruct_simplification_scan,cnf,assigned,units))
        self.assertEqual(engine.state()['entries'],0)
        cnf=((1,2),(-1,3)); weight=1+len(cnf)+2*sum(map(len,cnf))+2*3
        for limit in (0,1,weight-1,weight):
            engine=CheckedReconstruction(limit);counts=Counter()
            for _ in range(2):engine(cnf,{},counts,units=True)
            self.assertEqual(counts['indexed_check_hits'],int(limit==weight))
            self.assertLessEqual(engine.state()['peak_units'],limit)
        engine=CheckedReconstruction(weight);counts=Counter()
        for source in (cnf,((2,3),(-2,4)),cnf):engine(source,{1:True},counts,units=False)
        self.assertEqual(counts['indexed_check_evictions'],2)
        engine.clear();self.assertEqual(engine.state()['units'],0)
        for bad in (-1,True,1.5,'5'):
            with self.assertRaises(ValueError):CheckedReconstruction(bad)
            with self.assertRaises(ValueError):IndexedCheckInventory(checked_reconstruction_units=bad)

    def test_random_edits_large_identifiers_and_order(self):
        rng=random.Random(202611121155);engine=CheckedReconstruction(2048)
        for _ in range(500):
            n=rng.randrange(1,20);base=1<<1024 if rng.randrange(5)==0 else 0
            cnf=tuple(tuple(rng.choice((-1,1))*(base+rng.randrange(1,n+1))
                            for _ in range(rng.randrange(6))) for _ in range(rng.randrange(40)))
            for _ in range(3):
                assigned={base+i:rng.choice((True,False)) for i in rng.sample(range(1,n+3),rng.randrange(n+2))}
                for units in (False,True):
                    self.assertEqual(outcome(engine,cnf,assigned,units),
                                     outcome(reconstruct_simplification_scan,cnf,assigned,units))
            edited=cnf+((base+1,),)
            for units in (False,True):
                self.assertEqual(outcome(engine,edited,assigned,units),
                                 outcome(reconstruct_simplification_scan,edited,assigned,units))

    def test_prepared_archives_match_cold_checks_share_only_source_state(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        sources=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(202611121156)
        sources += [[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3))
                     for _ in range(24)] for _ in range(30)] + [hard_source()]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots=[];profiles=[]
            for cls in (PreparedProbeInventory,IndexedCheckInventory):
                path=Path(tmp)/(cls.__name__+'.db');old=PolarityHornInventory(path,max_depth=1)
                for source in sources:old.inspect(source)
                old.close();h=cls(path,max_depth=1);current=[]
                for source in sources:
                    r=h.inspect(source);current.append((r['root'],r['profile'],r['summary']))
                profiles.append(encode(current));h.close();snapshots.append(path.read_bytes())
                h=cls(path,max_depth=1)
                for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
                    reader=h.prepared if json.loads(key)[1]==h.prepared.config else h
                    reader._load(key)
                for source in sources:
                    r=h.inspect(source);self.assertFalse(r['metrics'].get('inserted_nodes',0))
                if cls is IndexedCheckInventory:
                    self.assertIs(h._checked_reconstruction,h.prepared._checked_reconstruction)
                    self.assertGreater(h.reconstruction_state()['entries'],0)
                    self.assertLessEqual(h.reconstruction_state()['peak_units'],32768)
                h.close();self.assertEqual(path.read_bytes(),snapshots[-1])
                if cls is IndexedCheckInventory:self.assertEqual(h.reconstruction_state()['units'],0)
            self.assertEqual(*snapshots);self.assertEqual(*profiles)

    def test_saved_frontier_checks(self):
        rows=json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        a,b=PreparedProbeInventory(),IndexedCheckInventory()
        try:
            for row in rows:
                cnf=tuple(tuple(c) for c in row['cnf'])
                self.assertEqual(encode(a._check_probes(cnf,row['probing'])),
                                 encode(b._check_probes(cnf,row['probing'])))
        finally:a.close();b.close()


if __name__=='__main__':unittest.main()
