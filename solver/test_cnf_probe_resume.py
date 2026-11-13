from collections import Counter
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from experiments.continue_cnf_probes import lineage, restore_report
from experiments.compare_cnf_probe_continuation import TABLES, digests, export_delta, compressed, sha


class ProbeResumeTests(unittest.TestCase):
    def fixture(self, tmp):
        seed = tmp/'seed'; db = sqlite3.connect(seed)
        for t in TABLES:
            db.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            db.execute(f'INSERT INTO {t} VALUES (?,?)', ('old','immutable'))
        db.commit(); db.close()
        previous = tmp/'previous.json'; previous.write_text('{}')
        reports = []; history = seed
        for i in range(2):
            expanded = tmp/f'history{i}'; shutil.copyfile(history,expanded); db = sqlite3.connect(expanded)
            for t in TABLES: db.execute(f'INSERT INTO {t} VALUES (?,?)', (f'new{i}',f'payload{i}'))
            db.commit(); db.close(); delta = tmp/f'delta{i}'; export_delta(history,expanded,delta)
            archive = tmp/f'delta{i}.gz'; compressed(delta,archive)
            report = dict(fingerprints={},seed_table_digests=digests(history),logical_table_digests=digests(expanded),
                baseline_closed=[False],final_closed=[False],
                delta=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta)))
            if i == 0: report['source_report_sha256'] = sha(previous)
            else: report['parent'] = dict(path=str(reports[-1]),sha256=sha(reports[-1]))
            path = tmp/f'report{i}.json'; path.write_text(json.dumps(report)); reports.append(path); history = expanded
        return seed,previous,reports,history

    def context(self, seed, previous, reports):
        def initial(path, tmp):
            shutil.copyfile(seed,path)
            return dict(final_closed=[False])
        return patch.multiple('experiments.continue_cnf_probes',BASE=reports[0],PREVIOUS=previous,restore=initial)

    def test_two_generation_reconstruction_preserves_every_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); seed,previous,reports,expected = self.fixture(tmp)
            before = {p:sha(p) for p in (seed,expected,*reports)}
            with self.context(seed,previous,reports):
                self.assertEqual([p for p,_ in lineage(reports[-1])],reports)
                result = restore_report(reports[-1],tmp/'restored',tmp)
            self.assertEqual(result['logical_table_digests'],digests(expected))
            self.assertEqual(digests(tmp/'restored'),digests(expected))
            self.assertEqual({p:sha(p) for p in before},before)

    def test_changed_parent_and_unknown_lineage_fail_before_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); seed,previous,reports,_ = self.fixture(tmp)
            with self.context(seed,previous,reports):
                reports[0].write_text(reports[0].read_text()+'\n')
                with self.assertRaisesRegex(ValueError,'Changed checkpoint parent'): lineage(reports[-1])
                unknown = tmp/'unknown'; unknown.write_text(json.dumps(dict(fingerprints={})))
                with self.assertRaisesRegex(ValueError,'Missing checkpoint parent'): lineage(unknown)

    def test_incompatible_baseline_and_corrupted_delta_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); seed,previous,reports,_ = self.fixture(tmp)
            report = json.loads(reports[-1].read_text()); report['baseline_closed'] = [True]
            reports[-1].write_text(json.dumps(report))
            with self.context(seed,previous,reports):
                with self.assertRaisesRegex(ValueError,'Incorrect checkpoint baseline'):
                    restore_report(reports[-1],tmp/'bad-baseline',tmp)
                report['baseline_closed'] = [False]; reports[-1].write_text(json.dumps(report))
                Path(report['delta']['path']).write_bytes(b'corrupted')
                with self.assertRaisesRegex(ValueError,'Changed checkpoint delta'):
                    restore_report(reports[-1],tmp/'bad-delta',tmp)

    def test_real_restart_advances_only_the_next_block(self):
        from solver.test_cnf_probe_continuation import ProbeContinuationTests
        from experiments.cnf_probe_continuation import ContinuationRoutes, search, TABLE
        from experiments.cnf_failed_literal import discover_probes
        helper = ProbeContinuationTests()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history'; h = helper.history(path); root = helper.seed(h,'clear')
            routes = ContinuationRoutes(h)
            for _ in range(2): search(h,root,routes,Counter(),state_limit=0,source_limit=1)
            saved = dict(h.db.execute(f'SELECT id,payload FROM {TABLE}')); h.close()
            h = helper.history(path); routes = ContinuationRoutes(h); counts = Counter()
            with patch('experiments.cnf_probe_continuation.discover_probes',wraps=discover_probes) as discovery:
                result = search(h,root,routes,counts,state_limit=0,source_limit=1)
            self.assertEqual(discovery.call_count,1)
            self.assertEqual([v['offset'] for v in result['visits']],[8])
            self.assertEqual(counts['probe_attempts'],8)
            self.assertEqual(counts['reused_prefix_attempts'],16)
            self.assertEqual(len(h.admitted),0)
            for key,payload in saved.items():
                self.assertEqual(h.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(key,)).fetchone(),(payload,))
            h.close()

    def test_opportunity_distinguishes_pending_and_exhausted_open_sources(self):
        from solver.test_cnf_probe_continuation import ProbeContinuationTests
        from experiments.cnf_probe_continuation import ContinuationRoutes
        from experiments.continue_cnf_probes import opportunity
        helper = ProbeContinuationTests()
        with tempfile.TemporaryDirectory() as tmp:
            h = helper.history(Path(tmp)/'history')
            clear = helper.seed(h,'clear'); forced = helper.seed(h,'forced')
            routes = ContinuationRoutes(h)
            initial = opportunity(h,routes,[clear,forced])
            self.assertEqual(len(initial['unstarted']),2)
            for _ in range(5): routes.advance(h,clear,Counter())
            routes.advance(h,forced,Counter()); _,record,target = routes.advance(h,forced,Counter())
            pending = opportunity(h,routes,[clear,forced])
            rows = {row['source_sha256']:row for row in pending['rows']}
            from experiments.compare_cnf_probe_continuation import sha_key
            self.assertEqual(rows[sha_key(clear)]['remaining_ranked_candidates'],0)
            self.assertEqual(rows[sha_key(clear)]['open_selected_cases'],[0])
            self.assertTrue(rows[sha_key(forced)]['pending'])
            self.assertEqual(rows[sha_key(forced)]['open_selected_cases'],[1])
            h.set_admission_budget(32); h._edge(target,0); routes.refresh(h)
            acquired = opportunity(h,routes,[clear,forced])
            row = next(row for row in acquired['rows'] if row['source_sha256']==sha_key(forced))
            self.assertFalse(row['pending']); self.assertEqual(row['open_selected_cases'],[])
            h.close()


if __name__ == '__main__': unittest.main()
