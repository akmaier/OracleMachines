"""Publish a fully checked SAT witness before solving a one-clause deletion.

Candidate matching uses the frozen ExtensionBank and common input coordinates.
A transferred answer is stored as an ordinary self-contained SAT certificate.
No UNSAT conclusion follows from a model, and no structural flag is a premise.
"""
from collections import Counter
import json
from experiments.cnf_clause_deletion_guard import removed_clause
from experiments.cnf_residual_dag import FORMAT as RESIDUAL_FORMAT, holds

FORMAT='checked-clause-deletion-witness-v1'
FIELDS={'format','stronger','stronger_root','removed_clause'}


def check_witness(solver, source, certificate, counts=None):
    counts=Counter() if counts is None else counts
    if type(certificate) is not dict or set(certificate)!=FIELDS or certificate['format']!=FORMAT:
        raise ValueError('Invalid witness transfer')
    clause=removed_clause(certificate['stronger'],source,counts)
    if json.dumps(clause)!=json.dumps(certificate['removed_clause']):raise ValueError('Wrong removed clause')
    normalized,names,root=solver._canonical(certificate['stronger'])
    if root!=certificate['stronger_root']:raise ValueError('Wrong stronger root')
    node=solver._read(root,normalized,purpose='witness_template')
    if node is None or node['answer'] is not True:raise ValueError('Transfer requires a checked SAT witness')
    model={old:node['model'][i] for i,old in enumerate(names)}
    if not holds(certificate['stronger'],model) or not holds(source,model):
        raise ValueError('Transferred model violates its source or query')
    counts['witness_validation_literals']+=sum(map(len,certificate['stronger']))+sum(map(len,source))
    counts['verified_witness_transfers']+=1
    return {v:model.get(v,False) for v in {abs(l) for c in source for l in c}}


def reuse_witness(solver, bank, source, counts=None):
    """Return provenance on a new publication; a miss never supplies a verdict."""
    counts=Counter() if counts is None else counts
    normalized,names,key=solver._canonical(source)
    if solver._read(key,normalized,purpose='witness_query') is not None:
        counts['witness_query_already_known']+=1
        return None
    for proposal in bank.candidates(source,counts):
        cnf,_,root=solver._canonical(proposal['stronger'])
        if root!=proposal['stronger_root']:raise ValueError('Unbound witness candidate')
        node=solver._read(root,cnf,purpose='witness_template')
        if node is None or node['answer'] is not True:
            counts['witness_nonpositive_or_missing_candidates']+=1
            continue
        certificate={**proposal,'format':FORMAT}
        model=check_witness(solver,source,certificate,counts)
        stored=dict(format=RESIDUAL_FORMAT,cnf=[list(c) for c in normalized],answer=True,
                    model=[model[v] for v in names])
        # The existing residual checker verifies this independent query witness.
        solver._store(key,stored)
        counts['published_witness_roots']+=1
        counts['published_witness_variables']+=len(names)
        return certificate
    return None
