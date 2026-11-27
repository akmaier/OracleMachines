from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_selective_width_buckets as k
from experiments.cnf_selective_width_panel import panel
from experiments.cnf_fresh_seed_panel import truth
from experiments.compare_cnf_pair_feedback_buckets import oracle

PARENT=Path('experiments/results/cnf-pair-feedback-buckets')
REMAINING=json.loads((PARENT/'remaining.json').read_text())['cases']
PROFILE=json.loads((PARENT/'leaf-width-comparison.json').read_text())['records']
ROW=next(r for r in PROFILE if r['id']=='d-k14')
OLD=json.loads(Path(ROW['one_round_proof']['path']).read_text())['nodes'][ROW['node']]['refinement']['terminal']['nodes'][-1]['bucket']
SOURCE=ROW['source']


class SelectiveWidthTests(unittest.TestCase):
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

    def test_random_small_with_tiny_quotas(self):
        rng=random.Random(2711271520)
        for _ in range(100):
            n=rng.randrange(3,9);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            self.checked(source,bag_limit=1,depth_limit=0,probe_limit=1,continuation_limit=1,pair_limit=8,learn_limit=2)

    def test_resume_equals_restart_and_preserves_prefix(self):
        before=deepcopy(OLD);a=Counter();b=Counter()
        ext,diag,got=k.continuation.discover(SOURCE,OLD,a,mode='resume')
        other,od,og=k.continuation.discover(SOURCE,OLD,b,mode='restart')
        self.assertEqual((ext,diag,got),(other,od,og));self.assertEqual(OLD,before)
        self.assertTrue(got['answer']);self.assertGreater(a['widen_reused_projection_steps'],0)
        self.assertEqual(a['widen_reused_projection_steps'],b['widen_repeated_projection_steps']);self.assertLess(a['bucket_projected_rows'],b['bucket_projected_rows'])

    def test_work_allowance_includes_original_prefix(self):
        prefix=deepcopy(OLD);cnf,_=k.native.normalize(SOURCE)
        _,_,spent=k.continuation.materialize(cnf,prefix['steps'],Counter());self.assertGreater(spent,0)
        extension,_,_=k.continuation.discover(SOURCE,prefix)
        prefix['limits']['work_limit']=spent
        ext,diag,got=k.continuation.discover(SOURCE,prefix)
        self.assertEqual(diag['reason'],'row-work');self.assertEqual(ext['steps'],[]);self.assertIsNone(got['answer'])
        with self.assertRaises(ValueError):k.continuation.check(SOURCE,prefix,extension)

    def test_changed_source_rejected(self):
        ext,_,_=k.continuation.discover(SOURCE,OLD)
        with self.assertRaises(ValueError):k.continuation.check(SOURCE+[[999999]],OLD,ext)

    def test_changed_steps_and_choices_rejected(self):
        ext,_,_=k.continuation.discover(SOURCE,OLD)
        for mutate in (lambda x:x['steps'][0]['inputs'].append(9999),lambda x:x['steps'][0].__setitem__('bits',x['steps'][0]['bits']^1),lambda x:x['steps'][0].__setitem__('choices',x['steps'][0]['choices']^1),lambda x:x['steps'].insert(0,deepcopy(OLD['steps'][0]))):
            bad=deepcopy(ext);mutate(bad)
            with self.assertRaises(ValueError):k.continuation.check(SOURCE,OLD,bad)

    def test_leaf_admission_before_materialization(self):
        source=[list(range(1,11))];prefix,_=k.bucket.discover(source,bag_limit=8);c=Counter()
        ext,diag,got=k.continuation.discover(source,prefix,c)
        self.assertEqual(diag['reason'],'leaf-width');self.assertIsNone(got['answer']);self.assertEqual(c['widen_materialized_leaf_rows'],0)

    def test_newly_admitted_wide_leaf(self):
        source=[list(range(1,10))];prefix,_=k.bucket.discover(source,bag_limit=8)
        ext,diag,got=k.continuation.discover(source,prefix);self.assertTrue(got['answer']);self.assertTrue(k.native.holds(source,got['model']));self.assertEqual(diag['reason'],'complete')

    def test_random_bucket_continuation_equivalence(self):
        rng=random.Random(2711271521)
        for _ in range(80):
            source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,9),3)] for _ in range(24)]
            p,_=k.bucket.discover(source,bag_limit=3,work_limit=2048)
            if p['status']!='unresolved':continue
            a=k.continuation.discover(source,p,mode='resume');b=k.continuation.discover(source,p,mode='restart');self.assertEqual(a,b)
            if a[2]['answer'] is not None:self.assertEqual(a[2]['answer'],truth(source)['answer'])

    def test_three_exposed_sat_roots(self):
        for row in REMAINING:
            if row['id'] not in ('d-k14','d-k15','f03'):continue
            for mode in ('one','two'):
                p,_=self.checked(row['source'],mode=mode);self.assertEqual(p['status'],'sat')

    def test_remaining_interaction_is_unknown(self):
        for row in REMAINING:
            if row['id'] not in ('d-d-j06','d-k09'):continue
            p,_=self.checked(row['source'],mode='two');self.assertEqual(p['status'],'unresolved')

    def test_restart_and_resume_root_certificates_match(self):
        row=next(r for r in REMAINING if r['id']=='d-k14');a,_=k.discover(row['source'],mode='one');b,_=k.discover(row['source'],mode='restart');b['mode']='one';self.assertEqual(a,b)

    def test_cold_check_has_no_acquisition(self):
        row=next(r for r in REMAINING if r['id']=='d-k14');p,_=k.discover(row['source'])
        with patch.object(k.continuation,'discover',side_effect=AssertionError('widen')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')),patch.object(k.bucket,'project',side_effect=AssertionError('project')),patch.object(k.joint,'discover',side_effect=AssertionError('pair')):
            self.assertTrue(k.check_certificate(row['source'],json.loads(json.dumps(p)))['answer'])

    def test_changed_refinement_policy_and_suffix_rejected(self):
        row=next(r for r in REMAINING if r['id']=='d-k14');p,_=k.discover(row['source']);i=next(i for i,n in enumerate(p['nodes']) if n['refinement'] and n['refinement']['widen'] is not None)
        for mutate in (lambda q:q['nodes'][i]['refinement'].__setitem__('widen',None),lambda q:q['nodes'][i]['refinement']['widen'].__setitem__('model',[]),lambda q:q['nodes'][i]['refinement']['rounds'][0]['terminal']['limits'].__setitem__('bag_limit',9)):
            bad=deepcopy(p);mutate(bad)
            with self.assertRaises(ValueError):k.check_certificate(row['source'],bad)

    def test_sparse_signed_model_transport(self):
        row=next(r for r in REMAINING if r['id']=='d-k14');source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(71*abs(l)+17) for l in c] for c in row['source']];self.checked(source)

    def test_policy_and_pair_limits(self):
        for opts in (dict(mode='feedback'),dict(bag_limit=12),dict(pair_limit=True),dict(extra_width=1)):
            with self.assertRaises(ValueError):k.discover([[1,2]],**opts)
        for mode in ('one','two'):
            c=Counter();k.discover(REMAINING[0]['source'],c,mode=mode);self.assertLessEqual(c['pair_attempts'],4*256*(2 if mode=='two' else 1))

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-selective-width-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
