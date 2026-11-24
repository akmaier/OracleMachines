from collections import Counter
from itertools import product
from copy import deepcopy
import random,unittest
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_certificate_solver import GuardCertificateSolver,transport_checked
from experiments.cnf_guard_probe_solver import GuardProbeSolver
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_fresh_mixtures import attempt,generate


class GuardCertificateTests(unittest.TestCase):
    def fixture(self):
        source=native.normalize([[-1,2],[-1,3],[-2,-3,4],[-1,-4],[1,5,6],
            [5,7,8],[-5,7,9],[5,-7,9],[-5,-7,-9]])[0]
        return source,conditional_unit(source,[[1,True]],Counter())

    def check(self,child,proof):
        s=native.ResidualSolver()
        try:
            key=native.token(child,Counter())
            s._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,proof=proof))
            self.assertFalse(s._read(key)['answer'])
        finally:s.close()

    def test_exhaustive_two_variable_formulas_and_further_conditioning(self):
        clauses=[tuple(l for l in pair if l) for pair in product((0,-1,1),(0,-2,2))]
        attempts=hits=0
        for mask in range(1<<len(clauses)):
            source=native.normalize([cl for i,cl in enumerate(clauses) if mask>>i&1])[0]
            for bits in product((None,False,True),repeat=2):
                fixed={i+1:b for i,b in enumerate(bits) if b is not None}
                t=conditional_unit(source,[list(p) for p in fixed.items()],Counter())
                if t is None:continue
                for extra in product((None,False,True),repeat=2):
                    context={i+1:b for i,b in enumerate(extra) if b is not None}
                    if any(context.get(v)!=b for v,b in t['assumptions']):continue
                    child,names=native.normalize(native.restrict_scan(source,context,Counter()))
                    proof=transport_checked(t,context,{v:i+1 for i,v in enumerate(names)},child,Counter());attempts+=1
                    if proof is not None:self.check(child,proof);hits+=1
        self.assertGreater(attempts,1000);self.assertGreater(hits,1000)

    def test_further_assignment_skips_steps_or_conflicts_early(self):
        source=native.normalize([[1],[-1,2],[-2]])[0]
        t=conditional_unit(source,[],Counter());self.assertIsNotNone(t)
        for v in (1,2):
            for b in (False,True):
                child,names=native.normalize(native.restrict_scan(source,{v:b},Counter()))
                c=Counter();proof=transport_checked(t,{v:b},{w:i+1 for i,w in enumerate(names)},child,c)
                # An empty-clause collapse can make other support clauses absent;
                # that conservative miss is handled by the native fallback.
                if proof is not None:self.check(child,proof)
        source=native.normalize([[-1,2],[-2,3],[-3,4],[-4,-1]])[0]
        t=conditional_unit(source,[[1,True]],Counter())
        totals=Counter()
        for bits in product((None,False,True),repeat=3):
            fixed={1:True,**{i+2:b for i,b in enumerate(bits) if b is not None}}
            child,names=native.normalize(native.restrict_scan(source,fixed,Counter()))
            c=Counter();proof=transport_checked(t,fixed,{v:i+1 for i,v in enumerate(names)},child,c)
            if proof is not None:self.check(child,proof)
            totals.update(c)
        self.assertGreater(totals['transport_skipped_steps'],0)
        self.assertGreater(totals['transport_early_conflicts'],0)

    def test_subset_missing_support_and_invalid_bindings_cannot_certify(self):
        source=native.normalize([[-1,-2],[2,3,4]])[0]
        t=conditional_unit(source,[[1,True],[2,True]],Counter())
        self.assertIsNone(transport_checked(t,{1:True,2:True},{3:1,4:2},(),Counter()))
        source,t=self.fixture()
        child,names=native.normalize(native.restrict_scan(source,{1:True},Counter()))
        mapping={v:i+1 for i,v in enumerate(names)}
        self.assertIsNone(transport_checked(t,{1:False},mapping,child,Counter()))
        self.assertIsNone(transport_checked(t,{1:True},{v:1 for v in names},child,Counter()))
        self.assertIsNone(transport_checked(t,{1:True},{**mapping,1:99},child,Counter()))

    def test_direct_transport_avoids_probe_propagation_and_checks_witness(self):
        source,t=self.fixture();a=GuardProbeSolver(templates=[t]);b=GuardCertificateSolver(templates=[t])
        try:
            x,y=a.solve(source),b.solve(source)
            self.assertEqual((x['answer'],x['model']),(y['answer'],y['model']))
            self.assertTrue(native.holds(source,y['model']))
            self.assertGreater(b.certificate_summary['counts']['transported_proofs'],0)
            self.assertLess(b.counts['bipolar_propagation_literal_visits'],a.counts['bipolar_propagation_literal_visits'])
            self.assertEqual(b.guard_summary,a.guard_summary)
            for key, in b.db.execute('SELECT id FROM cnf_residual_v1'):self.assertIsNotNone(b._read(key))
        finally:a.close();b.close()

    def test_empty_bank_reproduces_frozen_lazy_fallback(self):
        for seed in range(3):
            source=generate('random-three',24,0,seed=77+seed)[0]
            a=GuardProbeSolver(node_limit=32);b=GuardCertificateSolver(node_limit=32)
            try:
                x,y=attempt(a,source),attempt(b,source)
                self.assertEqual((x['status'],x['metrics']),(y['status'],y['metrics']))
                self.assertEqual(dict(a.db.execute('SELECT * FROM cnf_residual_v1')),dict(b.db.execute('SELECT * FROM cnf_residual_v1')))
                self.assertEqual(b.guard_summary['pending_end'],0);self.assertIsNone(b.certificate_records)
            finally:a.close();b.close()

    def test_limits_fall_back_and_invalid_limits_rejected(self):
        source,t=self.fixture()
        for kwargs in ({'certificate_literals':1},{'certificate_checks':1}):
            s=GuardCertificateSolver(templates=[t],**kwargs)
            try:
                r=s.solve(source);self.assertTrue(r['answer']);self.assertTrue(native.holds(source,r['model']))
                c=s.certificate_summary['counts']
                self.assertLessEqual(c.get('candidate_checks',0),s.certificate_checks)
                self.assertLessEqual(c.get('reserved_support_literals',0),s.certificate_literals)
            finally:s.close()
        for kwargs in ({'certificate_checks':False},{'certificate_literals':0}):
            with self.assertRaises(ValueError):GuardCertificateSolver(**kwargs)

    def test_sparse_input_names_and_deleted_supports(self):
        source,t=self.fixture();s=GuardCertificateSolver(templates=[t]);self.addCleanup(s.close)
        renamed=[[7*l for l in cl] for cl in source];r=s.solve(renamed)
        self.assertTrue(native.holds(renamed,r['model']))
        self.assertGreater(s.certificate_summary['counts']['transported_proofs'],0)
        s.solve([[1,2,3]]);self.assertEqual(s.guard_summary['eligible'],0)
        self.assertEqual(s.certificate_summary['counts'].get('transported_proofs',0),0)

    def test_invalid_template_and_invalid_transport_are_rejected(self):
        source,t=self.fixture();bad=deepcopy(t);bad['conflict']=10000
        s=GuardCertificateSolver(templates=[bad]);self.addCleanup(s.close)
        with self.assertRaises(ValueError):s.solve(source)
        s=GuardCertificateSolver(templates=[t]);self.addCleanup(s.close)
        with patch.object(s,'_certificate',return_value=dict(kind='units',trace=[],conflict=10000)):
            with self.assertRaises(ValueError):s.solve(source)

    def test_unlabelled_small_cases_agree_with_truth(self):
        rng=random.Random(202611240905)
        for sample in range(40):
            source=native.normalize([rng.sample([-4,-3,-2,-1,1,2,3,4],rng.randint(1,3)) for _ in range(10)])[0]
            ts=[];truth=False
            for bits in product((False,True),repeat=4):
                fixed=dict(enumerate(bits,1));truth|=native.holds(source,fixed)
                t=conditional_unit(source,[list(p) for p in fixed.items()],Counter())
                if t is not None:ts.append(t)
            s=GuardCertificateSolver(templates=ts)
            try:
                r=s.solve(source);self.assertEqual(r['answer'],truth)
                if truth:self.assertTrue(native.holds(source,r['model']))
            finally:s.close()


if __name__=='__main__':unittest.main()
