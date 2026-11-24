from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random
import tempfile
import unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover, compile_cover
from experiments.cnf_guard_cover_cases import family
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot


class GuardClauseCoverTests(unittest.TestCase):
    def compile(self, source, hints, graph, cover):
        solver = native.ResidualSolver(); self.addCleanup(solver.close)
        root = compile_cover(solver, source, hints, graph, cover, Counter())
        self.assertEqual(root, solver._canonical(source)[2])
        self.assertFalse(solver._read(root)['answer'])
        return solver, root

    def test_preserved_separation_compiles_and_reuses(self):
        from experiments.cnf_guard_wide_gap import evidence
        e = evidence(); source = tuple(map(tuple, e['source']))
        c = Counter(); cover = discover(source, e['graph'], dict(e['graph_model']), c)
        self.assertEqual(cover['clause'], [1, 2, 3])
        s, root = self.compile(source, e['hints'], e['graph'], cover)
        c = Counter(); self.assertEqual(compile_cover(s, source, e['hints'], e['graph'], cover, c), root)
        self.assertEqual(c['published_nodes'], 0); self.assertEqual(c['existing_nodes'], 1)

    def test_signed_renamings_and_growing_widths(self):
        rng = random.Random(202611241621)
        for width in range(3, 9):
            for _ in range(3):
                names = list(range(1, 4*width+1)); rng.shuffle(names)
                rename = {i: v*rng.choice((-1, 1)) for i, v in enumerate(names, 1)}
                source, _, hints, graph, model = family(width, rename)
                cover = discover(source, graph, model, Counter())
                self.assertIsNotNone(cover)
                self.compile(source, hints, graph, cover)

    def test_source_deletion_and_satisfiable_edits(self):
        for edit in ('delete_support', 'delete_wide', 'flip_wide'):
            source, _, hints, graph, model = family(edit=edit)
            self.assertIsNone(discover(source, graph, model, Counter()))
            self.assertTrue(any(native.holds(source, dict(enumerate(bits, 1))) for bits in product((False, True), repeat=12)))

    def test_missing_support_bad_clause_and_bad_edges_rejected_before_writes(self):
        source, _, hints, graph, model = family(); cover = discover(source, graph, model, Counter())
        mutations = []
        bad = deepcopy(cover); bad['clause_index'] = -1; mutations.append((source, hints, graph, bad))
        bad = deepcopy(cover); bad['paths'][0][0][1] = 10000; mutations.append((source, hints, graph, bad))
        bad = deepcopy(cover); bad['clause'][0] *= -1; mutations.append((source, hints, graph, bad))
        mutations.append((source, hints[1:], graph, cover))
        bad = deepcopy(hints); bad[0]['clause'] = [1]; mutations.append((source, bad, graph, cover))
        # Keep the same clause index after deleting a support if possible; any source-bound rejection suffices.
        edited = tuple(cl for cl in source if cl != tuple(hints[0]['template']['clauses'][0]))
        bad = deepcopy(cover); bad['clause_index'] = edited.index(tuple(cover['clause']))
        mutations.append((edited, hints, graph, bad))
        for args in mutations:
            s = native.ResidualSolver(); self.addCleanup(s.close); c = Counter()
            with self.assertRaises(ValueError): compile_cover(s, *args, c)
            self.assertEqual(c['published_nodes'], 0)

    def test_bounds_are_inconclusive_and_not_cached_absence(self):
        source, _, hints, graph, model = family()
        for kwargs, counter in ((dict(root_limit=1), 'root_limit_stops'),
                                (dict(edge_limit=1), 'edge_limit_stops'),
                                (dict(path_limit=1), 'path_limit_stops')):
            c = Counter(); self.assertIsNone(discover(source, graph, model, c, **kwargs)); self.assertEqual(c[counter], 1)
            self.assertIsNotNone(discover(source, graph, model, Counter()))
        self.assertIsNone(discover(source, graph, model, Counter(), width_limit=2))
        for kwargs in (dict(root_limit=0), dict(edge_limit=True), dict(width_limit=-1)):
            with self.assertRaises(ValueError): discover(source, graph, model, Counter(), **kwargs)
        with self.assertRaises(ValueError): discover(source, graph, {}, Counter())

    def test_exhaustive_binary_subsets_and_signed_wide_clauses(self):
        # Every subset of six binary clauses whose variables overlap the wider clause.
        # This covers stronger-prefix conflicts, original edges and shared path vertices.
        universe = [(-1, 2), (-1, -2), (-2, 3), (-2, -3), (-3, 1), (-3, -1)]
        found = 0
        for mask in range(64):
            graph = tuple(sorted(tuple(sorted(universe[i])) for i in range(6) if mask >> i & 1))
            model, proof = native.two_cnf(graph, Counter())
            if model is None or proof is not None: continue
            for signs in product((-1, 1), repeat=3):
                wide = tuple(sorted(sign*v for v, sign in enumerate(signs, 1)))
                source = native.normalize(graph+(wide,))[0]
                cover = discover(source, graph, model, Counter())
                if cover is None: continue
                found += 1
                self.assertFalse(any(native.holds(source, dict(enumerate(bits, 1))) for bits in product((False, True), repeat=3)))
                self.compile(source, [], graph, cover)
        self.assertGreater(found, 0)

    def test_cold_native_replay(self):
        source, _, hints, graph, model = family(5)
        cover = discover(source, graph, model, Counter())
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'db'; s = native.ResidualSolver(path)
            try: root = compile_cover(s, source, hints, graph, cover, Counter())
            finally: s.close()
            reader = CanonicalVerifySnapshot(path)
            try: self.assertFalse(reader._read(root)['answer'])
            finally: reader.close()


if __name__ == '__main__': unittest.main()
