from collections import Counter,defaultdict
import copy
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.cnf_learning_continuation import LearningBlocks,base_id,record_key
from experiments.cnf_trace_learning import acquire_learning
from experiments.cnf_residual_dag import normalize,holds,ResidualSolver,restrict
from experiments.cnf_simplification import discover_simplification
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose


class MemoryHistory:
    def __init__(self,fixture):
        self.db=sqlite3.connect(':memory:');self.nodes={fixture['source']:dict(
            cnf=fixture['cnf'],depth=fixture['depth'],kind='unresolved',summary=dict(closed=False))}
        for table in ('cnf_patterns_v1','cnf_probe_windows_v1','cnf_probe_continuations_v1'):
            self.db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT)')
        for block in fixture['blocks']:
            self.db.execute(f"INSERT INTO {block['table']} VALUES (?,?)",(block['id'],encode(block['payload'])))
    def _load(self,key):return self.nodes.get(key)
    def _canonical(self,cnf,depth):
        target,names=normalize(cnf);return target,names,encode([depth,target])
    def add_child(self,record,target):
        cnf,_,key=self._canonical(target,0)
        self.nodes[record['edge']['key']]=dict(cnf=cnf,kind='unresolved',summary=dict(closed=False))


class LearningContinuationTests(unittest.TestCase):
    def fixture(self):return json.loads(Path('solver/fixtures/learning-continuation.json').read_text())

    def successful(self,h,base):
        blocks=LearningBlocks(h,[base]);identity=base_id(base)
        first,_=blocks.advance(h,identity,Counter());second,target=blocks.advance(h,identity,Counter())
        self.assertEqual((first['offset'],first['probing']['status']),(4,'clear'))
        self.assertEqual((second['offset'],second['probing']['status']),(8,'forced'))
        return blocks,first,second,target

    def test_later_block_exact_target_and_model_lift(self):
        f=self.fixture();h=MemoryHistory(f);blocks,first,record,target=self.successful(h,f['base'])
        self.assertIsNone(first['edge']);h.add_child(record,target)
        solver=ResidualSolver();answer=solver.solve(h._load(record['edge']['key'])['cnf'])
        self.assertTrue(answer['answer']);self.assertTrue(holds(f['cnf'],blocks.lift(h,record,answer['model'])))
        wrong=copy.deepcopy(answer['model']);wrong[1]='true'
        with self.assertRaises(ValueError):blocks.lift(h,record,wrong)
        solver.close();h.db.close()

    def test_pending_replay_reuses_prefix_and_immutable_base(self):
        f=self.fixture();h=MemoryHistory(f);blocks,first,record,target=self.successful(h,f['base'])
        saved=encode(list(blocks.records.values()));routes=SimpleNamespace(by_source=defaultdict(list))
        blocks.attach(h,routes);self.assertFalse(routes.by_source)
        self.assertEqual(compose(h,[f['source']],routes,Counter())[0],[False])
        with patch('experiments.cnf_learning_continuation.discover_equivalence_probes',side_effect=AssertionError('rediscovery')):
            resumed=LearningBlocks(h,[f['base']],list(reversed(json.loads(saved))));counts=Counter()
            again,raw=resumed.advance(h,base_id(f['base']),counts)
        self.assertEqual(encode(again),encode(record));self.assertEqual(encode(raw),encode(target));self.assertEqual(counts.get('probe_attempts',0),0)
        self.assertEqual({record_key(r):r for r in json.loads(saved)},resumed.records)
        h.add_child(record,target);resumed.attach(h,routes);self.assertEqual(len(routes.by_source[f['source']]),1)
        resumed.attach(h,routes);self.assertEqual(len(routes.by_source[f['source']]),1);h.db.close()

    def test_missing_prefix_foreign_base_forgery_and_target_rejected(self):
        f=self.fixture();h=MemoryHistory(f);blocks,first,record,_=self.successful(h,f['base'])
        with self.assertRaises(ValueError):LearningBlocks(h,[f['base']],[record])
        with self.assertRaises(ValueError):LearningBlocks(h,[],[first])
        for field,value in [('base_sha256','foreign'),('width',True),('offset',True),('offset',12)]:
            bad=copy.deepcopy(record);bad[field]=value
            with self.assertRaises(ValueError):LearningBlocks(h,[f['base']],[first,bad])
        bad=copy.deepcopy(record);bad['edge']['names']=list(reversed(bad['edge']['names']))
        with self.assertRaises(ValueError):LearningBlocks(h,[f['base']],[first,bad])
        bad=copy.deepcopy(record);bad['probing']['attempts'][-1]['certificate']['conflict']=99999
        with self.assertRaises(ValueError):LearningBlocks(h,[f['base']],[first,bad])
        bad=copy.deepcopy(first);bad['edge']=record['edge']
        with self.assertRaises(ValueError):LearningBlocks(h,[f['base']],[bad])
        changed=copy.deepcopy(f['base']);changed['clauses'][0]['clause']=[1,2]
        with self.assertRaises(ValueError):LearningBlocks(h,[changed],[first])
        h.db.close()

    def test_small_complete_base_exhaustion_has_no_new_probes(self):
        cnf=((-1,2),(-1,3),(-2,-3,4));attempts=[]
        for v in range(1,5):
            for value in (False,True):
                cert=discover_simplification(restrict(cnf,{v:value},Counter()),Counter(),pure=False)
                attempts.append(dict(variable=v,value=value,certificate=cert))
        source=encode(cnf);f=dict(source=source,cnf=cnf,depth=0,blocks=[dict(table='cnf_patterns_v1',id=source,
            payload=dict(profile=dict(probing=dict(attempts=attempts))))]);h=MemoryHistory(f)
        refs=[dict(table='cnf_patterns_v1',id=source,index=i) for i in range(len(attempts))]
        base=acquire_learning(h,source,attempts,refs,Counter());self.assertIsNotNone(base)
        self.assertEqual(base['probing']['status'],'clear');blocks=LearningBlocks(h,[base]);counts=Counter()
        with patch('experiments.cnf_learning_continuation.discover_equivalence_probes',side_effect=AssertionError('new probe')):
            self.assertEqual(blocks.advance(h,base_id(base),counts),(None,None))
        self.assertEqual(counts['exhausted_learning_sources'],1);self.assertFalse(blocks.records);h.db.close()


if __name__=='__main__':unittest.main()
