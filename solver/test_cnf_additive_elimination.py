from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_additive_elimination import (
    AdditiveEliminationInventory, discover_additive_elimination,
    check_additive_elimination, lift_additive_elimination)
from experiments.cnf_clause_bound_elimination import ClauseBoundEliminationInventory, check_clause_elimination
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds, ResidualSolver


def projection(test, source, variable, growth=1):
    proof=dict(variable=variable)
    try: target=check_additive_elimination(source,proof,Counter(),clause_growth_limit=growth)
    except ValueError: return False
    support={abs(l) for c in source for l in c}; rest=sorted(support-{variable})
    test.assertLessEqual(len(target),len(source)+growth)
    test.assertLess({abs(l) for c in target for l in c},support)
    test.assertLessEqual(sum(map(len,target)),(len(source)+growth)*(len(support)-1))
    for values in itertools.product((False,True),repeat=len(rest)):
        model=dict(zip(rest,values)); expected=any(holds(source,model|{variable:b}) for b in (False,True))
        test.assertEqual(holds(target,model),expected,(source,variable,model))
        if expected:
            lifted=lift_additive_elimination(source,proof,model,Counter(),clause_growth_limit=growth)
            test.assertTrue(holds(source,lifted))
            for v in {abs(l) for c in target for l in c}: test.assertEqual(lifted[v],model[v])
    return True


