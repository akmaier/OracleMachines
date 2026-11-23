from copy import deepcopy
from itertools import product
from unittest.mock import patch
import json
import unittest
from experiments.cnf_conditional_unit_support import extract, materialize
from experiments.cnf_conditional_unit_cache import compact, check_cache
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_probed_partition import acquire


class ConditionalCacheTests(unittest.TestCase):
    def fixture(self):
        source = list(product((-1, 1), (-2, 2), (-3, 3)))
        s = ConsequencePrioritySolver(leaves=False)
        self.addCleanup(s.close)
        self.assertEqual(acquire(s, source, 256)['status'], 'unsat')
        return source, extract(s, source)[0]

    def test_roundtrip_materializes_in_empty_solver_without_search(self):
        source, bundle = self.fixture()
        cache = check_cache(json.loads(json.dumps(compact(bundle))))
        s = ConsequencePrioritySolver()
        self.addCleanup(s.close)
        with patch.object(s, '_expand', side_effect=AssertionError('Fresh search')):
            for entry in cache['entries']:
                result = materialize(s, source, entry['template'])
                self.assertFalse(s._read(result['root'])['answer'])
        self.assertNotIn('origin', cache)
        self.assertNotIn('tree', cache)

    def test_no_mutable_alias_with_archived_bundle(self):
        _, bundle = self.fixture()
        before = deepcopy(bundle)
        cache = compact(bundle)
        cache['entries'][0]['template']['trace'].clear()
        self.assertEqual(bundle, before)

    def test_corrupted_proof_or_schema_rejected(self):
        _, bundle = self.fixture()
        original = compact(bundle)
        variants = []
        cache = deepcopy(original); cache['entries'][0]['template']['conflict'] = True; variants.append(cache)
        cache = deepcopy(original); cache['entries'][0]['template']['assumptions'] = []; variants.append(cache)
        cache = deepcopy(original); cache['entries'][0]['whole_answer'] = False; variants.append(cache)
        cache = deepcopy(original); cache['format'] = 'unknown'; variants.append(cache)
        for cache in variants:
            with self.assertRaises(ValueError):
                check_cache(cache)
