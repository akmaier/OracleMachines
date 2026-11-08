from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_conditioning import ShortestClauseInventory
from experiments.cnf_fused_conditioning import FusedConditioningInventory, FusedShortestClauseInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, normalize
from experiments.cnf_simplification import SimplifyingPatternInventory
from solver.test_cnf_pattern_inventory import assignments, check_pointwise, parity


def check_fused_tree(h, key, seen=None):
    """Every branch preserves exact fibers, including unsatisfiable children."""
    seen = set() if seen is None else seen
    if key in seen: return
    seen.add(key); node = h._load(key)
    edges = (node['edges'] if node['kind']=='and' else
             [e for a in node['alternatives'] for e in a['edges']] if node['kind']=='or' else
             [node['edge']] if node['kind'] in ('project','simplify') else [])
    if node['kind'] != 'or':
        # The older helper has pointwise OR semantics, so do not recurse into
        # fused descendants with it. Check the current unchanged node only.
        check_pointwise(h, key, {e['key'] for e in edges})
    if node['kind'] == 'or':
        for ai, attempt in enumerate(node['alternatives']):
            for value, edge in zip((False,True), attempt['edges']):
                feasible = {tuple(model[v] for v in edge['names']) for model in assignments(node['cnf'])
                            if model[attempt['variable']]==value and holds(node['cnf'],model)}
                for model in assignments(h._load(edge['key'])['cnf']):
                    bits = tuple(model[i] for i in range(1,len(edge['names'])+1))
                    valid = holds(h._load(edge['key'])['cnf'],model)
                    assert valid == (bits in feasible)
                    if valid and hasattr(h,'lift_conditioned'):
                        lifted = h.lift_conditioned(key,ai,value,model)
                        assert holds(node['cnf'],lifted) and lifted[attempt['variable']]==value
                        assert all(lifted[v]==model[i] for i,v in enumerate(edge['names'],1))
    elif node['kind'] in ('project','simplify'):
        edge = node['edge']
        feasible = {tuple(model[v] for v in edge['names']) for model in assignments(node['cnf']) if holds(node['cnf'],model)}
        for model in assignments(h._load(edge['key'])['cnf']):
            bits = tuple(model[i] for i in range(1,len(edge['names'])+1))
            valid = holds(h._load(edge['key'])['cnf'],model)
            assert valid == (bits in feasible)
            if valid:
                lifted = h.lift(key,model)
                assert holds(node['cnf'],lifted)
                assert all(lifted[v]==model[i] for i,v in enumerate(edge['names'],1))
    for edge in edges: check_fused_tree(h,edge['key'],seen)


def mixed_source():
    # Neither whole-input terminal nor initially unit; a split exposes closure.
    return [(1,2,3),(-1,-2,-3),(-1,-2,4),(-3,-4,5),(-1,3,-5),(2,-3,-5),(-2,4,5)]


