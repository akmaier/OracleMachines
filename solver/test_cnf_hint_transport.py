from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_hint_transport import CoreHintStore, HintAssistedInventory, check_rup, discover_rup, transport_hints
from experiments.cnf_learning_fixed_order import discover_fixed_order_probes
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_pattern_inventory import encode
from solver.test_cnf_learning_core import core_source, core_common_source, core_equivalence_source
from solver.test_cnf_pattern_inventory import assignments


class HintTransportTests(unittest.TestCase):
    def test_exhaustive_small_rup_soundness(self):
        for variables, max_clauses in ((2,9),(3,3)):
            clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s)
                     for signs in itertools.product((-1,0,1),repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses,count):
                    core,names=normalize(source)
                    if any(not c for c in core):candidates=[()]
                    else:
                        candidates=[c for c in clauses if all(abs(l)<=len(names) for l in c) and len(c)<=2]
                    models=[a for a in assignments(core) if holds(core,a)]
                    for c in candidates:
                        clause=tuple(sorted(c));p=discover_rup(core,clause,Counter())
                        if p is not None:
                            check_rup(core,clause,p,Counter())
                            self.assertTrue(all(holds([clause],a) for a in models))

    def test_transported_forced_common_equivalence_and_edits(self):
        rng=random.Random(20261109064108);kinds=set();hints=0
        for source in (core_source(),core_common_source(),core_equivalence_source()):
            variants=[source,source[:-1],source+[(1,)]]
            for _ in range(8):
                names=list(range(1,9));rng.shuffle(names)
                mapping={i+1:v*31*rng.choice((-1,1)) for i,v in enumerate(names)}
                variants.append([tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)])
            for changed in variants:
                cnf,_=normalize(changed)
                for cap in (0,1,4,16):
                    p=discover_fixed_order_probes(cnf,4,cap,Counter())
                    with patch('experiments.cnf_hint_transport.discover_rup',side_effect=AssertionError('Fresh fallback forbidden')):
                        t=transport_hints(cnf,p,4,cap,Counter())
                    if p['status']=='learned':kinds.add(p['continuation']['status'])
                    for hint in t['hints']:
                        hints+=1;check_rup(t['core'],hint['clause'],hint['proof'],Counter())
                        self.assertTrue(all(not holds(t['core'],a) or holds([hint['clause']],a) for a in assignments(t['core'])))
                        fresh=discover_rup(t['core'],hint['clause'],Counter());self.assertIsNotNone(fresh)
                        check_rup(t['core'],hint['clause'],fresh,Counter())
        self.assertGreater(hints,0);self.assertEqual(kinds,{'forced','common','equivalence'})

    def test_wrong_parent_dependencies_rejected(self):
        cnf,_=normalize(core_source());p=discover_fixed_order_probes(cnf,4,4,Counter())
        bads=[]
        for field,value in (('attempt',False),('unit',999),('clause',[1,2])):
            b=copy.deepcopy(p);b['batch'][0][field]=value;bads.append(b)
        b=copy.deepcopy(p);b['attempts'][0]['certificate']['units'].append([999,999]);bads.append(b)
        for b in bads:
            with self.assertRaises(ValueError):transport_hints(cnf,b,4,4,Counter())
        with self.assertRaises(ValueError):transport_hints(cnf[:-1],p,4,4,Counter())

    def test_portable_proofs_reject_forged_reasons_and_bindings(self):
        cnf,_=normalize(core_source());p=discover_fixed_order_probes(cnf,4,4,Counter());t=transport_hints(cnf,p,4,4,Counter())
        h=next(h for h in t['hints'] if h['proof']['units']);core=t['core'];clause=h['clause']
        bads=[dict(units=[],conflict=h['proof']['conflict']),dict(units=h['proof']['units'],conflict=False),
              dict(units=h['proof']['units'],conflict=999),dict(h['proof'],parent='trusted')]
        b=copy.deepcopy(h['proof']);b['units'][0][1]=999;bads.append(b)
        b=copy.deepcopy(h['proof']);b['units'][0][0]=False;bads.append(b)
        for bad in bads:
            with self.assertRaises(ValueError):check_rup(core,clause,bad,Counter())
        for bad_clause in ([999],[-1,1],[False],list(clause)+[clause[0]]):
            with self.assertRaises(ValueError):check_rup(core,bad_clause,h['proof'],Counter())
        with self.assertRaises(ValueError):check_rup(tuple(reversed(core)),clause,h['proof'],Counter())

    def test_empty_clause_and_nonentailed_hints(self):
        core,_=normalize([(1,),(-1,)])
        p=discover_rup(core,(),Counter());check_rup(core,(),p,Counter())
        self.assertIsNone(discover_rup(((1,2),),(1,),Counter()))
        with self.assertRaises(ValueError):check_rup(((1,2),),(1,),dict(units=[],conflict=0),Counter())
        # Exact normalized false source has no variables.
        check_rup(((),),(),dict(units=[],conflict=0),Counter())

    def test_persistent_child_only_replay_and_corruption(self):
        cnf,_=normalize(core_source());p=discover_fixed_order_probes(cnf,4,4,Counter());t=transport_hints(cnf,p,4,4,Counter())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'hints.db';store=CoreHintStore(path)
            for h in t['hints']:store.put(t['core'],h['clause'],h['proof'])
            before=store.storage();store.close();raw=path.read_bytes()
            # No parent profile or graph is supplied to the new reader.
            store=CoreHintStore(path);self.assertEqual(store.audit(),len(t['hints']))
            for h in t['hints']:
                self.assertEqual(store.get(t['core'],h['clause']),h['proof'])
                store.put(t['core'],h['clause'],h['proof'])
            self.assertEqual(store.storage(),before);store.close();self.assertEqual(path.read_bytes(),raw)
            store=CoreHintStore(path);h=t['hints'][0];key=store.key(t['core'],h['clause'])
            self.assertIsNone(store.get(t['core'][:-1],h['clause']))
            record=dict(core=t['core'][:-1],clause=h['clause'],proof=h['proof'])
            with store.db:store.db.execute('UPDATE cnf_core_hints_v1 SET payload=? WHERE id=?',(encode(record),key))
            with self.assertRaises(ValueError):store.get(t['core'],h['clause'])
            record=dict(core=t['core'],clause=h['clause'],proof=dict(units=[],conflict=999))
            with store.db:store.db.execute('UPDATE cnf_core_hints_v1 SET payload=? WHERE id=?',(encode(record),key))
            store.close();store=CoreHintStore(path)
            with self.assertRaises(ValueError):store.audit()
            store.close()

    def test_hint_plan_fibers_and_contexts(self):
        inventory=HintAssistedInventory(max_depth=1)
        for source in (core_source(),core_common_source(),core_equivalence_source()):
            cnf,_=normalize(source);p=discover_fixed_order_probes(cnf,4,4,Counter());t=transport_hints(cnf,p,4,4,Counter())
            for hints in ([],t['hints'][:1],t['hints']):
                r=inventory.inspect_hints(t['core'],hints,1);plan=r['plan'];edge=plan['edge']
                child=inventory._load(edge['key']);names=edge['names']
                feasible={tuple(a[v] for v in names) for a in assignments(t['core']) if holds(t['core'],a)}
                for a in assignments(child['cnf']):
                    self.assertEqual(holds(child['cnf'],a),tuple(a[i] for i in range(1,len(names)+1)) in feasible)
                    if holds(child['cnf'],a):self.assertTrue(holds(t['core'],inventory.lift_hint_plan(plan,a)))
            bare=inventory.inspect_hints(t['core'],[],1)
            self.assertNotEqual(bare['key'],r['key'])
        inventory.close()

    def test_hint_plan_cold_replay_and_wrong_child(self):
        cnf,_=normalize(core_source());p=discover_fixed_order_probes(cnf,4,4,Counter());t=transport_hints(cnf,p,4,4,Counter())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plans.db';h=HintAssistedInventory(path,max_depth=1)
            r=h.inspect_hints(t['core'],t['hints'],1);key=r['key'];saved=h.hint_storage();h.close();raw=path.read_bytes()
            h=HintAssistedInventory(path,max_depth=1);h.audit_hints()
            self.assertEqual(h.inspect_hints(t['core'],t['hints'],1)['metrics'].get('hint_plans_inserted',0),0)
            self.assertEqual(h.hint_storage(),saved);h.close();self.assertEqual(raw,path.read_bytes())
            h=HintAssistedInventory(path,max_depth=1);bad=copy.deepcopy(r['plan']);bad['edge']=h._edge((),1)
            with h.db:h.db.execute('UPDATE cnf_hint_plans_v1 SET payload=? WHERE id=?',(encode(bad),key))
            h.close();h=HintAssistedInventory(path,max_depth=1)
            with self.assertRaises(ValueError):h.audit_hints()
            h.close()
