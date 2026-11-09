from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_learning_activity import (
    ActivityLearningInventory, discover_activity_probes,
    check_activity_probes, activity_choices)
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


def check_activity_fibers(source, cap):
    cnf, _ = normalize(source)
    result = discover_activity_probes(cnf, 4, cap, Counter())
    raw, fixed = check_activity_probes(cnf, result, 4, cap, Counter())
    old = discover_fixed_order_probes(cnf,4,cap,Counter())
    if old['status']=='learned': assert result['status']=='learned'
    if result['status'] in ('learned', 'learning_clear'):
        augmented = augment(cnf, result['batch'])
        for model in assignments(cnf): assert holds(cnf, model) == holds(augmented, model)
        checked = check_equivalence_probes(augmented,
            expand_references(result['continuation'], result['attempts']), 4, Counter(),
            _choices=activity_choices(cnf,result['attempts'],result['batch'],cap,4,Counter()))
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


class ActivityTests(unittest.TestCase):
    def test_exhaustive_small_model_fibers(self):
        for variables, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses, count):
                    for cap in (0, 1, 4): check_activity_fibers(source, cap)

    def test_forced_common_equivalence_and_lifts(self):
        for source, kind in [(core_source(),'forced'),(core_common_source(),'common'),
                             (core_equivalence_source(),'equivalence')]:
            result=check_activity_fibers(source,4)
            self.assertEqual(result['status'],'learned')
            self.assertEqual(result['continuation']['status'],kind)
            h=ActivityLearningInventory(max_depth=0)
            r=h.inspect(source);check_fused_tree(h,r['root']['key']);h.close()

    def test_saved_ranking_miss_with_same_batch_and_budget(self):
        report=json.loads(Path('experiments/results/cnf-hint-transport/report.json').read_text())
        cnf=report['cases'][97]['transport']['core']
        old=discover_fixed_order_probes(cnf,4,4,Counter())
        counts=Counter();new=discover_activity_probes(cnf,4,4,counts)
        self.assertEqual(old['batch'],new['batch'])
        self.assertEqual(old['status'],'learning_clear')
        self.assertEqual(new['status'],'learned')
        target,fixed=check_activity_probes(cnf,new,4,4,Counter())
        self.assertEqual(fixed,{19:False,13:False})
        self.assertEqual([a['variable'] for a in new['attempts'][::2]],[4,5,7,19])
        self.assertLessEqual(len(new['continuation']['attempts']),8)
        h=ActivityLearningInventory(max_depth=0);r=h.inspect(cnf)
        self.assertTrue(r['summary']['closed']);h.close()

    def test_original_trace_validation_precedes_reusing_choices(self):
        cnf,_=normalize(core_source());result=discover_activity_probes(cnf,4,4,Counter())
        bads=[]
        bad=copy.deepcopy(result);bad['attempts']=bad['attempts'][2:];bads.append(bad)
        bad=copy.deepcopy(result);bad['attempts'][:2],bad['attempts'][2:4]=bad['attempts'][2:4],bad['attempts'][:2];bads.append(bad)
        bad=copy.deepcopy(result);bad['attempts'][0]['certificate']['units'].append([999,999]);bads.append(bad)
        bad=copy.deepcopy(result);bad['continuation']['attempts'][0]['variable']=999;bads.append(bad)
        bad=copy.deepcopy(result);bad['batch'].reverse();bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):check_activity_probes(cnf,bad,4,4,Counter())

    def test_signed_edits_and_zero_budget(self):
        rng=random.Random(20261109083909)
        for source in (core_source(),core_common_source(),core_equivalence_source()):
            names=list(range(1,9));rng.shuffle(names)
            mapping={i+1:(v*37+5)*rng.choice((-1,1)) for i,v in enumerate(names)}
            variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            h=ActivityLearningInventory(max_depth=1)
            for changed in (source,variant,source+[(1,)],source[:-1],source+[(-1,8)]):
                check_activity_fibers(changed,4);r=h.inspect(changed);check_fused_tree(h,r['root']['key'])
            h.close()
            a=ActivityLearningInventory(learn_limit=0);b=CoreLearningInventory(learn_limit=0)
            x,y=a.inspect(source),b.inspect(source)
            self.assertEqual(x['profile'],y['profile']);self.assertEqual(x['summary'],y['summary'])
            a.close();b.close()

    def test_cold_policy_binding_and_preserved_old_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';old=CoreLearningInventory(path,max_depth=0)
            old.inspect(core_source());saved=dict(old.db.execute('SELECT * FROM cnf_patterns_v1'));old.close()
            h=ActivityLearningInventory(path,max_depth=0);r=h.inspect(core_source());key=r['root']['key']
            node=copy.deepcopy(h._load(key));check_fused_tree(h,key)
            for k,v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            self.assertNotIn(key,saved);h.close();raw=path.read_bytes()
            h=ActivityLearningInventory(path,max_depth=0)
            self.assertEqual(h.inspect(core_source())['metrics'].get('inserted_nodes',0),0)
            h.close();self.assertEqual(raw,path.read_bytes())
            node['edge']['key']=next(iter(saved))
            h=ActivityLearningInventory(path,max_depth=0)
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=ActivityLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(core_source())
            h.close()

    def test_saved_transitions_and_budget_overflow_preserve_old_reductions(self):
        data=json.loads(Path('experiments/results/cnf-core-order/mechanisms.json').read_text())
        transitions=overflows=0
        for c in data['shared_changes']:
            changed=c['before']['status']!=c['after']['status']
            overflow=len(set(c['active_core_choices'])|set(c['novel_old_choices']))>4
            if not (changed or overflow):continue
            cnf=c['cnf'];counts=Counter();p=discover_activity_probes(cnf,4,4,counts)
            check_activity_probes(cnf,p,4,4,Counter())
            self.assertEqual(p['batch'],c['before']['batch'])
            if changed or c['before']['status']=='learned':self.assertEqual(p['status'],'learned')
            choices=activity_choices(cnf,p['attempts'],p['batch'],4,4,Counter())
            kept=[v for v in c['old_choices'] if v in c['active_core_choices'] or v in c['novel_old_choices']]
            self.assertEqual(choices[:len(kept)],kept)
            self.assertLessEqual(len(choices),4)
            if changed:transitions+=1
            if overflow:
                overflows+=1;self.assertGreater(counts['activity_overflow_candidates'],0)
        self.assertEqual(transitions,255);self.assertEqual(overflows,7)

    def test_no_useful_candidate_has_empty_checked_continuation(self):
        data=json.loads(Path('experiments/results/cnf-core-order/mechanisms.json').read_text())
        c=next(c for c in data['shared_changes'] if not c['active_core_choices'] and not c['novel_old_choices'])
        counts=Counter();p=discover_activity_probes(c['cnf'],4,4,counts)
        self.assertEqual(p['status'],'learning_clear')
        self.assertEqual(p['continuation'],{'status':'clear','attempts':[]})
        self.assertEqual(counts['learning_continuation_probe_attempts'],0)
        check_activity_probes(c['cnf'],p,4,4,Counter())
        bad=copy.deepcopy(p);bad['continuation']['attempts']=[bad['attempts'][0]]
        with self.assertRaises(ValueError):check_activity_probes(c['cnf'],bad,4,4,Counter())
