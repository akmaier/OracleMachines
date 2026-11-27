"""Strict external CNF admission and a fixed existing frontier continuation.

Publisher labels and benchmark metadata are never passed to discovery/checking.
This adapter does not change the earlier ranking, limits, or local certificates.
"""
from collections import Counter
import re
from experiments import cnf_factor_conditioning as factors
previous=factors.previous
native=factors.native
FORMAT='cnf-external-factor-cutsets-v1'


def parse_dimacs(text):
    if type(text) is not str or len(text)>10*1024*1024:raise ValueError('Invalid or oversized DIMACS text')
    header=None;clauses=[];current=[];ended=False;sentinel=False
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('c'):continue
        tokens=line.split()
        if tokens[0]=='p':
            if header is not None or clauses or current or ended or len(tokens)!=4 or tokens[:2]!=['p','cnf'] or any(not re.fullmatch(r'[0-9]+',x) for x in tokens[2:]):raise ValueError('Invalid DIMACS header')
            header=tuple(map(int,tokens[2:]))
            if any(x>1000000 for x in header):raise ValueError('DIMACS admission limit')
            continue
        if header is None:raise ValueError('Missing DIMACS header')
        if tokens==['%']:
            if ended or current or len(clauses)!=header[1]:raise ValueError('Premature or duplicate DIMACS terminator')
            ended=True;continue
        if ended:
            # SATLIB's legacy files may append one zero after a percent marker.
            if tokens!=['0'] or sentinel:raise ValueError('Data after DIMACS terminator')
            sentinel=True;continue
        for token in tokens:
            if not re.fullmatch(r'-?[0-9]+',token):raise ValueError('Invalid DIMACS literal')
            literal=int(token)
            if abs(literal)>header[0]:raise ValueError('Out-of-range DIMACS variable')
            if literal:current.append(literal)
            else:clauses.append(current);current=[]
            if len(clauses)>header[1]:raise ValueError('Too many DIMACS clauses')
    if header is None or current or len(clauses)!=header[1]:raise ValueError('Incomplete DIMACS instance')
    return clauses,dict(variables=header[0],clauses=header[1])


def targets(context):
    return [i for i,n in enumerate(context['nodes']) if n['kind']=='leaf' and n['status']=='unresolved' and n['depth']==0 and n['refinement'] is not None]


def admitted(source,prefix):
    normalized,_=native.normalize(source)
    return all(len(c)<=prefix['limits']['bag_limit'] for c in normalized)


def discover(source,counts=None,*,expand=False):
    counts=Counter() if counts is None else counts
    if type(expand) is not bool:raise ValueError('Invalid expansion policy')
    context,diagnostic=previous.discover(source,counts,mode='two')
    base=previous.check_certificate(source,context,counts);status=context['status'];model=base['model'];attempts=[];details=[]
    if expand and status=='unresolved':
        for target in targets(context):
            local,prefix,_=factors.frontier(source,context,target,counts)
            certificate=None;reason='leaf-width';diag=None;result=dict(answer=None,model=None)
            if admitted(local,prefix):
                certificate,diag=factors.discover(local,prefix,counts)
                got=factors.check(local,prefix,certificate,counts)
                result=factors.lift_root(source,context,target,local,prefix,got,counts);reason=certificate['status']
            attempts.append(dict(target=target,certificate=certificate));details.append(dict(target=target,reason=reason,diagnostic=diag))
            if result['answer'] is True:status='sat';model=result['model'];break
    _,names=native.normalize(source,counts)
    proof=dict(format=FORMAT,expand=expand,context=context,attempts=attempts,status=status,model=None if model is None else [model[v] for v in names])
    check(source,proof,counts)
    return proof,dict(initial=diagnostic,expansion=details,eligible=len(targets(context)) if context['status']=='unresolved' else 0)


def check(source,proof,counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','expand','context','attempts','status','model'} or proof['format']!=FORMAT or type(proof['expand']) is not bool or type(proof['attempts']) is not list:raise ValueError('Invalid external-input certificate')
    context=proof['context']
    if type(context) is not dict or context.get('mode')!='two' or context.get('limits')!=previous.DEFAULTS:raise ValueError('Changed fixed baseline policy')
    got=previous.check_certificate(source,context,counts);status=context['status'];model=got['model'];attempts=proof['attempts']
    eligible=targets(context) if proof['expand'] and status=='unresolved' else []
    if len(attempts)>len(eligible) or any(type(a) is not dict or set(a)!={'target','certificate'} or type(a['target']) is not int for a in attempts) or [a['target'] for a in attempts]!=eligible[:len(attempts)]:raise ValueError('Changed expansion target order')
    for attempt in attempts:
        if status!='unresolved':raise ValueError('Expansion after checked root witness')
        target=attempt['target'];local,prefix,_=factors.frontier(source,context,target,counts);certificate=attempt['certificate']
        if not admitted(local,prefix):
            if certificate is not None:raise ValueError('Unmaterialized wide frontier')
        else:
            if type(certificate) is not dict or certificate.get('cut_limit')!=4 or certificate.get('clause_width')!=4:raise ValueError('Changed fixed cutset policy')
            leaf=factors.check(local,prefix,certificate,counts)
            result=factors.lift_root(source,context,target,local,prefix,leaf,counts)
            if result['answer'] is True:status='sat';model=result['model']
    if status=='unresolved' and len(attempts)!=len(eligible):raise ValueError('Unreported frontier attempt')
    _,names=native.normalize(source,counts);expected=None if model is None else [model[v] for v in names]
    if proof['status']!=status or proof['model']!=expected or (model is not None and (type(proof['model']) is not list or any(type(v) is not bool for v in proof['model']))):raise ValueError('Changed external root verdict or model')
    if model is not None and not native.holds(source,model):raise ValueError('External witness violates source')
    return dict(answer=None if status=='unresolved' else status=='sat',model=model)
