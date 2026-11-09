from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_polarity_horn import PolarityHornInventory, discover_polarity, check_polarity
from experiments.cnf_residual_dag import holds, normalize, ResidualSolver
from experiments.cnf_single_pass_inventory import SinglePassCheckInventory
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_signed_subsumption import check_signed_tree


def frontier():
    return json.loads(Path('experiments/results/cnf-single-pass-check/polarity-frontier.json').read_text())['rows']


def check_tree(h, key, seen=None):
    seen = set() if seen is None else seen
    if key in seen:return
    seen.add(key); node = h._load(key)
    edges = (node['edges'] if node['kind'] == 'and' else
             [e for a in node['alternatives'] for e in a['edges']] if node['kind'] == 'or' else
             [node['edge']] if node['kind'] in ('polarity', 'project', 'simplify', 'probe', 'subsumption') else [])
    if node['kind'] == 'polarity':
        edge = node['edge']; child = h._load(edge['key']); flips = set(node['polarity']['flipped'])
        for model in assignments(node['cnf']):
            local = {i: not model[v] if v in flips else model[v] for i, v in enumerate(edge['names'], 1)}
            assert holds(node['cnf'], model) == holds(child['cnf'], local)
            if holds(child['cnf'], local):assert h.lift(key, local) == model
    else:
        check_signed_tree(h, key, {e['key'] for e in edges})
    for edge in edges:check_tree(h, edge['key'], seen)


