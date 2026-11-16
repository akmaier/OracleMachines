"""Optional SAT reuse across one clause deletion, requiring checked UNSAT.

If F = G and C is UNSAT, every model of G falsifies every literal of C.
Thus only G restricted by not C needs solving. Structural coverage is never
used as an UNSAT premise. Discovery is exact in shared input coordinates.
"""
from collections import Counter
import json
from experiments.cnf_residual_dag import restrict, holds

FORMAT='checked-clause-deletion-guard-v1'


def clause_set(source, counts):
    result=set()
    for clause in source:
        counts['guard_input_literals']+=len(clause)
        if any(type(l) is not int or not l for l in clause):raise ValueError('Invalid literal')
        items=frozenset(clause)
        if any(-l in items for l in items):raise ValueError('Tautological clause is outside this interface')
        result.add(tuple(sorted(items)))
    return result


def removed_clause(stronger, weaker, counts=None):
    counts=Counter() if counts is None else counts
    a,b=clause_set(stronger,counts),clause_set(weaker,counts)
    counts['guard_clause_comparisons']+=len(a)+len(b)
    if not b<a or len(a-b)!=1:raise ValueError('Expected exactly one deleted clause in common coordinates')
    return list(next(iter(a-b)))


class ExtensionBank:
    """Small explicit candidate bank; proposals never certify UNSAT."""
    def __init__(self, templates, counts=None):
        counts=Counter() if counts is None else counts
        self.groups={}
        for item in templates:
            value=json.loads(json.dumps(item));clauses=clause_set(value['source'],counts)
            self.groups.setdefault(len(clauses),[]).append((value,clauses))
            counts['guard_bank_entries']+=1
    def candidates(self, source, counts):
        clauses=clause_set(source,counts)
        for item,other in self.groups.get(len(clauses)+1,()):
            counts['guard_candidates_compared']+=1
            counts['guard_clause_comparisons']+=len(clauses)
            if clauses<other:
                counts['guard_candidates_matched']+=1
                yield dict(format=FORMAT,stronger=item['source'],stronger_root=item['root'],
                           removed_clause=list(next(iter(other-clauses))))


def check_guard(solver, source, certificate, counts=None):
    counts=Counter() if counts is None else counts
    if (type(certificate) is not dict or set(certificate)!=
        {'format','stronger','stronger_root','removed_clause'} or certificate['format']!=FORMAT):
        raise ValueError('Invalid deletion guard')
    clause=removed_clause(certificate['stronger'],source,counts)
    if clause!=certificate['removed_clause']:raise ValueError('Wrong removed clause')
    normalized,_,root=solver._canonical(certificate['stronger'])
    if root!=certificate['stronger_root']:raise ValueError('Wrong stronger root')
    node=solver._read(root,normalized,purpose='guard')
    if node is None or node['answer'] is not False:raise ValueError('Guard requires an existing checked UNSAT proof')
    assignment={abs(l):l<0 for l in clause}
    target=restrict(source,assignment,counts)
    counts['verified_deletion_guards']+=1
    counts['guard_forced_variables']+=len(assignment)
    return assignment,target


def propose(solver, bank, source, counts=None):
    counts=Counter() if counts is None else counts
    for certificate in bank.candidates(source,counts):
        normalized,_,root=solver._canonical(certificate['stronger'])
        if root!=certificate['stronger_root']:raise ValueError('Unbound candidate root')
        node=solver._read(root,normalized,purpose='guard')
        if node is None or node['answer'] is not False:
            counts['guard_nonnegative_or_missing_candidates']+=1
            continue
        check_guard(solver,source,certificate,counts)
        return certificate
    return None


def lift(source, assignment, model):
    if type(model) is not dict or any(type(v) is not bool for v in model.values()):raise ValueError('Invalid target model')
    if any(v in model and model[v]!=b for v,b in assignment.items()):raise ValueError('Conflicting forced value')
    result={abs(l):False for c in source for l in c};result.update(model);result.update(assignment)
    if not holds(source,result):raise ValueError('Lifted model violates edited source')
    return result


def replay(solver, source, certificate, child):
    """Check a sidecar result; caller may disable _expand to require cold replay."""
    if certificate is None:assignment={};target=source
    else:assignment,target=check_guard(solver,source,certificate)
    result=solver.solve(target)
    if result['answer']!=child['answer'] or result['root']!=child['root']:
        raise ValueError('Changed child answer or identity')
    # Stored JSON converts model variable keys to strings.
    if json.dumps(result['model'],sort_keys=True)!=json.dumps(child['model'],sort_keys=True):
        expected=None if child['model'] is None else {int(k):v for k,v in child['model'].items()}
        if result['model']!=expected:raise ValueError('Changed child model')
    model=lift(source,assignment,result['model']) if result['answer'] else None
    return dict(answer=result['answer'],model=model,root=result['root'])
