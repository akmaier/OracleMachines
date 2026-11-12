from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_subsumed_elimination import (
    SubsumedEliminationInventory, discover_subsumed, check_subsumed, lift_subsumed)
from experiments.cnf_variable_elimination import VariableEliminationInventory, check_elimination
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize, ResidualSolver


def all_models(variables):
    return (dict(zip(variables, bits)) for bits in itertools.product((False, True), repeat=len(variables)))


def naive_certificate(cnf, x):
    omissions = []
    for a, p in enumerate(cnf):
        if x not in p: continue
        for b, n in enumerate(cnf):
            if -x not in n: continue
            c = (set(p)-{x}) | (set(n)-{-x})
            if any(-l in c for l in c): continue
            for i, r in enumerate(cnf):
                if x not in r and -x not in r and set(r) <= c:
                    omissions.append([a,b,i]); break
    return dict(variable=x, omissions=omissions)


def check_projection(test, cnf, proof):
    try: target = check_subsumed(cnf, proof, Counter())
    except ValueError: return 0
    x = proof['variable']; variables = sorted({abs(l) for c in cnf for l in c} - {x})
    for m in all_models(variables):
        expected = any(holds(cnf, m | {x:b}) for b in (False, True))
        test.assertEqual(holds(target, m), expected, (cnf, proof, m))
        if expected:
            lifted = lift_subsumed(cnf, proof, m, Counter()); test.assertTrue(holds(cnf, lifted))
            for v in {abs(l) for c in target for l in c}: test.assertEqual(lifted[v], m[v])
    return 1


