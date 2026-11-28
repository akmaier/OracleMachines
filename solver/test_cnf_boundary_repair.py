from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_boundary_repair as e


def seed(source, values=None):
    names = sorted({abs(v) for c in source for v in c})
    return dict(format=e.previous.FORMAT, names=names,
                values=[False]*len(names) if values is None else values)


def conditional(source, initial, free):
    local, _ = e.cofactor(source, initial, free)
    s = e.local_seed(local, initial)
    proof = e.previous_search.search(local, s, len(s['names']), record=True)['exclusion']
    return dict(format=e.CONDITIONAL, seed=initial, selected=free, proof=proof)


class BoundaryRepairTests(TestCase):
    def test_collector_preserves_search(self):
        for source in ([], [[]], [[1]], [[1], [-1]], [[1,2],[-1,3],[-2,-3]]):
            for values in product((False, True), repeat=len(seed(source)['names'])):
                initial = seed(source, list(values))
                for cap in (0, 1, 3, 100):
                    a=Counter(); b=Counter()
                    old=e.previous_search.search(source,initial,len(values),a,node_limit=cap,record=True)
                    new=e.collect(source,initial,len(values),b,node_limit=cap,record=True)
                    near=new.pop('near_model'); b.pop('boundary_model_values_copied')
                    self.assertEqual(old,new); self.assertEqual(a,b)
                    canonical=e.previous.capacity.canonical(source,Counter())
                    m=dict(zip(near['names'],near['values']))
                    self.assertEqual(sum(not any(m[abs(v)]==(v>0) for v in c) for c in canonical),new['diagnostic']['best_failed'])

    def test_incremental_matches_direct(self):
        source=[[1,2],[-1,3],[2,3],[1,2],[7,-7],[-3]]
        for values in product((False,True),repeat=4):
            initial=seed(source,list(values)); index=e.ConditionalIndex(source,initial)
            for free in ([],[1],[1,3],[1,2,3],[1,2,3,7]):
                index.extend(free)
                self.assertEqual(index.snapshot(),e.cofactor(source,initial,free))

    def test_conditional_not_global_unsat(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1])
        self.assertEqual(e.check_conditional(source,cert),dict(outside_context_excluded=True))
        self.assertTrue(e.previous.check(source,seed(source,[False,True]))['answer'])

    def test_changed_outside_assignment_rejected(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1])
        cert['seed']['values'][1]=True
        with self.assertRaises(ValueError): e.check_conditional(source,cert)

    def test_changed_free_set_rejected(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1]); cert['selected']=[1,2]
        with self.assertRaises(ValueError): e.check_conditional(source,cert)

    def test_changed_source_rejected(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1])
        with self.assertRaises(ValueError): e.check_conditional([[1,2]],cert)

    def test_partial_radius_rejected(self):
        source=[[1],[2]]; s=seed(source)
        p=e.previous_search.search(source,s,1,record=True)['exclusion']
        with self.assertRaises(ValueError): e.check_conditional(source,dict(format=e.CONDITIONAL,seed=s,selected=[1,2],proof=p))

    def test_direct_checker_does_not_use_index_or_search(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1])
        with patch.object(e,'ConditionalIndex',side_effect=AssertionError), patch.object(e.previous_search,'search',side_effect=AssertionError):
            self.assertTrue(e.check_conditional(source,cert)['outside_context_excluded'])

    def test_invalid_free_sets(self):
        for free in ([True], [0], [2,1], [1,1], [3], (1,)):
            with self.assertRaises(ValueError):e.cofactor([[1,2]],seed([[1,2]]),free)

    def test_no_shrinking_index(self):
        index=e.ConditionalIndex([[1,2]],seed([[1,2]]));index.extend([1])
        with self.assertRaises(ValueError):index.extend([])

    def test_proof_boundary_restores_outside_support(self):
        source=[[1,2],[-1,2]]; cert=conditional(source,seed(source),[1]);local,parents=e.cofactor(source,cert['seed'],[1])
        self.assertEqual(e.proof_boundary(local,parents,cert['proof'],[1]),[1,2])

    def test_duplicate_projection_chooses_one_parent(self):
        source=[[1,2], [1,2,3], [-1,2]]; initial=seed(source);cert=conditional(source,initial,[1]);local,parents=e.cofactor(source,initial,[1])
        self.assertEqual(e.proof_boundary(local,parents,cert['proof'],[1]),[1,2])

    def test_invalid_budgets(self):
        for key in ('node_limit','prefix_limit','max_rounds'):
            for value in (-1,True,1.5):
                with self.assertRaises(ValueError):e.repair([[1]],**{key:value})

    def test_zero_budget_no_negative_authority(self):
        result=e.repair([[1]],node_limit=0)
        self.assertIsNone(result['witness']);self.assertEqual(result['diagnostic']['expanded'],0)
        self.assertEqual(result['evidence']['rounds'],[])

    def test_empty_sources(self):
        self.assertIsNotNone(e.repair([])['witness'])
        self.assertIsNone(e.repair([[]])['witness'])

    def test_small_budget_and_signed_edits(self):
        source=[[-71,23],[71,400],[-23,-400],[999,-999]]
        for extra in ([], [[23]], [[71],[-71]]):
            for cap in (1,2,8,50):
                got=e.repair(source+extra,node_limit=cap,prefix_limit=1)
                self.assertLessEqual(got['diagnostic']['expanded'],cap)
                e.check_evidence(source+extra,got['evidence'])
                if got['witness']:self.assertTrue(e.previous.check(source+extra,got['witness'])['answer'])

    def test_evidence_checks_lift(self):
        source=[[1,2],[-1,2]]; initial=seed(source);cert=conditional(source,initial,[1])
        # Initial false clause contains both variables; an invented smaller round is rejected.
        evidence=dict(format=e.EVIDENCE,seed=initial,rounds=[dict(selected=[1],exclusion=cert['proof'],witness=None)])
        with self.assertRaises(ValueError):e.check_evidence(source,evidence)

    def test_tampered_conditional_proof(self):
        source=[[1,2],[-1,2]];cert=conditional(source,seed(source),[1])
        cert['proof']['nodes'].pop('0:0')
        with self.assertRaises(ValueError):e.check_conditional(source,cert)
