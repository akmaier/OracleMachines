from collections import Counter
from copy import deepcopy
from itertools import product
import unittest
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_probe_census import GuardProbeObserver,proposals,analyse_event,decode_key
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_fresh_mixtures import attempt,generate


class GuardProbeCensusTests(unittest.TestCase):
    def event(self,source,templates,fixed,subset=None):
        raw=native.restrict_scan(source,fixed,Counter()) if subset is None else subset
        cnf,names=native.normalize(raw);mapping=dict(enumerate(names,1));c=Counter()
        return dict(root=native.token(cnf,c),mapping=[list(p) for p in mapping.items()],fixed=[list(p) for p in fixed.items()],
            proposals=proposals(templates,range(len(templates)),mapping,fixed,c),tried=[])

    def test_local_probe_certificate_after_coordinate_renaming(self):
        source=native.normalize([[-1,-2,3],[-1,-2,-3]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter());e=self.event(source,[t],{1:True})
        r=analyse_event(source,[t],e);self.assertTrue(r['whole_residual']);self.assertEqual(len(r['candidates']),1)
        q=r['candidates'][0];self.assertEqual((q['variable'],q['value']),(1,True));self.assertIsNotNone(q['node'])
        s=native.ResidualSolver();self.addCleanup(s.close);s._store(q['root'],q['node']);self.assertFalse(s._read(q['root'])['answer'])

    def test_full_source_guard_is_not_a_subset_certificate(self):
        source=native.normalize([[-1,-2],[2,3,4]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter())
        e=self.event(source,[t],{1:True},subset=((2,3,4),))
        r=analyse_event(source,[t],e);self.assertFalse(r['whole_residual']);self.assertEqual(len(r['candidates']),1)
        self.assertIsNone(r['candidates'][0]['node'])

    def test_tried_polarity_and_different_variable_are_distinct(self):
        source=native.normalize([[-1,-2,3],[-1,-2,-3]])[0];t=conditional_unit(source,[[1,True],[2,True]],Counter())
        e=self.event(source,[t],{1:True});e['tried']=[dict(variable=1,value=False,excluded=None)]
        q=analyse_event(source,[t],e)['candidates'][0];self.assertFalse(q['tried']);self.assertFalse(q['different_variable'])
        e['tried'].append(dict(variable=1,value=True,excluded=None));self.assertTrue(analyse_event(source,[t],e)['candidates'][0]['tried'])

    def test_all_small_guard_matches_prove_only_negative_cofactors(self):
        source=native.normalize([[-1,-2,3],[-1,-2,-3]])[0];t=conditional_unit(source,[[1,True],[2,True]],Counter())
        hits=0
        for values in product((None,False,True),repeat=3):
            fixed={i+1:b for i,b in enumerate(values) if b is not None};e=self.event(source,[t],fixed)
            for q in analyse_event(source,[t],e)['candidates']:
                if q['node'] is not None:
                    hits+=1;cnf=q['node']['cnf'];n=len({abs(l) for c in cnf for l in c})
                    self.assertFalse(any(native.holds(cnf,dict(enumerate(bits,1))) for bits in product((False,True),repeat=n)))
        self.assertGreater(hits,0)

    def test_invalid_binding_and_key_rejected(self):
        source=native.normalize([[-1,-2,3],[-1,-2,-3]])[0];t=conditional_unit(source,[[1,True],[2,True]],Counter())
        e=self.event(source,[t],{1:True});bad=deepcopy(e);bad['mapping'][0][1]=999
        with self.assertRaises(ValueError):analyse_event(source,[t],bad)
        with self.assertRaises(ValueError):decode_key('[]')
        bad=deepcopy(e);bad['proposals']=[]
        with self.assertRaises(ValueError):analyse_event(source,[t],bad)

    def test_observation_does_not_change_search_or_native_payloads(self):
        for seed in range(4):
            source=generate('random-three',24,0,seed=seed+77)[0]
            a=LazyBinaryClosureSolver(node_limit=32);b=GuardProbeObserver(node_limit=32)
            try:
                x,y=attempt(a,source),attempt(b,source)
                self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
                self.assertEqual(dict(a.db.execute('SELECT id,payload FROM cnf_residual_v1')),dict(b.db.execute('SELECT id,payload FROM cnf_residual_v1')))
                for e in b.guard_report['events']:analyse_event(b.guard_report['source'],[],e)
            finally:a.close();b.close()

    def test_observation_limits_and_deleted_supports(self):
        source=generate('random-three',24,0,seed=77)[0]
        a=LazyBinaryClosureSolver(node_limit=32);b=GuardProbeObserver(node_limit=32,event_key_bytes=1)
        try:
            x,y=attempt(a,source),attempt(b,source);self.assertEqual(x['metrics'],y['metrics']);self.assertFalse(b.guard_report['events'])
            self.assertGreater(b.guard_report['counts'].get('event_limit_skips',0),0)
        finally:a.close();b.close()
        original=native.normalize([[-1,-2],[2,3,4]])[0];t=conditional_unit(original,[[1,True],[2,True]],Counter())
        b=GuardProbeObserver(templates=[t]);self.addCleanup(b.close);attempt(b,[[1,2,3]])
        self.assertEqual(b.guard_report['eligible'],[])


if __name__=='__main__':unittest.main()
