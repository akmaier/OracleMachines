from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,tempfile,unittest
from experiments import compare_cnf_strengthened_cross_pivot as s
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
k=s.kernel
OUT=Path('experiments/results/cnf-strengthened-cross-pivot')


class IteratedCrossPivotTests(unittest.TestCase):
    def test_exhaustive_small_and_generated_truth(self):
        clauses=((-2,),(-1,),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2));rng=random.Random(26112623)
        cases=[(2,[clauses[i] for i in range(8) if mask>>i&1]) for mask in range(256)]
        cases += [(5,[[v*rng.choice((-1,1)) for v in rng.sample(range(1,6),rng.randrange(1,5))] for _ in range(rng.randrange(1,25))]) for _ in range(60)]
        for n,source in cases:
            result,_=k.discover(source,Counter());k.validate(source,result,Counter());small=k.compact(source,result,Counter());k.validate(source,small,Counter())
            self.assertEqual(result['status'],small['status'])
            if result['status']=='refuted':self.assertFalse(any(k.k.native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=n)))

    def test_real_two_round_resume_matches_restart(self):
        case=s.base.load(OUT/'pilot-case.json');p=s.seed(case,Counter());once,first_search=k.discover(p[29],Counter(),order_source=p[0],round_limit=1)
        self.assertEqual(once['levels'][0],s.base.load(OUT/'pilot-summary.json'));self.assertEqual(once['reason'],'round_limit')
        saved=deepcopy(once);resumed,next_search=k.discover(p[29],Counter(),order_source=p[0],previous=once,round_limit=1)
        full,searches=k.discover(p[29],Counter(),order_source=p[0],round_limit=2)
        self.assertEqual(full,resumed);self.assertEqual(searches,first_search+next_search);self.assertEqual(saved,once)
        self.assertEqual(full,s.base.load(OUT/'pilot-chain-full.json'));self.assertEqual(full['status'],'refuted')

    def test_empty_and_contradictory_seeds(self):
        for source,status in (([], 'unresolved'),([[]],'refuted'),([[1],[-1]],'refuted')):
            chain,_=k.discover(source,Counter());k.validate(source,chain,Counter());self.assertEqual(chain['status'],status)
        with self.assertRaises(ValueError):k.discover([],Counter(),round_limit=0)
        with self.assertRaises(ValueError):k.discover([],Counter(),pivot_limit=True)

    def test_bounded_no_new_units_is_not_sat_and_can_be_rechecked(self):
        source=[list(row) for row in product((1,-1),(2,-2),(3,-3),(4,-4))];chain,_=k.discover(source,Counter(),pivot_limit=1)
        self.assertEqual(chain['reason'],'no_new_units');self.assertEqual(chain['status'],'unresolved')
        cc=Counter();again,search=k.discover(source,cc,previous=chain,pivot_limit=4)
        self.assertEqual(cc['feedback_open_rechecks'],1);self.assertEqual(len(search[0]),4);self.assertEqual(again['status'],'unresolved')
        self.assertFalse(any(k.k.native.holds(source,dict(enumerate(bits,1))) for bits in product((False,True),repeat=4)))

    def test_refuted_terminal_reuse_does_no_search(self):
        source=[list(row) for row in product((1,-1),(2,-2),(3,-3))];chain,_=k.discover(source,Counter());cc=Counter()
        again,search=k.discover(source,cc,previous=chain);self.assertEqual(again,chain);self.assertEqual(search,[])
        self.assertEqual(cc['feedback_terminal_reuses'],1);self.assertEqual(cc['probe_roots'],0)

    def test_compaction_keeps_exact_earlier_bank_binding(self):
        case=s.base.load(OUT/'pilot-case.json');p=s.seed(case,Counter());full=s.base.load(OUT/'pilot-chain-full.json');small=k.compact(p[29],full,Counter(),order_source=p[0])
        self.assertEqual(small['levels'][0],full['levels'][0]);self.assertEqual([len(x['lemmas']) for x in small['levels']],[2,7]);self.assertEqual(small,s.base.load(OUT/'pilot-chain-compact.json'))
        self.assertEqual(k.compact(p[29],small,Counter(),order_source=p[0]),small)

    def test_stale_banks_reordering_and_post_terminal_levels_rejected(self):
        case=s.base.load(OUT/'pilot-case.json');p=s.seed(case,Counter());chain=s.base.load(OUT/'pilot-chain-full.json')
        for kind in ('swap','skip','source','ordering','status','extra','lemma'):
            bad=deepcopy(chain)
            if kind=='swap':bad['levels'].reverse()
            elif kind=='skip':bad['levels'].pop(0)
            elif kind=='source':bad['seed'][0].append(9999)
            elif kind=='ordering':bad['order_source'].reverse()
            elif kind=='status':bad['status']='sat'
            elif kind=='extra':bad['levels'].append(deepcopy(bad['levels'][-1]))
            else:bad['levels'][0]['lemmas'][0]['assumption']*=-1
            with self.assertRaises(ValueError,msg=kind):k.validate(p[29],bad,Counter(),order_source=p[0])

    def test_native_two_round_certificate_and_warm_invalidation(self):
        case=s.base.load(OUT/'pilot-case.json');chain=s.base.load(OUT/'pilot-chain-compact.json')
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'db';solver=s.compiler.native.ResidualSolver(db);cc=Counter()
            try:
                root=s.compile_case(solver,case,chain,cc);self.assertEqual(root,case['root']);self.assertGreater(cc['cross_native_branch_expansions'],0)
                self.assertLessEqual(sum(cc[x] for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits')),262144)
                before=s.old.tables(solver.db);wc=Counter();self.assertEqual(s.compile_case(solver,case,chain,wc),root);self.assertEqual(wc['cross_native_extension_hits'],1)
                for kind in ('source','prefix','seed','proof'):
                    bc=deepcopy(case);bad=deepcopy(chain)
                    if kind=='source':bc['source'][0].append(9999)
                    elif kind=='prefix':bc['prefix']['status']='refuted'
                    elif kind=='seed':bad['levels'][0]['seed'][0].append(9999)
                    else:bad['levels'][1]['proof']['conflict']=999999
                    with self.assertRaises(ValueError):s.compile_case(solver,bc,bad,Counter())
                self.assertEqual(before,s.old.tables(solver.db))
            finally:solver.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(db)
                try:self.assertFalse(reader._read(root)['answer'])
                finally:reader.close()

    def test_generic_native_matches_one_level_compiler(self):
        p=s.base.load(s.PARENT/'protocol.json');case=s.old.bound(p['cases']['61-0']);summary=s.old.bound(p['records']['61-0']['compact']);prepared=s.seed(case,Counter())
        chain=dict(format=k.FORMAT,seed=list(map(list,prepared[29])),order_source=list(map(list,prepared[0])),levels=[summary],status='refuted',reason='refuted')
        tables=[]
        with tempfile.TemporaryDirectory() as td:
            for mode in ('old','generic'):
                solver=s.compiler.native.ResidualSolver(Path(td)/mode)
                try:
                    root=s.prior.compile_case(solver,case,summary,Counter()) if mode=='old' else s.compile_case(solver,case,chain,Counter())
                    self.assertEqual(root,case['root']);tables.append(s.old.tables(solver.db))
                finally:solver.close()
        self.assertEqual(*tables)

    def test_empty_overlay_preserves_parent_history(self):
        binding=s.base.load(s.PARENT/'checkpoint.json')['cross_pivot_feedback']['remaining'];before=deepcopy(s.rows())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'overlay';s.compact(path,dict(parent=binding,excluded=[[61,50]]));self.assertEqual(s.load_frontier(s.old.binding(path)),[])
            for removed in ([[61,50],[61,50]],[[999,0]]):
                s.compact(path,dict(parent=binding,excluded=removed))
                with self.assertRaises(ValueError):s.load_frontier(s.old.binding(path))
        self.assertEqual(before,s.rows())


if __name__=='__main__':unittest.main()
