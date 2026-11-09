from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_probe_rank import ProbeRankInventory, choices_after_checked_probes
from solver.test_cnf_polarity_horn import check_tree


def frontier():
    return json.loads(Path('experiments/results/cnf-polarity-horn/report.json').read_text())['frontiers']['polarity']


class ProbeRankTests(unittest.TestCase):
    def test_promotion_preserves_candidates_and_unknown_order(self):
        cnf = ((1, 2, 3, 4), (-1, -2, -3, -4))
        # Metadata-only ranking unit test: this internal helper assumes checked
        # proofs. Integration tests below exercise actual source-bound proofs.
        def attempt(v, b, n):
            return dict(variable=v, value=b, certificate=dict(units=[[10+i, i] for i in range(n)]))
        probing = dict(status='clear', attempts=[attempt(2,False,1),attempt(2,True,3),
                                               attempt(3,False,0),attempt(3,True,9)])
        counts = Counter()
        self.assertEqual(choices_after_checked_probes(cnf,probing,4,counts),[2,1,3,4])
        self.assertEqual(counts['probe_rank_unknown_candidates'],2)
        for limit in (0,1,2,4,8):
            before=shortest_balanced_choices(cnf,limit,Counter())
            after=choices_after_checked_probes(cnf,probing,limit,Counter())
            self.assertEqual(set(before),set(after));self.assertEqual(len(before),len(after))
        for status in ('skipped','forced','common','equivalence','learned'):
            self.assertEqual(choices_after_checked_probes(cnf,dict(status=status),4,Counter()),[1,2,3,4])
        # A continuation's larger effects must not be used as original proofs.
        probing['status']='learning_clear'
        probing['continuation']=dict(attempts=[attempt(4,False,100),attempt(4,True,100)])
        self.assertEqual(choices_after_checked_probes(cnf,probing,4,Counter()),[2,1,3,4])

    def test_all_frontier_closures_and_original_choices_preserved(self):
        old=PolarityHornInventory(max_depth=1);new=ProbeRankInventory(max_depth=1)
        changed=0
        for row in frontier():
            a=old.inspect(row['cnf']);b=new.inspect(row['cnf'])
            self.assertEqual(a['summary']['closed'],b['summary']['closed'])
            self.assertEqual(a['profile'],b['profile'])
            changed+=b['metrics'].get('probe_rank_changed_lists',0)
            self.assertIsNone(new._probe_rank_context)
        self.assertGreater(changed,0)
        for payload, in new.db.execute('SELECT payload FROM cnf_patterns_v1'):
            n=json.loads(payload)
            if n['kind']=='or':
                expected=choices_after_checked_probes(n['cnf'],n['profile']['probing'],4,Counter())
                self.assertEqual(set(expected),set(shortest_balanced_choices(n['cnf'],4,Counter())))
                self.assertEqual([a['variable'] for a in n['alternatives']],expected[:len(n['alternatives'])])
        old.close();new.close()

    def test_tiny_models_and_fresh_mixtures_at_depth_two(self):
        old=PolarityHornInventory(max_depth=2);new=ProbeRankInventory(max_depth=2)
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        cases=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
        rng=random.Random(202611091700)
        for _ in range(16):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4)))) for _ in range(20)]
            flips={v:rng.choice((-1,1)) for v in range(1,7)}
            signed=[tuple(l*flips[abs(l)] for l in c) for c in source]
            cases.extend([source,signed,source+[(1,)],source[:-1],source+[(1,-1)]])
        for cnf in cases:
            a=old.inspect(cnf);b=new.inspect(cnf)
            self.assertEqual(a['summary']['closed'],b['summary']['closed'])
            check_tree(new,b['root']['key'])
        old.close();new.close()

    def test_cold_trace_checks_no_rediscovery_and_corruption(self):
        sources=[frontier()[i]['cnf'] for i in (4,17,50)]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=PolarityHornInventory(path,max_depth=1)
            for source in sources:old.inspect(source)
            saved=dict(old.db.execute('SELECT id,payload FROM cnf_patterns_v1'));old.close()
            new=ProbeRankInventory(path,max_depth=1)
            for source in sources:new.inspect(source)
            for k,v in saved.items():self.assertEqual(new.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            key,node=next((k,json.loads(p)) for k,p in new.db.execute('SELECT id,payload FROM cnf_patterns_v1')
                          if 'conditioning_probe_rank' in k and json.loads(p)['kind']=='or'
                          and any(a['certificate']['units'] for a in json.loads(p)['profile']['probing'].get('attempts',[])))
            new.close();raw=path.read_bytes();new=ProbeRankInventory(path,max_depth=1)
            with patch.object(new,'_discover_probes',side_effect=AssertionError('new propagation')), \
                 patch('experiments.cnf_polarity_horn.discover_polarity',side_effect=AssertionError('new SCC')):
                for source in sources:
                    r=new.inspect(source);self.assertEqual(r['metrics'].get('inserted_nodes',0),0)
            new.close();self.assertEqual(path.read_bytes(),raw)
            mutations=[]
            bad=copy.deepcopy(node)
            attempt=next(a for a in bad['profile']['probing']['attempts'] if a['certificate']['units'])
            attempt['certificate']['units'][0][1]=999999;mutations.append(bad)
            bad=copy.deepcopy(node);bad['alternatives'][0]['variable']+=10000;mutations.append(bad)
            for bad in mutations:
                path.write_bytes(raw);new=ProbeRankInventory(path,max_depth=1)
                with new.db:new.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
                with self.assertRaises(ValueError):new._load(key)
                self.assertIsNone(new._probe_rank_context);new.close()

    def test_scope_restores_on_error_and_disallows_unbound_ranking(self):
        h=ProbeRankInventory();cnf=((1,2),);p=dict(probing=dict(status='skipped'))
        with self.assertRaises(ValueError):h._choices(cnf)
        with h._rank_scope(cnf,p):
            original=h._probe_rank_context
            with self.assertRaises(RuntimeError):
                with h._rank_scope((),p):raise RuntimeError('nested failure')
            self.assertIs(h._probe_rank_context,original)
        self.assertIsNone(h._probe_rank_context);h.close()
