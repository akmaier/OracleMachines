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
from experiments.cnf_obstruction_choices import ObstructionChoicesInventory, obstruction_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory, discover_polarity, check_polarity
from experiments.cnf_residual_dag import normalize, restrict
from solver.test_cnf_polarity_horn import check_tree


def frontier():
    return json.loads(Path('experiments/results/cnf-polarity-horn/report.json').read_text())['frontiers']['polarity']


def guarded_obstruction():
    # All four pairs refute renamability of two variables. Opposite guards add
    # another way of affecting the obstruction: whole source-clause deletion.
    core = [(1,2), (1,-2), (-1,2), (-1,-2)]
    return [(*c,3) for c in core]+[(*c,-3) for c in core]


class ObstructionChoiceTests(unittest.TestCase):
    def test_all_saved_frontier_choices_are_checked_and_bounded(self):
        for row in frontier():
            cnf = row['cnf']; proof = row['polarity']; counts = Counter()
            check_polarity(cnf, proof, counts)
            for limit in (0,1,4,64):
                choices = obstruction_choices(cnf, proof, limit, counts)
                self.assertEqual(len(choices),min(limit,len({abs(l) for c in cnf for l in c})))
                self.assertEqual(len(choices),len(set(choices)))
                self.assertEqual(choices,obstruction_choices(cnf,proof,limit,Counter()))
            with patch('experiments.cnf_polarity_horn.two_cnf',side_effect=AssertionError('rediscovery')):
                obstruction_choices(cnf,proof,4,Counter())

    def test_guard_support_is_not_only_pair_endpoints(self):
        cnf = guarded_obstruction()
        # Explicit shortest auxiliary contradiction uses pair endpoints 1 and 2
        # only; variable 3 still occurs in every supporting source clause.
        proof = dict(outcome='excluded',pairs=24,variable=1,
                     forward=[[2,2,0,1],[-1,3,0,1]],backward=[[2,0,0,1],[1,1,0,1]])
        check_polarity(cnf,proof,Counter())
        counts = Counter(); choices = obstruction_choices(cnf,proof,3,counts)
        self.assertIn(3,choices); self.assertEqual(counts['obstruction_rank_variables'],3)
        # A one-sided guard actually removes every original obstruction clause.
        one_side=cnf[:4]; one_proof=dict(proof,pairs=12)
        check_polarity(one_side,one_proof,Counter())
        target,_=normalize(restrict(one_side,{3:True},Counter()))
        self.assertIsNotNone(check_polarity(target,discover_polarity(target,Counter()),Counter()))

    def test_untouched_obstruction_survives_direct_restriction(self):
        # An extra independent variable does not change the witness clauses.
        for row in frontier()[:12]:
            source = row['cnf']; proof = row['polarity']; v=max(abs(l) for c in source for l in c)+1
            for value in (False,True):
                changed=restrict(source+[(v,)],{v:value},Counter())
                # Do not collapse an empty clause into terminal false: this
                # assertion concerns raw syntactic renamability only.
                certificate=discover_polarity(changed,Counter())
                self.assertEqual(certificate['outcome'],'excluded')
                check_polarity(changed,certificate,Counter())

    def test_fallback_and_bad_proofs(self):
        for cnf,cap in ((((1,2,3),),0), (((-1,2),),65536), ((),65536)):
            proof=discover_polarity(cnf,Counter(),pair_limit=cap)
            self.assertEqual(obstruction_choices(cnf,proof,4,Counter(),pair_limit=cap),
                             shortest_balanced_choices(cnf,4,Counter()))
        row=frontier()[0]; bad=copy.deepcopy(row['polarity']);bad['forward'][0][1]=99999
        with self.assertRaises(ValueError):obstruction_choices(row['cnf'],bad,4,Counter())
        for limit in (-1,True,1.5):
            with self.assertRaises(ValueError):obstruction_choices(row['cnf'],row['polarity'],limit,Counter())

    def test_tiny_and_random_decomposition_models(self):
        h=ObstructionChoicesInventory(max_depth=1)
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(512):
            r=h.inspect([c for i,c in enumerate(clauses) if mask>>i&1]);check_tree(h,r['root']['key'])
        rng=random.Random(202611091530)
        for _ in range(30):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3)) for _ in range(20)]
            for changed in (source,source+[(1,)],source[:-1]):
                r=h.inspect(changed);check_tree(h,r['root']['key'])
                self.assertIsNone(h._obstruction_context)
        h.close()

    def test_cold_evidence_reuse_and_corruption(self):
        source=frontier()[0]['cnf']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'store.db';old=PolarityHornInventory(path,max_depth=1)
            before=old.inspect(source);saved=dict(old.db.execute('SELECT id,payload FROM cnf_patterns_v1'));old.close()
            h=ObstructionChoicesInventory(path,max_depth=1);result=h.inspect(source)
            for k,v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            self.assertNotEqual(before['root']['key'],result['root']['key'])
            found=next((k,json.loads(p)) for k,p in h.db.execute('SELECT id,payload FROM cnf_patterns_v1') if 'conditioning_obstruction' in json.loads(p))
            key,node=found;h.close();raw=path.read_bytes()
            h=ObstructionChoicesInventory(path,max_depth=1)
            # Proof replay must not solve the auxiliary 2-CNF again.
            with patch('experiments.cnf_obstruction_choices.discover_polarity',side_effect=AssertionError('rediscovery')):
                again=h.inspect(source)
            self.assertEqual(again['metrics'].get('inserted_nodes',0),0);h.close();self.assertEqual(path.read_bytes(),raw)
            mutations=[]
            bad=copy.deepcopy(node);del bad['conditioning_obstruction'];mutations.append(bad)
            bad=copy.deepcopy(node);bad['conditioning_obstruction']['pairs']+=1;mutations.append(bad)
            bad=copy.deepcopy(node);bad['alternatives'][0]['variable']+=1000;mutations.append(bad)
            for bad in mutations:
                path.write_bytes(raw);h=ObstructionChoicesInventory(path,max_depth=1)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
                with self.assertRaises(ValueError):h.inspect(source)
                self.assertIsNone(h._obstruction_context);h.close()

    def test_capped_policy_reproduces_previous_choices_and_coverage(self):
        old=PolarityHornInventory(max_depth=1,polarity_pair_limit=0)
        new=ObstructionChoicesInventory(max_depth=1,polarity_pair_limit=0)
        for row in frontier()[:10]:
            a=old.inspect(row['cnf']);b=new.inspect(row['cnf'])
            self.assertEqual(a['summary'],b['summary'])
        old.close();new.close()
