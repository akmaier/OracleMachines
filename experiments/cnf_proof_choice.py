"""Prefer a checked ready support across two acquired frontiers.

If no matching core is ready, use the first legacy match, then the first causal
match. This is a deterministic heuristic, not minimum-cost proof selection.
Portfolio provenance references immutable, fingerprinted original indices.
"""
from collections import Counter
from unittest.mock import patch
from experiments.cnf_active_support import ActiveCoreBank
from experiments import cnf_active_support as active
from experiments.cnf_retained_causal import retained_bank
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_unsat_support import checked_subset
from experiments.cnf_incremental_support import check_proposals

FORMAT='checked-ready-support-portfolio-v1'
ORDER=('legacy','causal')


def compose(indices,bindings):
    if set(indices)!=set(ORDER) or set(bindings)!=set(ORDER):raise ValueError('Unbound portfolio banks')
    return dict(format=FORMAT,banks=bindings,
        cores=[core for name in ORDER for core in indices[name]['cores']],
        all_cores=[dict(bank=name,index=i) for name in ORDER for i in range(len(indices[name]['all_cores']))],
        origins=[dict(bank=name,index=i) for name in ORDER for i in range(len(indices[name]['origins']))])


class ProofChoiceBank:
    def __init__(self,solver,legacy,causal):
        self.solver=solver;self.counts=Counter()
        self.banks=(ActiveCoreBank(solver,legacy['cores']),retained_bank(solver,causal))
        for bank in self.banks:self.counts.update(bank.counts)
        self.offsets=(0,len(legacy['cores']))

    def _record(self,bank,hit,choice):
        return dict(**{k:v for k,v in hit.items() if k!='core'},bank=ORDER[bank],local_core=hit['core'],
            core=self.offsets[bank]+hit['core'],choice=choice)

    def reuse(self,source):
        clauses=clause_set(source,self.counts);fallback=None
        for bi,bank in enumerate(self.banks):
            for ci,(core,wanted) in enumerate(bank.cores):
                self.counts['choice_candidates']+=1;self.counts['choice_containment_clauses']+=len(wanted)
                if not wanted<=clauses:continue
                self.counts['choice_matches']+=1
                if fallback is None:fallback=(bi,ci)
                cnf,_,key=self.solver._canonical(core['source'])
                if key!=core['root']:raise ValueError('Unbound matched portfolio core')
                node=self.solver._read(key,cnf,purpose='choice_ready');self.counts['choice_ready_reads']+=1
                if node is None:continue
                if node['answer'] is not False:raise ValueError('Negative ready core required')
                inserted,root=checked_subset(self.solver,source,core['source'],self.counts)
                self.counts['ready_choices']+=1
                return self._record(bi,dict(core=ci,inserted=inserted,root=root),'ready')
        if fallback is None:return None
        bi,ci=fallback;bank=self.banks[bi];before=Counter(bank.counts);hit=bank.reuse(source)
        self.counts.update(bank.counts-before);self.counts['materialized_choices']+=1
        if hit is None or hit['core']!=ci:raise ValueError('Changed fallback order')
        return self._record(bi,hit,'materialized')


def audit_portfolio(path,records,prepared,catalogs,indices):
    """Audit both full index lineages on the frozen auditor's same snapshot."""
    if prepared.get('format')!=FORMAT:raise ValueError('Unknown portfolio format')
    if prepared!=compose(indices,prepared['banks']):raise ValueError('Changed portfolio references')
    def check_both(solver,ignored,used):
        return {name:check_proposals(solver,indices[name],used) for name in ORDER}
    with patch.object(active,'check_proposals',check_both):
        return active.audit_with_lineage(path,records,prepared,catalogs)
