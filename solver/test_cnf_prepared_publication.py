from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile,unittest
from experiments import cnf_prepared_publication as candidate,cnf_layered_feedback as prior
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_stopped_support import conditional_unit
from solver.test_cnf_layered_feedback import fixture,layers


def rows(s):return list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))


class PreparedPublicationTests(unittest.TestCase):
    def test_preparation_snapshots_input_and_transports_sparse_names(self):
        s=prior.native.ResidualSolver();self.addCleanup(s.close);raw=[[-100],[100]];counts=Counter()
        cnf,names,key,publish=candidate.prepare_frame(s,raw,counts);self.assertEqual(names,(100,));raw[0][0]=200
        _,trace,conflict=prior.native.propagate(cnf,Counter());before=s.counts['normalization_literal_visits']
        publish(dict(kind='units',trace=trace,conflict=conflict))
        self.assertEqual(s.counts['normalization_literal_visits'],before);self.assertFalse(s._read(key)['answer'])
        self.assertNotIn('_canonical',s.__dict__);self.assertEqual(counts['prepared_header_reuses'],1)
        self.assertEqual(s._canonical(raw)[:2],prior.native.normalize(raw))

    def test_invalid_input_and_proof_still_fail_and_restore(self):
        s=prior.native.ResidualSolver();self.addCleanup(s.close)
        for raw in ([[True]],[[1.0]],[[0]],[[None]],[["1"]]):
            with self.assertRaises(ValueError):candidate.prepare_frame(s,raw,Counter())
        cnf,_,key,publish=candidate.prepare_frame(s,[[1]],Counter())
        for proof in (dict(kind='empty'),dict(kind='unknown'),dict(kind='units',trace=[[1,99]],conflict=0),dict(kind='split',variable=1,low='missing',high='missing')):
            with self.assertRaises(ValueError):publish(proof)
            self.assertEqual(rows(s),[]);self.assertNotIn('_canonical',s.__dict__)
        with self.assertRaises(ValueError):s._store(key,dict(format=prior.native.FORMAT,cnf=[[True]],answer=False,proof=dict(kind='empty')))

    def test_parent_children_keep_independent_relation_checks(self):
        s=prior.native.ResidualSolver();self.addCleanup(s.close);source=prior.native.normalize([[-1,-2],[-1,2],[1,-2],[1,2]])[0]
        children=[]
        for bit in (False,True):
            cnf,_,key,publish=candidate.prepare_frame(s,prior.native.restrict_scan(source,{1:bit}),Counter())
            _,trace,conflict=prior.native.propagate(cnf,Counter());publish(dict(kind='units',trace=trace,conflict=conflict));children.append(key)
        _,_,key,publish=candidate.prepare_frame(s,source,Counter());before=s.counts['normalization_literal_visits']
        publish(dict(kind='split',variable=1,low=children[0],high=children[1]));self.assertFalse(s._read(key)['answer'])
        self.assertGreater(s.counts['normalization_literal_visits'],before)
        with self.assertRaises(ValueError):publish(dict(kind='split',variable=1,low='wrong',high=children[1]))
        self.assertNotIn('_canonical',s.__dict__)

    def test_all_small_frames_match_original_normalizer(self):
        clauses=[[],[1],[-1],[2],[-2],[1,1],[-1,1],[2,1],[-2,1],[100]]
        s=prior.native.ResidualSolver();self.addCleanup(s.close)
        for n in range(4):
            for parts in product(clauses,repeat=n):
                raw=list(parts);frame=candidate.prepare_frame(s,raw,Counter());cnf,names=prior.native.normalize(raw)
                self.assertEqual(frame[:3],(cnf,names,prior.native.token(cnf,Counter())))

    def test_layered_payloads_unchanged_with_headers_and_context_frames(self):
        source=fixture();seed,cl,new=layers(source);p=prior.discover(source,[],seed,cl,new,Counter())
        for selected in (False,True):
            outputs=[];metrics=[]
            for mode in ('baseline','headers','prepared'):
                s=prior.native.ResidualSolver();counts=Counter()
                try:
                    if mode=='baseline':key=prior.compile_program(s,source,[],seed,cl,new,p,counts,select_support=selected)
                    else:key=candidate.compile_program(s,source,[],seed,cl,new,p,counts,select_support=selected,reuse_frames=mode=='prepared')
                    self.assertFalse(s._read(key)['answer']);outputs.append(rows(s));metrics.append((counts,dict(s.counts)))
                    self.assertNotIn('_canonical',s.__dict__)
                finally:s.close()
            self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0],outputs[2])
            self.assertLess(metrics[2][1]['normalization_literal_visits'],metrics[0][1]['normalization_literal_visits'])
            for i in (1,2):self.assertEqual(metrics[0][1]['verified_nodes'],metrics[i][1]['verified_nodes'])
            if not selected:self.assertGreater(metrics[2][0]['prepared_context_reuses'],0)

    def test_checked_guards_and_both_cold_readers(self):
        source=fixture();ts=[conditional_unit(((-6,-1,3),(-1,3,6)),[[1,True],[3,False]],Counter())];seed,cl,new=layers(source,ts,limit=1);p=prior.discover(source,ts,seed,cl,new,Counter())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';s=prior.native.ResidualSolver(path)
            try:
                key=candidate.compile_program(s,source,ts,seed,cl,new,p,Counter());before=rows(s)
                self.assertEqual(key,candidate.compile_program(s,source,ts,seed,cl,new,p,Counter()));self.assertEqual(before,rows(s))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                r=cls(path)
                try:self.assertFalse(r._read(key)['answer'])
                finally:r.close()

    def test_bad_portable_layer_rejected_before_warm_reuse(self):
        source=fixture();seed,cl,new=layers(source);p=prior.discover(source,[],seed,cl,new,Counter());s=prior.native.ResidualSolver();self.addCleanup(s.close)
        candidate.compile_program(s,source,[],seed,cl,new,p,Counter());before=rows(s)
        bad=deepcopy(new);bad['probes'][0]['proof']['conflict']=99999
        with self.assertRaises(ValueError):candidate.compile_program(s,source,[],seed,cl,bad,p,Counter())
        self.assertEqual(before,rows(s));self.assertNotIn('_canonical',s.__dict__)

    def test_exceptions_preserve_existing_canonical_override(self):
        s=prior.native.ResidualSolver();self.addCleanup(s.close);ordinary=s._canonical;seen=[]
        def custom(raw):seen.append(raw);return ordinary(raw)
        s._canonical=custom;_,_,_,publish=candidate.prepare_frame(s,[[1]],Counter())
        with self.assertRaises(ValueError):publish(dict(kind='empty'))
        self.assertIs(s._canonical,custom);s._canonical([[1]]);self.assertEqual(len(seen),2)


if __name__=='__main__':unittest.main()
