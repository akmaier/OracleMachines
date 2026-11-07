"""Structural reuse tests check semantic boundaries against the native checker."""
from concurrent.futures import ThreadPoolExecutor
import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.components import analyze, conjunction
from solver.incremental import DEFAULT_INCREMENTAL
from solver.knowledge_store import KnowledgeStore
from solver.persistent import PersistentSolver
from solver.resources import Deadline
from solver.test_fast import var, neg, conj, disj, cnf_bits, HARD_UNSAT, MIXED


def block(i):
    return conj(disj(var(i), var(i+1)), disj(neg(var(i)), neg(var(i+1))))


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'results.sqlite3'

    def test_renamed_components_reuse_after_restart(self):
        with PersistentSolver(self.path, components=True) as s:
            first = s.solve(block(0), learn=False)
            self.assertEqual(first['components']['acquisitions'], 1)
        with PersistentSolver(self.path, components=True) as s:
            result = s.solve(conj(block(10), block(30)), learn=False)
            self.assertTrue(result['answer'])
            self.assertEqual(result['components']['acquisitions'], 0)
            self.assertEqual(result['components']['hits'], 2)
            self.assertEqual(result['components']['global_variables'], 4)
            self.assertEqual(s.audit()['checked'], 2)

    def test_connected_constraints_merge_and_do_not_glue_incompatible_models(self):
        with PersistentSolver(self.path, components=True) as s:
            first = s.solve(conj(var(0), neg(var(1))), learn=False)
            self.assertEqual(first['components']['components'], 2)
            connected = conj(conj(var(0), neg(var(1))), disj(neg(var(0)), var(1)))
            result = s.solve(connected, learn=False)
            self.assertFalse(result['answer'])
            self.assertEqual(result['components']['components'], 1)
            self.assertEqual(result['components']['largest_component_variables'], 2)
            self.assertFalse(s.solve(conj(var(0), neg(var(0))), learn=False)['answer'])

    def test_negative_embedding_survives_renaming_and_connecting_constraints(self):
        with PersistentSolver(self.path, components=True) as s:
            s.solve(conj(var(0), neg(var(0))), learn=False)
        with PersistentSolver(self.path, components=True) as s:
            renamed = conj(var(7), neg(var(7)))
            r = s.solve(renamed, learn=False)
            self.assertFalse(r['answer'])
            self.assertEqual(r['components']['acquisitions'], 0)
            # This clause merges the core with a new variable. The archived
            # negative subset is still valid although maximal shape changes.
            with patch.object(s, '_fast_live', wraps=s._fast_live) as live:
                r = s.solve(conj(renamed, disj(var(7), var(8))), learn=False)
                self.assertFalse(r['answer'])
                self.assertTrue(r['components']['negative_subsumption'])
                self.assertEqual(live.call_count, 1)  # wrapper only; no fresh solve
            self.assertTrue(s.solve(neg(renamed), learn=False)['answer'])
            self.assertTrue(s.solve(var(7), learn=False)['answer'])

    def test_native_rejects_wrong_embedding_paths_map_and_leaf_proof(self):
        bits = conj(var(0), neg(var(0)))
        with PersistentSolver(self.path, components=True) as s:
            s.solve(bits, learn=False)
            cert = json.loads(s.db.execute('SELECT certificate FROM proofs').fetchone()[0])
            self.assertTrue(s._request(dict(mode='verify_certificate', bits=bits, certificate=cert))['valid'])
            altered = []
            for field, value in [('paths', ['00', '1']), ('variables', [8]), ('proof', 'wrong')]:
                candidate = copy.deepcopy(cert)
                candidate[field] = value
                altered.append(candidate)
            for candidate in altered:
                try:
                    checked = s._request(dict(mode='verify_certificate', bits=bits, certificate=candidate))
                    self.assertFalse(checked['valid'])
                except ValueError:
                    pass
            self.assertFalse(s._request(dict(mode='verify_certificate', bits=neg(bits), certificate=cert))['valid'])

    def test_forged_component_witness_is_rejected_even_with_valid_object_hash(self):
        with PersistentSolver(self.path, components=True) as s:
            s.solve(var(0), learn=False)
            row = s.db.execute('SELECT key,object_id FROM component_entries').fetchone()
            entry = s.components.entry(row['key'])
            entry['witness'] = '0'
            with s.db:
                token = s.components.store.put('component_result', entry)[0]
                s.db.execute('UPDATE component_entries SET object_id=?', (token,))
            with self.assertRaisesRegex(ValueError, 'witness rejected'):
                s.solve(var(9), learn=False)
            self.assertEqual(s.stats()['entries'], 1)
            # Semantic audit must not consult the forged proposal component.
            self.assertEqual(s.audit()['checked'], 1)

    def test_prefix_dag_shares_previous_stages_and_shapes(self):
        with PersistentSolver(self.path, components=True) as s:
            for n in (1, 2, 4, 8):
                r = s.solve(conjunction([block(2*i) for i in range(n)]), learn=False)
                self.assertTrue(r['answer'])
            kinds = dict(s.db.execute('SELECT kind,count(*) FROM knowledge_objects GROUP BY kind'))
            # True terminator is a constant component; eight renamed XORs
            # use one shared shape, while each stage has its own final prefix.
            self.assertEqual(kinds['component_shape'], 2)
            self.assertEqual(kinds['component_result'], 2)
            self.assertEqual(kinds['component_prefix'], 8 + 4)
            self.assertEqual(r['components']['acquisitions'], 0)
            self.assertEqual(r['components']['largest_component_variables'], 2)
            self.assertEqual(r['components']['global_variables'], 16)

    def test_random_decompositions_and_mergers_match_truth_tables(self):
        rng = random.Random(179)
        with PersistentSolver(self.path, components=True) as s:
            for _ in range(45):
                clauses = []
                for base in (0, 3):
                    clauses += [[(base+i, bool(rng.randrange(2))) for i in rng.sample(range(3), 2)] for _ in range(7)]
                if rng.randrange(2):
                    clauses += [[(1, False), (4, True)]]
                expected = any(all(any(a[i] == sign for i, sign in c) for c in clauses)
                               for a in itertools.product((False, True), repeat=6))
                self.assertEqual(s.solve(cnf_bits(clauses), learn=False)['answer'], expected)

    def test_corrupt_compressed_object_is_rejected(self):
        with PersistentSolver(self.path, components=True) as s:
            s.solve(block(0), learn=False)
            with s.db:
                s.db.execute("UPDATE knowledge_objects SET payload=? WHERE kind='component_result'", (b'bad',))
            with self.assertRaises(Exception):
                s.solve(block(10), learn=False)
            self.assertEqual(s.stats()['entries'], 1)


