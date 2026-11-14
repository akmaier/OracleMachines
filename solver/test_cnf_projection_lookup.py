from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_projection_lookup import KernelIndex, kernel, signature, search
from experiments.cnf_projection_bridge import discover, check, record_key
from experiments.cnf_pattern_inventory import FORMAT, encode
from experiments.cnf_residual_dag import normalize
from experiments.cnf_coupled_pivots import BudgetedInventory


def explicit(cnf): return [list(c) for c in normalize(cnf)[0]]


class Authority:
    def __init__(self): self.config = {'test': 1}; self.rows = {}
    def _canonical(self, cnf, depth):
        normalized, names = normalize(cnf)
        return normalized, names, encode([FORMAT, self.config, depth, normalized])
    def add(self, cnf, depth=0):
        cnf=explicit(cnf); key=self._canonical(cnf,depth)[2]
        self.rows[key]=dict(cnf=cnf,depth=depth)
        return key
    def _load(self, key): return self.rows.get(key)


def fixture():
    r=json.loads(Path('experiments/results/cnf-projection-bridge/report.json').read_text())
    with gzip.open(r['target_keys']['path']) as f: small,large=json.load(f)
    return json.loads(large)[-1],json.loads(small)[-1]


class ProjectionLookupTests(unittest.TestCase):
    def test_kernel_matches_exhaustive_small_subset_definition(self):
        clauses=[tuple((i+1)*s for i,s in enumerate(signs) if s)
                 for signs in itertools.product((-1,0,1),repeat=3)]
        for size in range(4):
            for selected in itertools.combinations(clauses,size):
                cnf=explicit(selected)
                expected=tuple(tuple(c) for c in cnf if not any(set(d)<set(c) for d in cnf))
                self.assertEqual(kernel(cnf,Counter()),expected)

    def test_real_nonminimal_target_is_found_without_supplying_target(self):
        large,small=fixture(); h=Authority(); source=h.add(large); target=h.add(small)
        index=KernelIndex(':memory:',h.config)
        try:
            for key in (source,target,h.add([[1,2],[-1,2]])):index.add(key,Counter())
            self.assertLess(len(kernel(small,Counter())),len(small))
            records=search(h,source,index)
            self.assertIn((target,16),[(r['target'],r['proof']['variable']) for r in records])
            for r in records:check(large,h._load(r['target'])['cnf'],r['proof'])
        finally:index.close()

    def test_index_and_scan_agree_with_caps_and_depth_binding(self):
        large,small=fixture(); h=Authority(); source=h.add(large); target=h.add(small)
        index=KernelIndex(':memory:',h.config)
        try:
            for key in (source,target,h.add(small,1)):index.add(key,Counter())
            for cap in (0,1,64):
                a=search(h,source,index,target_limit=cap)
                b=search(h,source,index,mode='scan',target_limit=cap)
                self.assertEqual(a,b)
                self.assertTrue(all(r['target']==target for r in a))
            self.assertEqual(search(h,source,index,variable_limit=0),[])
            with self.assertRaises(ValueError):search(h,source,index,pair_limit=True)
        finally:index.close()

    def test_reopen_and_incremental_append_with_real_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'index';h=BudgetedInventory(':memory:',max_depth=0)
            try:
                h.set_admission_budget(32)
                source=h.inspect([[1,2],[-1,3],[2,3,4],[-4,2]])['root']['key']
                target=h.inspect([[-4,2],[2,3]])['root']['key']
                h.set_admission_budget(0)
                index=KernelIndex(path,h.config)
                self.assertEqual(search(h,source,index),[])
                self.assertTrue(index.add(target,Counter()));index.db.commit();index.close()
                index=KernelIndex(path,h.config)
                try:
                    self.assertFalse(index.add(target,Counter()))
                    with patch.object(h,'_discover',side_effect=AssertionError('new recognition')):
                        records=search(h,source,index)
                    self.assertTrue(records);self.assertFalse(h.admitted)
                finally:index.close()
            finally:h.close()

    def test_stale_entries_and_policy_mismatch_are_not_proofs(self):
        large,small=fixture();h=Authority();source=h.add(large);target=h.add(small)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'index';index=KernelIndex(path,h.config)
            index.add(target,Counter());index.db.commit()
            del h.rows[target]
            counts=Counter();self.assertEqual(search(h,source,index,counts),[])
            self.assertGreater(counts['missing_target_misses'],0);index.close()
            with self.assertRaises(ValueError):KernelIndex(path,{'test':2})

    def test_poisoned_signature_and_payload_cannot_supply_a_bridge(self):
        large,small=fixture();h=Authority();source=h.add(large);target=h.add(small)
        wrong=h.add([[1],[-1,2]])
        index=KernelIndex(':memory:',h.config)
        try:
            index.add(target,Counter());sig=index.db.execute('SELECT kernel FROM targets').fetchone()[0]
            index.add(wrong,Counter())
            index.db.execute('DELETE FROM targets WHERE id=?',(hashlib.sha256(target.encode()).digest(),))
            index.db.execute('UPDATE targets SET kernel=?',(sig,))
            self.assertEqual(search(h,source,index),[])
            index.db.execute('UPDATE targets SET id=?',(b'bad digest',))
            with self.assertRaises(ValueError):search(h,source,index)
        finally:index.close()

    def test_edited_sources_agree_with_target_supplied_search(self):
        large,small=fixture();h=Authority();target=h.add(small)
        index=KernelIndex(':memory:',h.config);index.add(target,Counter())
        try:
            variants=[large[:-1],large+[[1]],explicit([[-l for l in large[0]]]+large[1:])]
            for cnf in variants:
                source=h.add(cnf);actual=search(h,source,index)
                expected=discover(explicit(cnf),small)
                self.assertEqual(bool(actual),expected is not None)
                for r in actual:check(explicit(cnf),small,r['proof'])
        finally:index.close()


if __name__=='__main__':unittest.main()
