"""Exact affine completion over distinct assignments visible to leftover clauses.

This separate JSON certificate authority does not change native proof formats.
A full checked affine basis is retained; only its image on the leftover support
is enumerated. Missing extraction or a rank cap yields no verdict.
"""
from collections import Counter
from copy import deepcopy
from experiments import cnf_residual_dag as native
from experiments.cnf_affine_probe import bounded_extract
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_clause import make_space, check_space, model
from experiments.cnf_affine_negative import check_negative

FORMAT='cnf-affine-boundary-v1'
LIMITS=dict(boundary_limit=8,variables=256,clauses=4096,literals=16384,xors=65536)


def boundary_mask(cnf, affine):
    return sum(1 << (v-1) for v in {abs(l) for i in affine['leftovers'] for l in cnf[i]})


def image_basis(directions, keep, counts):
    """Select original basis vectors with independent boundary restrictions."""
    pivots={};selected=[]
    for i,vector in enumerate(directions):
        value=vector & keep;counts['boundary_projected_vectors']+=1
        while value:
            bit=value & -value
            if bit not in pivots:pivots[bit]=value;selected.append(i);break
            value ^= pivots[bit];counts['boundary_discovery_xors']+=1
    return selected


def check_image(space, keep, selected, counts):
    """Independence and spanning, checked without trusting greedy selection."""
    directions=space['directions']
    if (type(selected) is not list or any(type(i) is not int or not 0<=i<len(directions) for i in selected)
            or len(set(selected))!=len(selected)):
        raise ValueError('Invalid projected basis indices')
    pivots={}
    for i in selected:
        value=directions[i] & keep
        while value:
            bit=1 << (value.bit_length()-1)
            if bit not in pivots:pivots[bit]=value;break
            value ^= pivots[bit];counts['boundary_check_xors']+=1
        if not value:raise ValueError('Dependent projected basis')
    for vector in directions:
        value=vector & keep
        while value:
            bit=1 << (value.bit_length()-1)
            if bit not in pivots:raise ValueError('Incomplete projected image')
            value ^= pivots[bit];counts['boundary_check_xors']+=1
        counts['boundary_image_vectors_checked']+=1


def discover(source, counts=None, **limits):
    counts=Counter() if counts is None else counts
    if set(limits)-set(LIMITS):raise ValueError('Unknown boundary limit')
    limits={**LIMITS,**limits}
    if any(type(v) is not int or v<(0 if k=='boundary_limit' else 1) for k,v in limits.items()) or limits['boundary_limit']>8:
        raise ValueError('Invalid boundary limits')
    cnf,names=native.normalize(source,counts);n=len(names)
    record=dict(status='size-cap',variables=n,limits=limits)
    counts['boundary_input_literals']+=sum(map(len,cnf))
    if n>limits['variables'] or len(cnf)>limits['clauses'] or sum(map(len,cnf))>limits['literals']:return None,record
    affine=bounded_extract(cnf,counts,limits['xors'])
    if affine is None:record['status']='xor-cap';return None,record
    summary=check_affine(cnf,affine,counts);record.update(summary=summary,free=n-summary['rank'])
    proof=dict(format=FORMAT,cnf=list(map(list,cnf)),affine=affine,space=None,image=None,decision=None)
    if summary['inconsistent']:
        row=next(i for i,r in enumerate(affine['reductions']) if (r['mask'],r['rhs'])==(0,1))
        proof['decision']=dict(kind='linear-conflict',row=row);record['status']='linear-conflict'
    elif not affine['equations']:
        record['status']='no-equations';return None,record
    else:
        space=make_space(n,affine,counts);check_space(n,affine,space,counts)
        keep=boundary_mask(cnf,affine);selected=image_basis(space['directions'],keep,counts)
        check_image(space,keep,selected,counts);b=len(selected);record['boundary_rank']=b
        if b>limits['boundary_limit']:record['status']='boundary-cap';return None,record
        proof.update(space=space,image=selected);rejected=[];candidate=space['particular']
        packed=[]
        for cid in affine['leftovers']:
            pos=neg=0
            for lit in cnf[cid]:
                counts['boundary_packed_literals']+=1
                if lit>0:pos|=1<<(lit-1)
                else:neg|=1<<(-lit-1)
            packed.append((cid,pos,neg))
        for i in range(1<<b):
            if i:candidate ^= space['directions'][selected[(i & -i).bit_length()-1]];counts['boundary_candidate_xors']+=1
            counts['boundary_candidates']+=1;failed=None
            for cid,pos,neg in packed:
                counts['boundary_clause_checks']+=1
                if not (candidate & pos or ~candidate & neg):failed=cid;break
            if failed is None:
                proof['decision']=dict(kind='model',mask=candidate);record['status']='model';break
            rejected.append(failed)
        else:
            proof['decision']=dict(kind='exhaustion',rejected=rejected);record['status']='space-exhausted'
    check_certificate(source,proof,counts)
    return deepcopy(proof),record


