from collections import Counter
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

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


def fixed_order_source():
    # Sample 53, seed 20261109053116: distinct continuation orders, both clear.
    return [(-8,-7,-4),(-8,-6,-1),(-8,-5,4),(-8,-1,4),(-7,-6,-3),
            (-7,-6,-2),(-7,2),(-5,-3,1),(-5,-2,3),(-5,7),(-4,-1,6),
            (-4,2),(-3,-2,1),(1,8),(2,3,5),(2,3,6),(4,5,6),(4,7,8)]


def check_fixed_fibers(source, cap):
    cnf, _ = normalize(source)
    result = discover_fixed_order_probes(cnf, 4, cap, Counter())
    raw, fixed = check_fixed_order_probes(cnf, result, 4, cap, Counter())
    if result['status'] in ('learned', 'learning_clear'):
        augmented = augment(cnf, result['batch'])
        for model in assignments(cnf): assert holds(cnf, model) == holds(augmented, model)
        checked = check_equivalence_probes(augmented,
            expand_references(result['continuation'], result['attempts']), 4, Counter(),
            _choices=baseline_continuation_choices(cnf,result['attempts'],cap,4,Counter()))
        if result['status'] == 'learned': assert checked == (raw, fixed)
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


class LearningFixedOrderTests(unittest.TestCase):
    def test_exhaustive_small_fibers(self):
        for variables, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=variables)]
            for count in range(max_clauses+1):
                for source in itertools.combinations(clauses, count):
                    for cap in (0, 1, 4): check_fixed_fibers(source, cap)

    def test_old_ranking_with_selected_clauses(self):
        cnf, _ = normalize(fixed_order_source())
        fixed = discover_fixed_order_probes(cnf, 4, 4, Counter())
        selected = discover_selected_probes(cnf, 4, 4, Counter())
        self.assertEqual(fixed['batch'], selected['batch'])
        self.assertEqual(fixed['attempts'], selected['attempts'])
        self.assertEqual(baseline_continuation_choices(cnf, fixed['attempts'], 4, 4, Counter()), [2,1,7,8])
        self.assertEqual(probe_choices(augment(cnf,fixed['batch']),4,Counter()), [2,7,1,6])
        self.assertNotEqual(fixed['continuation'], selected['continuation'])
        counts = Counter(); check_fixed_order_probes(cnf, fixed, 4, 4, counts)
        self.assertGreater(counts['fixed_order_reconstructions'], 0)
        self.assertGreater(counts['learning_candidate_visits'], 0)
        with self.assertRaises(ValueError): check_fixed_order_probes(cnf, selected, 4, 4, Counter())
        for cap in (0,1,4,16): check_fixed_fibers(cnf, cap)

    def test_preserved_priorities_disabled_learning_and_mixtures(self):
        rng = random.Random(20261109043246)
        sources = [fixed_order_source(), learning_source(), equivalence_source()]
        for _ in range(60):
            sources.append([tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.choice((2,3,4))))
                            for _ in range(rng.randrange(8,24))])
        h = FixedOrderLearningInventory(max_depth=2)
        for source in sources:
            names = sorted({abs(l) for c in source for l in c})
            perm = rng.sample(names, len(names)); mapping = {v: p*37*rng.choice((-1,1)) for v,p in zip(names,perm)}
            variant = [tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            for changed in (source, variant, source+[(1,)], source[:-1]):
                check_fixed_fibers(changed, 4)
                r = h.inspect(changed); check_fused_tree(h, r['root']['key'])
        h.close()
        a = FixedOrderLearningInventory(learn_limit=0); b = CompactProbeClosureInventory(learn_limit=0)
        for source in sources[:3]:
            x,y = a.inspect(source), b.inspect(source)
            self.assertEqual(x['profile'], y['profile']); self.assertEqual(x['summary'], y['summary'])
        a.close(); b.close()

    def test_wrong_selection_dependencies_and_order_rejected(self):
        cnf, _ = normalize(fixed_order_source()); result = discover_fixed_order_probes(cnf, 4, 4, Counter())
        self.assertIn(result['status'], ('learned', 'learning_clear'))
        bads = [discover_selected_probes(cnf,4,4,Counter())]
        bad = copy.deepcopy(result); bad['batch'] = learning_batch(cnf, result['attempts'], 4, Counter()); bads.append(bad)
        bad = copy.deepcopy(result); bad['batch'].reverse(); bads.append(bad)
        for field, value in (('attempt', False), ('unit', 999), ('clause', [1, -8])):
            bad = copy.deepcopy(result); bad['batch'][0][field] = value; bads.append(bad)
        bad = copy.deepcopy(result); bad['attempts'][0]['certificate']['units'].append([999,999]); bads.append(bad)
        bads.append(dict(status='clear', attempts=result['attempts']))
        for bad in bads:
            with self.assertRaises(ValueError): check_fixed_order_probes(cnf, bad, 4, 4, Counter())
        with self.assertRaises(ValueError): check_fixed_order_probes(cnf[:-1], result, 4, 4, Counter())

    def test_cold_coexistence_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'; old = SelectedLearningInventory(path, max_depth=0)
            old.inspect(fixed_order_source()); saved = dict(old.db.execute('SELECT * FROM cnf_patterns_v1')); old.close()
            h = FixedOrderLearningInventory(path, max_depth=0); r = h.inspect(fixed_order_source()); key = r['root']['key']
            node = copy.deepcopy(h._load(key)); check_fused_tree(h, key)
            for k,v in saved.items(): self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0],v)
            h.close(); raw = path.read_bytes(); h = FixedOrderLearningInventory(path, max_depth=0)
            self.assertEqual(h.inspect(fixed_order_source())['metrics'].get('inserted_nodes',0),0)
            h.close(); self.assertEqual(raw, path.read_bytes())
            node['profile']['probing']['batch'].reverse(); h = FixedOrderLearningInventory(path,max_depth=0)
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(encode(node),key))
            h.close(); h = FixedOrderLearningInventory(path,max_depth=0)
            with self.assertRaises(ValueError): h.inspect(fixed_order_source())
            h.close()
