from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_learning_core_order import (
    CoreOrderLearningInventory, discover_core_order_probes,
    check_core_order_probes, checked_core_choices)
from experiments.cnf_learning_core import CoreLearningInventory
from experiments.cnf_learning_fixed_order import discover_fixed_order_probes
from experiments.cnf_probe_closure_reuse import expand_references
from experiments.cnf_probe_equivalence import check_equivalence_probes
from experiments.cnf_probe_learning import augment
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds
from solver.test_cnf_learning_core import core_source, core_common_source, core_equivalence_source
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_fused_conditioning import check_fused_tree


def check_order_fibers(source, cap):
    cnf, _ = normalize(source)
    result = discover_core_order_probes(cnf, 4, cap, Counter())
    raw, fixed = check_core_order_probes(cnf, result, 4, cap, Counter())
    if result['status'] in ('learned', 'learning_clear'):
        augmented = augment(cnf, result['batch'])
        for model in assignments(cnf): assert holds(cnf, model) == holds(augmented, model)
        checked = check_equivalence_probes(augmented,
            expand_references(result['continuation'], result['attempts']), 4, Counter(),
            _choices=checked_core_choices(cnf,result['attempts'],cap,4,Counter()))
        if result['status'] == 'learned':
            assert checked[1] == fixed
            for a in assignments(cnf): assert holds(checked[0],a) == holds(raw,a)
    target, names = normalize(raw)
    feasible = {tuple(a[v] for v in names) for a in assignments(cnf) if holds(cnf, a)}
    reduction = result['continuation'] if result['status'] == 'learned' else result
    for model in assignments(target):
        assert holds(target, model) == (tuple(model[i] for i in range(1, len(names)+1)) in feasible)
        if holds(target, model):
            lifted = {abs(l): False for c in cnf for l in c}; lifted.update(fixed)
            lifted.update((v, model[i]) for i, v in enumerate(names, 1))
            if reduction['status'] == 'equivalence':
                for v, rep in reduction['witness']['mapping']:
                    lifted[v] = lifted[abs(rep)] if rep > 0 else not lifted[abs(rep)]
            assert holds(cnf, lifted)
    return result


class CoreOrderTests(unittest.TestCase):
    def test_exhaustive_small_model_fibers(self):
        for variables, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses, count):
                    for cap in (0, 1, 4): check_order_fibers(source, cap)

    def test_forced_common_equivalence_and_lifts(self):
        for source, kind in [(core_source(),'forced'),(core_common_source(),'common'),
                             (core_equivalence_source(),'equivalence')]:
            result=check_order_fibers(source,4)
            self.assertEqual(result['status'],'learned')
            self.assertEqual(result['continuation']['status'],kind)
            h=CoreOrderLearningInventory(max_depth=0)
            r=h.inspect(source);check_fused_tree(h,r['root']['key']);h.close()

    def test_saved_ranking_miss_with_same_batch_and_budget(self):
        report=json.loads(Path('experiments/results/cnf-hint-transport/report.json').read_text())
        cnf=report['cases'][97]['transport']['core']
        old=discover_fixed_order_probes(cnf,4,4,Counter())
        counts=Counter();new=discover_core_order_probes(cnf,4,4,counts)
        self.assertEqual(old['batch'],new['batch'])
        self.assertEqual(old['status'],'learning_clear')
        self.assertEqual(new['status'],'learned')
        target,fixed=check_core_order_probes(cnf,new,4,4,Counter())
        self.assertEqual(fixed,{19:False,13:False})
        self.assertEqual([a['variable'] for a in new['attempts'][::2]],[4,5,7,19])
        self.assertLessEqual(len(new['continuation']['attempts']),8)
        self.assertEqual(counts['fixed_order_reconstructions'],0)
        self.assertEqual(counts['fresh_continuation_probes'],0)
        h=CoreOrderLearningInventory(max_depth=0);r=h.inspect(cnf)
        self.assertTrue(r['summary']['closed']);h.close()

    def test_original_trace_validation_precedes_reusing_choices(self):
        cnf,_=normalize(core_source());result=discover_core_order_probes(cnf,4,4,Counter())
        bads=[]
        bad=copy.deepcopy(result);bad['attempts']=bad['attempts'][2:];bads.append(bad)
        bad=copy.deepcopy(result);bad['attempts'][:2],bad['attempts'][2:4]=bad['attempts'][2:4],bad['attempts'][:2];bads.append(bad)
        bad=copy.deepcopy(result);bad['attempts'][0]['certificate']['units'].append([999,999]);bads.append(bad)
        bad=copy.deepcopy(result);bad['continuation']['attempts'][0]['variable']=999;bads.append(bad)
        bad=copy.deepcopy(result);bad['batch'].reverse();bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_core_order_probes(cnf,bad,4,4,Counter())

    def test_signed_edits_and_zero_budget(self):
        rng=random.Random(20261109073810)
        for source in (core_source(),core_common_source(),core_equivalence_source()):
            names=list(range(1,9));rng.shuffle(names)
            mapping={i+1:(v*37+5)*rng.choice((-1,1)) for i,v in enumerate(names)}
            variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            h=CoreOrderLearningInventory(max_depth=1)
            for changed in (source,variant,source+[(1,)],source[:-1],source+[(-1,8)]):
                check_order_fibers(changed,4);r=h.inspect(changed);check_fused_tree(h,r['root']['key'])
            h.close()
            a=CoreOrderLearningInventory(learn_limit=0);b=CoreLearningInventory(learn_limit=0)
            x,y=a.inspect(source),b.inspect(source)
            self.assertEqual(x['profile'],y['profile']);self.assertEqual(x['summary'],y['summary'])
            a.close();b.close()

    def test_cold_policy_binding_and_preserved_old_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=CoreLearningInventory(path,max_depth=0)
            old.inspect(core_source());saved=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=CoreOrderLearningInventory(path,max_depth=0);r=h.inspect(core_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key));check_fused_tree(h,key)
            for k,v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            self.assertNotIn(key,saved);h.close();raw=path.read_bytes()
            h=CoreOrderLearningInventory(path,max_depth=0)
            self.assertEqual(h.inspect(core_source())['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            node['edge']['key']=next(iter(saved))
            h=CoreOrderLearningInventory(path,max_depth=0)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=CoreOrderLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(core_source())
            h.close()
