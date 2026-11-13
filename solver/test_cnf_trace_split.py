from collections import Counter,defaultdict
import copy
import itertools
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory,AdmissionExhausted
from experiments.cnf_learning_continuation import ContinuedLearningRoutes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds,normalize
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_simplification import discover_simplification
from experiments.cnf_residual_dag import restrict
from experiments.cnf_trace_split import candidates,make_record,verify,attach,lift


class TraceSplitTests(unittest.TestCase):
    def history(self,path):
        h=BudgetedInventory(path,max_depth=2,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        for table in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1','cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit();return h

    def seed(self,h):
        cnf=json.loads(Path('solver/fixtures/trace-split.json').read_text());h.set_admission_budget(32)
        key=h._edge(cnf,0)['key'];self.assertEqual(h._load(key)['kind'],'unresolved')
        routes=ContinuedLearningRoutes(h);rows=candidates(h,key,routes,Counter())
        self.assertEqual(rows[0]['rank'][-1],5);return key,routes,rows[0]['record']

    def test_two_children_close_and_lift_every_satisfying_assignment(self):
        with tempfile.TemporaryDirectory() as td:
            h=self.history(Path(td)/'h');key,routes,record=self.seed(h);targets,fixed=verify(h,record,Counter())
            source=h._load(key)['cnf'];variable=next(iter(fixed[0]));models=[]
            for bits in itertools.product((False,True),repeat=10):
                model=dict(enumerate(bits,1));branch=int(model[variable]);consistent=all(model[v]==b for v,b in fixed[branch].items())
                self.assertEqual(holds(source,model),consistent and holds(targets[branch],model))
            h.set_admission_budget(32)
            for target,edge in zip(targets,record['edges']):
                self.assertEqual(h._edge(target,0),edge)
                child=h._load(edge['key']);found=False
                for bits in itertools.product((False,True),repeat=len(edge['names'])):
                    model=dict(enumerate(bits,1))
                    if holds(child['cnf'],model):
                        found=True;self.assertTrue(holds(source,lift(h,record,len(models)==1,model)))
                self.assertTrue(found);models.append(found)
            self.assertTrue(attach(h,routes,record,Counter()));closed,plan=compose(h,[key],routes,Counter())
            self.assertEqual(closed,[True]);verify_plan(h,plan,[key],routes,Counter());h.close()

    def test_partial_acquisition_does_not_create_coverage_and_cold_reuses(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h=self.history(path);key,routes,record=self.seed(h);targets,_=verify(h,record,Counter())
            h.set_admission_budget(0)
            with self.assertRaises(AdmissionExhausted):h._edge(targets[0],0)
            self.assertFalse(attach(h,routes,record,Counter()));self.assertEqual(compose(h,[key],routes,Counter())[0],[False])
            h.set_admission_budget(32);h._edge(targets[0],0)
            self.assertFalse(attach(h,routes,record,Counter()));h._edge(targets[1],0);h.close()
            h=self.history(path);h.set_admission_budget(0)
            with patch.object(h,'_discover',side_effect=AssertionError('rediscovery')):
                routes=ContinuedLearningRoutes(h);self.assertTrue(attach(h,routes,record,Counter()))
                self.assertEqual(compose(h,[key],routes,Counter())[0],[True]);self.assertFalse(h.admitted)
            h.close()

    def test_missing_or_forged_branches_and_models_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h=self.history(Path(td)/'h');_,_,record=self.seed(h)
            mutations=[]
            for field in ('edges','references'):
                item=copy.deepcopy(record);item[field].pop();mutations.append(item)
                item=copy.deepcopy(record);item[field][1]=item[field][0];mutations.append(item)
            item=copy.deepcopy(record);item['edges'][0]['names']=[999];mutations.append(item)
            item=copy.deepcopy(record);item['references'][0]['id']='foreign';mutations.append(item)
            for item in mutations:
                with self.assertRaises(ValueError):verify(h,item,Counter())
            with self.assertRaises(ValueError):lift(h,record,0,{})
            with self.assertRaises(ValueError):lift(h,record,False,{})
            h.close()

    def test_equal_canonical_children_retain_both_bindings(self):
        cnf=((1,2),(-1,3));source='source';attempts=[];nodes={}
        for value in (False,True):
            cert=discover_simplification(restrict(cnf,{1:value},Counter()),Counter(),pure=False)
            attempts.append(dict(variable=1,value=value,certificate=cert))
        node=dict(cnf=cnf,depth=0,kind='unresolved',summary=dict(closed=False),profile=dict(probing=dict(attempts=attempts)))
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE cnf_patterns_v1(id TEXT,payload TEXT)')
        db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',(source,encode(node)));nodes[source]=node
        def canonical(cnf,depth):
            normalized,names=normalize(cnf,Counter());return normalized,list(names),encode(normalized)
        h=SimpleNamespace(db=db,_load=lambda key:nodes.get(key),_canonical=canonical)
        refs=[dict(table='cnf_patterns_v1',id=source,index=i) for i in (0,1)]
        record=make_record(h,source,refs,Counter());self.assertEqual(record['edges'][0],record['edges'][1])
        child=record['edges'][0]['key'];nodes[child]=dict(cnf=(),summary=dict(closed=True))
        routes=SimpleNamespace(by_source=defaultdict(list));self.assertTrue(attach(h,routes,record,Counter()))
        self.assertEqual(routes.by_source[source][0][1],[child,child])
        self.assertNotEqual(lift(h,record,False,{}),lift(h,record,True,{}))
        closed,plan=compose(h,[source],routes,Counter());self.assertEqual(closed,[True]);verify_plan(h,plan,[source],routes,Counter());db.close()


if __name__=='__main__':unittest.main()
