from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_frontier_pivots import frontier_ancestors,search
from experiments.cnf_pivot_alternatives import open_ancestors,verify_trial
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_frontier_pivots import delta_from_seed,digests
from experiments.compare_cnf_pivot_alternatives import TABLES,apply_delta


class FrontierPivotTests(unittest.TestCase):
    def test_seed_delta_keeps_old_trials_and_rebuilds_idempotently(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);seed=tmp/'seed';history=tmp/'history';delta=tmp/'delta';rebuilt=tmp/'rebuilt'
            with sqlite3.connect(seed) as db:
                for table in TABLES:
                    db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                    db.execute(f'INSERT INTO {table} VALUES (?,?)',('old','{}'))
            shutil.copyfile(seed,history)
            with sqlite3.connect(history) as db:
                for table in TABLES:db.execute(f'INSERT INTO {table} VALUES (?,?)',('new','{"x":1}'))
            preserved,added=delta_from_seed(seed,history,delta)
            self.assertEqual(preserved,{t:1 for t in TABLES});self.assertEqual(added,{t:1 for t in TABLES})
            shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
            self.assertEqual(digests(history),digests(rebuilt));before=rebuilt.read_bytes()
            apply_delta(rebuilt,delta);self.assertEqual(rebuilt.read_bytes(),before)
            for table in TABLES:
                with sqlite3.connect(history) as db:db.execute(f'UPDATE {table} SET payload=? WHERE id=?',('bad','old'))
                with self.assertRaises(ValueError):delta_from_seed(seed,history,tmp/('bad-'+table))
                with sqlite3.connect(history) as db:db.execute(f'UPDATE {table} SET payload=? WHERE id=?',('{}','old'))

    def test_selected_dag_distance_shared_children_and_unselected_edges(self):
        def node(kind,**extra):return dict(kind=kind,summary=dict(closed=kind=='family'),**extra)
        def edge(key):return dict(key=key)
        nodes={'leaf':node('unresolved'),'closed':node('family'),
            'near':node('eliminate',edge=edge('leaf')),
            'middle':node('eliminate',edge=edge('near')),
            'other':node('eliminate',edge=edge('leaf')),
            'unselected':node('eliminate',edge=edge('leaf')),
            'or':node('or',selected=0,alternatives=[dict(edges=[edge('other'),edge('closed')]),dict(edges=[edge('unselected'),edge('leaf')])]),
            'and':node('and',edges=[edge('middle'),edge('or'),edge('middle')]),
            'root':node('eliminate',edge=edge('and'))}
        class H:
            def _load(self,key):return nodes.get(key)
        h=H();counts=Counter()
        self.assertEqual(open_ancestors(h,'root',2,Counter()),['root','middle'])
        self.assertEqual(frontier_ancestors(h,'root',2,counts),['near','other'])
        self.assertEqual(counts['available_elimination_ancestors'],4)
        self.assertEqual(counts['selected_ancestor_heights'],2)
        self.assertEqual(frontier_ancestors(h,'root',99,Counter()),['near','other','middle','root'])
        self.assertEqual(frontier_ancestors(h,'root',0,Counter()),[])
        with self.assertRaises(ValueError):frontier_ancestors(h,'missing',2,Counter())
        nodes['leaf']=node('eliminate',edge=edge('root'))
        with self.assertRaises(ValueError):frontier_ancestors(h,'root',2,Counter())

    def test_reuse_does_not_spend_new_trial_budget_and_checks_binding(self):
        source=json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        h=AnchoredAdditiveInventory(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        root=h.inspect(source)['root']['key'];known={}
        first=search(h,root,Counter(),known,policy='early',ancestor_limit=2,trial_limit=2)
        self.assertEqual(len(first),2)
        for r in first:known[encode([r['source'],r['variable']])]=r
        counts=Counter();second=search(h,root,counts,known,policy='early',ancestor_limit=2,trial_limit=2)
        self.assertEqual(len(second),2);self.assertEqual(counts['reused_trials'],2)
        self.assertTrue(set(encode(r) for r in first).isdisjoint(encode(r) for r in second))
        for r in second:verify_trial(h,r,Counter());known[encode([r['source'],r['variable']])]=r
        # A failed cache result is only about this exact trial. Corrupt payloads
        # must never turn a skip into an unchecked closure.
        bad=copy.deepcopy(known);bad[next(iter(bad))]['summary']['closed']=True
        with self.assertRaises(ValueError):search(h,root,Counter(),bad,policy='early',ancestor_limit=2)
        bad=copy.deepcopy(known);bad[next(iter(bad))]['variable']=-1
        with self.assertRaises(ValueError):search(h,root,Counter(),bad,policy='early',ancestor_limit=2)
        self.assertEqual(search(h,root,Counter(),known,trial_limit=0),[])
        self.assertEqual(search(h,root,Counter(),known,ancestor_limit=0),[])
        with self.assertRaises(ValueError):search(h,root,Counter(),known,policy='unknown')
        h.close()

    def test_frontier_policy_uses_existing_exact_trial_checker(self):
        source=json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        h=AnchoredAdditiveInventory(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        root=h.inspect(source)['root']['key'];counts=Counter()
        records=search(h,root,counts,{},trial_limit=3)
        self.assertLessEqual(len(records),3);self.assertGreater(counts['selected_ancestors'],0)
        for record in records:verify_trial(h,record,Counter())
        with patch('experiments.cnf_frontier_pivots.alternatives',side_effect=AssertionError('rediscovery')):
            for record in records:verify_trial(h,record,Counter())
        h.close()


if __name__=='__main__':unittest.main()
