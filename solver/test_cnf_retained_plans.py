from collections import Counter
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_retained_plans import RetainedPlanInventory
from experiments.cnf_residual_dag import holds
from solver.test_cnf_pattern_inventory import assignments


class RetainedPlanTests(unittest.TestCase):
    def test_exact_closed_reuse_and_renaming_without_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=PolarityHornInventory(path,max_depth=1)
            source=[(-1,2),(-2,3)];r=old.inspect(source);old.close()
            h=RetainedPlanInventory(path,max_depth=1)
            with patch.object(h,'_profile',side_effect=AssertionError('new profile')):
                result=h.inspect([(-10,20),(-20,30)])
            node=h._load(result['root']['key'])
            self.assertEqual(node['kind'],'retained_plan');self.assertEqual(node['reference'],r['root']['key'])
            self.assertEqual(result['metrics']['inserted_nodes'],1)
            for model in assignments(node['cnf']):
                if holds(node['cnf'],model):self.assertEqual(h.lift(result['root']['key'],model),model)
            with self.assertRaises(ValueError):h.lift(result['root']['key'],{1:True})
            h.close()

    def test_no_preparation_is_inconclusive_and_matches_fallback(self):
        rng=random.Random(202611091713)
        baseline=BinaryPathInventory(max_depth=1);h=RetainedPlanInventory(max_depth=1)
        for _ in range(35):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,6),rng.choice((2,3,4)))) for _ in range(16)]
            a=baseline.inspect(source);b=h.inspect(source)
            self.assertEqual(a['summary'],b['summary']);self.assertEqual(a['profile'],b['profile'])
            self.assertEqual(b['metrics'].get('retained_plan_hits',0),0)
        h.close();baseline.close()

    def test_unclosed_and_edited_sources_do_not_inherit_closure(self):
        h=RetainedPlanInventory(max_depth=0)
        hard=json.loads(Path('experiments/results/cnf-polarity-horn/report.json').read_text())['frontiers']['polarity'][1]['cnf']
        old=h.prepared.inspect(hard);self.assertFalse(old['summary']['closed'])
        result=h.inspect(hard);self.assertNotEqual(h._load(result['root']['key'])['kind'],'retained_plan')
        old=h.prepared.inspect([(-1,2)]);self.assertTrue(old['summary']['closed'])
        result=h.inspect([(-1,2),(1,2,3)])
        self.assertNotEqual(h._load(result['root']['key'])['kind'],'retained_plan')
        h.close()

    def test_corrupted_references_profiles_and_old_proofs_rejected(self):
        h=RetainedPlanInventory(max_depth=1);source=[(-1,2),(-2,3)]
        old=h.prepared.inspect(source);r=h.inspect(source);key=r['root']['key'];node=h._load(key)
        mutations=[]
        for i,value in [(1,{}),(2,0),(3,[[1]])]:
            bad=copy.deepcopy(node);ref=json.loads(bad['reference']);ref[i]=value;bad['reference']=encode(ref);mutations.append(bad)
        bad=copy.deepcopy(node);bad['profile']['shape']['variables']+=1;mutations.append(bad)
        bad=copy.deepcopy(node);bad['summary']['closed']=False;mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):h._check(key,bad)
        h.checked.clear();h.prepared.checked.clear()
        oldnode=json.loads(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(old['root']['key'],)).fetchone()[0])
        oldnode['profile']['shape']['variables']+=1
        with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(oldnode),old['root']['key']))
        with self.assertRaises(ValueError):h.inspect(source)
        h.close()

    def test_cold_byte_preservation_and_missing_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=PolarityHornInventory(path,max_depth=1)
            source=[(1,2),(-1,-2)];prior=old.inspect(source)
            saved=dict(old.db.execute('SELECT id,payload FROM cnf_patterns_v1'));old.close()
            h=RetainedPlanInventory(path,max_depth=1);h.inspect(source)
            for k,p in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],p)
            h.close();raw=path.read_bytes();h=RetainedPlanInventory(path,max_depth=1)
            with patch.object(h,'_discover',side_effect=AssertionError('new acquisition')):
                result=h.inspect(source)
            self.assertEqual(result['metrics'].get('inserted_nodes',0),0);h.close();self.assertEqual(path.read_bytes(),raw)
            h=RetainedPlanInventory(path,max_depth=1)
            with h.db:h.db.execute('DELETE FROM cnf_patterns_v1 WHERE id=?',(prior['root']['key'],))
            with self.assertRaises(ValueError):h.inspect(source)
            h.close()