class PolarityHornTests(unittest.TestCase):
    def test_exhaustive_recognition_and_bijective_models(self):
        for n, max_clauses in ((2, 9), (3, 3)):
            clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                       for signs in itertools.product((-1, 0, 1), repeat=n)]
            for size in range(max_clauses+1):
                for cnf in itertools.combinations(clauses, size):
                    expected = any(all(sum((lit > 0) != bits[abs(lit)-1] for lit in c) <= 1 for c in cnf)
                                   for bits in itertools.product((False, True), repeat=n))
                    proof = discover_polarity(cnf, Counter()); target = check_polarity(cnf, proof, Counter())
                    self.assertEqual(proof['outcome'] == 'recognized', expected)
                    if target is not None:
                        flips = set(proof['flipped'])
                        for model in assignments(cnf):
                            changed = {v: not value if v in flips else value for v, value in model.items()}
                            self.assertEqual(holds(cnf, model), holds(target, changed))

    def test_exact_saved_frontier_exposures_and_terminal_lifts(self):
        h = PolarityHornInventory(max_depth=0, candidate_limit=0); solver = ResidualSolver()
        kinds = Counter()
        for row in frontier():
            result = h.inspect(row['cnf']); node = h._load(result['root']['key']); kinds[node['kind']] += 1
            self.assertEqual(result['summary']['closed'], row['recognized'])
            if node['kind'] == 'polarity':
                child = h._load(node['edge']['key']); solved = solver.solve(child['cnf'])
                if solved['answer']:self.assertTrue(holds(node['cnf'], h.lift(result['root']['key'], solved['model'])))
                with self.assertRaises(ValueError):h.lift(result['root']['key'], {})
            else:self.assertEqual(node['polarity']['outcome'], 'excluded')
        self.assertEqual(kinds, {'polarity': 35, 'unresolved': 113}); h.close(); solver.close()

    def test_exclusion_is_not_original_unsat_and_edited_bindings(self):
        solver = ResidualSolver()
        row = next(r for r in frontier() if not r['recognized'] and solver.solve(r['cnf'])['answer'])
        proof = discover_polarity(row['cnf'], Counter())
        self.assertEqual(proof['outcome'], 'excluded'); check_polarity(row['cnf'], proof, Counter())
        self.assertTrue(solver.solve(row['cnf'])['answer']); solver.close()
        positive = next(r['cnf'] for r in frontier() if r['recognized'])
        proof = discover_polarity(positive, Counter()); flips = set(proof['flipped'])
        # Add a clause with two positive occurrences *after* the claimed rename.
        variables = sorted({abs(lit) for c in positive for lit in c})[:2]
        added = [(-v if v in flips else v) for v in variables]
        edited = positive+[added]; proof['pairs'] += 1
        with self.assertRaisesRegex(ValueError, 'not Horn'):check_polarity(edited, proof, Counter())

    def test_forged_positive_negative_and_budget_certificates(self):
        for row in (next(r for r in frontier() if r['recognized']), next(r for r in frontier() if not r['recognized'])):
            cnf = row['cnf']; good = discover_polarity(cnf, Counter()); bads = []
            bad = copy.deepcopy(good); bad['pairs'] += 1; bads.append(bad)
            bad = copy.deepcopy(good); bad['unexpected'] = 1; bads.append(bad)
            if good['outcome'] == 'recognized':
                for flipped in ([True], [9999], good['flipped']+good['flipped'], []):
                    bad = copy.deepcopy(good); bad['flipped'] = flipped; bads.append(bad)
            else:
                bad = copy.deepcopy(good); bad['variable'] = True; bads.append(bad)
                bad = copy.deepcopy(good); bad['forward'] = []; bads.append(bad)
                for index, value in ((0, 0), (1, 9999), (2, -1), (3, True)):
                    bad = copy.deepcopy(good); bad['forward'][0][index] = value; bads.append(bad)
                bad = copy.deepcopy(good); bad['backward'] = good['forward']; bads.append(bad)
            for bad in bads:
                with self.assertRaises(ValueError):check_polarity(cnf, bad, Counter())
        cnf = ((1, 2, 3),); proof = discover_polarity(cnf, Counter(), pair_limit=2)
        self.assertEqual(proof['outcome'], 'unresolved'); check_polarity(cnf, proof, Counter(), pair_limit=2)
        with self.assertRaises(ValueError):check_polarity(cnf, proof, Counter(), pair_limit=3)
        with self.assertRaises(ValueError):check_polarity(cnf, discover_polarity(cnf, Counter()), Counter(), pair_limit=2)
        for cnf in (((0,),), ((True,),), ((1, 1),), ((1, -1),)):
            with self.assertRaises(ValueError):discover_polarity(cnf, Counter())
        for limit in (-1, True, 1.5, '3'):
            with self.assertRaises(ValueError):PolarityHornInventory(polarity_pair_limit=limit)

    def test_checker_never_reruns_auxiliary_discovery(self):
        for row in frontier():
            proof = discover_polarity(row['cnf'], Counter())
            with patch('experiments.cnf_polarity_horn.two_cnf', side_effect=AssertionError('reran SCC')):
                check_polarity(row['cnf'], proof, Counter())

    def test_all_tiny_trees_and_random_mixtures_edits(self):
        h = PolarityHornInventory(max_depth=1)
        clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
                   for signs in itertools.product((-1, 0, 1), repeat=2)]
        for mask in range(512):
            r = h.inspect([c for i, c in enumerate(clauses) if mask >> i & 1]); check_tree(h, r['root']['key'])
        rng = random.Random(202611091450)
        for _ in range(30):
            source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(2, 5)))
                      for _ in range(15)]
            for edited in (source, source+[(1,)], source[:-1], source+[(1, -1)]+source[:1]):
                result = h.inspect(edited); check_tree(h, result['root']['key'])
        h.close()

    def test_signed_variants_and_cap_preserve_old_closures(self):
        rows = [r for r in frontier() if r['recognized']][:8]
        h = PolarityHornInventory(max_depth=0); old = SinglePassCheckInventory(max_depth=0)
        capped = PolarityHornInventory(max_depth=0, polarity_pair_limit=0); rng = random.Random(1451)
        for row in rows:
            source = row['cnf']; names = sorted({abs(lit) for c in source for lit in c}); shuffled = names[:]; rng.shuffle(shuffled)
            mapping = {v: (w*71+3)*rng.choice((-1, 1)) for v, w in zip(names, shuffled)}
            variant = [[mapping[abs(lit)]*(1 if lit > 0 else -1) for lit in reversed(c)] for c in reversed(source)]
            for cnf in (source, variant):self.assertTrue(h.inspect(cnf)['summary']['closed'])
            before = old.inspect(source); after = capped.inspect(source)
            self.assertEqual(before['summary'], after['summary'])
            if not after['summary']['closed']:
                self.assertEqual(capped._load(after['root']['key'])['polarity']['outcome'], 'unresolved')
        for source in ([(1,)], [(1, 2), (-1, 3)], [(1, 2), (3, 4)], [(1, 2, 3), (-1, -2, -3)]):
            a = old.inspect(source); b = h.inspect(source)
            if a['summary']['closed']:self.assertTrue(b['summary']['closed'])
            if h._load(b['root']['key'])['kind'] not in ('polarity', 'unresolved'):
                self.assertNotIn('polarity', h._load(b['root']['key']))
        h.close(); old.close(); capped.close()

    def test_old_rows_cold_replay_corruption_and_policy_identity(self):
        source = next(r['cnf'] for r in frontier() if r['recognized'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.db'; old = SinglePassCheckInventory(path, max_depth=0)
            old_result = old.inspect(source); saved = dict(old.db.execute('SELECT id,payload FROM cnf_patterns_v1')); old.close()
            h = PolarityHornInventory(path, max_depth=0); result = h.inspect(source); key = result['root']['key']
            node = copy.deepcopy(h._load(key)); self.assertNotEqual(key, old_result['root']['key'])
            for k, v in saved.items():self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (k,)).fetchone()[0], v)
            h.close(); raw = path.read_bytes(); h = PolarityHornInventory(path, max_depth=0)
            again = h.inspect(source); self.assertEqual(again['metrics'].get('inserted_nodes', 0), 0)
            h.close(); self.assertEqual(path.read_bytes(), raw)
            bads = []
            bad = copy.deepcopy(node); bad['polarity']['flipped'] = []; bads.append(bad)
            bad = copy.deepcopy(node); bad['edge']['names'].reverse(); bads.append(bad)
            bad = copy.deepcopy(node); bad['edge']['key'] = old_result['root']['key']; bads.append(bad)
            bad = copy.deepcopy(node); del bad['subsumption']; bads.append(bad)
            bad = copy.deepcopy(node); del bad['polarity']; bads.append(bad)
            bad = copy.deepcopy(node); bad['summary']['closed'] = False; bads.append(bad)
            for bad in bads:
                path.write_bytes(raw); h = PolarityHornInventory(path, max_depth=0)
                with h.db:h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(bad), key))
                h.close(); h = PolarityHornInventory(path, max_depth=0)
                with self.assertRaises(ValueError):h.inspect(source)
                h.close()
