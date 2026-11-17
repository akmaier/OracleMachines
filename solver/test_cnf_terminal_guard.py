from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase,main
from unittest.mock import patch
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard
from experiments.cnf_proof_choice import ProofChoiceBank
from experiments.cnf_terminal_guard import TerminalGuardSelector


class TerminalGuardTests(TestCase):
    def fixture(self,recursive=False):
        s=ResidualSolver(leaves=False,decompose=False,matching=False,positive_subsumption=False);self.addCleanup(s.close)
        source=([list(c) for c in product(*[(-i,i) for i in (1,2,3)])] if recursive else [[1],[-1]])+[[8,9],[-8,10]]
        entries=[]
        for c in [[8],[9]]:
            stronger=source+[c];r=s.solve(stronger);entries.append(dict(source=stronger,root=r['root']))
        origin=source+[[20]];s.solve(origin)
        core=CausalSupportExtractor(s,materialize=False).source_core(origin)
        extensions=ExtensionBank(entries);guards=list(extensions.candidates(source,Counter()))
        return s,source,extensions,guards,core

    def bank(self,s,cores):
        return ProofChoiceBank(s,dict(cores=[]),dict(cores=cores,deferred=True,causal_unit_slicing=True))

    def test_terminal_match_derives_one_core_then_normal_target(self):
        s,source,ext,guards,core=self.fixture();bank=self.bank(s,[core]);selector=TerminalGuardSelector();before=s.archive_storage()[0]
        self.assertIsNone(s._read(core['root']))
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh terminal search')):
            chosen,trace=selector.select(s,ext,source,guards[0],bank)
            self.assertEqual(chosen,guards[1]);self.assertEqual(trace['attempts'][0]['status'],'terminal')
            self.assertEqual(s.archive_storage()[0]-before,1)
            _,target=check_guard(s,source,chosen);self.assertEqual(bank.reuse(target)['choice'],'ready')
            self.assertFalse(s.solve(target)['answer']);self.assertLessEqual(s.archive_storage()[0]-before,2)
        self.assertEqual(selector.counts['terminal_materialization_nodes'],1)

    def test_unit_origin_with_child_is_rejected_without_publication(self):
        s,source,ext,guards,core=self.fixture()
        # Treat the index as an untrusted hint: even a checked UNSAT origin
        # must have the terminal form before this selector may derive from it.
        recursive=[list(c) for c in product(*[(-i,i) for i in (20,21)])]+[[40]]
        s.leaves=True
        core=deepcopy(core);core['origin']=s.solve(recursive)['root'];node=s._read(core['origin'])
        self.assertIsNone(s._read(core['root']))
        self.assertEqual(node['proof']['kind'],'units');self.assertIsNone(node['proof'].get('conflict'))
        with patch.object(s,'_store',side_effect=AssertionError('Recursive publication')),patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            chosen,trace=TerminalGuardSelector().select(s,ext,source,guards[0],self.bank(s,[core]))
        self.assertIsNone(chosen);self.assertEqual(trace['attempts'][0]['terminal_checks'],[dict(core=0,terminal=False)])

    def test_later_ready_match_precedes_pending_terminal(self):
        s,source,ext,guards,core=self.fixture();other=[[1],[-1],[-8,10]];r=s.solve(other)
        ready=dict(source=other,root=r['root'],origin=r['root'])
        with patch.object(s,'_store',side_effect=AssertionError('Unneeded terminal publication')):
            chosen,trace=TerminalGuardSelector().select(s,ext,source,guards[0],self.bank(s,[core,ready]))
        self.assertEqual(chosen,guards[1]);self.assertEqual(trace['attempts'][0]['status'],'ready')
        self.assertIsNone(s._read(core['root']))

    def test_zero_budget_never_inspects_or_publishes_terminal(self):
        s,source,ext,guards,core=self.fixture()
        with patch.object(s,'_store',side_effect=AssertionError('Zero-budget publication')):
            chosen,trace=TerminalGuardSelector(0).select(s,ext,source,guards[0],self.bank(s,[core]))
        self.assertIsNone(chosen);self.assertEqual(trace['attempts'],[])

    def test_missing_origin_is_only_a_hint(self):
        s,source,ext,guards,core=self.fixture();core=deepcopy(core);core['origin']='missing'
        with patch.object(s,'_store',side_effect=AssertionError('Missing origin publication')):
            chosen,trace=TerminalGuardSelector().select(s,ext,source,guards[0],self.bank(s,[core]))
        self.assertIsNone(chosen);self.assertFalse(trace['selected'])

    def test_positive_origin_cannot_certify_terminal(self):
        s,source,ext,guards,core=self.fixture();core=deepcopy(core);core['origin']=s.solve([[30]])['root']
        with self.assertRaises(ValueError):TerminalGuardSelector().select(s,ext,source,guards[0],self.bank(s,[core]))


if __name__=='__main__':main()
