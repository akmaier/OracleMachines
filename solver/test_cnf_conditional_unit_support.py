from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import random,unittest
from experiments.cnf_conditional_unit_support import extract,check_template,transport,match,materialize,ExtractionBudget
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,restrict,holds,token,FORMAT

CUBE=list(product((-1,1),(-2,2),(-3,3)))


class ConditionalUnitSupportTests(unittest.TestCase):
    def solver(self,**kwargs):
        s=ConsequencePrioritySolver(**kwargs);self.addCleanup(s.close);return s

    def donor(self,source=None):
        source=CUBE if source is None else source;s=self.solver(leaves=False);r=acquire(s,source,256)
        self.assertEqual(r['status'],'unsat');return s,extract(s,source)[0]

    def test_source_bound_leaf_lifting_and_full_guard_cover(self):
        s,b=self.donor();self.assertGreater(len(b['entries']),1)
        for e in b['entries']:
            self.assertTrue(match(CUBE,e['template']))
            check_template(e['template'])
        for bits in product((False,True),repeat=3):
            model=dict(zip(range(1,4),bits))
            self.assertTrue(any(all(model[v]==bit for v,bit in e['path_assignment']) for e in b['entries']))

    def test_ancestor_units_are_lifted_and_irrelevant_reasons_removed(self):
        source=[(5,)]+CUBE;s,b=self.donor(source)
        self.assertTrue(all([5] not in e['template']['clauses'] for e in b['entries']))
        self.assertTrue(all(match(source,e['template']) for e in b['entries']))

    def test_irrelevant_split_assumptions_can_be_removed(self):
        s=self.solver();source=[(1,),(-1,),(2,3)];cnf,_,key=s._canonical(source)
        children=[acquire(s,restrict(cnf,{2:bit}),256)['result']['root'] for bit in (False,True)]
        s._store(key,dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,proof=dict(kind='split',variable=2,low=children[0],high=children[1])))
        bundle,_=extract(s,source)
        self.assertEqual(len(bundle['entries']),2)
        for e in bundle['entries']:
            self.assertEqual(e['template']['assumptions'],[]);self.assertEqual(len(e['path_assignment']),1)

    def test_sparse_signed_transport_preserves_conditional_truth(self):
        _,b=self.donor();mapping={1:-71,2:901,3:-11}
        target=[sorted(mapping[abs(l)]*(1 if l>0 else -1) for l in cl) for cl in CUBE]
        for e in b['entries']:
            t=transport(e['template'],mapping);self.assertTrue(match(target,t))
            self.assertFalse(any(holds(t['clauses'],dict(zip((11,71,901),bits))) and all(dict(zip((11,71,901),bits))[v]==bit for v,bit in t['assumptions']) for bits in product((False,True),repeat=3)))

    def test_partial_support_match_is_not_a_whole_query_answer(self):
        s=self.solver();source=[(1,),(2,3)];t=dict(clauses=[[1]],assumptions=[[1,False]],trace=[],conflict=0)
        self.assertTrue(holds(source,{1:True,2:True,3:False}))
        r=materialize(s,source,t);self.assertTrue(r['conditional']);self.assertEqual(r['assignment'],[[1,False]])
        self.assertNotEqual(r['root'],s._canonical(source)[2]);self.assertIsNone(s._read(s._canonical(source)[2]))
        with self.assertRaises(ValueError):materialize(s,source,t,context=[])

    def test_missing_reason_and_bad_unit_evidence_are_rejected(self):
        s=self.solver();t=dict(clauses=[[-2],[1],[-1,2]],assumptions=[],trace=[[1,1],[2,2]],conflict=0)
        # Sort and remap the hand-written template before validating it.
        t=dict(clauses=[[-2],[-1,2],[1]],assumptions=[],trace=[[1,2],[2,1]],conflict=0);check_template(t)
        self.assertFalse(match([[-1,2],[1]],t))
        with self.assertRaises(ValueError):materialize(s,[[-1,2],[1]],t)
        for field,value in (('conflict',True),('trace',[[1,0]]),('assumptions',[[1,True]])):
            bad=deepcopy(t);bad[field]=value
            with self.assertRaises(ValueError):check_template(bad)

    def test_invalid_maps_and_assignments_fail_closed(self):
        t=dict(clauses=[[-2],[-1,2],[1]],assumptions=[],trace=[[1,2],[2,1]],conflict=0)
        for mapping in ({1:3,2:-3},{1:True,2:2},{1:3},{1:0,2:2}):
            with self.assertRaises(ValueError):transport(t,mapping)
        for pairs in ([[1,0]],[[True,False]],[[1,False],[1,False]]):
            bad=deepcopy(t);bad['assumptions']=pairs
            with self.assertRaises(ValueError):check_template(bad)

    def test_stronger_context_is_rechecked_with_no_fresh_sat_search(self):
        _,b=self.donor();s=self.solver()
        for e in b['entries']:
            t=e['template'];fixed=dict(t['assumptions']);extra=next(v for v in (1,2,3) if v not in fixed);fixed[extra]=True
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
                r=materialize(s,CUBE,t,context=[[v,bit] for v,bit in sorted(fixed.items())])
            self.assertFalse(s._read(r['root'])['answer'])

    def test_unknown_endpoints_and_missing_children_are_not_promoted(self):
        s=self.solver();source=[(1,2),(1,-2),(-1,2),(-1,-2)];acquire(s,source,256);b,_=extract(s,source)
        self.assertEqual(b['entries'],[]);self.assertIn('unresolved',b['tree'])
        s,b=self.donor([(5,)]+CUBE);root=s._read(b['origin']);child=root['proof']['child'];original=s._read
        with patch.object(s,'_read',side_effect=lambda key,*a,**kw: None if key==child else original(key,*a,**kw)):
            with self.assertRaises(ValueError):extract(s,[(5,)]+CUBE)

    def test_budget_and_positive_origin_rejected_without_publication(self):
        s,b=self.donor();before=s.archive_storage()
        with self.assertRaises(ExtractionBudget):extract(s,CUBE,node_limit=1)
        with self.assertRaises(ExtractionBudget):extract(s,CUBE,literal_limit=1)
        self.assertEqual(s.archive_storage(),before)
        acquire(s,[(7,)],256)
        with self.assertRaises(ValueError):extract(s,[(7,)])

    def test_random_signed_deletions_match_exhaustive_cofactor_truth(self):
        _,b=self.donor();s=self.solver();rng=random.Random(833)
        for _ in range(64):
            source=[cl for cl in CUBE if rng.random()<0.85]
            for e in b['entries']:
                t=e['template']
                if not match(source,t):continue
                r=materialize(s,source,t);fixed=dict(r['assignment'])
                self.assertFalse(any(holds(source,{**dict(zip(range(1,4),bits)),**fixed}) for bits in product((False,True),repeat=3)))
                self.assertFalse(s._read(r['root'])['answer'])


if __name__=='__main__':unittest.main()
