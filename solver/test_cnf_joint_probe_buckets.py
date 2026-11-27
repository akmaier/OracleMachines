from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_joint_probe_buckets as k
from experiments.cnf_joint_probe_panel import hidden_pair,panel
from experiments.cnf_fresh_seed_panel import truth
from experiments.compare_cnf_selective_probes import oracle

REMAINING=json.loads(Path('experiments/results/cnf-selective-probes/remaining.json').read_text())['cases'][:4]


class JointProbeTests(unittest.TestCase):
    def checked(self,source,**options):
        p,d=k.discover(source,**options);got=k.check_certificate(source,p)
        if got['answer'] is not None:
            expected=truth(source) if len({abs(l) for c in source for l in c})<=8 else oracle(source)
            self.assertEqual(got['answer'],expected['answer'])
            if got['answer']:self.assertTrue(k.native.holds(source,got['model']))
        return p,d

    def test_exhaustive_two_variable_formulas(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1];cnf,_=k.native.normalize(source)
            ev,_=k.joint.discover(cnf);learned=k.joint.check(cnf,ev)
            for a in product((False,True),repeat=2):
                model=dict(enumerate(a,1))
                if k.native.holds(cnf,model):self.assertTrue(k.native.holds(learned,model))
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=1)

    def test_random_small_with_tiny_quotas(self):
        rng=random.Random(2711271317)
        for _ in range(100):
            n=rng.randrange(3,9);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            self.checked(source,bag_limit=1,depth_limit=0,probe_limit=2,continuation_limit=2,pair_limit=8,learn_limit=3)

    def test_binary_consequence_without_single_failure(self):
        cnf,_=k.native.normalize(hidden_pair(0));idx=k.probes.prepare_index(cnf,Counter())
        for v in range(1,7):
            for l in (v,-v):self.assertIsNone(k.probes.indexed_probe(cnf,l,idx,Counter()))
        ev,_=k.joint.discover(cnf);clauses=k.joint.check(cnf,ev)
        self.assertIn((-2,-1),clauses)

    def test_deleting_conflict_removes_target_consequence(self):
        cnf,_=k.native.normalize(hidden_pair(0)[:-1]);ev,_=k.joint.discover(cnf)
        self.assertNotIn((-2,-1),k.joint.check(cnf,ev))

    def test_restart_and_shared_evidence_identical(self):
        cnf,_=k.native.normalize(hidden_pair(0));a=Counter();b=Counter()
        p,d=k.joint.discover(cnf,a,mode='restart');q,e=k.joint.discover(cnf,b,mode='shared')
        self.assertEqual((p,d),(q,e));self.assertLess(b['pair_prefix_builds'],a['pair_prefix_builds']);self.assertGreater(b['pair_prefix_hits'],0)
        self.assertEqual(a['pair_copied_state_entries'],b['pair_copied_state_entries'])

    def test_prefix_state_does_not_change_across_extensions(self):
        cnf,_=k.native.normalize(hidden_pair(0));c=Counter();idx=k.probes.prepare_index(cnf,c);state=k.joint.prefix(cnf,idx,1,c);before=deepcopy(state)
        for b in (2,-2,3,-3):k.joint.extend(cnf,idx,state,b,c);self.assertEqual(state,before)

    def test_clashing_second_assumption_is_checked(self):
        cnf=((-1,2),);ev=dict(prefixes=[dict(assumption=1,trace=[[2,0]],conflict=None)],clauses=[dict(prefix=0,second=-2,trace=[],conflict='assumption')])
        # Existing clauses are rejected; add a third-variable implication chain.
        cnf=((-2,3),(-1,2));ev['prefixes'][0]['trace']=[[2,1],[3,0]];ev['clauses'][0]['second']=-3
        self.assertEqual(k.joint.check(cnf,ev),((-1,3),))
        bad=deepcopy(ev);bad['clauses'][0]['second']=3
        with self.assertRaises(ValueError):k.joint.check(cnf,bad)

    def test_conflicting_prefix_proves_redundant_binary_clause(self):
        cnf=((-1,), (2,3));ev,_=k.joint.discover(cnf)
        self.assertTrue(any(h['conflict'] is not None for h in ev['prefixes']));k.joint.check(cnf,ev)

    def test_corrupt_or_unused_pair_evidence_rejected(self):
        cnf,_=k.native.normalize(hidden_pair(0));ev,_=k.joint.discover(cnf)
        for change in (lambda q:q['clauses'][0].__setitem__('prefix',999),lambda q:q['clauses'][0].__setitem__('second',0),lambda q:q['prefixes'][0].__setitem__('assumption',True),lambda q:q['prefixes'].append(deepcopy(q['prefixes'][0])),lambda q:q['clauses'].append(deepcopy(q['clauses'][0]))):
            bad=deepcopy(ev);change(bad)
            with self.assertRaises(ValueError):k.joint.check(cnf,bad)
        with self.assertRaises(ValueError):k.joint.check(cnf,ev,learn_limit=1)

    def test_base_and_width_controls_translate(self):
        for row in REMAINING:
            for bag in (8,9):
                p,_=k.discover(row['source'],mode='base',bag_limit=bag);q,_=k.prior.discover(row['source'],mode='restart',bag_limit=bag)
                p['format']=q['format'];p['mode']='restart';p['limits'].pop('pair_limit');p['limits'].pop('learn_limit')
                for n in p['nodes']:self.assertIsNone(n.pop('refinement'))
                self.assertEqual(p,q)

    def test_exposed_sat_and_unsat_roots_close(self):
        for i,expected in ((0,'sat'),(3,'unsat')):
            p,_=self.checked(REMAINING[i]['source']);self.assertEqual(p['status'],expected)
            q,_=k.discover(REMAINING[i]['source'],mode='restart');q['mode']='shared';self.assertEqual(p,q)

    def test_unknown_stays_unknown(self):
        for row in REMAINING[1:3]:
            p,_=self.checked(row['source']);self.assertEqual(p['status'],'unresolved')

    def test_cold_replay_has_no_acquisition(self):
        source=REMAINING[0]['source'];p,_=k.discover(source)
        with patch.object(k.joint,'discover',side_effect=AssertionError('pair')),patch.object(k.prior,'discover',side_effect=AssertionError('terminal')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')),patch.object(k.joint,'prefix',side_effect=AssertionError('prefix')):
            self.assertTrue(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_source_and_refinement_corruption_rejected(self):
        source=REMAINING[0]['source'];p,_=k.discover(source);i=next(i for i,n in enumerate(p['nodes']) if n['refinement'])
        for change in (lambda q:q['nodes'][i]['refinement'].__setitem__('evidence',{}),lambda q:q['nodes'][i]['refinement']['terminal']['limits'].__setitem__('depth_limit',1),lambda q:q.__setitem__('mode','base')):
            bad=deepcopy(p);change(bad)
            with self.assertRaises(ValueError):k.check_certificate(source,bad)
        with self.assertRaises(ValueError):k.check_certificate(source+[[1]],p)

    def test_signed_sparse_model_transport(self):
        source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(29*abs(l)+13) for l in c] for c in REMAINING[0]['source']]
        self.checked(source)

    def test_policy_bounds(self):
        for args in (dict(pair_limit=0),dict(learn_limit=True),dict(mode='other'),dict(unexpected=2)):
            with self.assertRaises(ValueError):k.discover([[1,2]],**args)
        c=Counter();k.discover(REMAINING[0]['source'],c)
        self.assertLessEqual(c['pair_attempts'],4*256);self.assertLessEqual(c['pair_learned_clauses'],4*32)

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-joint-probe-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
