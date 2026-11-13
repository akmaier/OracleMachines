from collections import Counter
import copy
from itertools import combinations, product
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_trace_learning import (implication_graph,discover_graph,check_graph,
    acquire_learning,verify_learning,checked_augmentation,lift_learning,LearnedTraceRoutes)
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_coupled_pivots import BudgetedInventory,AdmissionExhausted
from experiments.cnf_simplification import discover_simplification
from experiments.cnf_residual_dag import restrict,normalize,holds,ResidualSolver
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose,verify_plan


class LocalHistory:
    """Small checker interface; real inventory/restart is covered separately."""
    def __init__(self,cnf,attempts):
        self.db=sqlite3.connect(':memory:'); self.nodes={}
        self.source=encode(cnf); self.nodes[self.source]=dict(cnf=cnf,kind='unresolved',depth=0)
        self.db.execute('CREATE TABLE cnf_patterns_v1 (id TEXT PRIMARY KEY,payload TEXT)')
        self.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',(self.source,encode(dict(profile=dict(probing=dict(attempts=attempts))))))
    def _load(self,key): return self.nodes.get(key)
    def _canonical(self,cnf,depth):
        target,names=normalize(cnf); return target,names,encode([depth,target])
    def add_target(self,record):
        raw,_=verify_learning(self,record,Counter()); target,_,key=self._canonical(raw,0)
        self.nodes[key]=dict(cnf=target)


def attempts_for(cnf):
    result=[]
    for v in sorted({abs(l) for c in cnf for l in c}):
        for b in (False,True):
            cert=discover_simplification(restrict(cnf,{v:b},Counter()),Counter(),pure=False)
            if cert['conflict'] is None: result.append(dict(variable=v,value=b,certificate=cert))
    return result


