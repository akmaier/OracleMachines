from collections import Counter,defaultdict
import copy
import itertools
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from experiments.cnf_bootstrap_conditioning import initialize,acquire_record,verify,attach,lift,verify_positive,choices,TABLE
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_residual_dag import holds
from experiments.cnf_route_composition import compose
from experiments.cnf_expanded_coverage import expand


class BootstrapConditioningTests(unittest.TestCase):
    def test_external_positive_rule_closes_a_previously_open_source(self):
        source=json.loads(Path('solver/fixtures/trace-split.json').read_text())
        h=CompleteAdmissionInventory(max_depth=1,probe_limit=4,learn_limit=4,clause_growth_limit=2);initialize(h)
        try:
            h.set_admission_budget(64);key=h._edge(source,0)['key']
            self.assertFalse(h._load(key)['summary']['closed'])
            record=acquire_record(h,key,5,Counter());targets,_=verify(h,record,Counter())
            for target in targets:h._edge(target,0)
            routes=SimpleNamespace(by_source=defaultdict(list));self.assertTrue(attach(h,routes,record,Counter()))
            closed,plan=compose(h,[key],routes,Counter());self.assertEqual(closed,[True])
            proof=expand(h,plan,[key],routes,Counter())
            self.assertTrue(any(s['rule']['kind']=='bootstrap_split' for s in proof['steps']))
            verify_positive(h,proof,[key],[record],Counter())
            with self.assertRaises(ValueError):verify_positive(h,proof,[key],[],Counter())
        finally:h.close()

    def test_exhaustive_two_variable_fibers_and_lift(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        h=CompleteAdmissionInventory(max_depth=1);initialize(h);checked=0
        try:
            for mask in range(512):
                source=[c for i,c in enumerate(clauses) if mask>>i&1];h.set_admission_budget(32)
                key=h._edge(source,0)['key'];cnf=h._load(key)['cnf'];support=sorted({abs(l) for c in cnf for l in c})
                for variable in support:
                    record=acquire_record(h,key,variable,Counter());targets,fixed=verify(h,record,Counter())
                    for bits in itertools.product((False,True),repeat=len(support)):
                        model=dict(zip(support,bits));branch=int(model[variable])
                        consistent=all(model[v]==b for v,b in fixed[branch].items())
                        self.assertEqual(holds(cnf,model),consistent and holds(targets[branch],model));checked+=1
                    for value,target,branch in zip((False,True),targets,record['branches']):
                        h._edge(target,0);edge=branch['edge'];child=h._load(edge['key'])
                        for bits in itertools.product((False,True),repeat=len(edge['names'])):
                            model=dict(enumerate(bits,1))
                            if holds(child['cnf'],model):self.assertTrue(holds(cnf,lift(h,record,value,model)))
            self.assertGreater(checked,1000)
        finally:h.close()

    def test_pairs_without_binary_clauses_and_cold_immutable_reuse(self):
        source=((1,2,3),(-1,-2,-3),(1,-2,3),(-1,2,-3))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h=CompleteAdmissionInventory(path,max_depth=1);initialize(h)
            try:
                h.set_admission_budget(64);key=h._edge(source,0)['key'];selected=choices(h,key,Counter())
                self.assertTrue(selected)
                counts=Counter();record=acquire_record(h,key,selected[0],counts)
                self.assertEqual(counts['bootstrap_fresh_assumptions'],2)
                saved=dict(h.db.execute(f'SELECT id,payload FROM {TABLE}'))
                targets,_=verify(h,record,Counter());routes=SimpleNamespace(by_source=defaultdict(list))
                self.assertFalse(attach(h,routes,record,Counter()))
                for target in targets:h._edge(target,0)
                self.assertTrue(attach(h,routes,record,Counter()))
                closed,plan=compose(h,[key],routes,Counter());self.assertTrue(closed[0])
                positive=expand(h,plan,[key],routes,Counter())
            finally:h.close()
            h=CompleteAdmissionInventory(path,max_depth=1);h.set_admission_budget(0)
            try:
                with patch('experiments.cnf_bootstrap_conditioning.discover_simplification',side_effect=AssertionError('fresh assumptions')):
                    self.assertEqual(acquire_record(h,key,selected[0],Counter()),record)
                    verify_positive(h,positive,[key],[record],Counter())
                self.assertEqual(dict(h.db.execute(f'SELECT id,payload FROM {TABLE}')),saved)
                self.assertFalse(h.admitted)
            finally:h.close()

    def test_missing_polarity_and_foreign_binding_rejected(self):
        h=CompleteAdmissionInventory(max_depth=1);initialize(h)
        try:
            h.set_admission_budget(32);key=h._edge(((1,2),(-1,3)),0)['key'];record=acquire_record(h,key,1,Counter())
            bad=copy.deepcopy(record);bad['branches'].pop()
            with self.assertRaises(ValueError):verify(h,bad,Counter())
            bad=copy.deepcopy(record);bad['branches'][0]=bad['branches'][1]
            with self.assertRaises(ValueError):verify(h,bad,Counter())
            bad=copy.deepcopy(record);bad['branches'][0]['edge']['names']=[999]
            with self.assertRaises(ValueError):verify(h,bad,Counter())
            for variable in (True,0,99):
                with self.assertRaises(ValueError):acquire_record(h,key,variable,Counter())
        finally:h.close()


if __name__=='__main__':unittest.main()