class SubsumedEliminationTests(unittest.TestCase):
    def test_exhaustive_projection_and_model_restoration(self):
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1,0,1), repeat=2)]
        accepted = 0; omissions = 0
        for mask in range(512):
            cnf = tuple(c for i,c in enumerate(clauses) if mask >> i & 1)
            for x in {abs(l) for c in cnf for l in c}:
                proof = naive_certificate(cnf,x); omissions += len(proof['omissions'])
                accepted += check_projection(self,cnf,proof)
            proof = discover_subsumed(cnf,Counter())
            if proof['variable'] is not None: self.assertTrue(check_projection(self,cnf,proof))
        self.assertGreater(accepted,900); self.assertGreater(omissions,100)

    def test_random_signed_renamings_edits_and_all_pivots(self):
        rng = random.Random(202611121440)
        for _ in range(160):
            cnf,_ = normalize([tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(1,5)))
                               for _ in range(rng.randrange(1,20))])
            names = {v: ((1<<130)+64*v)*rng.choice((-1,1)) for v in range(1,7)}
            cnf = tuple(tuple(names[abs(l)]*(1 if l>0 else -1) for l in c) for c in cnf)
            for x in {abs(l) for c in cnf for l in c}: check_projection(self,cnf,naive_certificate(cnf,x))
            edited = tuple(dict.fromkeys(cnf+((abs(names[1]),),)))
            p = discover_subsumed(edited,Counter())
            if p['variable'] is not None: self.assertTrue(check_projection(self,edited,p))

    def test_growth_rescue_anchored_search_and_independent_check(self):
        cnf = ((1,2,3),(1,4,5),(-1,6,7),(-1,8,9),(2,6),(4,8))
        p = dict(variable=1, omissions=[[0,2,4],[1,3,5]])
        with self.assertRaises(ValueError): check_elimination(cnf,dict(variable=1),Counter())
        self.assertTrue(check_projection(self,cnf,p))
        with patch('experiments.cnf_subsumed_elimination.discover_subsumed',side_effect=AssertionError('discovery')):
            self.assertEqual(check_subsumed(cnf,p,Counter()), ((2,3,8,9),(2,6),(4,5,6,7),(4,8)))
        # A retained subclause may start at any resolvent literal, not just its minimum.
        cnf = ((1,2,3),(-1,4,5),(3,5))
        self.assertTrue(check_projection(self,cnf,dict(variable=1,omissions=[[0,1,2]])))

    def test_reject_invalid_reasons_limits_and_models(self):
        cnf = ((1,2,3),(1,4,5),(-1,6,7),(-1,8,9),(2,6),(4,8))
        p = dict(variable=1, omissions=[[0,2,4],[1,3,5]])
        for reason in ([[0,2,0]], [[0,2,5]], [[0,2,99]], [[2,0,4]], [[0,2,4],[0,2,4]], [[True,2,4]], [[0,2,-1]]):
            with self.assertRaises(ValueError): check_subsumed(cnf,dict(variable=1,omissions=reason),Counter())
        for proof in ({},dict(variable=True,omissions=[]),dict(variable=None,omissions=[[0,2,4]]),
                      dict(variable=1,omissions=()), dict(variable=1,omissions=[],extra=0)):
            with self.assertRaises(ValueError): check_subsumed(cnf,proof,Counter())
        with self.assertRaises(ValueError): check_subsumed(cnf,p,Counter(),pair_limit=3)
        with self.assertRaises(ValueError): check_subsumed(((1,2),(-1,-2),(2,)),dict(variable=1,omissions=[[0,1,2]]),Counter())
        for limit in (-1,True,'1'):
            with self.assertRaises(ValueError): discover_subsumed(cnf,Counter(),candidate_limit=limit)
        self.assertEqual(discover_subsumed(cnf,Counter(),candidate_limit=0),dict(variable=None,omissions=[]))
        for m in ({},{2:True},{2:1,3:True,4:True,5:True,6:True,7:True,8:True,9:True}):
            with self.assertRaises(ValueError): lift_subsumed(cnf,p,m,Counter())
        # A removed pivot clause cannot justify its own omitted resolvent.
        tiny=((1,2),(-1,3)); fake=dict(variable=1,omissions=[[0,1,0]])
        with self.assertRaises(ValueError): check_subsumed(tiny,fake,Counter())

    def test_saved_growth_barriers_persistence_lifts_and_corruption(self):
        report=json.loads(Path('experiments/results/cnf-variable-elimination-originals/report.json').read_text())
        leaves=next(r for r in report['results'] if r['mode']=='bounded')['frontier']
        analysis=json.loads(Path('experiments/results/cnf-variable-elimination-probe/structure-reuse.json').read_text())
        row=next(r for r in analysis['rows'] if r['suite']=='originals' and r['mode']=='bounded')
        eligible={r['key_sha256'] for r in row['opportunities'] if r['subsumption_non_growing']}
        cases=[l['cnf'] for l in leaves if l['key_sha256'] in eligible]
        self.assertEqual(len(cases),10)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'a.db'; old=VariableEliminationInventory(path,max_depth=0)
            for cnf in cases: old.inspect(cnf)
            before={t:old.db.execute(f'SELECT id,payload FROM {t}').fetchall() for t in ('cnf_patterns_v1','cnf_pattern_sources_v1')}
            old.close(); h=SubsumedEliminationInventory(path,max_depth=0); solver=ResidualSolver()
            for cnf in cases: h.inspect(cnf)
            nodes=[(k,json.loads(p)) for k,p in h.db.execute('SELECT id,payload FROM cnf_patterns_v1')
                   if json.loads(p).get('subsumed_elimination',{}).get('variable') is not None]
            self.assertGreaterEqual(len(nodes),10)
            for k,n in nodes:
                child=h._load(n['edge']['key']); a,b=solver.solve(n['cnf']),solver.solve(child['cnf'])
                self.assertEqual(a['answer'],b['answer'])
                if b['answer']: self.assertTrue(holds(n['cnf'],h.lift(k,b['model'])))
            for table,rows in before.items():
                for k,p in rows: self.assertEqual(h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(k,)).fetchone(),(p,))
            h.close();solver.close(); snapshot=path.read_bytes(); h=SubsumedEliminationInventory(path,max_depth=0)
            with patch('experiments.cnf_subsumed_elimination.discover_subsumed',side_effect=AssertionError('cold discovery')):
                for cnf in cases: self.assertFalse(h.inspect(cnf)['metrics'].get('inserted_nodes',0))
                for k,_ in nodes: h._load(k)
            h.close();self.assertEqual(path.read_bytes(),snapshot)
            k,n=nodes[0]
            for kind in ('reason','edge','summary','fallback'):
                bad=copy.deepcopy(n)
                if kind=='reason': bad['subsumed_elimination']['omissions'][0][2]=len(n['cnf'])
                elif kind=='edge': bad['edge']['names']=[]
                elif kind=='summary': bad['summary']['unresolved_literals']+=1
                else: bad['elimination']['variable']=bad['subsumed_elimination']['variable']
                h=SubsumedEliminationInventory(path,max_depth=0)
                with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),k))
                with self.assertRaises(ValueError): h._load(k)
                with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(n),k))
                h.close()


if __name__=='__main__': unittest.main()
