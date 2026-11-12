from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_pivot_alternatives import alternatives,search,covered,verify_trial
from experiments.cnf_additive_elimination import check_additive_elimination,lift_additive_elimination
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_pattern_inventory import encode


class PivotAlternativesTests(unittest.TestCase):
    def test_exhaustive_small_candidates_and_projection(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=tuple(c for i,c in enumerate(clauses) if mask>>i&1)
            for growth in (0,2):
                rows=alternatives(source,None,Counter(),clause_growth_limit=growth)
                expected={}
                for v in {abs(l) for c in source for l in c}:
                    try:expected[v]=check_additive_elimination(source,dict(variable=v),Counter(),clause_growth_limit=growth)
                    except ValueError:continue
                self.assertEqual({r['variable']:r['target'] for r in rows},expected)
                self.assertEqual([r['score'] for r in rows],sorted(r['score'] for r in rows))
                for r in rows:
                    rest=sorted({abs(l) for c in source for l in c}-{r['variable']})
                    for bits in itertools.product((False,True),repeat=len(rest)):
                        model=dict(zip(rest,bits))
                        self.assertEqual(holds(r['target'],model),any(holds(source,model|{r['variable']:b}) for b in (False,True)))
        source=((1,2),(1,3),(-1,4),(-1,5),(-1,6))
        self.assertNotIn(1,[r['variable'] for r in alternatives(source,None,Counter(),pair_limit=5)])
        self.assertNotIn(2,[r['variable'] for r in alternatives(source,2,Counter())])
        self.assertEqual(alternatives(source,None,Counter(),candidate_limit=0),[])

    def test_invalid_sources_limits_and_large_identifiers(self):
        for bad in (((0,),),((True,),),((1,1),),((1,-1),),((1,),(1,))):
            with self.assertRaises(ValueError):alternatives(bad,None,Counter())
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):alternatives(((1,),),None,Counter(),candidate_limit=bad)
            with self.assertRaises(ValueError):alternatives(((1,),),None,Counter(),clause_growth_limit=bad)
        for selected in (0,True,-1,'1'):
            with self.assertRaises(ValueError):alternatives(((1,),),selected,Counter())
        v=2**130+3;source=((v,-2),(v,3),(-v,4))
        for row in alternatives(source,None,Counter()):
            self.assertEqual(row['target'],check_additive_elimination(source,dict(variable=row['variable']),Counter(),clause_growth_limit=2))

    def test_recomposition_requires_complete_alternatives(self):
        def n(kind,**extra):return dict(kind=kind,summary=dict(closed=kind=='family'),**extra)
        def e(key):return dict(key=key)
        nodes={'a':n('unresolved'),'b':n('unresolved'),'c':n('family'),
            'and':n('and',edges=[e('a'),e('b')]),
            'or':n('or',selected=0,alternatives=[dict(edges=[e('a'),e('b')]),dict(edges=[e('b'),e('c')])]),
            'unary':n('eliminate',edge=e('or'))}
        class H:
            def _load(self,key):return nodes.get(key)
        h=H()
        self.assertFalse(covered(h,'and',{'a'},Counter()))
        self.assertFalse(covered(h,'or',{'a'},Counter()))
        self.assertTrue(covered(h,'or',{'b'},Counter()))
        self.assertTrue(covered(h,'unary',{'b'},Counter()))
        self.assertTrue(covered(h,'and',{'a','b'},Counter()))
        with self.assertRaises(ValueError):covered(h,'missing',set(),Counter())

    def test_bounded_search_replay_models_and_tampering(self):
        source=json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        options=dict(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';h=AnchoredAdditiveInventory(path,**options)
            r=h.inspect(source);root=r['root']['key'];self.assertFalse(r['summary']['closed'])
            before=encode(h._load(root));counts=Counter()
            self.assertEqual(search(h,root,counts,trial_limit=0),[])
            self.assertEqual(search(h,root,counts,ancestor_limit=0),[])
            records=search(h,root,counts,ancestor_limit=2,trial_limit=3)
            self.assertEqual(len(records),3);self.assertEqual(counts['recognition_trials'],3)
            self.assertGreater(counts['candidate_projections'],3)
            self.assertEqual(encode(h._load(root)),before)
            solver=ResidualSolver()
            for record in records:
                verify_trial(h,record,Counter());node=h._load(record['source']);child=h._load(record['edge']['key'])
                a,b=solver.solve(node['cnf']),solver.solve(child['cnf']);self.assertEqual(a['answer'],b['answer'])
                if b['answer']:
                    model={v:b['model'][i] for i,v in enumerate(record['edge']['names'],1)}
                    self.assertTrue(holds(node['cnf'],lift_additive_elimination(node['cnf'],dict(variable=record['variable']),model,Counter(),clause_growth_limit=2)))
            solver.close();h.close()
            h=AnchoredAdditiveInventory(path,**options)
            for record in json.loads(encode(records)):verify_trial(h,record,Counter())
            size=h.storage();again=search(h,root,Counter(),ancestor_limit=2,trial_limit=3)
            self.assertEqual(encode(records),encode(again));self.assertEqual(h.storage(),size)
            bad=copy.deepcopy(records[0]);bad['summary']['closed']=True
            with self.assertRaises(ValueError):verify_trial(h,bad,Counter())
            bad=copy.deepcopy(records[0]);bad['edge']['names']=[]
            with self.assertRaises(ValueError):verify_trial(h,bad,Counter())
            bad=copy.deepcopy(records[0]);bad['variable']=True
            with self.assertRaises(ValueError):verify_trial(h,bad,Counter())
            bad=copy.deepcopy(records[0]);bad['source']='missing'
            with self.assertRaises(ValueError):verify_trial(h,bad,Counter())
            with patch('experiments.cnf_pivot_alternatives.alternatives',side_effect=AssertionError('rediscovery')):
                for record in records:verify_trial(h,record,Counter())
            h.close()


if __name__=='__main__':unittest.main()
