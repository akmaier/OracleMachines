from collections import Counter, defaultdict
import copy
import json
from pathlib import Path
import unittest
from experiments.cnf_route_composition import CheckedRoutes, compose, verify_plan


class RouteCompositionTests(unittest.TestCase):
    def test_real_escape_catalog_and_corrupted_binding(self):
        from experiments.cnf_coupled_pivots import BudgetedInventory
        from experiments.cnf_growth_escape import TABLE, search, trial_key
        from experiments.cnf_pattern_inventory import encode
        core = json.loads(Path('experiments/results/cnf-coupled-pivots-originals/core-admission-audit.json').read_text())['cores'][0]
        h = BudgetedInventory(max_depth=0, probe_limit=4, learn_limit=4, clause_growth_limit=2)
        try:
            h.set_admission_budget(32); root = h.inspect(core['source'])['root']['key']
            for table in ('cnf_pivot_trials_v1', 'cnf_coupled_trials_v1', TABLE):
                h.db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            rows, stop = search(h, root, {}, Counter()); self.assertIsNone(stop)
            self.assertEqual(len(rows), 1); self.assertTrue(rows[0]['summary']['closed'])
            record = rows[0]; identity = trial_key(record)
            with h.db: h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (identity, encode(record)))
            routes = CheckedRoutes(h); result, plan = compose(h, [root], routes, Counter())
            self.assertEqual(result, [True]); verify_plan(h, plan, [root], routes, Counter())
            self.assertEqual(plan['steps'][-1]['rule'], dict(kind='growth', id=identity))
            bad = copy.deepcopy(record); bad['edge']['names'] = []
            with h.db: h.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?', (encode(bad), identity))
            with self.assertRaises(ValueError): CheckedRoutes(h)
        finally: h.close()

    def test_finite_alternatives_cycles_and_complete_branch_coverage(self):
        def node(kind, **fields): return dict(kind=kind, summary=dict(closed=kind=='family'), **fields)
        nodes = dict(
            closed=node('family'), open=node('unresolved'), rescued=node('unresolved'),
            chain=node('eliminate', edge=dict(key='rescued')),
            both=node('and', edges=[dict(key='chain'),dict(key='closed')]),
            partial=node('and', edges=[dict(key='chain'),dict(key='open')]),
            conditioning=node('or', alternatives=[dict(edges=[dict(key='closed'),dict(key='open')]),
                dict(edges=[dict(key='chain'),dict(key='closed')])]),
            incomplete=node('or', alternatives=[dict(edges=[dict(key='closed'),dict(key='open')])]),
            repeated=node('and', edges=[dict(key='chain'),dict(key='chain')]),
            cycle1=node('unresolved'), cycle2=node('unresolved'))
        class H:
            def _load(self, key): return nodes.get(key)
        class Routes:
            # Internal checked-route graph fixture: serialized-edge verification
            # is exercised on real records by the experiment's cold validator.
            by_source = defaultdict(list, {
                'rescued': [(dict(kind='growth', id='g'), ['closed'])],
                'cycle1': [(dict(kind='pivot', id='a'), ['cycle2'])],
                'cycle2': [(dict(kind='coupled', id='b'), ['cycle1'])]})
        h, routes = H(), Routes(); roots = ['both','partial','conditioning','incomplete','repeated','cycle1']
        result, plan = compose(h, roots, routes, Counter())
        self.assertEqual(result, [True,False,True,False,True,False])
        self.assertTrue(verify_plan(h, plan, ['both','conditioning','repeated'], routes, Counter()))
        self.assertEqual(next(s['rule']['index'] for s in plan['steps'] if s['source']=='conditioning'), 1)
        for mutate in (
            lambda p:p['steps'].reverse(),
            lambda p:p['steps'].pop(0),
            lambda p:p['steps'].append(p['steps'][0]),
            lambda p:p['steps'][-1].update(rule=dict(kind='base')),
            lambda p:p['roots'].append('cycle1')):
            bad = copy.deepcopy(plan); mutate(bad)
            with self.assertRaises(ValueError): verify_plan(h, bad, plan['roots'], routes, Counter())
        # A real base entering the cycle makes a finite derivation possible; the
        # alternative cycle itself is still never used as circular support.
        routes.by_source['cycle2'].append((dict(kind='growth', id='c'), ['closed']))
        result, plan = compose(h, ['cycle1'], routes, Counter())
        self.assertEqual(result, [True]); verify_plan(h, plan, ['cycle1'], routes, Counter())


if __name__ == '__main__': unittest.main()
