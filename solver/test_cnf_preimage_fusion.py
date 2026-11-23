from collections import Counter
from itertools import product
import random,unittest
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_preimage_fusion import fused_preimage,fused_preimages
from experiments.cnf_residual_dag import normalize,token,restrict
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget
from experiments.cnf_probed_partition import acquire


class Canonicalizer:
    def __init__(self):self.counts=Counter()
    def _canonical(self,cnf):
        result,names=normalize(cnf,self.counts);return result,names,token(result,self.counts)


def request(cnf,ids,assignment,selected=None):
    child,_=normalize(restrict([cnf[i] for i in ids],assignment))
    return child,token(child,Counter()),list(range(len(child))) if selected is None else selected


class PreimageFusionTests(unittest.TestCase):
    def extractor(self):return CausalSupportExtractor(Canonicalizer(),materialize=False)

    def compare(self,cnf,ids,assignment,selected=None):
        child,key,selected=request(cnf,ids,assignment,selected)
        old=self.extractor();new=self.extractor()
        self.assertEqual(old._preimage(cnf,ids,assignment,key,selected),fused_preimage(new,cnf,ids,assignment,key,selected))
        self.assertEqual(old.counts['restriction_literal_visits'],new.counts['restriction_literal_visits'])
        return new

    def test_unchanged_clauses_reuse_order_without_renormalizing(self):
        cnf,_=normalize([(-1,3),(1,2,4),(3,4)]);e=self.compare(cnf,range(len(cnf)),{})
        self.assertEqual(e.counts['preimage_unchanged_clauses'],len(cnf))
        self.assertEqual(e.solver.counts['normalization_literal_visits'],0)

    def test_duplicate_preimages_preserve_first_input_representative(self):
        cnf,_=normalize([(1,2),(2,)])
        for ids in ([0,1],[1,0]):
            child,key,selected=request(cnf,ids,{1:False})
            self.assertEqual(fused_preimage(self.extractor(),cnf,ids,{1:False},key,selected),{ids[0]})
            self.compare(cnf,ids,{1:False})

    def test_empty_clause_collapse_and_true_residual(self):
        cnf,_=normalize([(1,),(2,3)])
        e=self.compare(cnf,range(len(cnf)),{1:False});self.assertEqual(e.counts['preimage_empty_collapses'],1)
        self.compare(cnf,range(len(cnf)),{1:True,2:True});self.compare((),[],{})

    def test_negative_positive_compaction_and_clause_reordering(self):
        cnf,_=normalize([(-100,-20,7),(-20,3),(-7,20),(3,7,100)])
        self.compare(cnf,list(reversed(range(len(cnf)))),{1:False,3:True})

    def test_bad_edge_and_indices_are_rejected(self):
        cnf,_=normalize([(1,2),(3,4)]);e=self.extractor();child,key,selected=request(cnf,[0,1],{})
        with self.assertRaises(ValueError):fused_preimage(e,cnf,[0,1],{},key+'x',selected)
        for ids in ([-1],[2],[True]):
            with self.assertRaises(ValueError):fused_preimage(e,cnf,ids,{},key,selected)
        for selected in ([-1],[2],[True]):
            with self.assertRaises(ValueError):fused_preimage(e,cnf,[0,1],{},key,selected)

    def test_all_small_clause_sets_and_partial_assignments(self):
        clauses=[(-2,),(-1,),(),(1,),(2,),(-2,-1),(-2,1),(-1,2),(1,2)]
        checked=0
        for mask in range(1<<len(clauses)):
            cnf,_=normalize([cl for i,cl in enumerate(clauses) if mask>>i&1])
            for values in product((None,False,True),repeat=2):
                fixed={i+1:value for i,value in enumerate(values) if value is not None}
                self.compare(cnf,range(len(cnf)),fixed);checked+=1
        self.assertEqual(checked,4608)

    def test_random_subsets_mappings_and_selected_clauses(self):
        rng=random.Random(632)
        for _ in range(192):
            raw=[[(1 if rng.randrange(2) else -1)*v for v in rng.sample(range(1,9),rng.randrange(1,5))] for _ in range(rng.randrange(1,20))]
            cnf,_=normalize(raw);ids=rng.sample(range(len(cnf)),rng.randrange(len(cnf)+1));fixed={v:bool(rng.randrange(2)) for v in rng.sample(range(1,9),rng.randrange(9))}
            child,_,_=request(cnf,ids,fixed);selected=rng.sample(range(len(child)),rng.randrange(len(child)+1))
            self.compare(cnf,ids,fixed,selected)

    def test_scoped_override_restores_after_exception(self):
        old=CausalSupportExtractor._preimage
        with self.assertRaisesRegex(RuntimeError,'test'):
            with fused_preimages():
                self.assertIs(CausalSupportExtractor._preimage,fused_preimage);raise RuntimeError('test')
        self.assertIs(CausalSupportExtractor._preimage,old)

    def test_plan_recipes_and_all_native_payloads_are_identical(self):
        source=list(product((-1,1),(-2,2),(-3,3)))+[(4,5,6)]
        results=[]
        for fused in (False,True):
            s=ConsequencePrioritySolver()
            try:
                root=acquire(s,source,256)['result']['root'];plan=CausalPlan(s)
                if fused:
                    with fused_preimages():result=plan.prepare(root);plan.emit(root)
                else:result=plan.prepare(root);plan.emit(root)
                results.append((result,plan.plans,list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY rowid'))))
                if fused:self.assertGreater(plan.counts['preimage_calls'],0)
            finally:s.close()
        self.assertEqual(results[0],results[1])

    def test_existing_plan_budgets_still_apply(self):
        s=ConsequencePrioritySolver()
        try:
            root=acquire(s,list(product((-1,1),(-2,2),(-3,3))),256)['result']['root']
            with fused_preimages():
                with self.assertRaises(SupportBudget):CausalPlan(s,node_limit=1).prepare(root)
                with self.assertRaises(PlanBudget):CausalPlan(s,byte_limit=1).prepare(root)
        finally:s.close()


if __name__=='__main__':unittest.main()
