"""Checked, resumable rounds of cross-pivot implication feedback.

Each round's failed branches concern exactly the preceding augmented bank.
No-new-units is a bounded search outcome, never a SAT certificate.
"""
from copy import deepcopy
from experiments import cnf_cross_pivot_feedback as joint
k=joint.k
FORMAT='cnf-iterated-cross-pivot-v1'


def validate(source,chain,counts,*,order_source=None):
    chain=deepcopy(chain);seed,order=k._seed(source,order_source,counts)
    if type(chain) is not dict or set(chain)!={'format','seed','order_source','levels','status','reason'} or chain['format']!=FORMAT:
        raise ValueError('Invalid feedback chain')
    if chain['seed']!=list(map(list,seed)) or chain['order_source']!=list(map(list,order)) or type(chain['levels']) is not list:
        raise ValueError('Changed feedback seed or ordering')
    bank=seed;terminal=None
    for summary in chain['levels']:
        if terminal is not None:raise ValueError('Feedback after a terminal round')
        _,_,grown=joint.validate(bank,summary,counts,order_source=order)
        if summary['status']=='refuted':terminal='refuted'
        elif grown==bank:terminal='no_new_units'
        bank=grown;counts['feedback_checked_levels']+=1
    status='refuted' if terminal=='refuted' else 'unresolved'
    if chain['status']!=status or chain['reason']!=(terminal or 'round_limit'):raise ValueError('Wrong feedback outcome')
    return seed,order,bank


def discover(source,counts,*,order_source=None,previous=None,round_limit=2,pivot_limit=16,**limits):
    if any(type(v) is not int or v<1 for v in (round_limit,pivot_limit)):raise ValueError('Positive feedback limits required')
    seed,order=k._seed(source,order_source,counts);bank=seed;searches=[]
    chain=dict(format=FORMAT,seed=list(map(list,seed)),order_source=list(map(list,order)),levels=[],status='unresolved',reason='round_limit')
    if previous is not None:
        _,_,bank=validate(seed,previous,counts,order_source=order);chain=deepcopy(previous)
        if chain['status']=='refuted':counts['feedback_terminal_reuses']+=1;return chain,searches
        if chain['reason']=='no_new_units':
            # A larger search budget can find information the old pass missed.
            # Its last bank was unchanged, so replace that empty feedback round.
            chain['levels'].pop();chain['reason']='round_limit'
            counts['feedback_open_rechecks']+=1
    for _ in range(round_limit):
        fixed,_,conflict=k.native.propagate(bank,counts)
        pivots=[] if conflict is not None else list(dict.fromkeys(abs(l) for l in k.frozen.roots(order) if abs(l) not in fixed))[:pivot_limit]
        partitions=[]
        for pivot in pivots:
            part=joint.conditioned.discover(bank,pivot,counts,order_source=order,**limits);partitions.append(part)
            if part['status']=='refuted':break
        summary=joint.collect(bank,partitions,counts,order_source=order);grown=joint.bank(bank,summary['lemmas'])
        chain['levels'].append(summary);searches.append(partitions);counts['feedback_discovered_levels']+=1
        if summary['status']=='refuted':chain.update(status='refuted',reason='refuted');break
        if grown==bank:chain['reason']='no_new_units';break
        bank=grown
    return chain,searches


def compact(source,chain,counts,*,order_source=None):
    seed,order,_=validate(source,chain,counts,order_source=order_source);chain=deepcopy(chain);bank=seed
    for i,summary in enumerate(chain['levels']):
        # Earlier round contents are the exact input bindings of later rounds.
        if i==len(chain['levels'])-1:chain['levels'][i]=joint.compact(bank,summary,counts,order_source=order)
        else:bank=joint.bank(bank,summary['lemmas'])
    validate(seed,chain,counts,order_source=order);return chain
