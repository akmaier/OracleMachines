"""Checked two-way conditioning with resumable saturation in each branch.

A failed branch proves only its negated condition. Both checked refutations are
required to refute the seed; an open or exhausted branch is never SAT authority.
"""
from collections import Counter
from copy import deepcopy
from experiments import cnf_checked_probe_saturation as kernel
FORMAT='cnf-conditioned-saturation-v1'


def prepare(source,pivot,order_source,counts):
    seed,order=kernel._seed(source,order_source,counts)
    if type(pivot) is not int or pivot<1 or pivot not in {abs(l) for cl in seed for l in cl}:
        raise ValueError('Conditioning requires a live seed variable')
    return seed,order


def validate(source,result,counts,*,order_source=None):
    source,result,order_source=deepcopy((source,result,order_source))
    if type(result) is not dict or set(result)!={'format','seed','order_source','pivot','low','high','status'} or result['format']!=FORMAT:
        raise ValueError('Invalid conditioned saturation record')
    seed,order=prepare(source,result['pivot'],order_source,counts)
    if result['seed']!=list(map(list,seed)) or result['order_source']!=list(map(list,order)):
        raise ValueError('Changed conditioned seed or ordering')
    for name,lit in (('low',-result['pivot']),('high',result['pivot'])):
        kernel.validate((*seed,(lit,)),result[name],counts,order_source=order)
        counts['conditioned_checked_branches']+=1
    if result['low']['trace_limit']!=result['high']['trace_limit']:raise ValueError('Inconsistent branch trace bounds')
    status='refuted' if all(result[name]['status']=='refuted' for name in ('low','high')) else 'unresolved'
    if result['status']!=status:raise ValueError('Both branches are required for refutation')
    return seed,order


def discover(source,pivot,counts,*,order_source=None,previous=None,**limits):
    seed,order=prepare(source,pivot,order_source,counts);saved=deepcopy(previous)
    if saved is not None:
        validate(seed,saved,counts,order_source=order)
        if saved['pivot']!=pivot:raise ValueError('Changed conditioning pivot')
    result=dict(format=FORMAT,seed=list(map(list,seed)),order_source=list(map(list,order)),pivot=pivot,status='unresolved')
    for name,lit in (('low',-pivot),('high',pivot)):
        result[name]=kernel.discover((*seed,(lit,)),counts,order_source=order,previous=None if saved is None else saved[name],**limits)
        counts['conditioned_branch_calls']+=1
    if all(result[name]['status']=='refuted' for name in ('low','high')):result['status']='refuted'
    return result
