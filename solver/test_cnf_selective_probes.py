from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_selective_probes as k
from experiments.cnf_selective_probe_panel import panel
from experiments.cnf_fresh_seed_panel import truth
from experiments.compare_cnf_probe_relations import oracle

FRONTIER=json.loads(Path('experiments/results/cnf-probe-relations/frontier-inputs.json').read_text())


class SelectiveProbeTests(unittest.TestCase):
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
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=1,probe_limit=1,continuation_limit=2)

    def test_random_wider_with_small_quotas(self):
        rng=random.Random(2711271218)
        for _ in range(100):
            n=rng.randrange(3,9);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            for mode in ('restart','resume'):self.checked(source,mode=mode,bag_limit=1,probe_limit=3,continuation_limit=5)

    def test_controls_translate_exactly(self):
        for row in FRONTIER:
            for mode in ('base','eager'):
                p,_=k.discover(row['source'],mode=mode);q,_=k.prior.discover(row['source'],probe_limit=128 if mode=='base' else 256)
                p['format']=q['format'];p['mode']='relations';p['limits'].pop('continuation_limit');p['limits']['probe_limit']=q['limits']['probe_limit']
                for e in p['edges']:self.assertFalse(e.pop('continuation'))
                self.assertEqual(p,q)

    def test_known_frontier_and_restart_proof_equality(self):
        for row in FRONTIER:
            p,_=self.checked(row['source']);q,_=k.discover(row['source'],mode='restart');q['mode']='resume'
            self.assertNotEqual(p['status'],'unresolved');self.assertEqual(p,q)

    def test_sparse_signed_source_lifting(self):
        source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(29*abs(l)+13) for l in c] for c in FRONTIER[1]['source']]
        self.checked(source)

    def test_clear_cursor_reuses_exact_index(self):
        cnf=((1,2,3),);c=Counter();records,closed,data,diag,cursor=k.advance(cnf,2,8,k.DEFAULTS,c)
        self.assertFalse(records);self.assertEqual(cursor.offset,2);before=c['probe_index_builds']
        with patch.object(k.probes,'prepare_index',side_effect=AssertionError('rebuild')):
            _,after,_,d,end=k.advance(closed,4,8,k.DEFAULTS,c,cursor)
        self.assertEqual(after,cnf);self.assertEqual(d['reason'],'no-failed-literal');self.assertIsNone(end)
        self.assertEqual(c['probe_index_builds'],before);self.assertEqual(c['continuation_skipped_attempts'],2)

    def test_restart_explicitly_repeats_clear_prefix(self):
        cnf=((1,2,3),);c=Counter();*_,cursor=k.advance(cnf,2,8,k.DEFAULTS,c)
        rebuilt=k.restart_cursor(cursor,c)
        self.assertEqual(c['continuation_repeated_attempts'],2);self.assertIsNot(rebuilt.index,cursor.index)

    def test_changed_source_and_schedule_reject_cursor(self):
        cnf=((1,2,3),);*_,cursor=k.advance(cnf,2,8,k.DEFAULTS,Counter())
        for bad in (k.Cursor(((1,2),),cursor.starts,cursor.offset,cursor.index),k.Cursor(cnf,(9,),cursor.offset,cursor.index),k.Cursor(cnf,cursor.starts,999,cursor.index)):
            with self.assertRaises(ValueError):k.advance(cnf,4,8,k.DEFAULTS,Counter(),bad)

    def test_successful_clear_probes_never_certify_sat(self):
        p,_=self.checked([[1,2,3]],probe_limit=1,continuation_limit=1,bag_limit=1,depth_limit=0)
        self.assertEqual(p['status'],'unresolved');self.assertFalse(p['edges'][0]['continuation'])

    def test_closed_gate_reuses_bucket_result(self):
        c=Counter()
        with patch.object(k.bucket,'discover',wraps=k.bucket.discover) as spy:
            p,_=k.discover([[1,2,3]],c,probe_limit=1,continuation_limit=1,depth_limit=0)
        self.assertEqual(p['status'],'sat');self.assertEqual(spy.call_count,1);self.assertEqual(c['continuation_attempts'],0)

    def test_failed_round_does_not_retain_stale_cursor(self):
        from experiments.cnf_probe_relation_panel import failure
        cnf,_=k.native.normalize(failure(0));records,closed,_,_,cursor=k.advance(cnf,1,8,k.DEFAULTS,Counter())
        self.assertTrue(records);self.assertNotEqual(closed,cnf);self.assertIsNone(cursor)

    def test_extension_corruption_and_source_edit_rejected(self):
        source=FRONTIER[1]['source'];p,_=k.discover(source);i=next(i for i,e in enumerate(p['edges']) if e['continuation'])
        for change in (lambda q:q['edges'][i].__setitem__('continuation',{}),lambda q:q.__setitem__('mode','base'),lambda q:q['edges'][i]['continuation'][0]['failures'][0].__setitem__('assumption',99999),lambda q:q['edges'][i]['continuation'][0].__setitem__('units',[]),lambda q:q['edges'][i].__setitem__('cursor',{})):
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)
        with self.assertRaises(ValueError):k.check_certificate(source+[[1]],p)

    def test_cold_replay_has_no_discovery_or_cursor(self):
        source=FRONTIER[1]['source'];p,_=k.discover(source)
        with patch.object(k,'advance',side_effect=AssertionError('probe')),patch.object(k,'prepare_edge',side_effect=AssertionError('edge')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')),patch.object(k.probes,'prepare_index',side_effect=AssertionError('index')):
            self.assertTrue(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_limits_remain_explicit(self):
        for opts in (dict(continuation_limit=True),dict(continuation_limit=0),dict(probe_limit=512),dict(mode='other'),dict(extra=1)):
            with self.assertRaises(ValueError):k.discover([[1,2]],**opts)
        c=Counter();k.discover(FRONTIER[-1]['source'],c)
        self.assertLessEqual(c['probe_attempts'],7*256)

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-selective-probes')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
