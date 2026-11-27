from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,threading,unittest
from experiments import cnf_verified_operators as v
from experiments import cnf_selective_width_buckets as k
from experiments.cnf_fresh_seed_panel import truth


class VerifiedOperatorTests(unittest.TestCase):
    def setUp(self):
        self.source=[[-1,2],[1,2],[-2,3],[2,-3]]
        self.proof,_=v.bucket.discover(self.source)

    def test_exhaustive_two_variable_sources(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        bank=v.VerifiedOperators()
        for mask in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];proof,_=v.bucket.discover(source)
            got=v.check_certificate(source,proof,session=bank)
            self.assertEqual(got,v.LEGACY_CHECK(source,proof));self.assertEqual(got['answer'],truth(source)['answer'])

    def test_random_small_projection_programs(self):
        rng=random.Random(2711271657);bank=v.VerifiedOperators()
        for _ in range(120):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            proof,_=v.bucket.discover(source,bag_limit=rng.choice((2,3,5,8)))
            got=v.check_certificate(source,proof,session=bank)
            self.assertEqual(got,v.LEGACY_CHECK(source,proof))
            if got['answer'] is not None:self.assertEqual(got['answer'],truth(source)['answer'])

    def test_hit_avoids_rows_but_not_step_checks(self):
        bank=v.VerifiedOperators();a=Counter();b=Counter()
        v.check_certificate(self.source,self.proof,a,session=bank);v.check_certificate(self.source,self.proof,b,session=bank)
        self.assertGreater(a['bucket_verified_rows'],0);self.assertEqual(b['bucket_verified_rows'],0)
        self.assertEqual(b['verified_operator_hits'],len(self.proof['steps']));self.assertEqual(b['bucket_checked_steps'],len(self.proof['steps']))

    def test_hit_rejects_changed_bits_and_choices(self):
        bank=v.VerifiedOperators();v.check_certificate(self.source,self.proof,session=bank)
        for field in ('bits','choices'):
            proof=deepcopy(self.proof);proof['steps'][0][field]^=1
            with self.assertRaises(ValueError):v.check_certificate(self.source,proof,session=bank)

    def test_hit_rejects_incomplete_incident_bucket(self):
        bank=v.VerifiedOperators();v.check_certificate(self.source,self.proof,session=bank)
        proof=deepcopy(self.proof);proof['steps'][0]['inputs'].pop()
        with self.assertRaises(ValueError):v.check_certificate(self.source,proof,session=bank)

    def test_changed_source_rejected(self):
        bank=v.VerifiedOperators();v.check_certificate(self.source,self.proof,session=bank)
        with self.assertRaises(ValueError):v.check_certificate(self.source+[[4]],self.proof,session=bank)

    def test_hit_still_checks_root_witness(self):
        bank=v.VerifiedOperators();v.check_certificate(self.source,self.proof,session=bank)
        proof=deepcopy(self.proof);proof['model']=[False]*len(proof['model'])
        with self.assertRaises(ValueError):v.check_certificate(self.source,proof,session=bank)

    def test_failed_step_does_not_seed_bank(self):
        bank=v.VerifiedOperators();bad=deepcopy(self.proof);bad['steps'][0]['bits']^=1
        with self.assertRaises(ValueError):v.check_certificate(self.source,bad,session=bank)
        self.assertEqual(bank.stats()['entries'],0)
        self.assertEqual(v.check_certificate(self.source,self.proof,session=bank),v.LEGACY_CHECK(self.source,self.proof))

    def test_mutating_old_certificate_does_not_mutate_key(self):
        bank=v.VerifiedOperators();proof=deepcopy(self.proof);v.check_certificate(self.source,proof,session=bank)
        proof['steps'][0]['scope'].append(999)
        c=Counter();v.check_certificate(self.source,self.proof,c,session=bank);self.assertEqual(c['bucket_verified_rows'],0)
        with self.assertRaises(ValueError):v.check_certificate(self.source,proof,session=bank)

    def test_local_order_embedding_reuses_nonconstant_operator(self):
        bank=v.VerifiedOperators();c=Counter()
        # Force the same exact nonconstant projection at different variable
        # ranks. The greedy discovery order would eliminate degree-one leaves
        # first and produce constants, so this is a checked partial program.
        for source,pivot in (([[1,2],[-1,3]],1),([[1],[2,3],[-2,4]],2)):
            proof,_=v.bucket.discover(source);proof['status']='unresolved';proof['model']=None
            proof['steps']=[dict(variable=pivot,inputs=[i for i,clause in enumerate(proof['cnf']) if pivot in map(abs,clause)],scope=[pivot+1,pivot+2],bits=14,choices=4)]
            self.assertIsNone(v.LEGACY_CHECK(source,proof)['answer'])
            v.check_certificate(source,proof,c,session=bank)
        self.assertEqual(c['verified_operator_saved_nonconstant_rows'],4)

    def test_entry_and_byte_caps_only_affect_reuse(self):
        for opts in (dict(max_entries=0),dict(max_bytes=0),dict(max_entries=1),dict(max_bytes=1000)):
            bank=v.VerifiedOperators(**opts)
            for _ in range(2):self.assertEqual(v.check_certificate(self.source,self.proof,session=bank),v.LEGACY_CHECK(self.source,self.proof))
            stats=bank.stats();self.assertLessEqual(stats['entries'],stats['max_entries']);self.assertLessEqual(stats['key_bytes'],stats['max_bytes'])

    def test_new_session_is_cold(self):
        for _ in range(2):
            c=Counter();v.check_certificate(self.source,self.proof,c,session=v.VerifiedOperators());self.assertGreater(c['bucket_verified_rows'],0)

    def test_installed_hook_restores_after_error_and_rejects_nesting(self):
        with self.assertRaises(ValueError):
            with v.installed(v.VerifiedOperators()):
                with self.assertRaises(RuntimeError):
                    with v.installed(None):pass
                raise ValueError('test')
        self.assertIs(v.bucket.check_certificate,v.LEGACY_CHECK)

    def test_hook_rejects_background_execution(self):
        errors=[]
        def run():
            try:
                with v.installed(None):pass
            except RuntimeError:errors.append(True)
        t=threading.Thread(target=run);t.start();t.join();self.assertEqual(errors,[True])

    def test_invalid_bounds_and_wide_leaf_admission(self):
        for opts in (dict(max_entries=True),dict(max_bytes=-1)):
            with self.assertRaises(ValueError):v.VerifiedOperators(**opts)
        source=[list(range(1,15))];proof,_=v.bucket.discover(source)
        with patch.object(v,'leaf',side_effect=AssertionError('wide table')):self.assertIsNone(v.check_certificate(source,proof,session=v.VerifiedOperators())['answer'])

    def test_full_root_cold_replay_without_discovery(self):
        out=Path('experiments/results/cnf-selective-width-buckets');row=next(r for r in json.loads((out/'panel.json').read_text()) if r['id']=='d-d-k14')
        report=json.loads((out/'two-0/report.json').read_text());root=k.native.token(k.native.normalize(row['source'])[0],Counter());proof=json.loads((out/'two-0'/report['stored'][root]).read_text());expected=k.check_certificate(row['source'],proof)
        with patch.object(k,'discover',side_effect=AssertionError('root discovery')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket discovery')),patch.object(k.bucket,'project',side_effect=AssertionError('projection')):
            with v.installed(v.VerifiedOperators()):
                for _ in range(2):self.assertEqual(k.check_certificate(row['source'],proof),expected)


if __name__=='__main__':unittest.main()
