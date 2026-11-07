from pathlib import Path
import itertools
import json
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.persistent import PersistentSolver
from solver.relations import pack,unpack,project
from solver.resources import Deadline
from solver.manifests import Manifest
from solver.interfaces import counters
from solver.test_fast import var,neg,conj,disj,cnf_bits
from experiments.run_expanded import balanced


def xor(i,j):return conj(disj(var(i),var(j)),disj(neg(var(i)),neg(var(j))))
def chain(n):return balanced([xor(i,i+1) for i in range(n)],conj,'0010')


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'results.sqlite3'

    def test_lazy_rows_remain_unknown_and_are_persistent(self):
        bits=disj(var(0),disj(var(1),var(2)))
        with PersistentSolver(self.path,interfaces=True) as s:
            result=s.expand(add={'clause':bits})
            self.assertTrue(result['answer'])
            self.assertGreater(result['interfaces']['unknown_rows'],0)
            self.assertLess(result['interfaces']['leaf_rows'],8)
            count=s.db.execute('SELECT count(*) FROM interface_rows').fetchone()[0]
            self.assertGreater(count,0)
        with PersistentSolver(self.path,interfaces=True) as s:
            repeated=s.expand(result['state'])
            self.assertTrue(repeated['answer'])
            self.assertEqual(repeated['interfaces']['leaf_rows'],0)
            self.assertGreater(repeated['interfaces']['native_replays'],0)
            self.assertGreater(repeated['interfaces']['native_row_acquisitions'],0)

    def test_poisoned_partial_row_is_rechecked_after_restart(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            result=s.expand(add={'clause':disj(var(0),var(1))})
            with s.db:s.db.execute('UPDATE interface_rows SET answer=1-answer')
        with PersistentSolver(self.path,interfaces=True) as s:
            with self.assertRaises(ValueError):s.expand(result['state'])
            self.assertEqual(s.db.execute('SELECT count(*) FROM expansion_states').fetchone()[0],1)

    def test_delta_broad_leaf_falls_back_and_can_be_removed(self):
        with PersistentSolver(self.path,interfaces=True,max_interface=1) as s:
            broad=disj(var(0),disj(var(1),var(2)))
            a=s.expand(add={'large':broad})
            self.assertTrue(a['answer']);self.assertIsNotNone(a['fallback_reason'])
            b=s.expand(a['state'],remove=['large'])
            self.assertTrue(b['answer']);self.assertIsNone(b['fallback_reason'])
            self.assertTrue(s.expand(a['state'])['answer'])

    def test_invalid_empty_delta_types_are_not_silently_coerced(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            with self.assertRaises(ValueError):s.expand(add=[])
            with self.assertRaises(ValueError):s.expand(remove={})

    def test_invalid_delta_encoding_cannot_be_normalized_into_a_valid_formula(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            with self.assertRaises(ValueError):s.expand(add={'bad':'01x0'})
            self.assertEqual(s.db.execute('SELECT count(*) FROM expansion_states').fetchone()[0],0)

    def test_native_binding_rejects_dropped_constraint(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            s.expand(add={'a':var(0)})
            leaf=next(r[0] for r in s.db.execute('SELECT id FROM interface_nodes') if s.interfaces.read(r[0])['definition']['kind']=='leaf')
            check=s._request(dict(mode='factor_bind',id='forged',bits=conj(var(0),neg(var(0))),active=[leaf]))
            self.assertFalse(check['valid'])

    def test_connected_chain_reuses_small_interfaces(self):
        with PersistentSolver(self.path,interfaces=True,reuse_exact=False) as s:
            a=s.solve(chain(8),learn=False)
            b=s.solve(chain(9),learn=False)
            self.assertTrue(a['answer'] and b['answer'])
            self.assertEqual(b['backend'],'interfaces')
            self.assertLessEqual(b['interfaces']['max_bag'],2)
            self.assertLess(b['interfaces']['node_acquisitions'],8)
            self.assertGreater(b['interfaces']['node_hits'],10)
            self.assertEqual(s.audit()['checked'],2)

    def test_delta_extension_deletion_and_old_snapshot(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            a=s.expand(add={'edge0':xor(0,1),'start':var(0)})
            b=s.expand(a['state'],add={'edge1':xor(1,2),'end':neg(var(2))})
            self.assertFalse(b['answer'])
            c=s.expand(b['state'],remove=['end'])
            self.assertTrue(c['answer'])
            self.assertTrue(s.expand(a['state'])['answer'])
            self.assertEqual(s.expand(a['state'])['interfaces']['input_bytes'],0)
            self.assertEqual(s.db.execute('SELECT count(*) FROM expansion_states').fetchone()[0],3)

    def test_restart_rechecks_saved_evidence_and_reuses_tables(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            a=s.expand(add={'chain':chain(12),'start':var(0)})
        with PersistentSolver(self.path,interfaces=True) as s:
            b=s.expand(a['state'],add={'end':neg(var(12))})
            self.assertFalse(b['answer'])
            self.assertGreater(b['interfaces']['node_hits'],10)
            self.assertGreater(b['interfaces']['native_definitions'],0)

    def test_forged_negative_context_is_rejected(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            a=s.expand(add={'p':var(0),'n':neg(var(0))})
            row=s.db.execute('SELECT evidence FROM expansion_states WHERE id=?',(a['state'],)).fetchone()
            evidence=s.interfaces.store.get(row[0],'expansion_result')
            checked=s._request(dict(mode='factor_query',active=[],answer=False,root=evidence['root']))
            self.assertFalse(checked['valid'])

    def test_all_relation_encodings_roundtrip_and_reject_bad_diagrams(self):
        from solver.relations import dense_pack
        rng=random.Random(41)
        for width in range(9):
            rows=[rng.choice([None,False,True]) for _ in range(1<<width)]
            self.assertEqual(unpack(pack(rows),width),rows)
            self.assertEqual(unpack(dense_pack(rows),width),rows)
        parity=[bool(i.bit_count()%2) for i in range(1024)]
        encoded=pack(parity)
        self.assertEqual(encoded['encoding'],'bdd')
        self.assertEqual(unpack(encoded,10),parity)
        encoded['nodes'][0][1]=3
        with self.assertRaises(ValueError):unpack(encoded,10)

    def test_unknown_is_not_unsat(self):
        relation=[False,None,True,None]
        self.assertEqual(unpack(pack(relation),2),relation)
        scope,rows,choices=project([dict(scope=[0,1],rows=relation)],0,Deadline(2),counters())
        self.assertEqual(scope,[1]);self.assertEqual(rows,[True,None])
        self.assertEqual(choices,[True,None])

    def test_random_formulas_match_independent_truth_tables(self):
        rng=random.Random(812)
        with PersistentSolver(self.path,interfaces=True,max_interface=5) as s:
            for _ in range(60):
                clauses=[[(i,bool(rng.randrange(2))) for i in rng.sample(range(5),3)] for _ in range(20)]
                expected=any(all(any(a[i]==b for i,b in c) for c in clauses) for a in itertools.product((False,True),repeat=5))
                r=s.solve(cnf_bits(clauses),learn=False)
                self.assertEqual(r['answer'],expected)
                self.assertEqual(r['backend'],'interfaces')

    def test_width_overflow_falls_back_without_false_answer(self):
        # A complete four-variable constraint graph exceeds an interface cap 1.
        bits=balanced([xor(i,j) for i in range(4) for j in range(i)],conj,'0010')
        with PersistentSolver(self.path,interfaces=True,max_interface=1) as s:
            r=s.solve(bits,learn=False)
            self.assertFalse(r['answer'])
            self.assertNotEqual(r['backend'],'interfaces')

    def test_avl_history_is_lossless_under_random_updates(self):
        rng=random.Random(81)
        with PersistentSolver(self.path,interfaces=True) as s:
            m=Manifest(s.interfaces.store,Deadline(5),counters());root=None;expected={};history=[]
            for _ in range(100):
                key=str(rng.randrange(30))
                if key in expected and rng.randrange(2):
                    del expected[key]
                    with s.db:root=m.update(root,key,None)
                else:
                    value=str(rng.randrange(100));expected[key]=value
                    with s.db:root=m.update(root,key,value)
                history.append((root,dict(expected)))
            for root,expected in history:self.assertEqual(dict(m.items(root)),expected)

    def test_codec_never_expands_new_payload_and_legacy_remains_readable(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            with s.db:
                a=s.interfaces.store.put('small',[1])[0]
                b=s.interfaces.store.put('large','0'*10000)[0]
            self.assertEqual(s.interfaces.store.get(a,'small'),[1])
            self.assertEqual(s.interfaces.store.get(b,'large'),'0'*10000)
            self.assertTrue(all(r[0]<=r[1] for r in s.db.execute('SELECT length(payload),raw_bytes FROM knowledge_objects')))
            self.assertEqual({r[0] for r in s.db.execute('SELECT codec FROM knowledge_objects')},{'raw','zlib'})

    def test_native_factor_certificate_rejects_changed_original(self):
        bits=conj(var(0),neg(var(0)))
        with PersistentSolver(self.path,interfaces=True) as s:
            self.assertFalse(s.solve(bits,learn=False)['answer'])
            cert=json.loads(s.db.execute('SELECT certificate FROM proofs').fetchone()[0])
            self.assertTrue(s._verify_certificate(bits,cert))
            self.assertFalse(s._verify_certificate(var(0),cert))

    def test_failed_removal_does_not_create_answer_snapshot(self):
        with PersistentSolver(self.path,interfaces=True) as s:
            a=s.expand(add={'x':var(0)})
            with self.assertRaises(KeyError):s.expand(a['state'],remove=['missing'])
            self.assertEqual(s.db.execute('SELECT count(*) FROM expansion_states').fetchone()[0],1)

if __name__=='__main__':unittest.main()