@unittest.skipUnless(DEFAULT_INCREMENTAL.is_file(), 'Build incremental bridge first')
class RestartTests(unittest.TestCase):
    setUp = StructureTests.setUp

    def test_learned_clauses_and_definitions_survive_restart(self):
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            r = s.solve(HARD_UNSAT, learn=False)
            self.assertGreater(r['incremental']['archived_new_clauses'], 0)
            old_nodes = r['incremental']['shared_nodes'] - 1
            old_clauses = r['incremental']['archived_clauses']
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            r = s.solve(neg(neg(HARD_UNSAT)), learn=False)
            self.assertFalse(r['answer'])
            self.assertEqual(r['incremental']['restored_nodes'], old_nodes)
            self.assertEqual(r['incremental']['restored_clauses'], old_clauses)
            self.assertEqual(r['incremental']['new_definition_clauses'], 0)
            self.assertEqual(r['backend'], 'cadical')  # independent LRAT still required
            self.assertTrue(s.solve(MIXED, learn=False)['answer'])

    def test_corrupt_saved_clause_cannot_create_false_unsat(self):
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            s.solve(MIXED, learn=False)
            # Hash-valid but semantically false proposal clause: make the
            # restored proposal solver inconsistent with its permanent -1.
            s.incremental.store.append([], [[1]])
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            r = s.solve(neg(neg(MIXED)), learn=False)
            self.assertTrue(r['answer'])
            self.assertEqual(r['incremental']['verdict'], 20)
            self.assertEqual(r['backend'], 'cadical')

    def test_concurrent_sessions_fork_without_mixing_variable_ids(self):
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            s.solve(MIXED, learn=False)
        def run(bits):
            with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
                return s.solve(bits, learn=False)['answer']
        with ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(run, [HARD_UNSAT, conj(var(30), neg(var(31)))]))
        self.assertEqual(answers, [False, True])
        with PersistentSolver(self.path, backend='cadical', incremental=True) as s:
            self.assertTrue(s.solve(neg(neg(MIXED)), learn=False)['answer'])
            self.assertEqual(s.db.execute('SELECT count(DISTINCT session) FROM incremental_sessions').fetchone()[0], 4)
            self.assertEqual(s.audit()['checked'], 4)

    def test_schema_five_migration_preserves_existing_tables(self):
        with PersistentSolver(self.path, learned=True) as s:
            s.solve(MIXED)
            before = {t: list(map(tuple, s.db.execute('SELECT * FROM '+t))) for t in
                      ('results', 'proofs', 'models', 'measurements', 'portfolio', 'active_witness')}
            with s.db:
                s.db.execute('PRAGMA user_version=5')
        with PersistentSolver(self.path, incremental=True, components=True) as s:
            for t, rows in before.items():
                self.assertEqual(rows, list(map(tuple, s.db.execute('SELECT * FROM '+t))))
            self.assertEqual(s.db.execute('PRAGMA user_version').fetchone()[0], 6)


if __name__ == '__main__':
    unittest.main()