class TraceLearningTests(unittest.TestCase):
    def test_small_learned_clauses_and_exact_model_lift(self):
        clauses=[tuple(v*s for v,s in zip(vs,signs)) for width in (2,3)
            for vs in combinations((1,2,3),width) for signs in product((-1,1),repeat=width)]
        records=rewrites=0
        for size in range(1,4):
            for cnf in combinations(clauses,size):
                attempts=attempts_for(cnf); h=LocalHistory(cnf,attempts)
                refs=[dict(table='cnf_patterns_v1',id=h.source,index=i) for i in range(len(attempts))]
                record=acquire_learning(h,h.source,attempts,refs,Counter())
                if record is not None:
                    records+=1; _,expanded=checked_augmentation(h,record,Counter()); verify_learning(h,record,Counter())
                    for values in product((False,True),repeat=3):
                        model=dict(zip((1,2,3),values)); self.assertEqual(holds(cnf,model),holds(expanded,model))
                    if record['edge'] is not None:
                        rewrites+=1; h.add_target(record); child=h._load(record['edge']['key'])['cnf']
                        for values in product((False,True),repeat=len(record['edge']['names'])):
                            model=dict(enumerate(values,1))
                            if holds(child,model): self.assertTrue(holds(cnf,lift_learning(h,record,model,Counter())))
                h.db.close()
        self.assertGreater(records,0); self.assertGreater(rewrites,0)

    def test_graph_certificates_agree_with_independent_transitive_closure(self):
        rng=random.Random(13112026); vertices=(-3,-2,-1,1,2,3)
        for _ in range(100):
            graph={x:{y for y in vertices if rng.randrange(5)==0} for x in vertices}
            cert=discover_graph(graph,Counter()); check_graph(graph,cert,Counter())
            reach={(x,y) for x in vertices for y in graph[x]}|{(x,x) for x in vertices}
            for pivot in vertices:
                for x in vertices:
                    for y in vertices:
                        if (x,pivot) in reach and (pivot,y) in reach: reach.add((x,y))
            for root,tree in zip(sorted(graph),cert['trees']):
                self.assertEqual({x for x,_ in tree},{y for x,y in reach if x==root})
        graph={-2:set(),-1:{2},1:set(),2:{1}}; cert=discover_graph(graph,Counter())
        bad=copy.deepcopy(cert); bad['trees'][1].pop()
        with self.assertRaises(ValueError):check_graph(graph,bad,Counter())
        bad=copy.deepcopy(cert); bad['conclusions']['forced_literals']=[]
        with self.assertRaises(ValueError):check_graph(graph,bad,Counter())
        bad=copy.deepcopy(cert); bad['trees'][2][0]=[True,True]
        with self.assertRaises(ValueError):check_graph(graph,bad,Counter())

    def test_conditional_implications_include_contrapositives(self):
        cnf=((-1,2),(-1,3),(-2,-3,4)); attempts=attempts_for(cnf)
        graph=implication_graph(cnf,attempts,Counter())
        self.assertIn(4,graph[1]); self.assertIn(-1,graph[-4])
        bad=copy.deepcopy(attempts); bad[0]['certificate']['units']=[[4,9999]]
        with self.assertRaises(ValueError):implication_graph(cnf,bad,Counter())

    def history(self,path):
        fixture=json.loads(Path('solver/fixtures/trace-learning.json').read_text())
        h=BudgetedInventory(path,**fixture['options']); h.set_admission_budget(32)
        for t in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1','cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        self.assertEqual(h._edge(fixture['cnf'],fixture['depth'])['key'],fixture['source'])
        with h.db:
            for b in fixture['blocks']: h.db.execute(f"INSERT OR IGNORE INTO {b['table']} VALUES (?,?)",(b['id'],encode(b['payload'])))
        return h,fixture

    def test_real_history_pending_restart_binding_and_no_rediscovery(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,f=self.history(path);a,refs=source_attempts(h,f['source'],Counter())
            record=acquire_learning(h,f['source'],a,refs,Counter());self.assertEqual(record,f['record'])
            h.set_admission_budget(0);target,_=verify_learning(h,record,Counter());routes=LearnedTraceRoutes(h,learning=[record])
            self.assertNotIn(f['source'],routes.by_source)
            with self.assertRaises(AdmissionExhausted):h._edge(target,f['depth'])
            h.close();h,f=self.history(path);h.set_admission_budget(32)
            self.assertEqual(h._edge(target,f['depth']),record['edge']);routes=LearnedTraceRoutes(h,learning=[record])
            closed,plan=compose(h,[f['source']],routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
            child=h._load(record['edge']['key']);solver=ResidualSolver();answer=solver.solve(child['cnf'])
            if answer['answer']:self.assertTrue(holds(f['cnf'],lift_learning(h,record,answer['model'],Counter())))
            solver.close();h.close();before=path.read_bytes();h,f=self.history(path);h.set_admission_budget(0)
            with patch('experiments.cnf_trace_learning.discover_equivalence_probes',side_effect=AssertionError('new search')):
                again=LearnedTraceRoutes(h,learning=[record]);verify_learning(h,record,Counter())
                self.assertEqual(compose(h,[f['source']],again,Counter())[0],closed)
            h.close();self.assertEqual(before,path.read_bytes())

    def test_forged_reasons_clauses_bounds_and_edges_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h,f=self.history(Path(td)/'h'); record=f['record']; bads=[]
            for field,value in [('reference',True),('reference',999),('unit',999),('clause',[1,2])]:
                bad=copy.deepcopy(record);bad['clauses'][0][field]=value;bads.append(bad)
            bad=copy.deepcopy(record);bad['references'].append(bad['references'][0]);bads.append(bad)
            bad=copy.deepcopy(record);bad['clauses']*=17;bads.append(bad)
            bad=copy.deepcopy(record);bad['edge']['names'].reverse();bads.append(bad)
            bad=copy.deepcopy(record)
            next(a for a in bad['probing']['attempts'] if a['certificate']['units'])['certificate']['units'][0][1]=99999
            bads.append(bad)
            bad=copy.deepcopy(record);bad['references'][0]['id']='foreign';bads.append(bad)
            for bad in bads:
                with self.assertRaises(ValueError):verify_learning(h,bad,Counter())
            h.close()


if __name__=='__main__':unittest.main()