class AdditiveEliminationTests(unittest.TestCase):
    def test_exhaustive_projection_and_lift(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        accepted=0
        for mask in range(512):
            source=tuple(c for i,c in enumerate(clauses) if mask>>i&1)
            for growth in (0,1,2):
                for v in {abs(l) for c in source for l in c}: accepted+=projection(self,source,v,growth)
                p=discover_additive_elimination(source,Counter(),clause_growth_limit=growth)
                if p['variable'] is not None: self.assertTrue(projection(self,source,p['variable'],growth))
        self.assertGreater(accepted,2700)

    def test_random_edits_signed_large_identifiers(self):
        rng=random.Random(202611121844)
        for _ in range(120):
            cnf,_=normalize([tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(1,5)))
                             for _ in range(rng.randrange(1,20))])
            names={v:((1<<130)+v*64)*rng.choice((-1,1)) for v in range(1,7)}
            cnf=tuple(tuple(names[abs(l)]*(1 if l>0 else -1) for l in c) for c in cnf)
            for v in {abs(l) for c in cnf for l in c}: projection(self,cnf,v)
            edited=tuple(dict.fromkeys(cnf+((abs(names[1]),),)))
            p=discover_additive_elimination(edited,Counter())
            if p['variable'] is not None: self.assertTrue(projection(self,edited,p['variable']))

    def test_fixed_clause_growth_and_chain_bound(self):
        for negative_count,growth in ((3,1),(4,2)):
            cnf=((1,2),(1,3))+tuple((-1,v) for v in range(4,4+negative_count)); p=dict(variable=1)
            with self.assertRaises(ValueError): check_clause_elimination(cnf,p,Counter())
            target=check_additive_elimination(cnf,p,Counter(),clause_growth_limit=growth)
            self.assertEqual(len(target)-len(cnf),growth)
            self.assertTrue(projection(self,cnf,1,growth))
            with self.assertRaises(ValueError): check_additive_elimination(cnf,p,Counter(),clause_growth_limit=growth-1)
            with self.assertRaises(ValueError): check_additive_elimination(cnf,p,Counter(),pair_limit=2*negative_count-1,clause_growth_limit=growth)
            with patch('experiments.cnf_additive_elimination.discover_additive_elimination',side_effect=AssertionError('discovery')):
                self.assertEqual(check_additive_elimination(cnf,p,Counter(),clause_growth_limit=growth),target)
            current=target; steps=1; n0=len({abs(l) for c in cnf for l in c}); m0=len(cnf)
            payload=sum(map(len,cnf))+sum(map(len,current))
            while current:
                p=discover_additive_elimination(current,Counter(),clause_growth_limit=growth)
                if p['variable'] is None: break
                current=check_additive_elimination(current,p,Counter(),clause_growth_limit=growth); steps+=1
                self.assertLessEqual(len(current),m0+growth*steps)
                self.assertLessEqual(sum(map(len,current)),(m0+growth*steps)*(n0-steps))
                payload+=sum(map(len,current))
            self.assertLessEqual(steps,n0)
            self.assertLessEqual(payload,(n0+1)*(m0+growth*n0)*n0)
        over=((1,2),(1,3),(1,4),(-1,5),(-1,6),(-1,7))
        with self.assertRaises(ValueError): check_additive_elimination(over,dict(variable=1),Counter(),clause_growth_limit=2)

    def test_invalid_sources_certificates_limits_and_models(self):
        cnf=((1,2),(-1,3))
        for p in ({},{'variable':True},{'variable':0},{'variable':-1},{'variable':'1'},{'variable':7},{'variable':1,'target':[]}):
            with self.assertRaises(ValueError): check_additive_elimination(cnf,p,Counter())
        for bad in (((0,),),((True,),),((1,1),),((1,-1),),((1,),(1,))):
            with self.assertRaises(ValueError): check_additive_elimination(bad,dict(variable=None),Counter())
        for limit in (-1,True,1.2):
            with self.assertRaises(ValueError): discover_additive_elimination(cnf,Counter(),candidate_limit=limit)
            with self.assertRaises(ValueError): AdditiveEliminationInventory(elimination_pair_limit=limit)
            with self.assertRaises(ValueError): AdditiveEliminationInventory(clause_growth_limit=limit)
            with self.assertRaises(ValueError): discover_additive_elimination(cnf,Counter(),clause_growth_limit=limit)
            with self.assertRaises(ValueError): check_additive_elimination(cnf,dict(variable=None),Counter(),clause_growth_limit=limit)
        self.assertEqual(discover_additive_elimination(cnf,Counter(),candidate_limit=0),dict(variable=None))
        for model in ({},{2:False,3:False},{2:1,3:True},{2:True,3:True,-1:False}):
            with self.assertRaises(ValueError): lift_additive_elimination(cnf,dict(variable=1),model,Counter())

    def test_saved_opportunities_restart_model_lifts_and_corruption(self):
        report=json.loads(Path('experiments/results/cnf-clause-bound-elimination-originals/report.json').read_text())
        leaves=next(r for r in report['results'] if r['mode']=='clause_bound')['frontier']
        diagnostic=json.loads(Path('experiments/results/cnf-clause-bound-elimination-originals/growth-barriers.json').read_text())
        rows=next(r for r in diagnostic['reports'] if r['suite']=='originals')['leaves']
        eligible={r['key_sha256'] for r in rows if r['min_clause_delta'] is not None and r['min_clause_delta']<=2}
        cases=[r['cnf'] for r in leaves if r['key_sha256'] in eligible]
        self.assertEqual(len(cases),50); one=0
        for cnf in cases:
            p1=discover_additive_elimination(cnf,Counter(),clause_growth_limit=1)
            p2=discover_additive_elimination(cnf,Counter(),clause_growth_limit=2)
            self.assertIsNotNone(p2['variable'])
            if p1['variable'] is not None:
                one+=1; self.assertEqual(p1,p2)
            target=check_additive_elimination(cnf,p2,Counter(),clause_growth_limit=2)
            self.assertLessEqual(len(target),len(cnf)+2)
        self.assertEqual(one,32)
        cases=cases[:6]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db'; old=ClauseBoundEliminationInventory(path,max_depth=0)
            for cnf in cases: old.inspect(cnf)
            before={t:old.db.execute(f'SELECT id,payload FROM {t}').fetchall() for t in ('cnf_patterns_v1','cnf_pattern_sources_v1')}
            old.close(); h=AdditiveEliminationInventory(path,max_depth=0,clause_growth_limit=2); solver=ResidualSolver()
            for cnf in cases: h.inspect(cnf)
            nodes=[(k,json.loads(p)) for k,p in h.db.execute('SELECT id,payload FROM cnf_patterns_v1')
                   if json.loads(p).get('additive_elimination',{}).get('variable') is not None]
            self.assertGreaterEqual(len(nodes),6)
            for k,n in nodes:
                child=h._load(n['edge']['key']); a,b=solver.solve(n['cnf']),solver.solve(child['cnf'])
                self.assertEqual(a['answer'],b['answer'])
                if b['answer']: self.assertTrue(holds(n['cnf'],h.lift(k,b['model'])))
            for table,rows in before.items():
                for k,p in rows:self.assertEqual(h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(k,)).fetchone(),(p,))
            h.close();solver.close();snapshot=path.read_bytes();h=AdditiveEliminationInventory(path,max_depth=0,clause_growth_limit=2)
            with patch('experiments.cnf_additive_elimination.discover_additive_elimination',side_effect=AssertionError('cold discovery')):
                for cnf in cases:self.assertFalse(h.inspect(cnf)['metrics'].get('inserted_nodes',0))
                for k,_ in nodes:h._load(k)
            h.close();self.assertEqual(path.read_bytes(),snapshot)
            k,n=nodes[0]
            for mode in ('pivot','edge','summary','fallback'):
                bad=copy.deepcopy(n)
                if mode=='pivot':bad['additive_elimination']['variable']=100000
                elif mode=='edge':bad['edge']['names']=[]
                elif mode=='summary':bad['summary']['unresolved_literals']+=1
                else:bad['clause_elimination']['variable']=bad['additive_elimination']['variable']
                h=AdditiveEliminationInventory(path,max_depth=0,clause_growth_limit=2)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),k))
                with self.assertRaises(ValueError):h._load(k)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(n),k))
                h.close()


if __name__=='__main__':unittest.main()
