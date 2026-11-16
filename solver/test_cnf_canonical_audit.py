from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from experiments.cnf_canonical_audit import CanonicalAuditInventory,audit,base
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_canonical_source import canonical_source


class CanonicalAuditTests(unittest.TestCase):
    def fixture(self,path,queries_path):
        h=base.CompleteAdmissionInventory(path,**base.OPTIONS);base.split.initialize(h);h.set_admission_budget(128)
        source=base.load('solver/fixtures/trace-split.json');roots=[h._edge(source,d)['key'] for d in (0,1)]
        ScopedNestedRefinement(h,roots[0]).batch(state_limit=128,pair_limit=8)
        base.write(queries_path,[dict(case=0,source=source,roots=roots)])
        return h,dict(options=base.OPTIONS,queries=dict(path=str(queries_path)))

    def test_complete_audits_match_frozen_checker_and_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,protocol=self.fixture(path,Path(td)/'q');h.close();before=base.sha(path)
            plain=audit(path,protocol);fast=audit(path,protocol,canonical=True)
            from experiments.compare_cnf_scoped_refinement import audit as frozen
            reference=frozen(path,protocol)
            for k in ('coverage','patterns','pairs','original_bindings','no_acquisition'):
                self.assertEqual(plain[k],fast[k]);self.assertEqual(plain[k],reference[k])
            self.assertGreater(fast['normalization_counts']['canonical_order_reuses'],0)
            self.assertEqual(before,base.sha(path))

    def test_all_verifier_views_keep_original_keys_and_fallbacks(self):
        from experiments.cnf_expanded_coverage import verifier_views
        old=base.CompleteAdmissionInventory(':memory:',**base.OPTIONS);fast=CanonicalAuditInventory(':memory:',**base.OPTIONS)
        try:
            for (_,a),(_,b) in zip(verifier_views(old),verifier_views(fast),strict=True):
                for source in ([],[[]],[[1,-2],[2,3]],[[-9,7],[7,9]],[[1,-1],[2,2]],[[3],[1]]):
                    self.assertEqual(a._canonical(source,0),b._canonical(source,0))
            source=[[-1,2],[1,2]];a=canonical_source(source,Counter());source[0][1]=3
            self.assertNotEqual(a,canonical_source(source,Counter()))
        finally:old.close();fast.close()

    def test_forged_required_record_and_unrelated_record_are_rejected(self):
        for unrelated in (False,True):
            with self.subTest(unrelated=unrelated),tempfile.TemporaryDirectory() as td:
                path=Path(td)/'h';h,protocol=self.fixture(path,Path(td)/'q')
                try:
                    if unrelated:
                        h.set_admission_budget(128);root=h._edge(((1,2),(-1,2)),0)['key']
                        record=base.split.acquire_record(h,root,1,Counter());identity=base.split.record_key(record)
                    else:
                        identity,payload=h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} LIMIT 1').fetchone();record=base.load_json(payload)
                    bad=copy.deepcopy(record);bad['branches'].pop()
                    h.db.execute(f'UPDATE {base.split.TABLE} SET payload=? WHERE id=?',(base.encode(bad),identity));h.db.commit()
                finally:h.close()
                for mode in (False,True):
                    with self.assertRaises(ValueError):audit(path,protocol,canonical=mode)

    def test_foreign_original_or_noncanonical_stored_node_fails(self):
        for kind in ('original','node'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                path=Path(td)/'h';q=Path(td)/'q';h,protocol=self.fixture(path,q)
                try:
                    if kind=='original':
                        data=base.load(q);data[0]['source']=[[123]];base.write(q,data)
                    else:
                        key,payload=h.db.execute('SELECT id,payload FROM cnf_patterns_v1 WHERE length(payload)>2000 LIMIT 1').fetchone()
                        node=base.load_json(payload);node['cnf'].append(list(node['cnf'][0]))
                        h.db.execute('UPDATE cnf_patterns_v1 SET payload=? WHERE id=?',(base.encode(node),key));h.db.commit()
                finally:h.close()
                for mode in (False,True):
                    with self.assertRaises((ValueError,AssertionError)):audit(path,protocol,canonical=mode)


if __name__=='__main__':unittest.main()
