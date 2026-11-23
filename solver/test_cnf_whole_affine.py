from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_whole_affine as policy
from experiments.cnf_affine_probe import bounded_extract
from experiments.cnf_affine_negative import NegativeStore,FORMAT,check_negative,compile_proof
from experiments.cnf_residual_dag import normalize,token,holds
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_ordered_probe import OrderedProbeSolver


class WholeAffineTests(unittest.TestCase):
    def solver(self,cls=policy.WholeAffineSolver,**kwargs):
        s=cls(**kwargs);self.addCleanup(s.close);return s

    def test_consistent_core_exhaustion_uses_existing_authority(self):
        s=self.solver(node_limit=0);r=s.solve([(-1,),(-2,),(1,2)])
        self.assertFalse(r['answer']);self.assertEqual(r['authority'],FORMAT)
        self.assertEqual(r['metrics']['whole_affine_candidates'],1)
        self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
        node=s.affine.read(r['root']);self.assertEqual(node['proof']['decision']['kind'],'exhaustion')
        self.assertIsNone(s._read(r['root']))

    def test_positive_completion_is_full_source_checked_native_model(self):
        s=self.solver(node_limit=0);source=[(101,),(-101,509),(999,-999)]
        r=s.solve((iter(c) for c in source))
        self.assertTrue(r['answer']);self.assertEqual(r['authority'],'native')
        self.assertTrue(holds(source,r['model']))
        self.assertEqual(r['metrics']['whole_affine_candidates'],2)
        self.assertEqual(r['metrics']['whole_affine_positive_publications'],1)
        self.assertTrue(s._read(r['root'])['answer'])
        self.assertTrue(s.witness_pool)

    def test_known_results_skip_completion_and_retain_stored_payload(self):
        s=self.solver();sources=[[(-1,),(-2,),(1,2)],[(1,),(-1,2)]]
        for src in sources:s.solve(src)
        old={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in ('cnf_residual_v1','cnf_affine_negative_v1')}
        with patch.object(policy,'complete_prepared',side_effect=AssertionError('known')),patch.object(s,'_expand',side_effect=AssertionError('search')):
            for src in sources:s.solve(src)
        for t in old:self.assertEqual(old[t],dict(s.db.execute(f'SELECT id,payload FROM {t}')))

    def test_no_equations_and_free_cap_keep_native_fallback(self):
        for src,metric in (([(1,2,3)],'whole_affine_no_equation_skips'),
                ([(1,)]+[(i,i+1,i+2) for i in range(2,14,3)],'whole_affine_free_cap_skips')):
            s=self.solver();old=self.solver(OrderedProbeSolver)
            with patch.object(policy,'complete_prepared',side_effect=AssertionError('ineligible')):
                r=s.solve(src)
            self.assertEqual(r['answer'],old.solve(src)['answer']);self.assertEqual(r['metrics'][metric],1)
            self.assertGreater(r['metrics']['expanded_nodes'],0)

    def test_xor_stop_and_native_budget_stop_supply_no_verdict(self):
        hard=[tuple(v if b else -v for v,b in enumerate(bits,1)) for bits in product((False,True),repeat=4)]
        hard += [tuple(v if b else -v for v,b in enumerate(bits,1)) for bits in product((False,True),repeat=3)]
        s=self.solver(affine_xors=1,node_limit=0)
        with self.assertRaisesRegex(RuntimeError,'Residual expansion budget exhausted'):s.solve(hard)
        self.assertEqual(s.counts['affine_probe_xor_stops'],1)
        self.assertEqual(s.affine.storage()[0],0)

    def test_completion_cap_and_source_validation(self):
        for n in (-1,9,True,1.5):
            with self.assertRaises(ValueError):policy.WholeAffineSolver(completion_free_limit=n)
        s=self.solver()
        for bad in (0,True,1.5):
            with self.assertRaises((ValueError,TypeError)):s.solve([[bad]])

    def test_mutated_space_and_missing_rejection_are_rejected(self):
        cnf,names=normalize([(-1,),(-2,),(1,2),(3,4,5)])
        af=bounded_extract(cnf,Counter(),65536);root=token(cnf,Counter())
        model,evidence=policy.complete_prepared(cnf,root,af,Counter(),8)
        self.assertIsNone(model);proof=compile_proof(evidence)
        check_negative(cnf,len(names),proof,Counter())
        bad=deepcopy(proof);bad['decision']['rejected'].pop()
        with self.assertRaises(ValueError):check_negative(cnf,len(names),bad,Counter())
        bad=deepcopy(proof);bad['decision']['space']['directions'][0]=0
        with self.assertRaises(ValueError):check_negative(cnf,len(names),bad,Counter())
        bad=deepcopy(af);bad['equations'][0]['rhs']^=1
        with self.assertRaises(ValueError):policy.complete_prepared(cnf,root,bad,Counter(),8)

    def test_small_cnf_truth_and_no_equation_controls(self):
        rng=random.Random(202611232157);s=self.solver()
        for _ in range(256):
            src=[[rng.choice((-1,1))*v for v in rng.sample(range(1,6),rng.choice((1,2,3,4)))]
                 for _ in range(rng.randrange(1,20))]
            truth=any(holds(src,dict(zip(range(1,6),bits))) for bits in product((False,True),repeat=5))
            r=s.solve(src);self.assertEqual(r['answer'],truth)
            if truth:self.assertTrue(holds(src,r['model']))

    def test_cold_native_and_extension_readers_with_no_reconstruction_search(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=policy.WholeAffineSolver(path)
            try:
                sources=[[(-1,),(-2,),(1,2)],[(1,),(-1,2)],[(1,2,3),(-1,-2,-3)]]
                answers=[s.solve(src)['answer'] for src in sources]
                native=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                affine=dict(s.db.execute('SELECT id,payload FROM cnf_affine_negative_v1'))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path);store=NegativeStore(r)
                try:
                    for key,payload in native.items():self.assertEqual(r._read(key),json.loads(payload))
                    for key,payload in affine.items():self.assertEqual(store.read(key),json.loads(payload))
                finally:r.close()
            s=policy.WholeAffineSolver(path)
            try:
                with patch.object(s,'_expand',side_effect=AssertionError('fresh search')):
                    self.assertEqual([s.solve(src)['answer'] for src in sources],answers)
            finally:s.close()

    def test_frozen_unresolved_whole_input_has_checked_exhaustion(self):
        cases=json.loads(Path('experiments/results/cnf-ordered-probe/holdout-cases.json').read_text())
        s=self.solver(node_limit=0);r=s.solve(cases[43]['source'])
        self.assertFalse(r['answer']);self.assertEqual(r['authority'],FORMAT)
        self.assertEqual(r['metrics']['whole_affine_candidates'],16)
        self.assertEqual(r['metrics']['whole_affine_negative_publications'],1)
        node=s.affine.read(r['root']);self.assertEqual(len(node['proof']['decision']['rejected']),16)


if __name__=='__main__':unittest.main()
