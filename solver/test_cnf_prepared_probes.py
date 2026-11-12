import copy
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_retained_plans import RetainedPlanInventory
from experiments.cnf_polarity_horn import PolarityHornInventory


def hard_source():
    return json.loads(Path('experiments/results/cnf-polarity-horn/report.json').read_text())['frontiers']['polarity'][1]['cnf']


class PreparedProbeTests(unittest.TestCase):
    def test_open_plan_reuses_probe_evidence_without_claiming_closure(self):
        h = PreparedProbeInventory(max_depth=0)
        try:
            source = hard_source(); old = h.prepared.inspect(source)
            self.assertFalse(old['summary']['closed'])
            result = h.inspect(source)
            self.assertFalse(result['summary']['closed'])
            self.assertEqual(result['metrics']['prepared_probe_reuses'], 1)
            self.assertIsNone(h._pending_probe)
            self.assertLessEqual(h.probe_cache_state()['bytes'], h.probe_cache_state()['limit_bytes'])
        finally: h.close()

    def test_cold_invalid_trace_rejected_and_pending_cleared(self):
        h = PreparedProbeInventory(max_depth=0)
        try:
            source = hard_source(); result = h.prepared.inspect(source)
            key = result['root']['key']; node = copy.deepcopy(h.prepared._load(key))
            node['profile']['probing']['attempts'] = []
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?', (encode(node), key))
            with self.assertRaises(ValueError): h.inspect(source)
            self.assertIsNone(h._pending_probe)
            self.assertEqual(h.probe_cache_state()['entries'], 0)
            self.assertTrue(h.inspect([(1,)])['summary']['closed'])
        finally: h.close()

    def test_different_source_and_settings_do_not_reuse_hint(self):
        h = PreparedProbeInventory(max_depth=0)
        try:
            source = hard_source(); h.prepared.inspect(source)
            changed = source + [[999]]
            # Directly stage a known source hint, then request another source.
            cnf, _, key = h.prepared._canonical(source, 0)
            hint = h.prepared._load(key)
            h._unclosed_hint(cnf, 0, hint)
            other, _, _ = h._canonical(changed, 0)
            h._discover_probes(other)
            self.assertEqual(h.counts['prepared_probe_reuses'], 0)
            h._pending_probe = None
            h.config['probe_limit'] = 0
            h._unclosed_hint(cnf, 0, hint)
            self.assertIsNone(h._pending_probe)
            self.assertEqual(h.counts['prepared_probe_incompatible'], 1)
        finally: h.close()

    def test_exhaustive_small_and_seeded_prepared_archives_match(self):
        clauses = [tuple(s*(i+1) for i,s in enumerate(signs) if s)
                   for signs in itertools.product((-1,0,1), repeat=2)]
        sources = [[c for i,c in enumerate(clauses) if mask>>i & 1] for mask in range(512)]
        rng = random.Random(202611121100)
        sources += [[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,7),3))
                     for _ in range(24)] for _ in range(30)]
        sources += [hard_source()]
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = []; results = []; hits = []
            for cls in (RetainedPlanInventory, PreparedProbeInventory):
                path = Path(tmp) / (cls.__name__ + '.db')
                old = PolarityHornInventory(path, max_depth=1)
                for source in sources: old.inspect(source)
                old.close(); h = cls(path, max_depth=1); current = []; reused = 0
                for source in sources:
                    r = h.inspect(source); current.append((r['root'], r['profile'], r['summary']))
                    reused += r['metrics'].get('prepared_probe_reuses', 0)
                snapshots.append({table: list(h.db.execute(f'SELECT * FROM {table} ORDER BY id'))
                                  for table in ('cnf_patterns_v1', 'cnf_pattern_sources_v1')})
                results.append(current); hits.append(reused); h.close()
                raw = path.read_bytes(); h = cls(path, max_depth=1)
                for source in sources:
                    r = h.inspect(source)
                    self.assertEqual(r['metrics'].get('inserted_nodes', 0), 0)
                    self.assertEqual(r['metrics']['inserted_sources'], 0)
                h.close(); self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(encode(results[0]), encode(results[1]))
            self.assertEqual(snapshots[0], snapshots[1]); self.assertGreater(hits[1], 0)

    def test_empty_history_remains_identical(self):
        a, b = RetainedPlanInventory(max_depth=1), PreparedProbeInventory(max_depth=1)
        try:
            source = hard_source(); x, y = a.inspect(source), b.inspect(source)
            self.assertEqual(encode(x['profile']), encode(y['profile']))
            self.assertEqual(x['summary'], y['summary']); self.assertEqual(x['root'], y['root'])
            self.assertEqual(y['metrics'].get('prepared_probe_reuses', 0), 0)
        finally: a.close(); b.close()


if __name__ == '__main__': unittest.main()
