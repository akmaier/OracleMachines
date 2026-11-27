from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_pair_feedback_buckets as k
from experiments import cnf_joint_probe_buckets as previous
from experiments.cnf_pair_feedback_panel import panel
from experiments.cnf_fresh_seed_panel import truth
from experiments.compare_cnf_joint_probe_buckets import oracle

REMAINING=json.loads(Path('experiments/results/cnf-joint-probe-buckets/remaining.json').read_text())['cases']


class PairFeedbackTests(unittest.TestCase):
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
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=1)

    def test_random_small_feedback_semantics(self):
        rng=random.Random(2711271417)
        for _ in range(120):
            n=rng.randrange(3,9);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            p,_=self.checked(source,bag_limit=1,depth_limit=0,probe_limit=1,continuation_limit=1,pair_limit=16,learn_limit=4)
            for node in p['nodes']:
                ref=node['refinement']
                if ref is None:continue
                current=tuple(map(tuple,node['cnf']))
                for rnd in ref['rounds']:
                    learned=k.joint.check(current,rnd['evidence'],pair_limit=16,learn_limit=4)
                    for bits in product((False,True),repeat=len({abs(l) for c in current for l in c})):
                        model=dict(enumerate(bits,1))
                        if k.native.holds(current,model):self.assertTrue(k.native.holds(learned,model))
                    augmented=k.relations.clean_quotient(current+learned,Counter())
                    terminal=rnd['terminal'];k.prior.check_certificate(augmented,terminal)
                    if terminal['status']=='unresolved':current,_=k.terminal_transport(augmented,terminal,Counter())

    def test_one_round_controls_are_exact_previous_programs(self):
        for row in REMAINING:
            for mode,multiplier in (('base',1),('larger',2)):
                p,_=k.discover(row['source'],mode=mode)
                q,_=previous.discover(row['source'],mode='shared',pair_limit=256*multiplier,learn_limit=32*multiplier)
                p['format']=q['format'];p['mode']=q['mode'];p['limits']=q['limits']
                for n in p['nodes']:
                    if n['refinement'] is not None:n['refinement']=n['refinement']['rounds'][0]
                self.assertEqual(p,q)

    def test_three_exposed_sat_roots_lift(self):
        for row in REMAINING:
            if row['id'] not in ('d-j07','k16','k17'):continue
            p,_=self.checked(row['source']);self.assertEqual(p['status'],'sat')
            self.assertTrue(any(n['refinement'] and len(n['refinement']['rounds'])==2 for n in p['nodes']))

    def test_remaining_unknown_is_not_certified_by_exhaustion(self):
        row=next(r for r in REMAINING if r['id']=='d-j06')
        p,_=self.checked(row['source']);self.assertEqual(p['status'],'unresolved');self.assertIsNone(p['model'])

    def test_sparse_signed_sources_and_added_equivalences(self):
        row=REMAINING[0];source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(43*abs(l)+7) for l in c] for c in row['source']]
        for extra in ([],[[9999999,-source[0][0]],[-9999999,source[0][0]]]):self.checked(source+extra)

    def test_no_new_clause_stops(self):
        source=((1,2,3),);ref,diag,status,model=k.discover_refinement(source,'feedback',k.DEFAULTS,Counter())
        self.assertIsNone(ref);self.assertEqual(diag['reason'],'no-new-clause');self.assertEqual(len(diag['rounds']),1)

    def test_cold_check_does_not_discover(self):
        source=REMAINING[0]['source'];p,_=k.discover(source)
        with patch.object(k.joint,'discover',side_effect=AssertionError('pair acquisition')),patch.object(k.prior,'discover',side_effect=AssertionError('terminal acquisition')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket acquisition')):
            self.assertTrue(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_feedback_reordering_wrong_source_and_bad_terminal(self):
        source=REMAINING[0]['source'];p,_=k.discover(source)
        idx=next(i for i,n in enumerate(p['nodes']) if n['refinement'] and len(n['refinement']['rounds'])==2)
        def rounds(q):return q['nodes'][idx]['refinement']['rounds']
        changes=[lambda q:rounds(q).reverse(),lambda q:rounds(q).append(deepcopy(rounds(q)[0])),lambda q:rounds(q).__setitem__(1,deepcopy(rounds(q)[0])),lambda q:rounds(q)[1]['terminal']['limits'].__setitem__('depth_limit',1),lambda q:rounds(q)[1]['terminal']['cnf'].append([999999]),lambda q:rounds(q)[1]['evidence']['clauses'][0].__setitem__('prefix',9999),lambda q:q.__setitem__('mode','base')]
        for change in changes:
            bad=deepcopy(p);change(bad)
            with self.assertRaises(ValueError):k.check_certificate(source,bad)
        with self.assertRaises(ValueError):k.check_certificate(source+[[999999]],p)

    def test_empty_and_excess_rounds_rejected(self):
        for ref in ({},{'rounds':[]},{'rounds':[{}]*3},{'rounds':[dict(evidence=dict(prefixes=[],clauses=[]),terminal={})]}):
            with self.assertRaises(ValueError):k.check_refinement(((1,2),),ref,'feedback',k.DEFAULTS,Counter())

    def test_matched_maximum_pair_budget(self):
        for row in REMAINING:
            for mode in k.MODES:
                c=Counter();k.discover(row['source'],c,mode=mode)
                self.assertLessEqual(c['pair_attempts'],4*(256 if mode=='base' else 512))
                self.assertLessEqual(c['pair_learned_clauses'],4*(32 if mode=='base' else 64))

    def test_invalid_policy(self):
        for args in (dict(pair_limit=0),dict(pair_limit=2049),dict(learn_limit=True),dict(mode='shared'),dict(feedback_round_limit=9)):
            with self.assertRaises(ValueError):k.discover([[1,2]],**args)

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-pair-feedback-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
