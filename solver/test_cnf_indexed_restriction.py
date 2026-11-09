from collections import Counter
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_indexed_restriction import IndexedRestriction
from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_ordered_propagation_inventory import OrderedPropagationInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, restrict, restrict_scan, restriction_engine
from solver.test_cnf_implied_subsumption import implication_source


class IndexedRestrictionTests(unittest.TestCase):
    def test_all_ordered_small_formulas_and_partial_assignments(self):
        literals=(-2,-1,1,2)
        clauses=[()]+[(a,) for a in literals]+list(itertools.product(literals,repeat=2))
        engine=IndexedRestriction(256)
        assignments=[{i+1:v for i,v in enumerate(values) if v is not None}
                     for values in itertools.product((None,False,True),repeat=2)]
        for size in range(4):
            for cnf in itertools.product(clauses,repeat=size):
                for assignment in assignments:
                    result=engine(cnf,assignment)
                    self.assertEqual(result,restrict_scan(cnf,assignment))
                    for a,b in itertools.product((False,True),repeat=2):
                        complete={1:a,2:b}
                        if all(complete[v]==value for v,value in assignment.items()):
                            self.assertEqual(holds(result,complete),holds(cnf,complete))
                    self.assertLessEqual(engine.state()['units'],256)

    def test_unchanged_clause_sharing_and_source_identity(self):
        cnf=((1,-2,3),(-1,4),(5,6),())
        engine=IndexedRestriction();counts=Counter()
        result=engine(cnf,{1:True},counts)
        self.assertEqual(result,((4,),(5,6),()))
        self.assertIs(result[1],cnf[2]);self.assertIs(result[2],cnf[3])
        engine(cnf,{1:False},counts)
        self.assertEqual(counts['indexed_restriction_hits'],1)
        equal=tuple(tuple(list(c)) for c in cnf)
        self.assertIsNot(equal,cnf)
        engine(equal,{1:True},counts)
        self.assertEqual(counts['indexed_restriction_admissions'],2)
        self.assertEqual(counts['indexed_restriction_hits'],1)
        changed=cnf+((-4,),)
        self.assertEqual(engine(changed,{1:True}),restrict_scan(changed,{1:True}))
        self.assertEqual(engine(cnf,{}),cnf)

    def test_mutable_inputs_and_unusual_types_cannot_inherit_identity(self):
        engine=IndexedRestriction();counts=Counter()
        cnf=[[1,-2],[3]]
        self.assertEqual(engine(cnf,{1:True},counts),((3,),))
        cnf[0][0]=-1
        self.assertEqual(engine(cnf,{1:True},counts),((-2,),(3,)))
        self.assertEqual(engine.state()['entries'],0)
        for cnf in (((True,2),),((0,2),),([1,2],)):
            self.assertEqual(engine(cnf,{1:True},counts),restrict_scan(cnf,{1:True}))
            self.assertEqual(engine.state()['entries'],0)
        class Int(int):pass
        class Tuple(tuple):pass
        for cnf in (((Int(1),2),),Tuple(((1,2),)),(Tuple((1,2)),)):
            self.assertEqual(engine(cnf,{1:True}),restrict_scan(cnf,{1:True}))
            self.assertEqual(engine.state()['entries'],0)
        cnf=((1,2),)
        for assignment in ({1:1},{True:False},{-1:True},{0:True}):
            self.assertEqual(engine(cnf,assignment),restrict_scan(cnf,assignment))
            self.assertEqual(engine.state()['entries'],0)

    def test_budget_oversize_eviction_and_close(self):
        cnf=((1,2),(-1,3));weight=1+len(cnf)+sum(map(len,cnf))
        for limit in (0,weight-1,weight):
            engine=IndexedRestriction(limit);counts=Counter()
            for _ in range(2):self.assertEqual(engine(cnf,{1:True},counts),restrict_scan(cnf,{1:True}))
            self.assertEqual(counts['indexed_restriction_hits'],int(limit==weight))
            self.assertLessEqual(engine.state()['peak_units'],limit)
        engine=IndexedRestriction(weight);counts=Counter()
        for source in (cnf,((2,3),(-2,4)),cnf):engine(source,{1:True},counts)
        self.assertEqual(counts['indexed_restriction_evictions'],2)
        self.assertEqual(counts['indexed_restriction_hits'],0)
        engine.clear();self.assertEqual(engine.state()['entries'],0)
        for bad in (-1,True,1.5,'5'):
            with self.assertRaises(ValueError):IndexedRestriction(bad)
            with self.assertRaises(ValueError):IndexedRestrictionInventory(restriction_units=bad)

    def test_random_edits_sparse_and_large_identifiers(self):
        rng=random.Random(202611091310);engine=IndexedRestriction(2048)
        for _ in range(1000):
            n=rng.randrange(1,20)
            base=1<<1024 if rng.randrange(5)==0 else 0
            cnf=tuple(tuple(rng.choice((-1,1))*(base+rng.randrange(1,n+1))
                            for _ in range(rng.randrange(6))) for _ in range(rng.randrange(40)))
            for _ in range(3):
                assignment={base+i:rng.choice((True,False)) for i in rng.sample(range(1,n+3),rng.randrange(n+2))}
                self.assertEqual(engine(cnf,assignment),restrict_scan(cnf,assignment))
            cnf=cnf+((base+1,),)
            self.assertEqual(engine(cnf,assignment),restrict_scan(cnf,assignment))

    def test_scope_restoration_and_independent_reconstruction(self):
        cnf=((1,2),(-1,3));counts=Counter();engine=IndexedRestriction()
        with self.assertRaises(RuntimeError):
            with restriction_engine(engine):
                self.assertEqual(restrict(cnf,{1:True},counts),((3,),))
                with restriction_engine(None):restrict(cnf,{1:True},counts)
                restrict(cnf,{1:False},counts)
                raise RuntimeError('restore')
        self.assertEqual(counts['indexed_restriction_calls'],2)
        restrict(cnf,{1:True},counts)
        self.assertEqual(counts['indexed_restriction_calls'],2)
        self.assertGreater(counts['restriction_literal_visits'],0)
        from experiments.cnf_simplification import check_simplification
        def forbidden(*args):raise AssertionError('checker used indexed restriction')
        with restriction_engine(forbidden):
            result=check_simplification(((1,),(-1,2)),
                dict(units=[[1,0],[2,1]],conflict=None,pure_rounds=[]),Counter(),pure=False)
        self.assertEqual(result,((),{1:True,2:True}))

    def test_archive_byte_identity_and_cold_replay(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        cases=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(202611091311)
        cases += [implication_source()]+[[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3))
                                         for _ in range(24)] for _ in range(20)]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots=[]
            for cls in (OrderedPropagationInventory,IndexedRestrictionInventory):
                path=Path(tmp)/(cls.__name__+'.db');h=cls(path,max_depth=1)
                for source in cases:h.inspect(source)
                h.close();snapshots.append(path.read_bytes())
            self.assertEqual(*snapshots)
            path=Path(tmp)/'OrderedPropagationInventory.db';h=IndexedRestrictionInventory(path,max_depth=1)
            self.assertEqual(h.restriction_state()['entries'],0)
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):h._load(key)
            self.assertGreater(h.counts['indexed_restriction_calls'],0)
            for source in cases:
                r=h.inspect(source);self.assertEqual(r['metrics'].get('inserted_nodes',0),0)
                self.assertEqual(r['metrics']['inserted_sources'],0)
            h.close();self.assertEqual(h.restriction_state()['entries'],0)
            self.assertEqual(path.read_bytes(),snapshots[0])

    def test_saved_frontier_checks_and_source_edits(self):
        rows=json.loads(Path('experiments/results/cnf-implied-subsumption/mechanisms.json').read_text())['frontier']
        old=OrderedPropagationInventory();new=IndexedRestrictionInventory(restriction_units=2048)
        for row in rows:
            cnf=tuple(tuple(c) for c in row['cnf']);proof=row['probing']
            self.assertEqual(encode(old._check_probes(cnf,proof)),encode(new._check_probes(cnf,proof)))
            self.assertEqual(encode(old._discover_probes(cnf)),encode(new._discover_probes(cnf)))
        old.close();new.close()
