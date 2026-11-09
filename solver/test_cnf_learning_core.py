from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_learning_core import CoreLearningInventory, check_core_probes, core_after_checked_continuation
from experiments.cnf_probe_closure_reuse import discover_reuse_probes, check_reuse_probes
from experiments.cnf_learning_fixed_order import (
    FixedOrderLearningInventory, baseline_continuation_choices,
    discover_fixed_order_probes, check_fixed_order_probes)
from experiments.cnf_learning_selection import SelectedLearningInventory, discover_selected_probes
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_closure_compact import CompactProbeClosureInventory
from experiments.cnf_probe_closure_reuse import batch_inactive, expand_references
from experiments.cnf_probe_equivalence import discover_equivalence_probes, check_equivalence_probes
from experiments.cnf_probe_learning import learning_batch, augment
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_probe_learning import learning_source, equivalence_source


def core_source():
    # Forced fixture, sample 15 at seed 20261109064122.
    return [(-8,1,3),(-8,3,7),(-7,-2,-1),(-7,-1,2),(-6,-1,7),(-5,-4,7),
            (-5,-3,6),(-5,-3,8),(-5,1,6),(-4,2),(-4,2,5),(-3,-2,7),
            (-3,2,4),(-3,4,8),(-1,7,8),(1,4,5),(1,8),(2,3,5),(5,6,8),(5,7)]


def core_equivalence_source():
    # Sample 58 at the same seed.
    return [(-8,-2,4),(-8,4,5),(-8,5,6),(-7,-4,8),(-7,-2),(-7,-1,4),
            (-7,2,6),(-6,-4,3),(-6,2,3),(-6,4,8),(-5,-4,3),(-5,-2,7),
            (-5,3,6),(-4,-3,5),(-4,2,7),(-3,4,7),(-1,8),(1,2,3),(3,4)]


def core_common_source():
    # Sample 391 at the same seed.
    return [(-8,-6,-2),(-8,-2,7),(-8,-1,7),(-8,1,3),(-8,6),(-7,-6,-1),
            (-7,-6,1),(-7,-6,5),(-6,-5,3),(-6,-3,2),(-6,-1,2),(-6,1,8),
            (-5,-4,3),(-5,-4,6),(-4,3,7),(-3,1,8),(-2,1,6),(3,4),(3,5,7),(6,7)]


def check_core_fibers(source, cap):
    cnf, _ = normalize(source)
    result = discover_fixed_order_probes(cnf, 4, cap, Counter())
    raw, fixed = check_core_probes(cnf, result, 4, cap, Counter())
    if result['status'] in ('learned', 'learning_clear'):
        augmented = augment(cnf, result['batch'])
        for model in assignments(cnf): assert holds(cnf, model) == holds(augmented, model)
        checked = check_equivalence_probes(augmented,
            expand_references(result['continuation'], result['attempts']), 4, Counter(),
            _choices=baseline_continuation_choices(cnf,result['attempts'],cap,4,Counter()))
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


