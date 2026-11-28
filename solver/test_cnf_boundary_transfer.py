from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from experiments import acquire_cnf_boundary_transfer as a
from experiments import compare_cnf_boundary_transfer as c


class BoundaryTransferTests(TestCase):
    def test_signed_transport_every_assignment(self):
        source=[[1,2],[-1,3],[-2,-3],[7,-7]];variant,mapping=a.rename(source,51)
        for values in product((False,True),repeat=4):
            m=dict(zip(sorted(mapping),values));n={abs(w):m[v] if w>0 else not m[v] for v,w in mapping.items()}
            holds=lambda f,x:all(any(x[abs(v)]==(v>0) for v in clause) for clause in f)
            self.assertEqual(holds(source,m),holds(variant,n))

    def test_emit_parse_empty_and_sparse(self):
        for source in ([],[[]],[[12,-200],[12,12],[999,-999]]):
            self.assertEqual(a.parse_dimacs(a.emit(source))[0],source)

    def test_raw_reload_and_binding(self):
        with TemporaryDirectory() as d:
            path=Path(d);raw=path/'input.cnf';raw.write_text(a.emit([[1]]));panel=path/'panel.json'
            c.write(panel,[dict(id='opaque',source=[[1]],raw=c.binding(raw))]);p=dict(panel=c.binding(panel))
            self.assertEqual(c.source_rows(p)[0]['source'],[[1]])
            raw.write_text(a.emit([[-1]]))
            with self.assertRaises(AssertionError):c.source_rows(p)

    def test_parsed_copy_cannot_override_raw(self):
        with TemporaryDirectory() as d:
            path=Path(d);raw=path/'input.cnf';raw.write_text(a.emit([[1]]));panel=path/'panel.json'
            c.write(panel,[dict(id='opaque',source=[[-1]],raw=c.binding(raw))])
            with self.assertRaises(AssertionError):c.source_rows(dict(panel=c.binding(panel)))

    def test_unknown_not_unsat(self):
        for mode in c.MODES:
            proof,evidence,_=c.discover([[1],[-1]],mode,Counter())
            self.assertIsNone(c.check([[1],[-1]],proof)['answer']);c.e.check_evidence([[1],[-1]],evidence)

    def test_unchanged_frozen_limits(self):
        self.assertEqual((c.e.NODE_LIMIT,c.e.PREFIX_LIMIT,c.e.MAX_ROUNDS),(20000,10000,8))
