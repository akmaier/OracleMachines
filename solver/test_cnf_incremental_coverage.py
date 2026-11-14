from collections import Counter, defaultdict
import copy
import itertools
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_route_composition import compose, verify_plan


class Inventory:
    def __init__(self, nodes): self.nodes = nodes; self.reads = []
    def _load(self, key): self.reads.append(key); return self.nodes.get(key)


class Routes:
    def __init__(self): self.by_source = defaultdict(list)
    def add(self, source, name, children):
        self.by_source[source].append((dict(kind='test', id=name), children))


def node(closed=False):
    return dict(kind='family' if closed else 'unresolved', summary=dict(closed=closed))


class IncrementalCoverageTests(unittest.TestCase):
    def check(self, index, h, routes):
        closed, _ = compose(h, index.roots, routes, Counter())
        self.assertEqual(index.closed(), closed)
        plan = index.certificate()
        verify_plan(h, plan, plan['roots'], routes, Counter())
        index.audit(h, routes, Counter())

    def test_exhaustive_three_node_graphs_and_base_sets(self):
        keys = ['a','b','c']; pairs = list(itertools.product(keys, repeat=2))
        for mask in range(1 << len(pairs)):
            for bases in range(8):
                h = Inventory({k:node(bool(bases & (1 << i))) for i,k in enumerate(keys)})
                routes = Routes(); index = CoverageIndex(h, keys, routes, Counter())
                for i,(a,b) in enumerate(pairs):
                    if mask & (1 << i): routes.add(a, str(i), [b])
                index.refresh(h, routes, Counter()); self.check(index, h, routes)

    def test_random_incremental_and_or_graphs(self):
        rng = random.Random(4103)
        for _ in range(80):
            keys = list('abcdefg'); h = Inventory({k:node(k=='g') for k in keys})
            routes = Routes(); index = CoverageIndex(h, ['a'], routes, Counter())
            for j in range(16):
                routes.add(rng.choice(keys), str(j), [rng.choice(keys) for _ in range(rng.randrange(3))])
                index.refresh(h, routes, Counter()); self.check(index, h, routes)
            loaded = CoverageIndex.load(index.payload(), h, ['a'], routes, Counter())
            self.check(loaded, h, routes)

    def test_cycles_duplicate_premises_and_negative_invalidation(self):
        h = Inventory({k:node(k=='z') for k in ['a','b','c','z']}); routes = Routes()
        routes.add('a','both',['b','b']); routes.add('b','cycle',['c']); routes.add('c','cycle',['b'])
        index = CoverageIndex(h, ['a'], routes, Counter()); self.assertEqual(index.closed(), [False])
        routes.add('c','exit',['z']); counts = Counter(); index.refresh(h, routes, counts)
        self.assertEqual(index.closed(), [True]); self.assertEqual(counts['checked_option_sources'], 2)
        self.assertEqual(counts['discharged_premises'], 5); self.check(index, h, routes)

    def test_split_requires_both_children_and_unchanged_sources_not_loaded(self):
        h = Inventory({k:node(k=='z') for k in ['a','b','c','z']}); routes = Routes()
        routes.add('a','split',['b','c']); routes.add('b','one',['z'])
        index = CoverageIndex(h, ['a'], routes, Counter()); self.assertEqual(index.closed(), [False])
        h.reads.clear(); index.refresh(h, routes, Counter()); self.assertEqual(h.reads, [])
        routes.add('c','two',['z']); h.reads.clear(); index.refresh(h, routes, Counter())
        self.assertEqual(h.reads, ['c']); self.assertEqual(index.closed(), [True]); self.check(index,h,routes)

    def test_removed_rebound_and_missing_rules_fail_without_mutation(self):
        h = Inventory({'a':node(),'b':node(True)}); routes = Routes(); routes.add('a','edge',['b'])
        index = CoverageIndex(h, ['a'], routes, Counter()); before = index.payload()
        for bad in (Routes(), copy.deepcopy(routes)):
            if bad.by_source: bad.by_source['a'][0][1].append('b')
            with self.assertRaises(ValueError): index.refresh(h, bad, Counter())
            self.assertEqual(index.payload(), before)
        routes.add('a','missing',['not-present'])
        with self.assertRaises(ValueError): index.refresh(h,routes,Counter())
        self.assertEqual(index.payload(), before)

    def test_cold_catalog_checks_reject_omissions_and_rebindings(self):
        h = Inventory({'a':node(),'b':node(True)}); routes = Routes(); routes.add('a','edge',['b'])
        index = CoverageIndex(h,['a'],routes,Counter()); original = index.payload()
        mutations = [lambda p:p['rules'].pop(), lambda p:p['rules'].pop(0),
            lambda p:p['rules'][0][2].clear(), lambda p:p['external'].clear(),
            lambda p:p['roots'].clear(), lambda p:p['keys'].append('extra'),
            lambda p:p['rules'].append(p['rules'][0]), lambda p:p['rules'][0][2].append(True)]
        for mutate in mutations:
            bad = copy.deepcopy(original); mutate(bad)
            with self.assertRaises(ValueError): CoverageIndex.load(bad,h,['a'],routes,Counter())
        h.nodes['a'] = node(True)
        with self.assertRaises(ValueError): CoverageIndex.load(original,h,['a'],routes,Counter())

    def test_unreachable_routes_are_retained_until_source_becomes_reachable(self):
        h = Inventory({'a':node(),'b':node(),'z':node(True)}); routes = Routes()
        index = CoverageIndex(h,['a'],routes,Counter()); routes.add('b','hidden',['z'])
        counts=Counter(); index.refresh(h,routes,counts); self.assertEqual(counts['checked_option_sources'],0)
        routes.add('a','entry',['b']); index.refresh(h,routes,Counter()); self.check(index,h,routes)
        self.assertEqual(index.closed(),[True])

    def test_actual_pending_forced_route_activates_on_target_admission(self):
        from experiments.cnf_coupled_pivots import BudgetedInventory
        from experiments.cnf_probe_continuation import ContinuationRoutes
        from experiments.cnf_source_local import advance_one
        from solver.test_cnf_source_local import seed, OPTIONS
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history'; key,_=seed(path,'forced')
            h=BudgetedInventory(path,**OPTIONS)
            try:
                h.set_admission_budget(0); routes=ContinuationRoutes(h)
                advance_one(h,routes,key,Counter()); routes=ContinuationRoutes(h)
                index=CoverageIndex(h,[key],routes,Counter())
                self.assertFalse(routes.by_source.get(key))
                h.set_admission_budget(32); advance_one(h,routes,key,Counter())
                refreshed=ContinuationRoutes(h); self.assertTrue(refreshed.by_source[key])
                counts=Counter(); index.refresh(h,refreshed,counts)
                self.assertGreater(counts['added_rules'],0); self.check(index,h,refreshed)
            finally: h.close()


if __name__=='__main__': unittest.main()
