from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_clause_bound_elimination import (
    ClauseBoundEliminationInventory, discover_clause_elimination,
    check_clause_elimination, lift_clause_elimination)
from experiments.cnf_variable_elimination import VariableEliminationInventory, check_elimination
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds, ResidualSolver


def projection(test, source, variable):
    proof=dict(variable=variable)
    try: target=check_clause_elimination(source,proof,Counter())
    except ValueError: return False
    support={abs(l) for c in source for l in c}; rest=sorted(support-{variable})
    test.assertLessEqual(len(target),len(source))
    test.assertLess({abs(l) for c in target for l in c},support)
    test.assertLessEqual(sum(map(len,target)),len(source)*(len(support)-1))
    for values in itertools.product((False,True),repeat=len(rest)):
        model=dict(zip(rest,values)); expected=any(holds(source,model|{variable:b}) for b in (False,True))
        test.assertEqual(holds(target,model),expected,(source,variable,model))
        if expected:
            lifted=lift_clause_elimination(source,proof,model,Counter())
            test.assertTrue(holds(source,lifted))
            for v in {abs(l) for c in target for l in c}: test.assertEqual(lifted[v],model[v])
    return True


class ClauseBoundEliminationTests(unittest.TestCase):
    def test_exhaustive_projection_and_lift(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=2)]
        accepted=0
        for mask in range(512):
            source=tuple(c for i,c in enumerate(clauses) if mask>>i&1)
            for v in {abs(l) for c in source for l in c}: accepted+=projection(self,source,v)
            p=discover_clause_elimination(source,Counter())
            if p['variable'] is not None: self.assertTrue(projection(self,source,p['variable']))
        self.assertGreater(accepted,900)

    def test_random_edits_signed_large_identifiers(self):
        rng=random.Random(202611121542)
        for _ in range(180):
            cnf,_=normalize([tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(1,5)))
                             for _ in range(rng.randrange(1,20))])
            names={v:((1<<130)+v*64)*rng.choice((-1,1)) for v in range(1,7)}
            cnf=tuple(tuple(names[abs(l)]*(1 if l>0 else -1) for l in c) for c in cnf)
            for v in {abs(l) for c in cnf for l in c}: projection(self,cnf,v)
            edited=tuple(dict.fromkeys(cnf+((abs(names[1]),),)))
            p=discover_clause_elimination(edited,Counter())
            if p['variable'] is not None: self.assertTrue(projection(self,edited,p['variable']))

    def test_literal_growth_is_allowed_but_clause_growth_is_not(self):
        cnf=((1,2,3),(1,4,5),(-1,6,7),(-1,8,9)); p=dict(variable=1)
        with self.assertRaises(ValueError): check_elimination(cnf,p,Counter())
        target=check_clause_elimination(cnf,p,Counter())
        self.assertEqual((len(target),sum(map(len,target))),(4,16))
        self.assertTrue(projection(self,cnf,1))
        with self.assertRaises(ValueError): check_clause_elimination(cnf,p,Counter(),pair_limit=3)
        grows=((1,2),(1,3),(1,4),(-1,5),(-1,6),(-1,7))
        with self.assertRaises(ValueError): check_clause_elimination(grows,p,Counter())
        with patch('experiments.cnf_clause_bound_elimination.discover_clause_elimination',side_effect=AssertionError('discovery')):
            self.assertEqual(check_clause_elimination(cnf,p,Counter()),target)
        # A multi-step admitted chain has decreasing support and bounded CNF size.
        current=cnf; steps=0; original_n=9; original_m=4
        while current:
            p=discover_clause_elimination(current,Counter())
            if p['variable'] is None: break
            current=check_clause_elimination(current,p,Counter()); steps+=1
            self.assertLessEqual(sum(map(len,current)),original_m*(original_n-steps))
        self.assertLessEqual(steps,original_n)

    def test_invalid_sources_certificates_limits_and_models(self):
        cnf=((1,2),(-1,3))
        for p in ({},{'variable':True},{'variable':0},{'variable':-1},{'variable':'1'},{'variable':7},{'variable':1,'target':[]}):
            with self.assertRaises(ValueError): check_clause_elimination(cnf,p,Counter())
        for bad in (((0,),),((True,),),((1,1),),((1,-1),),((1,),(1,))):
            with self.assertRaises(ValueError): check_clause_elimination(bad,dict(variable=None),Counter())
        for limit in (-1,True,1.2):
            with self.assertRaises(ValueError): discover_clause_elimination(cnf,Counter(),candidate_limit=limit)
            with self.assertRaises(ValueError): ClauseBoundEliminationInventory(elimination_pair_limit=limit)
        self.assertEqual(discover_clause_elimination(cnf,Counter(),candidate_limit=0),dict(variable=None))
        for model in ({},{2:False,3:False},{2:1,3:True},{2:True,3:True,-1:False}):
            with self.assertRaises(ValueError): lift_clause_elimination(cnf,dict(variable=1),model,Counter())

    def test_saved_opportunities_restart_model_lifts_and_corruption(self):
        report=json.loads(Path('experiments/results/cnf-subsumed-elimination-originals/report.json').read_text())
        leaves=next(r for r in report['results'] if r['mode']=='subsumed')['frontier']
        diagnostic=json.loads(Path('experiments/results/cnf-subsumed-elimination-originals/growth-opportunity.json').read_text())
        rows=next(r for r in diagnostic['reports'] if r['suite']=='originals')['leaves']
        eligible={r['key_sha256'] for r in rows if r['min_extra_literals_without_subsumption'] is not None}
        cases=[r['cnf'] for r in leaves if r['key_sha256'] in eligible]
        self.assertEqual(len(cases),48)
        for cnf in cases:
            proof=discover_clause_elimination(cnf,Counter()); self.assertIsNotNone(proof['variable'])
            target=check_clause_elimination(cnf,proof,Counter()); self.assertLessEqual(len(target),len(cnf))
        cases=cases[:6]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db'; old=VariableEliminationInventory(path,max_depth=0)
            for cnf in cases: old.inspect(cnf)
            before={t:old.db.execute(f'SELECT id,payload FROM {t}').fetchall() for t in ('cnf_patterns_v1','cnf_pattern_sources_v1')}
            old.close(); h=ClauseBoundEliminationInventory(path,max_depth=0); solver=ResidualSolver()
            for cnf in cases: h.inspect(cnf)
            nodes=[(k,json.loads(p)) for k,p in h.db.execute('SELECT id,payload FROM cnf_patterns_v1')
                   if json.loads(p).get('clause_elimination',{}).get('variable') is not None]
            self.assertGreaterEqual(len(nodes),6)
            for k,n in nodes:
                child=h._load(n['edge']['key']); a,b=solver.solve(n['cnf']),solver.solve(child['cnf'])
                self.assertEqual(a['answer'],b['answer'])
                if b['answer']: self.assertTrue(holds(n['cnf'],h.lift(k,b['model'])))
            for table,rows in before.items():
                for k,p in rows:self.assertEqual(h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(k,)).fetchone(),(p,))
            h.close();solver.close();snapshot=path.read_bytes();h=ClauseBoundEliminationInventory(path,max_depth=0)
            with patch('experiments.cnf_clause_bound_elimination.discover_clause_elimination',side_effect=AssertionError('cold discovery')):
                for cnf in cases:self.assertFalse(h.inspect(cnf)['metrics'].get('inserted_nodes',0))
                for k,_ in nodes:h._load(k)
            h.close();self.assertEqual(path.read_bytes(),snapshot)
            k,n=nodes[0]
            for mode in ('pivot','edge','summary','fallback'):
                bad=copy.deepcopy(n)
                if mode=='pivot':bad['clause_elimination']['variable']=100000
                elif mode=='edge':bad['edge']['names']=[]
                elif mode=='summary':bad['summary']['unresolved_literals']+=1
                else:bad['elimination']['variable']=bad['clause_elimination']['variable']
                h=ClauseBoundEliminationInventory(path,max_depth=0)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),k))
                with self.assertRaises(ValueError):h._load(k)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(n),k))
                h.close()


if __name__=='__main__':unittest.main()
