from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import random
import unittest

from experiments.cnf_affine_completion import complete
from experiments.cnf_affine_negative import NegativeStore, FORMAT, TABLE, CHAIN, compile_proof, check_negative, compose, check_composed
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_clause_deletion_guard import FORMAT as GUARD
from solver.test_cnf_affine_completion import parity, truth


def exhausted():
    return parity((1,2),0)+[[1,3],[1,-3],[-2,4],[-2,-4]]


class AffineNegativeTests(unittest.TestCase):
    def setup_store(self):
        solver=ResidualSolver(node_limit=0);self.addCleanup(solver.close)
        return solver,NegativeStore(solver,create=True)

    def test_both_negative_kinds_publish_without_search(self):
        for source,kind in ((exhausted(),'exhaustion'),(parity((1,2,3),0)+parity((1,2,3),1),'linear-conflict')):
            s,store=self.setup_store();_,e=complete(s,source)
            with patch.object(s,'_expand',side_effect=AssertionError('Search')),patch.object(s,'_store',side_effect=AssertionError('Native publication')):
                child=store.publish(source,e);record=compose(store,source,[],child)
                check_composed(store,record)
            self.assertFalse(child['answer']);self.assertEqual(store.storage()[0],1);self.assertEqual(s.archive_storage()[0],0)
            self.assertEqual(store.read(child['root'])['proof']['decision']['kind'],kind)
            self.assertEqual(record['format'],CHAIN)
            self.assertIsNone(s._read(child['root']))
            self.assertFalse(store.lookup(source)['answer'])
            self.assertIsNone(store.lookup([[100,101]]))

    def test_cold_replay_signed_source_and_native_rows_unchanged(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'archive';s=ResidualSolver(path);store=NegativeStore(s,create=True)
            try:
                s.solve([[9],[-9]]);before=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
                source=[[-17*l for l in c[::-1]] for c in exhausted()[::-1]];_,e=complete(s,source)
                child=store.publish(source,e);record=compose(store,source,[],child)
                self.assertEqual(before,dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally:s.close()
            s=ResidualSolver(path);store=NegativeStore(s)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Cold search')),patch.object(s,'_store',side_effect=AssertionError('Cold write')):
                    check_composed(store,record)
                    self.assertFalse(s.solve([[9],[-9]])['answer'])
            finally:s.close()

    def test_guard_composition_checks_native_premise(self):
        s=ResidualSolver();self.addCleanup(s.close);store=NegativeStore(s,create=True)
        target=exhausted();source=target+[[99]];stronger=source+[[-99]]
        premise=s.solve(stronger);guard=dict(format=GUARD,stronger=stronger,stronger_root=premise['root'],removed_clause=[-99])
        _,e=complete(s,target);child=store.publish(target,e)
        record=compose(store,source,[guard],child);self.assertFalse(record['answer'])
        bad=deepcopy(record);bad['guards'][0]['stronger_root']='wrong'
        with self.assertRaises(ValueError):check_composed(store,bad)
        bad=deepcopy(record);bad['format']='checked-guard-chain-v1'
        with self.assertRaises(ValueError):check_composed(store,bad)

    def test_rejects_incomplete_basis_coverage_and_satisfied_clause(self):
        s,store=self.setup_store();source=exhausted();_,e=complete(s,source)
        bad=deepcopy(e);bad['space']['directions'].pop()
        with self.assertRaises(ValueError):store.publish(source,bad)
        bad=deepcopy(e);bad['rejected'].pop()
        with self.assertRaises(ValueError):store.publish(source,bad)
        cnf,names,_=s._canonical(source);p=compile_proof(e)
        candidate=e['space']['particular']
        cid=next(i for i in e['affine']['leftovers'] if any(bool(candidate&(1<<(abs(l)-1)))==(l>0) for l in cnf[i]))
        p['decision']['rejected'][0]=cid
        with self.assertRaises(ValueError):check_negative(cnf,len(names),p,Counter())
        self.assertEqual(store.storage()[0],0)

    def test_source_extraction_row_and_header_corruption(self):
        s,store=self.setup_store();source=parity((1,2,3),0)+parity((1,2,3),1);_,e=complete(s,source)
        for mutate in (lambda x:x['affine']['equations'][0]['clauses'].pop(),
                       lambda x:x['affine']['reductions'][-1].update(rhs=0),
                       lambda x:x.update(root='wrong')):
            bad=deepcopy(e);mutate(bad)
            with self.assertRaises(ValueError):store.publish(source,bad)
        child=store.publish(source,e);node=deepcopy(store.read(child['root']))
        node['format']='cnf-residual-v1'
        with self.assertRaises(ValueError):store.verify(child['root'],node)
        node=deepcopy(store.read(child['root']));node['proof']['decision']['row']=True
        with self.assertRaises(ValueError):store.verify(child['root'],node)

    def test_duplicate_retains_first_payload_and_checks_stored_corruption(self):
        s,store=self.setup_store();source=exhausted();_,e=complete(s,source);child=store.publish(source,e)
        before=s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(child['root'],)).fetchone()[0]
        store.publish(source,e)
        self.assertEqual(before,s.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?',(child['root'],)).fetchone()[0])
        # Deliberate corruption ends the owned append-only session; a new store
        # must reject it and duplicate publication must not hide it in memory.
        bad=json.loads(before);bad['proof']['decision']['rejected']=[]
        with s.db:s.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?',(json.dumps(bad),child['root']))
        with self.assertRaises(ValueError):NegativeStore(s).read(child['root'])
        with self.assertRaises(ValueError):store.publish(source,e)

    def test_dimension_cap_precedes_space_check(self):
        s,store=self.setup_store();source=parity((1,2),0)+[[v,v+1] for v in range(3,13)]
        _,e=complete(s,source);self.assertEqual(e['status'],'free-cap')
        e.update(status='space-exhausted',space={},rejected=[])
        with patch('experiments.cnf_affine_negative.check_space',side_effect=AssertionError('Over-cap basis')):
            with self.assertRaises(ValueError):store.publish(source,e)
        _,positive=complete(s,parity((1,2),0))
        with self.assertRaises(ValueError):compile_proof(positive)

    def test_exhaustive_small_and_random_mixtures(self):
        rng=random.Random(2026111805);pool=parity((1,2,3),0)+parity((1,2,3),1)
        sources=[[c for i,c in enumerate(pool) if mask>>i&1] for mask in range(256)]
        for _ in range(128):
            source=parity(tuple(rng.sample(range(1,7),3)),rng.randrange(2))
            source += [[rng.choice((-1,1))*v for v in rng.sample(range(1,7),rng.randrange(1,5))] for _ in range(rng.randrange(0,17))]
            sources.append(source)
        negatives=0
        for source in sources:
            s=ResidualSolver();store=NegativeStore(s,create=True)
            try:
                choice,e=complete(s,source)
                if e['status'] in ('linear-conflict','space-exhausted'):
                    self.assertFalse(truth(source));negatives+=1
                    child=store.publish(source,e);self.assertFalse(child['answer'])
                    check_composed(NegativeStore(s),compose(store,source,[],child))
                elif choice:self.assertTrue(truth(source))
            finally:s.close()
        self.assertGreater(negatives,30)


if __name__=='__main__':unittest.main()
