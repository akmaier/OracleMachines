"""Recognize a stored canonical CNF directly, then run every original proof rule.

The one-use binding transports only a checked immutable canonicalization triple
into the original verifier. It authenticates neither the certificate nor its
children. External inputs and residual transformations still use normalize.
"""
from experiments.cnf_known_quotient import KnownQuotientSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import token


def canonical_certificate(raw,counts):
    """Return the exact normalizer triple iff a JSON CNF is already canonical.

    Check strict literal/clause order, nonzero exact integers, no tautologies,
    compact positive support, and the empty-clause collapse. No sort or rename.
    Set operations have their usual Python costs; integer bit lengths matter.
    """
    counts['canonical_form_calls']+=1
    if type(raw) is not list:raise ValueError('Certificate CNF must be a list')
    clauses=[];variables=set();previous=None
    for clause in raw:
        counts['canonical_form_clauses']+=1
        if type(clause) is not list:raise ValueError('Certificate clause must be a list')
        if not clause and len(raw)!=1:raise ValueError('Noncanonical empty clause')
        seen=set();last=None
        for lit in clause:
            counts['canonical_form_literal_visits']+=1
            if type(lit) is not int or not lit:raise ValueError('CNF literals must be nonzero integers')
            if last is not None and lit<=last:raise ValueError('Noncanonical literal order')
            if -lit in seen:raise ValueError('Tautological certificate clause')
            seen.add(lit);variables.add(abs(lit));last=lit
        frozen=tuple(clause)
        if previous is not None and frozen<=previous:raise ValueError('Noncanonical clause order')
        clauses.append(frozen);previous=frozen
    # Positive, distinct support with maximum equal to cardinality is 1..n.
    # Do this before constructing names, so huge sparse IDs cannot allocate 1..max.
    if max(variables,default=0)!=len(variables):raise ValueError('Noncompact certificate variables')
    cnf=tuple(clauses);names=tuple(range(1,len(variables)+1))
    counts['canonical_form_name_variables']+=len(names)
    return cnf,names,token(cnf,counts)


class CanonicalVerifyMixin:
    def __init__(self,*args,**kwargs):
        self._verification_canonical=None
        super().__init__(*args,**kwargs)

    def _canonical(self,cnf):
        pending=self._verification_canonical
        if pending is not None and cnf is pending[0]:
            # Consume before the original verifier can visit any child. Identity
            # binds this call, not a later equal-looking or mutable input.
            self._verification_canonical=None
            self.counts['canonical_form_reuses']+=1
            return pending[1]
        return super()._canonical(cnf)

    def _verify(self,key,node):
        raw=node['cnf'];result=canonical_certificate(raw,self.counts)
        prior=self._verification_canonical;self._verification_canonical=(raw,result)
        try:return super()._verify(key,node)
        finally:self._verification_canonical=prior


class CanonicalVerifySolver(CanonicalVerifyMixin,KnownQuotientSolver):
    pass


class CanonicalVerifySnapshot(CanonicalVerifyMixin,SnapshotResidualSolver):
    pass
