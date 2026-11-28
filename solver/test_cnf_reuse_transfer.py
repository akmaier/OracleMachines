from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from experiments import compare_cnf_reuse_transfer as s
from solver.test_cnf_selective_learning import SQUARE


class ReuseTransferTests(TestCase):
    def test_explicit_caps_and_parent_free_fresh(self):
        with patch.object(s, 'parent_data', side_effect=AssertionError):
            for mode, limit in [('parent20000', 20000), ('fresh8000', 8000)]:
                proof, diag = s.discover({'source': SQUARE}, mode, Counter())
                self.assertEqual(proof['kind'], 'unsat')
                self.assertEqual(diag['expansion']['node_limit'], limit)
        with self.assertRaises(KeyError): s.discover({'source': []}, 'bad', Counter())

    def test_empty_fallback(self):
        deleted, variants = s.edits([], {'derivations': []})
        self.assertIsNone(deleted)
        self.assertEqual(variants, [('deletion', []), ('bridge', [[1, 102], [-102]])])

    def test_no_derivation_fallback_uses_canonical_order(self):
        source = [[37, 11], [-11], [37, 11]]
        deleted, variants = s.edits(source, {'derivations': []})
        self.assertEqual(deleted, 0)
        self.assertEqual(variants[0][1], list(map(list, s.e.canonical(source, Counter())[1:])))
        self.assertEqual(variants[1][1][-2:], [[11, 138], [-138]])

    def test_derivation_selects_original_premise(self):
        proof, _ = s.discover({'source': SQUARE}, 'parent20000', Counter())
        deleted, variants = s.edits(SQUARE, proof)
        self.assertEqual(deleted, proof['derivations'][0][0])
        self.assertNotIn(list(s.e.canonical(SQUARE, Counter())[deleted]), variants[0][1])

    def test_all_parent_kinds_included(self):
        for source, limit, kind in [([[1]], 20000, 'sat'), (SQUARE, 20000, 'unsat'), (SQUARE, 0, 'unknown')]:
            proof, _ = s.e.search(source, s.e.baseline.prior.prior.proposal(source, Counter()), node_limit=limit)
            self.assertEqual(proof['kind'], kind)
            self.assertEqual([k for k, _ in s.edits(source, proof)[1]], ['deletion', 'bridge'])

    def test_parent_sat_witness_is_not_inherited(self):
        source = [[1]]; parent, _ = s.discover({'source': source}, 'parent20000', Counter())
        with patch.object(s, 'parent_data', return_value=(source, parent)):
            proof, _ = s.discover({'source': [[1], [-1]]}, 'reuse8000', Counter())
        self.assertEqual(proof['kind'], 'unsat')

    def test_parent_raw_hash_checked(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.cnf'; path.write_text(s.emit([[1]])); raw = s.binding(path)
            path.write_text(s.emit([[-1]]))
            with self.assertRaises(AssertionError): s.parent_data({'parent_raw': raw}, Counter())

    def test_parent_proof_hash_checked(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.cnf'; path.write_text(s.emit([[1]]))
            cert = Path(temp) / 'proof.json'; s.write(cert, {'kind': 'sat'}); binding = s.binding(cert)
            s.write(cert, {'kind': 'unknown'})
            with self.assertRaises(AssertionError):
                s.parent_data({'parent_raw': s.binding(path), 'parent_source': [[1]], 'parent_certificate': binding}, Counter())