class FusedConditioningTests(unittest.TestCase):
    def test_exhaustive_two_variable_inputs(self):
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s) for signs in itertools.product((-1,0,1),repeat=2)]
        h = FusedConditioningInventory(max_depth=2)
        for mask in range(1<<len(clauses)):
            r=h.inspect([c for i,c in enumerate(clauses) if mask>>i&1]);check_fused_tree(h,r['root']['key'])
        h.close()

    def test_random_all_fibers_and_unchanged_plans(self):
        rng=random.Random(202611082355)
        for old_cls,new_cls,pure in ((SimplifyingPatternInventory,FusedConditioningInventory,False),
                                    (ShortestClauseInventory,FusedShortestClauseInventory,False),
                                    (SimplifyingPatternInventory,FusedConditioningInventory,True)):
            old=old_cls(max_depth=2,simplify_pure=pure);new=new_cls(max_depth=2,simplify_pure=pure)
            fusions=0
            for _ in range(60):
                source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(2,5)))
                        for _ in range(rng.randrange(10,25))]
                if rng.randrange(4)==0:source+=parity((1,2,3),rng.randrange(2))
                a,b=old.inspect(source),new.inspect(source)
                self.assertEqual(a['summary'],b['summary']);self.assertEqual(a['profile'],b['profile'])
                fusions+=b['metrics'].get('fused_conditioning_edges',0)
                check_fused_tree(new,b['root']['key'])
                names=list(range(1,7));rng.shuffle(names);mapping=dict(zip(range(1,7),(v*73+11 for v in names)))
                variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
                for changed in (variant+variant[:1]+[(99999,-99999)],source+[(1,)],source+[(-1,)]):
                    a,b=old.inspect(changed),new.inspect(changed)
                    self.assertEqual(a['summary'],b['summary']);check_fused_tree(new,b['root']['key'])
            self.assertGreater(fusions,0);old.close();new.close()

    def test_no_fusion_of_recognized_or_disjoint_intermediate(self):
        h=FusedConditioningInventory(max_depth=2)
        for source in ([(1,2),(-1,3)],[(1,2,3),(-1,-2,-3),(8,9)]):
            cnf,_=normalize(source,Counter())
            edge=h._conditioning_edge(cnf,3,False,1)
            self.assertNotIn('closure',edge)
            h._check_conditioning_edge(edge,cnf,3,False,1)
        h.close()

    def test_forged_reason_transport_and_missing_closure(self):
        h=FusedConditioningInventory(max_depth=2)
        r=h.inspect(mixed_source())
        fused=[(key,n,ai,value,e) for key,n in h.checked.items() if n['kind']=='or'
               for ai,a in enumerate(n['alternatives']) for value,e in zip((False,True),a['edges']) if 'closure' in e]
        self.assertTrue(fused)
        key,node,ai,value,edge=fused[0]
        variable=node['alternatives'][ai]['variable'];depth=node['depth']-1
        mutations=[]
        bad=copy.deepcopy(edge);bad['closure']['units'][0][0]*=-1;mutations.append(bad)
        bad=copy.deepcopy(edge);bad['closure']['units'][0][1]=9999;mutations.append(bad)
        bad=copy.deepcopy(edge);bad['names']+=[9999];mutations.append(bad)
        bad=copy.deepcopy(edge);bad['closure']['units'].pop();mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):h._check_conditioning_edge(bad,node['cnf'],variable,value,depth)
        # A valid old-style node is semantically sound but omits this policy's
        # required fusion. It must not be accepted as an exact policy trace.
        from experiments.cnf_residual_dag import restrict
        oldedge=h._edge(restrict(node['cnf'],{variable:value}),depth)
        with self.assertRaisesRegex(ValueError,'Omitted'):
            h._check_conditioning_edge(oldedge,node['cnf'],variable,value,depth)
        h.close()

    def test_cold_replay_coexistence_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'archive.db';old=SimplifyingPatternInventory(path,max_depth=2,simplify_pure=False)
            old.inspect(mixed_source());prior=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=FusedConditioningInventory(path,max_depth=2);r=h.inspect(mixed_source())
            for k,v in prior.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            key,node=next((k,n) for k,n in h.checked.items() if n['kind']=='or' and any('closure' in e for a in n['alternatives'] for e in a['edges']))
            h.close();before=path.read_bytes()
            h=FusedConditioningInventory(path,max_depth=2);again=h.inspect(mixed_source())
            self.assertEqual(again['metrics'].get('inserted_nodes',0),0);self.assertEqual(again['metrics']['inserted_sources'],0)
            h.close();self.assertEqual(path.read_bytes(),before)
            h=FusedConditioningInventory(path,max_depth=2);bad=copy.deepcopy(node)
            edge=next(e for a in bad['alternatives'] for e in a['edges'] if 'closure'in e)
            edge['closure']['units'][0][1]=9999
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(bad),key))
            h.close();h=FusedConditioningInventory(path,max_depth=2)
            with self.assertRaises(ValueError):h.inspect(mixed_source())
            h.close()

    def test_existing_intermediate_root_remains_and_bad_lift_rejected(self):
        h=FusedConditioningInventory(max_depth=2)
        r=h.inspect(mixed_source());node=h._load(r['root']['key'])
        self.assertEqual(node['kind'],'or')
        from experiments.cnf_residual_dag import restrict
        variable=node['alternatives'][0]['variable'];raw=restrict(node['cnf'],{variable:False})
        oldedge=h._edge(raw,1);before=h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(oldedge['key'],)).fetchone()[0]
        edge=h._conditioning_edge(node['cnf'],variable,False,1)
        h._check_conditioning_edge(edge,node['cnf'],variable,False,1)
        self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(oldedge['key'],)).fetchone()[0],before)
        with self.assertRaises(ValueError):h.lift_conditioned(r['root']['key'],0,0,{})
        with self.assertRaises(ValueError):h.lift_conditioned(r['root']['key'],999,True,{})
        h.close()