def check_certificate(source, proof, counts=None):
    """Check full source equivalence, image completeness, and verdict independently.

    Exhaustion uses binary coefficients rather than the producer's Gray walk.
    The rejection at Gray index j belongs to coefficient vector j xor (j>>1).
    All inputs are rechecked even if a caller already knows the root.
    """
    counts=Counter() if counts is None else counts
    cnf,names=native.normalize(source,counts);n=len(names)
    if (type(proof) is not dict or set(proof)!={'format','cnf','affine','space','image','decision'}
            or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf))):
        raise ValueError('Invalid or source-mismatched boundary proof')
    summary=check_affine(cnf,proof['affine'],counts);d=proof['decision']
    if type(d) is not dict:raise ValueError('Invalid boundary decision')
    if d.get('kind')=='linear-conflict':
        if proof['space'] is not None or proof['image'] is not None:raise ValueError('Unexpected conflict space')
        check_negative(cnf,n,dict(affine=proof['affine'],decision=d),counts)
        return dict(answer=False,model=None,boundary_rank=None,free=n-summary['rank'])
    if summary['inconsistent']:raise ValueError('Inconsistent affine space')
    space=proof['space'];check_space(n,proof['affine'],space,counts)
    keep=boundary_mask(cnf,proof['affine']);selected=proof['image'];check_image(space,keep,selected,counts)
    b=len(selected)
    if b>8:raise ValueError('Boundary exceeds versioned rank limit')
    if d.get('kind')=='model':
        if set(d)!={'kind','mask'} or type(d['mask']) is not int or not 0<=d['mask']<1<<n:
            raise ValueError('Invalid model mask')
        witness=model(d['mask'],n)
        if not native.holds(cnf,witness):raise ValueError('Model violates source')
        counts['boundary_model_literals_checked']+=sum(map(len,cnf))
        result={name:witness[i] for i,name in enumerate(names,1)}
        return dict(answer=True,model=result,boundary_rank=b,free=n-summary['rank'])
    if d.get('kind')!='exhaustion' or set(d)!={'kind','rejected'}:raise ValueError('Invalid exhaustion')
    rejected=d['rejected'];leftovers=set(proof['affine']['leftovers'])
    if (type(rejected) is not list or len(rejected)!=1<<b or any(type(cid) is not int or cid not in leftovers for cid in rejected)):
        raise ValueError('Missing boundary coverage')
    # Direct binary reconstruction and inverse Gray indexing differ from discovery.
    for coeff in range(1<<b):
        mask=space['particular']
        for bit,index in enumerate(selected):
            if coeff>>bit & 1:mask ^= space['directions'][index];counts['boundary_verify_candidate_xors']+=1
        gray_index=coeff;shift=coeff>>1
        while shift:gray_index ^= shift;shift >>= 1
        clause=cnf[rejected[gray_index]]
        if any(bool(mask & (1<<(abs(l)-1)))==(l>0) for l in clause):raise ValueError('Rejection clause is satisfied')
        counts['boundary_rejections_checked']+=1;counts['boundary_rejection_literals_checked']+=len(clause)
    return dict(answer=False,model=None,boundary_rank=b,free=n-summary['rank'])