class LearningCoreTests(unittest.TestCase):
    def test_exhaustive_small_fibers(self):
        for variables, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses, count):
                    for cap in (0, 1, 4): check_core_fibers(source, cap)

    def test_forced_common_and_equivalence_cores(self):
        for source, kind in [(core_source(),'forced'),(core_common_source(),'common'),
                             (core_equivalence_source(),'equivalence')]:
            cnf,_ = normalize(source); result = discover_fixed_order_probes(cnf,4,4,Counter())
            self.assertEqual(result['status'],'learned'); self.assertEqual(result['continuation']['status'],kind)
            counts=Counter(); core,_=check_core_probes(cnf,result,4,4,counts)
            self.assertGreater(counts['core_excluded_clause_occurrences'],0)
            for cap in (0,1,4,16): check_core_fibers(cnf,cap)
            h=CoreLearningInventory(max_depth=0); r=h.inspect(cnf)
            self.assertEqual(r['profile']['probing']['status'],'learned')
            check_fused_tree(h,r['root']['key']);h.close()

    def test_proved_conflict_is_not_discarded(self):
        source=learning_source()
        # Two copies force opposite values of shared output 7. The original
        # bounded probes are clear, but learned continuation refutes both sides.
        opposite=[tuple(-l if abs(l)==7 else (abs(l)+7)*(1 if l>0 else -1) for l in c) for c in source]
        cnf,_=normalize(source+opposite);p=discover_fixed_order_probes(cnf,4,4,Counter())
        self.assertEqual(p['status'],'learned');self.assertIsNotNone(p['continuation']['closure']['conflict'])
        counts=Counter();core,_=check_core_probes(cnf,p,4,4,counts)
        self.assertEqual(core,((),));self.assertEqual(counts['core_preserved_conflicts'],1)
        self.assertFalse(any(holds(cnf,a) for a in assignments(cnf)))
        bad=copy.deepcopy(p);bad['continuation']['closure']['conflict']=999
        with self.assertRaises(ValueError):check_core_probes(cnf,bad,4,4,Counter())

    def test_augmented_child_cannot_replace_core_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';h=CoreLearningInventory(path,max_depth=0)
            r=h.inspect(core_source());key=r['root']['key'];node=copy.deepcopy(h._load(key))
            augmented,_=check_fixed_order_probes(node['cnf'],node['profile']['probing'],4,4,Counter())
            wrong=h._edge(augmented,node['depth']);self.assertNotEqual(wrong,node['edge'])
            node['edge']=wrong
            with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close();h=CoreLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError):h.inspect(core_source())
            h.close()

    def test_distinct_valid_views_share_the_same_core(self):
        fixtures=json.loads(Path('experiments/results/cnf-learning-selection/selection-paths.json').read_text())['paths']
        cnf=next(x['parent_cnf'] for x in fixtures if x['lost_source_paths']==[956])
        views=[]; cores=[]
        for discover,check in [(discover_reuse_probes,check_reuse_probes),
                               (discover_fixed_order_probes,check_fixed_order_probes)]:
            p=discover(cnf,4,4,Counter());target,fixed=check(cnf,p,4,4,Counter())
            self.assertEqual(fixed,{14:False});views.append(target)
            cores.append(core_after_checked_continuation(cnf,p,target,fixed,Counter())[0])
        self.assertNotEqual(views[0],views[1]);self.assertEqual(cores[0],cores[1]);self.assertEqual(len(cores[0]),54)
        h=CoreLearningInventory(max_depth=1);a=h.inspect(cores[0]);b=h.inspect(cores[1])
        self.assertEqual(a['root']['key'],b['root']['key']);self.assertEqual(b['metrics'].get('inserted_nodes',0),0)
        check_fused_tree(h,a['root']['key']) if a['profile']['shape']['variables']<=8 else h._load(a['root']['key'])
        h.close()

    def test_preserved_priorities_disabled_learning_and_mixtures(self):
        rng = random.Random(20261109043246)
        sources = [core_source(), core_common_source(), core_equivalence_source(), learning_source(), equivalence_source()]
        for _ in range(60):
            sources.append([tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4))))
                            for _ in range(rng.randrange(8,24))])
        h = CoreLearningInventory(max_depth=2)
        for source in sources:
            names = sorted({abs(l) for c in source for l in c})
            perm = rng.sample(names, len(names)); mapping = {v: p*37*rng.choice((-1,1)) for v,p in zip(names,perm)}
            variant = [tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source, variant, source+[(1,)], source[:-1]):
                check_core_fibers(changed, 4)
                r = h.inspect(changed); check_fused_tree(h, r['root']['key'])
        h.close()
        a = CoreLearningInventory(learn_limit=0); b = CompactProbeClosureInventory(learn_limit=0)
        for source in sources[:3]:
            x,y = a.inspect(source), b.inspect(source)
            self.assertEqual(x['profile'], y['profile']); self.assertEqual(x['summary'], y['summary'])
        a.close(); b.close()

    def test_wrong_selection_dependencies_and_order_rejected(self):
        cnf, _ = normalize(core_source()); result = discover_fixed_order_probes(cnf, 4, 4, Counter())
        self.assertIn(result['status'], ('learned', 'learning_clear'))
        bads = []
        bad = copy.deepcopy(result); bad['batch'].reverse(); bads.append(bad)
        for field, value in (('attempt', False), ('unit', 999), ('clause', [1, -8])):
            bad = copy.deepcopy(result); bad['batch'][0][field] = value; bads.append(bad)
        bad = copy.deepcopy(result); bad['attempts'][0]['certificate']['units'].append([999,999]); bads.append(bad)
        bads.append(dict(status='clear', attempts=result['attempts']))
        for bad in bads:
            with self.assertRaises(ValueError): check_core_probes(cnf, bad, 4, 4, Counter())
        with self.assertRaises(ValueError): check_core_probes(cnf[:-1], result, 4, 4, Counter())

    def test_cold_coexistence_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'; old = FixedOrderLearningInventory(path, max_depth=0)
            old.inspect(core_source()); saved = dict(old.db.execute('SELECT * FROM cnf_patterns_v1')); old.close()
            h = CoreLearningInventory(path, max_depth=0); r = h.inspect(core_source()); key = r['root']['key']
            node = copy.deepcopy(h._load(key)); check_fused_tree(h, key)
            for k,v in saved.items(): self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close(); raw = path.read_bytes(); h = CoreLearningInventory(path, max_depth=0)
            self.assertEqual(h.inspect(core_source())['metrics'].get('inserted_nodes',0),0)
            h.close(); self.assertEqual(raw, path.read_bytes())
            node['profile']['probing']['batch'].reverse(); h = CoreLearningInventory(path,max_depth=0)
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close(); h = CoreLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError): h.inspect(core_source())
            h.close()
