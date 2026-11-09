from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_binary_paths import BinaryPathInventory, discover_binary_paths, check_binary_paths
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import normalize, holds
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_signed_subsumption import check_signed_tree


def check_tree(h,key,seen=None):
    seen=set() if seen is None else seen
    if key in seen:return
    seen.add(key);node=h._load(key)
    edges=(node['edges'] if node['kind']=='and' else
           [e for a in node['alternatives'] for e in a['edges']] if node['kind']=='or' else
           [node['edge']] if 'edge' in node else [])
    if node['kind']=='binary_paths':
        edge=node['edge'];child=h._load(edge['key'])
        for model in assignments(node['cnf']):
            local={i:model[v] for i,v in enumerate(edge['names'],1)}
            assert holds(node['cnf'],model)==holds(child['cnf'],local)
            if holds(child['cnf'],local):assert holds(node['cnf'],h.lift(key,local))
    elif node['kind']=='polarity':
        edge=node['edge'];child=h._load(edge['key']);flips=set(node['polarity']['flipped'])
        for model in assignments(node['cnf']):
            local={i:not model[v] if v in flips else model[v] for i,v in enumerate(edge['names'],1)}
            assert holds(node['cnf'],model)==holds(child['cnf'],local)
            if holds(child['cnf'],local):assert holds(node['cnf'],h.lift(key,local))
    else:check_signed_tree(h,key,{e['key'] for e in edges})
    for edge in edges:check_tree(h,edge['key'],seen)


class BinaryPathTests(unittest.TestCase):
    def test_shared_prefixes_and_kept_reasons(self):
        cnf=((-1,2),(-2,3),(-3,4),(-1,3,5),(-1,4,6))
        counts=Counter();cert=discover_binary_paths(cnf,counts)
        self.assertEqual(cert['removed'],[[3,2],[4,3]])
        self.assertEqual(len(cert['proof']),4)  # one root and three shared edges
        self.assertEqual(check_binary_paths(cnf,cert,Counter()),cnf[:3])
        self.assertGreater(counts['binary_path_reach_hits'],0)
        for model in assignments(cnf):self.assertEqual(holds(cnf,model),holds(cnf[:3],model))

    def test_exhaustive_small_and_signed_edited_model_equivalence(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=3)]
        sources=itertools.chain.from_iterable(itertools.combinations(clauses,n) for n in range(4))
        rng=random.Random(202611091620);randoms=[]
        for _ in range(40):
            f=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,6),rng.choice((2,3,4)))) for _ in range(18)]
            randoms.extend([f,f+[(1,)],f[1:]])
        for source in itertools.chain(sources,randoms):
            cnf,_=normalize(source)
            for cap in (0,1,64):
                cert=discover_binary_paths(cnf,Counter(),root_limit=cap)
                core=check_binary_paths(cnf,cert,Counter(),root_limit=cap)
                for model in assignments(cnf):self.assertEqual(holds(cnf,model),holds(core,model))
                for c in cnf:
                    if len(c)<=2:self.assertIn(c,core)

    def test_forged_paths_wide_reasons_and_circular_deletion_rejected(self):
        source=((-1,2),(-2,3),(-1,3,4));good=discover_binary_paths(source,Counter());mutations=[]
        bad=copy.deepcopy(good);bad['proof'][1][0]=1;mutations.append(bad)
        bad=copy.deepcopy(good);bad['proof'][1][2]=2;mutations.append(bad)
        bad=copy.deepcopy(good);bad['removed'][0][0]=0;mutations.append(bad)
        bad=copy.deepcopy(good);bad['proof'][0][0]=-1;mutations.append(bad)
        bad=copy.deepcopy(good);bad['proof'].append([99]);mutations.append(bad)
        bad=copy.deepcopy(good);bad['removed'].append(bad['removed'][0]);mutations.append(bad)
        bad=copy.deepcopy(good);bad['proof'][1][1]=True;mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):check_binary_paths(source,bad,Counter())
        with self.assertRaises(ValueError):check_binary_paths(source[1:],good,Counter())
        for source in (((1,1,2),),((1,-1,2),),((0,),),((True,),)):
            with self.assertRaises(ValueError):discover_binary_paths(source,Counter())
        for cap in (-1,True,1.5):
            with self.assertRaises(ValueError):discover_binary_paths((),Counter(),root_limit=cap)

    def test_inconclusive_empty_proposal_is_not_a_class_exclusion(self):
        cnf=((-1,2),(-2,3),(-1,3,4))
        empty=dict(proof=[],removed=[])
        self.assertEqual(check_binary_paths(cnf,empty,Counter()),cnf)
        self.assertTrue(discover_binary_paths(cnf,Counter())['removed'])
        self.assertEqual(discover_binary_paths(cnf,Counter(),root_limit=0),empty)

    def test_integrated_tiny_and_random_models(self):
        h=BinaryPathInventory(max_depth=1);rng=random.Random(202611091621)
        for _ in range(65):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4)))) for _ in range(18)]
            r=h.inspect(source);check_tree(h,r['root']['key'])
        h.close()

    def test_cold_reuse_corruption_and_old_rows(self):
        source=json.loads(Path('experiments/results/cnf-polarity-horn/report.json').read_text())['frontiers']['polarity'][1]['cnf']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=PolarityHornInventory(path,max_depth=0);old.inspect(source)
            saved=dict(old.db.execute('SELECT id,payload FROM cnf_patterns_v1'));old.close()
            h=BinaryPathInventory(path,max_depth=0);r=h.inspect(source);node=h._load(r['root']['key'])
            self.assertEqual(node['kind'],'binary_paths')
            for key,payload in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()[0],payload)
            h.close();raw=path.read_bytes();h=BinaryPathInventory(path,max_depth=0)
            with patch('experiments.cnf_binary_paths.discover_binary_paths',side_effect=AssertionError('new reachability')):
                again=h.inspect(source)
            self.assertEqual(again['metrics'].get('inserted_nodes',0),0);h.close();self.assertEqual(path.read_bytes(),raw)
            node['binary_paths']['proof'][-1][-1]=999999
            h=BinaryPathInventory(path,max_depth=0)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),r['root']['key']))
            with self.assertRaises(ValueError):h.inspect(source)
            h.close()
