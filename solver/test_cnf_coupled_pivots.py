from collections import Counter,defaultdict
import copy
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_coupled_pivots import (
    AdmissionExhausted,BudgetedInventory,FrontierIndex,project_pair,lift_pair,
    search,verify_coupled,coupled_key,select_divergent)
from experiments.cnf_pivot_alternatives import search as first_search
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds,ResidualSolver


class CoupledPivotTests(unittest.TestCase):
    def test_exhaustive_two_step_projection_and_model_lift(self):
        clauses=[tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        accepted=0
        for mask in range(512):
            source=tuple(c for i,c in enumerate(clauses) if mask>>i&1)
            for variables in ([1,2],[2,1]):
                try:_,target=project_pair(source,variables,Counter())
                except ValueError:continue
                accepted+=1
                self.assertEqual(holds(target,{}),any(holds(source,{1:a,2:b}) for a,b in itertools.product((False,True),repeat=2)))
                if holds(target,{}):self.assertTrue(holds(source,lift_pair(source,variables,{},Counter())))
        self.assertGreater(accepted,400)
        v=2**130+3;source=((v,2),(-v,3),(-2,4),(-3,4))
        _,target=project_pair(source,[v,2],Counter())
        for values in itertools.product((False,True),repeat=2):
            model=dict(zip((3,4),values))
            if holds(target,model):self.assertTrue(holds(source,lift_pair(source,[v,2],model,Counter())))
        for bad in ([1,1],[True,2],[0,2],[1],(1,2)):
            with self.assertRaises(ValueError):project_pair(source,bad,Counter())

    def test_admission_cap_preserves_completed_children_and_restart(self):
        source=((1,2),(3,4,5));options=dict(max_depth=0)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history';h=BudgetedInventory(path,**options)
            h.set_admission_budget(2)
            with self.assertRaises(AdmissionExhausted):h.inspect(source)
            self.assertEqual(len(h.admitted),2);self.assertEqual(h.admission_counts['denied_states'],1)
            saved=list(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'));self.assertEqual(len(saved),1)
            h.close();h=BudgetedInventory(path,**options);h.set_admission_budget(2)
            result=h.inspect(source);self.assertTrue(result['summary']['closed']);self.assertEqual(len(h.admitted),2)
            self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(saved[0][0],)).fetchone(),(saved[0][1],))
            h.set_admission_budget(0);again=h.inspect(source);self.assertEqual(again['root'],result['root']);self.assertEqual(len(h.admitted),0)
            h.close();plain=AnchoredAdditiveInventory(**options);plain.inspect(source)
            plain_rows=dict(plain.db.execute('SELECT id,payload FROM cnf_patterns_v1'));plain.close()
            h=AnchoredAdditiveInventory(path,**options)
            self.assertEqual(dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')),plain_rows)
            for key in plain_rows:h._load(key)
            h.close()

    def test_coupled_checker_actual_history_and_tampering(self):
        source=json.loads(Path('solver/fixtures/pivot-alternatives.json').read_text())['source']
        h=BudgetedInventory(max_depth=0,probe_limit=4,learn_limit=4,clause_growth_limit=2);h.set_admission_budget(200)
        root=h.inspect(source)['root']['key'];first=first_search(h,root,Counter(),ancestor_limit=4,trial_limit=30)
        known={encode([r['source'],r['variable']]):r for r in first};index=FrontierIndex(h);counts=Counter()
        before=h.storage();empty,stop=search(h,root,known,{},index,Counter(),state_limit=0)
        self.assertEqual(empty,[]);self.assertIsNotNone(stop);self.assertEqual(h.storage(),before)
        records,stop=search(h,root,known,{},index,counts,state_limit=32)
        self.assertTrue(records);self.assertIsNone(stop);self.assertLessEqual(len(h.admitted),32)
        for record in records:verify_coupled(h,record,known,Counter())
        before=h.storage();cache={coupled_key(r):r for r in records};reuse_counts=Counter()
        repeated,stop=search(h,root,known,cache,index,reuse_counts,state_limit=0)
        self.assertEqual(repeated,[]);self.assertIsNone(stop);self.assertGreater(reuse_counts['reused_coupled_trials'],0)
        self.assertEqual(h.storage(),before)
        # Independently exercise model lifting on a real checked first trial.
        candidates=[]
        for r in first:
            node=h._load(r['source']);a=r['variable']
            for b in sorted({abs(l) for c in node['cnf'] for l in c}-{a}):
                try:_,target=project_pair(node['cnf'],[a,b],Counter())
                except ValueError:continue
                h.set_admission_budget(200);edge=h._edge(target,node['depth'])
                candidates.append(dict(source=r['source'],variables=[a,b],edge=edge,summary=h._load(edge['key'])['summary']))
                break
            if candidates:break
        self.assertTrue(candidates)
        record=candidates[0];verify_coupled(h,record,known,Counter())
        solver=ResidualSolver();node=h._load(record['source']);child=h._load(record['edge']['key'])
        a,b=solver.solve(node['cnf']),solver.solve(child['cnf']);self.assertEqual(a['answer'],b['answer'])
        if b['answer']:
            model={v:b['model'][i] for i,v in enumerate(record['edge']['names'],1)}
            self.assertTrue(holds(node['cnf'],lift_pair(node['cnf'],record['variables'],model,Counter())))
        solver.close()
        for field,value in [('variables',[1,1]),('edge',dict(key=record['edge']['key'],names=[])),('source','missing')]:
            bad=copy.deepcopy(record);bad[field]=value
            with self.assertRaises(ValueError):verify_coupled(h,bad,known,Counter())
        bad=copy.deepcopy(record);bad['summary']['closed']=not bad['summary']['closed']
        with self.assertRaises(ValueError):verify_coupled(h,bad,known,Counter())
        with patch('experiments.cnf_coupled_pivots.alternatives',side_effect=AssertionError('rediscovery')):
            verify_coupled(h,json.loads(encode(record)),known,Counter())
        h.close()

    def test_divergence_selection_preserves_shared_leaf_multiplicity(self):
        def node(kind,**extra):return dict(kind=kind,summary=dict(closed=False),profile=dict(shape=dict(literals=3)),**extra)
        nodes={'a':node('unresolved'),'b':node('unresolved'),
            'source':node('and',edges=[dict(key='a'),dict(key='a')]),
            'same':node('and',edges=[dict(key='a'),dict(key='a')]),
            'changed':node('and',edges=[dict(key='a'),dict(key='b')])}
        class H:
            def _load(self,key):return nodes.get(key)
        h=H();index=FrontierIndex(h)
        self.assertEqual(index.frontier('source'),Counter(a=2))
        trials=[dict(source='source',variable=i,edge=dict(key=k),summary=dict(closed=False)) for i,k in enumerate(('same','changed'),1)]
        selected=select_divergent(h,'source',{'source':trials},index,4,Counter())
        self.assertEqual(selected,[trials[1]])


if __name__=='__main__':unittest.main()
